"""collect (PRH + OpenStreetMap) -> merge -> opt-out -> read websites -> channels -> score -> private/."""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import json
import time
from pathlib import Path

from . import compliance, dashboard, enrich, geo, merge, score
from .log import say
from .sources import SourceResult, osm, prh

ALL = {"all", "finland", "suomi", "koko suomi", ""}


def area_spec(cfg: dict, g: geo.Geo) -> tuple[list[str] | None, set[str], set[str]]:
    """(municipalities to query, or None for the whole country; municipality filter; region filter).

    `area` may be "all", or a list mixing municipalities (Vantaa) and regions (Uusimaa, Pirkanmaa).
    """
    raw = cfg.get("area", "all")
    names = [raw] if isinstance(raw, str) else list(raw or [])
    if not names or any(str(n).strip().lower() in ALL for n in names):
        return None, set(), set()
    regions = {n.strip().lower() for n in names if g.is_region(n)}
    munis = {n.strip().lower() for n in names if not g.is_region(n)}
    query = None if regions else sorted(n.strip() for n in names)
    return query, munis, regions


def collect(cfg: dict, root: Path, only: set[str] | None = None, area: list[str] | None = None) -> list[SourceResult]:
    segs = cfg["segments"]
    # The OSM cache holds place names, and a sole trader's place may carry the owner's name: keep it private.
    jobs = {"prh": (prh.fetch, (area, segs)), "osm": (osm.fetch, (area, segs, root / "private" / "osm-cache.json",
                                                 cfg.get("osm_refresh_days", 0)))}
    results = []
    with cf.ThreadPoolExecutor(2) as ex:
        futs = {n: ex.submit(fn, *a) for n, (fn, a) in jobs.items() if only is None or n in only}
        for n, f in futs.items():
            try:
                results.append(f.result())
            except Exception as e:   # a broken source must not sink the run
                results.append(SourceResult(name=n, ok=False, error=f"{type(e).__name__}: {e}"))
    return results


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def run(cfg: dict, root: Path, today: dt.date | None = None, only: set[str] | None = None,
        read_sites: bool = True, segments: set[str] | None = None) -> dict:
    today = today or dt.date.today()
    private, data_dir = root / "private", root / "data"
    if segments:
        cfg = dict(cfg, segments={k: v for k, v in cfg["segments"].items() if k in segments})
    g = geo.Geo(data_dir / "geo.json")
    if not g.ok:
        geo.download(data_dir / "geo.json")
        g = geo.Geo(data_dir / "geo.json")
    query_area, want_munis, want_regions = area_spec(cfg, g)
    say("Collecting: " + (", ".join(query_area) if query_area else "the whole country")
        + f", {len(cfg['segments'])} kinds of business")
    results = collect(cfg, root, only, query_area)
    if results and not any(r.ok for r in results):
        raise RuntimeError("every source failed: " + "; ".join(f"{r.name}: {r.error}" for r in results))
    by = {r.name: r.items for r in results}
    leads, mstats = merge.merge(by.get("prh", []), by.get("osm", []))
    say(f"Merged: {len(leads):,} businesses ({mstats['matched']:,} map places matched to a company)")
    funnel = {"companies": mstats["companies"], "places": mstats["places"], "matched": mstats["matched"],
              "merged": len(leads), "opted_out": 0, "expired": 0, "low_score": 0}

    for b in leads:
        b.municipality, b.region = g.names(g.locate(b.postcode, b.lat, b.lon, b.city))
    # PRH's location filter matches any address; keep businesses whose place is in the area.
    before = len(leads)
    if want_munis or want_regions:
        leads = [b for b in leads if (b.municipality or b.city).lower() in want_munis
                 or b.region.lower() in want_regions]
    funnel["outside_area"] = before - len(leads)

    optout = compliance.OptOut(data_dir / "optout.json")
    ledger = load_json(data_dir / "seen.json", {})   # id -> {"first": date, "contacted": date?, "expired": bool}
    # Statuses you synced from the dashboard (also how they reach the online radar, via data/shared.enc).
    for lid, c in load_json(data_dir / "contacts.json", {}).items():
        led = ledger.setdefault(lid, {"first": c.get("contacted") or today.isoformat()})
        if c.get("contacted") and c.get("contacted") >= led.get("contacted", ""):
            led.update(contacted=c["contacted"], status=c.get("status", ""))
            led.pop("expired", None)
    kept = []
    for b in leads:
        if optout.blocked(b):
            funnel["opted_out"] += 1
            continue
        kept.append(b)
    leads = kept

    ecfg = cfg.get("enrichment", {})
    cache = enrich.SiteCache(private / "sites.json", ecfg.get("refresh_days", 30))
    guesses = enrich.DomainGuesses(data_dir / "domains.json")
    if read_sites and ecfg.get("enabled", True):
        # Website work gets a fixed time, so a run always finishes; the rest is read on the next run.
        deadline = time.monotonic() + ecfg.get("max_minutes", 30) * 60
        guesses.run(leads, ecfg.get("max_domain_guesses_per_run", 250), deadline)
        guesses.save()
        cache.crawl(leads, ecfg.get("max_sites_per_run", 300), ecfg.get("max_pages_per_site", 4), deadline)
        cache.save()
    for b in leads:
        if b.domain:
            enrich.apply(b, cache.get(b.domain))
    # A second check now that we know the emails and phones from the website.
    blocked = {b.id for b in leads if optout.blocked(b)}
    funnel["opted_out"] += len(blocked)
    leads = [b for b in leads if b.id not in blocked]

    retention = cfg.get("retention_days", 180)
    out = []
    for b in leads:
        led = ledger.setdefault(b.id, {"first": today.isoformat()})
        b.first_seen = led["first"]
        # Delete after the retention period unless a conversation started (reply, meeting, customer).
        talking = led.get("status") in ("replied", "meeting", "customer")
        last = led.get("contacted") or led["first"]
        if led.get("expired") or (not talking and (today - dt.date.fromisoformat(last)).days > retention):
            led["expired"] = True
            funnel["expired"] += 1
            continue
        b.channels = compliance.channels(b)
        score.score(b, cfg, today)
        if b.score < cfg.get("min_score", 0):
            funnel["low_score"] += 1
            continue
        out.append(b)
    out.sort(key=lambda b: (-b.score, b.name.lower()))
    # Keep website data only for businesses still shown; forget the rest.
    cache.prune({b.domain for b in out if b.domain})
    cache.save()

    counts: dict[str, int] = {}
    for b in out:
        counts[b.segment] = counts.get(b.segment, 0) + 1
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "date": today.isoformat(),
        "first_run": all(v["first"] == today.isoformat() for v in ledger.values()),
        "new_today": sum(1 for b in out if b.first_seen == today.isoformat()),
        "funnel": funnel,
        "sites": dict(cache.stats, guessed=guesses.found),
        "sources": [{"name": r.name, "ok": r.ok, "fetched": len(r.items), "detail": r.detail, "error": r.error}
                    for r in results],
        "segments": {k: {"label": v.get("label", k), "count": counts.get(k, 0)} for k, v in cfg["segments"].items()},
        "area": "whole country" if query_area is None and not want_regions else ", ".join(
            sorted(want_regions | want_munis)).title(),
        "offers": cfg.get("offers", {}),
        "sender": cfg.get("sender", {}),
        "outreach": cfg.get("outreach", {}),
        "follow_up_days": cfg.get("follow_up_days", 10),
        "audit": cfg.get("audit", {}),
        "email_daily_limit": cfg.get("email_daily_limit", 25),
        "leads": [b.to_public() for b in out],
    }
    private.mkdir(parents=True, exist_ok=True)
    (private / "leads.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (private / "dashboard.html").write_text(dashboard.build(payload), encoding="utf-8")
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "seen.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    return payload
