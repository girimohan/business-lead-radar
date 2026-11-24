from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
import webbrowser
from pathlib import Path

import yaml

from . import compliance, dashboard, geo, pipeline, secure

ROOT = Path(__file__).resolve().parent.parent


def load_cfg(path: str) -> dict:
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    tpl = ROOT / "outreach.yaml"
    if tpl.exists():
        cfg.setdefault("outreach", yaml.safe_load(tpl.read_text(encoding="utf-8")))
    # Online, sender details you'd rather not commit can come from the RADAR_SENDER secret (YAML).
    extra = yaml.safe_load(os.environ.get("RADAR_SENDER") or "") or {}
    cfg["sender"] = {**cfg.get("sender", {}), **{k: v for k, v in extra.items() if v}}
    return cfg


def write_shared() -> str:
    """With RADAR_PASSPHRASE set, encrypt the opt-out list and contact statuses into data/shared.enc for GitHub."""
    p = os.environ.get("RADAR_PASSPHRASE", "")
    if len(p) < secure.MIN_PASSPHRASE:
        return ""
    out = ROOT / "data" / "shared.enc"
    out.write_bytes(secure.pack_state(ROOT, p, secure.SHARED_FILES))
    return (f"Encrypted for the online radar: {out}\n"
            '  git add data/shared.enc; git commit -m "Sync tracker"; git push')


def cmd_run(args) -> int:
    cfg = load_cfg(args.config)
    if args.area:
        cfg["area"] = [a.strip() for a in args.area.split(",")]
    only = set(args.sources.split(",")) if args.sources else None
    segs = set(args.segments.split(",")) if args.segments else None
    try:
        payload = pipeline.run(cfg, ROOT, dt.date.today(), only, read_sites=not args.no_sites, segments=segs)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1
    (ROOT / "private" / "digest.md").write_text(dashboard.digest(payload), encoding="utf-8")
    f, L = payload["funnel"], payload["leads"]
    em = sum(1 for b in L if b["channels"].get("email", {}).get("allowed"))
    ph = sum(1 for b in L if not b["channels"].get("email", {}).get("allowed") and b["channels"].get("phone", {}).get("allowed"))
    print(f"{f['companies']:,} companies (PRH) + {f['places']:,} places (OSM), {f['matched']} matched -> "
          f"{len(L):,} leads ({em} may be emailed, {ph} phone first; {payload['new_today']} new; "
          f"{f['opted_out']} opted out)")
    for s in payload["sources"]:
        print(f"  {s['name']:5} {'ok ' if s['ok'] else 'ERR'} {s['fetched']:>6,}  {s['error'] or s['detail']}")
    w = payload["sites"]
    print(f"  websites: read {w['read']}, cached {w['cached']}, failed {w['failed']}")
    out = ROOT / "private" / "dashboard.html"
    print(f"Dashboard: {out}")
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a", encoding="utf-8") as fh:
            fh.write(f"new_today={payload['new_today']}\nkept={len(L)}\nemailable={em}\n"
                     f"first_run={'true' if payload['first_run'] else 'false'}\n")
    (ROOT / "private" / "notice.md").write_text(dashboard.notice(payload, os.environ.get("DASHBOARD_URL", "")),
                                                encoding="utf-8")
    if args.open:
        webbrowser.open(out.as_uri())
    if not cfg.get("sender", {}).get("name") or not cfg.get("sender", {}).get("email"):
        print("Tip: fill in sender.name, sender.email and sender.privacy_url in config.yaml; every message must say who it is from.")
    return 0


def cmd_sync(args) -> int:
    """Read a tracker file downloaded from the dashboard: opt-outs, contacted dates, contact log."""
    tracker = json.loads(Path(args.file).read_text(encoding="utf-8"))
    oo = compliance.OptOut(ROOT / "data" / "optout.json")
    seen_path = ROOT / "data" / "seen.json"
    ledger = pipeline.load_json(seen_path, {})
    n_dnc = n_contacted = 0
    rows = []
    contacts_path = ROOT / "data" / "contacts.json"
    contacts = pipeline.load_json(contacts_path, {})
    for lid, t in tracker.items():
        if t.get("status") == "dnc":
            keys = [f"id:{t['business_id']}" if t.get("business_id") else "", f"domain:{t['domain']}" if t.get("domain") else "",
                    f"phone:{t['phone']}" if t.get("phone") else "", f"name:{t.get('name', '').lower()}|{t.get('postcode', '')}"]
            keys += [f"email:{e}" for e in t.get("emails", [])]
            oo.add(keys, how=f"marked in dashboard {t.get('date', '')}")
            n_dnc += 1
        if t.get("status") and t["status"] != "dnc":
            led = ledger.setdefault(lid, {"first": t.get("date") or dt.date.today().isoformat()})
            led["contacted"] = t.get("date") or dt.date.today().isoformat()
            led["status"] = t["status"]
            led.pop("expired", None)
            contacts[lid] = {"contacted": led["contacted"], "status": t["status"]}
            n_contacted += 1
        for e in t.get("log", []):
            rows.append([e.get("date", ""), t.get("name", ""), t.get("business_id", ""), e.get("channel", ""),
                         e.get("status", ""), t.get("to", ""), (t.get("consent") or {}).get("date", "")])
    oo.save()
    contacts_path.write_text(json.dumps(contacts, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    seen_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    log = ROOT / "private" / "contact-log.csv"
    log.parent.mkdir(exist_ok=True)
    with log.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "business", "business_id", "channel", "status", "emailed_to", "consent_date"])
        w.writerows(sorted(rows))
    print(f"{n_dnc} added to the opt-out list, {n_contacted} marked as contacted, {len(rows)} log rows -> {log}")
    msg = write_shared()
    print(msg or "Tip: set RADAR_PASSPHRASE to also update the online radar (data/shared.enc).")
    return 0


