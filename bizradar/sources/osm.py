"""OpenStreetMap via the Overpass API (data © OpenStreetMap contributors, ODbL 1.0).

Finds the places themselves (cafés, restaurants, salons...), including sole traders that are not in PRH open
data. Tags often include website, phone and opening hours; a business ID only rarely.
Attribution "© OpenStreetMap contributors" must be shown wherever the data is displayed.
"""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

from .. import http
from ..log import say
from ..models import Business
from ..text import domain_of, legal_form_from_name, normalize_phone, normalize_url
from . import SourceResult, osm_extract

ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]


def build_query(municipality: str | None, segments: dict) -> str:
    """Places with these tags in one municipality, or in the whole of Finland when municipality is None."""
    parts = []
    for s in segments.values():
        for tag in s.get("osm", []):           # "shop=hairdresser"
            k, v = tag.split("=", 1)
            parts.append(f'nwr(area.a)["{k}"="{v}"]["name"];')
    area = (f'area["name"="{municipality}"]["admin_level"="8"]["boundary"="administrative"]->.a;' if municipality
            else 'area["ISO3166-1"="FI"]["admin_level"="2"]->.a;')
    return f'[out:json][timeout:{120 if municipality else 240}];{area}({"".join(parts)});out tags center;'



def segment_of(tags: dict, segments: dict) -> str:
    for key, s in segments.items():
        for tag in s.get("osm", []):
            k, v = tag.split("=", 1)
            if tags.get(k) == v:
                return key
    return ""


def parse(el: dict, municipality: str, segments: dict) -> Business | None:
    t = el.get("tags", {})
    name = t.get("name", "").strip()
    seg = segment_of(t, segments)
    if not name or not seg or t.get("disused") or t.get("opening_hours") == "closed":
        return None
    if t.get("brand") or t.get("brand:wikidata"):   # chains (Hesburger, Robert's Coffee...) decide centrally
        return None
    ref = f"{el['type']}/{el['id']}"
    b = Business(id=f"osm:{ref}", name=name, segment=seg, osm_ref=ref,
                 city=t.get("addr:city", municipality), postcode=t.get("addr:postcode", ""),
                 street=" ".join(x for x in (t.get("addr:street"), t.get("addr:housenumber")) if x),
                 opening_hours=t.get("opening_hours", ""))
    c = el.get("center") or el
    b.lat, b.lon = c.get("lat"), c.get("lon")
    form = legal_form_from_name(name)
    if form != "unknown":
        b.legal_form, b.legal_form_source = form, "name"
    bid = t.get("ref:FI:ytunnus") or t.get("ref:vatin", "").replace("FI", "")
    if bid and len(bid) == 8 and "-" not in bid:
        bid = bid[:7] + "-" + bid[7:]
    if bid:
        b.business_id = bid
    site = t.get("website") or t.get("contact:website") or t.get("url")
    if site:
        b.website, b.domain = normalize_url(site), domain_of(site)
        b.note("website", "osm", ref)
    phone = normalize_phone(t.get("phone") or t.get("contact:phone") or "")
    if phone:
        b.phone, b.phone_source = phone, "OpenStreetMap"
        b.note("phone", "osm", ref)
    b.instagram = t.get("contact:instagram", "")
    b.facebook = t.get("contact:facebook", "")
    # OSM email tags are copied from somewhere; the radar only uses emails it sees on the business's own site.
    b.signals["osm_email_tag"] = bool(t.get("email") or t.get("contact:email"))
    b.note("place", "osm", ref)
    return b


def _overpass(q: str, read_timeout: int = 90) -> dict | None:
    """Public Overpass servers are often busy: try each mirror once, with a pause between."""
    last = ""
    for ep in ENDPOINTS:
        try:
            return http.request("POST", ep, data={"data": q}, timeout=(10, read_timeout), tries=1)
        except http.FetchError as e:
            last = str(e)
            time.sleep(5)
    raise http.FetchError(last)