def cmd_optout(args) -> int:
    """Add an opt-out by hand: a Y-tunnus, email, domain or phone (for a 'no' received by email or phone)."""
    oo = compliance.OptOut(ROOT / "data" / "optout.json")
    keys = []
    for v in args.values:
        v = v.strip().lower()
        if "@" in v:
            keys += [f"email:{v}", f"domain:{v.split('@')[1]}"] if args.whole_domain else [f"email:{v}"]
        elif v.startswith("+") or v.replace(" ", "").isdigit():
            from .text import normalize_phone
            keys.append(f"phone:{normalize_phone(v)}")
        elif len(v) == 9 and v[7] == "-":
            keys.append(f"id:{v}")
        else:
            keys.append(f"domain:{v.removeprefix('www.')}")
    oo.add(keys, how=args.how or "added by hand")
    oo.save()
    print(f"opt-out list now has {len(oo.entries)} entries")
    msg = write_shared()
    if msg:
        print(msg)
    return 0


def cmd_seal(args) -> int:
    html = (ROOT / "private" / "dashboard.html").read_text(encoding="utf-8")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(secure.seal_page(html, secure.passphrase_from_env()), encoding="utf-8")
    (out.parent / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    print(f"Encrypted dashboard: {out}")
    return 0


def cmd_state(args) -> int:
    """Run state between GitHub Actions runs (actions/cache), encrypted. `shared` = data/shared.enc from you."""
    p = secure.passphrase_from_env()
    shared = args.action == "shared"
    files = secure.SHARED_FILES if shared else secure.STATE_FILES
    path = Path(args.file or (ROOT / "data" / "shared.enc" if shared else ROOT / ".state" / "state.bin"))
    if args.action == "save":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(secure.pack_state(ROOT, p, files))
        print(f"State saved: {path}")
        return 0
    if not path.exists():
        print("No data/shared.enc yet." if shared else "Nothing saved yet; starting fresh.")
        return 0
    try:
        print("Restored: " + (", ".join(secure.unpack_state(path.read_bytes(), ROOT, p, files)) or "nothing"))
    except secure.BadPassphrase:
        print(f"{path.name} doesn't open with this passphrase (was it changed?); ignoring it.")
    return 0


def cmd_geo(args) -> int:
    d = geo.download(ROOT / "data" / "geo.json")
    print(f"{len(d['municipalities'])} municipalities, {len(d['regions'])} regions, {len(d['postcodes'])} postcodes")
    return 0


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="bizradar", description="Find local businesses Barmo fits, and how to reach them lawfully.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="collect, read websites, write private/dashboard.html")
    r.add_argument("--config", default=str(ROOT / "config.yaml"))
    r.add_argument("--area", help="'all', or comma-separated municipalities and/or regions (Vantaa,Kerava or Pirkanmaa)")
    r.add_argument("--segments", help="comma-separated segment keys from config (e.g. hair,beauty)")
    r.add_argument("--sources", help="prh, osm or both (default)")
    r.add_argument("--no-sites", action="store_true", help="skip reading business websites")
    r.add_argument("--open", action="store_true", help="open the dashboard when done")
    r.set_defaults(fn=cmd_run)
    s = sub.add_parser("sync", help="apply a tracker file downloaded from the dashboard")
    s.add_argument("file")
    s.set_defaults(fn=cmd_sync)
    o = sub.add_parser("optout", help="add a business that said no (email, phone, Y-tunnus or domain)")
    o.add_argument("values", nargs="+")
    o.add_argument("--how", help="e.g. 'replied by email 2026-12-01'")
    o.add_argument("--whole-domain", action="store_true", help="for an email: block the whole domain")
    o.set_defaults(fn=cmd_optout)
    se = sub.add_parser("seal", help="encrypt the dashboard with RADAR_PASSPHRASE for publishing")
    se.add_argument("--out", default=str(ROOT / "site" / "index.html"))
    se.set_defaults(fn=cmd_seal)
    st = sub.add_parser("state", help="save/load the run's state, or load data/shared.enc (RADAR_PASSPHRASE)")
    st.add_argument("action", choices=["save", "load", "shared"])
    st.add_argument("--file")
    st.set_defaults(fn=cmd_state)
    g = sub.add_parser("geo", help="refresh data/geo.json (municipalities, regions, postcodes) from Statistics Finland")
    g.set_defaults(fn=cmd_geo)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