def box_query(box: tuple, segments: dict, timeout: int = 90) -> str:
    """Places with these tags inside a (south, west, north, east) box, in Finland only (the boxes of border
    regions reach into Sweden, Norway and Russia)."""
    s, w, n, e = box
    parts = []
    for seg in segments.values():
        for tag in seg.get("osm", []):
            k, v = tag.split("=", 1)
            parts.append(f'nwr(area.a)({s},{w},{n},{e})["{k}"="{v}"]["name"];')
    area = 'area["ISO3166-1"="FI"]["admin_level"="2"]->.a;'
    return f'[out:json][timeout:{timeout}];{area}({"".join(parts)});out tags center;'


def _fetch_regions(tiles: dict, segments: dict, cache: dict, refresh_days: int, save, res: SourceResult,
                   budget_minutes: float = 60) -> tuple[list[str], int, int]:
    """Whole country, one region at a time: small queries the busy public servers accept, where one query for
    all of Finland times out. Each region asks for every kind still missing at once; if that fails, one kind at
    a time. Answers are cached per (region, kind). Returns (errors, reused, stale)."""
    segs = {k: s for k, s in segments.items() if s.get("osm")}
    deadline = time.monotonic() + budget_minutes * 60
    errors, reused, stale, fails = [], 0, 0, 0
    seen: set[str] = set()
    today = dt.date.today()

    def ck(region, key):
        return f"R:{region}|{key}|{','.join(segs[key]['osm'])}"

    def ask(region, box, keys) -> bool:
        nonlocal fails
        if time.monotonic() > deadline:
            return False
        if fails >= 3:   # the servers are struggling: give them a minute
            time.sleep(60)
            fails = 0
        try:
            els = (_overpass(box_query(box, {k: segs[k] for k in keys}), 120) or {}).get("elements", [])
        except http.FetchError as e:
            fails += 1
            say(f"OSM {region}/{'+'.join(keys) if len(keys) < 4 else f'{len(keys)} kinds'}: failed ({e})")
            return False
        fails = 0
        by = {k: [] for k in keys}
        for el in els:
            k = segment_of(el.get("tags", {}), {k: segs[k] for k in keys})
            if k:
                by[k].append(el)
        for k in keys:
            cache[ck(region, k)] = {"date": today.isoformat(), "elements": by[k]}
        save()
        time.sleep(2)   # Overpass asks for gaps between queries
        return True

    for region, box in tiles.items():
        need = []
        for k in segs:
            hit = cache.get(ck(region, k))
            if hit and (today - dt.date.fromisoformat(hit["date"])).days < refresh_days:
                reused += 1
            else:
                need.append(k)
        if need and not ask(region, box, need):
            for k in need:
                if not ask(region, box, [k]):
                    if ck(region, k) in cache:
                        stale += 1
                    else:
                        errors.append(f"{region}/{k}: no answer")
        n = 0
        for k in segs:
            for el in (cache.get(ck(region, k)) or {}).get("elements", []):
                ref = f"{el.get('type')}/{el.get('id')}"
                if ref in seen:   # region boxes overlap at the borders
                    continue
                seen.add(ref)
                b = parse(el, "", segments)
                if b:
                    res.items.append(b)
                    n += 1
        say(f"OSM {region}: {n:,} places" + (f" ({len(need)} kinds asked)" if need else " (all reused)"))
    # Keep only this run's answers (drops the old whole-country entries).
    for k in [k for k in cache if not k.startswith(("R:", "PBF"))]:
        del cache[k]
    save()
    return errors, reused, stale


def fetch(municipalities: list[str] | None, segments: dict, cache_path: Path | None = None,
          refresh_days: int = 0, tiles: dict | None = None, extract: Path | None = None) -> SourceResult:
    """One query per municipality and segment; for the whole country (municipalities None), one region at a
    time when `tiles` (region -> box) is given, else one query per segment. A query that fails falls back to
    that query's last good answer."""
    res = SourceResult(name="osm")
    cache = {}
    if cache_path:
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}

    def save():
        if cache_path:   # keep each answer even if the run is stopped later
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    if municipalities is None and extract is not None:
        # The whole country from Geofabrik's Finland file: no load on the public Overpass servers.
        tagsig = sorted(t for s in segments.values() for t in s.get("osm", []))
        try:
            if not osm_extract.download(extract, refresh_days):
                raise RuntimeError("no map file")
            stamp = int(extract.stat().st_mtime)
            hit = cache.get("PBF") or {}
            if hit.get("stamp") == stamp and hit.get("tags") == tagsig:
                elements = hit["elements"]
            else:
                elements = osm_extract.scan(extract, segments)
                cache = {"PBF": {"stamp": stamp, "tags": tagsig, "date": dt.date.today().isoformat(),
                                 "elements": elements}}
                save()
            source = f"Geofabrik Finland file of {dt.date.fromtimestamp(stamp)}"
        except Exception as e:   # no download, no pyosmium...: last good scan, else ask the servers region by region
            hit = cache.get("PBF")
            say(f"OSM: the Finland file could not be used ({type(e).__name__}: {e})"
                + (f"; using the scan of {hit['date']}" if hit else "; asking the servers region by region"))
            if not hit:
                elements = None
            else:
                elements, source = hit["elements"], f"scan of {hit['date']} (download failed)"
        if elements is not None:
            for el in elements:
                b = parse(el, "", segments)
                if b:
                    res.items.append(b)
            say(f"OSM: {len(res.items):,} places from the {source}")
            res.detail = source
            return res

    if municipalities is None and tiles:
        errors, reused, stale = _fetch_regions(tiles, segments, cache, refresh_days, save, res)
        res.ok = bool(res.items) or not errors
        res.error = "; ".join(errors[:3]) + (f" (+{len(errors) - 3} more)" if len(errors) > 3 else "")
        res.detail = (f"{len(tiles)} regions" + (f", {reused} answers reused from the last {refresh_days} days" if reused else "")
                      + (f", {stale} from an older run" if stale else ""))
        return res
    errors, stale, down, fresh = [], 0, 0, 0
    for m in municipalities or [None]:
        for key, seg in segments.items():
            if not seg.get("osm"):
                continue
            ck = f"{m or 'FI'}|{key}|{','.join(seg['osm'])}"
            hit = cache.get(ck)
            if hit and (dt.date.today() - dt.date.fromisoformat(hit["date"])).days < refresh_days:
                fresh += 1   # places change slowly: reuse a recent answer and spare the public servers
                say(f"OSM {m or 'Finland'}/{key}: {len(hit['elements']):,} places (reused from {hit['date']})")
                for el in hit["elements"]:
                    b = parse(el, m or "", segments)
                    if b:
                        res.items.append(b)
                continue
            try:
                if down >= 2:   # two queries in a row failed on every mirror: the servers are overloaded today
                    raise http.FetchError("skipped, Overpass servers busy")
                elements = (_overpass(build_query(m, {key: seg}), 90 if m else 260) or {}).get("elements", [])
                cache[ck] = {"date": dt.date.today().isoformat(), "elements": elements}
                down = 0
                say(f"OSM {m or 'Finland'}/{key}: {len(elements):,} places")
                if cache_path:   # keep each answer even if the run is stopped later
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            except http.FetchError as e:
                down += 1
                say(f"OSM {m or 'Finland'}/{key}: failed ({e})" + (", using the last good answer" if ck in cache else ""))
                if ck in cache:
                    elements, stale = cache[ck]["elements"], stale + 1
                else:
                    errors.append(f"{m or 'FI'}/{key}: {e}")
                    continue
            for el in elements:
                b = parse(el, m or "", segments)
                if b:
                    res.items.append(b)
            time.sleep(1 if m else 5)   # Overpass asks for gaps between queries
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    res.ok = bool(res.items) or not errors
    res.error = "; ".join(errors[:3]) + (f" (+{len(errors) - 3} more)" if len(errors) > 3 else "")
    res.detail = ((f"{len(municipalities)} municipalities" if municipalities else "whole country")
                  + (f", {fresh} queries reused from the last {refresh_days} days" if fresh else "")) + (f", {stale} queries from last good run" if stale else "")
    return res
