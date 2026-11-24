from __future__ import annotations

import json
from pathlib import Path

TEMPLATE = Path(__file__).with_name("dashboard_template.html")


def compact(payload: dict) -> dict:
    """The same data, smaller: empty fields dropped, channel reasons and provenance as short lists.

    Across the whole country there are tens of thousands of leads; the page expands this back on load.
    """
    whys: dict[str, int] = {}
    leads = []
    for b in payload["leads"]:
        c = {k: v for k, v in b.items() if v not in ("", None, [], {}) or k in ("id", "name", "score")}
        if "channels" in c:
            c["channels"] = {k: [1 if ch.get("allowed") else 0, ch.get("to", ""), whys.setdefault(ch.get("why", ""), len(whys)),
                                 1 if ch.get("role_unlock") else 0] for k, ch in c["channels"].items()}
        if "provenance" in c:
            known = {b.get("business_id"), b.get("osm_ref"), b.get("website")}
            c["provenance"] = [[p["field"], p["source"]] + ([p["ref"]] if p.get("ref") and p["ref"] not in known else [])
                               for p in c["provenance"]]
        if "emails" in c:
            c["emails"] = [{k: v for k, v in e.items() if v} for e in c["emails"]]
        leads.append(c)
    return dict(payload, leads=leads, whys=list(whys), compact=True)


def build(payload: dict) -> str:
    """The dashboard as one self-contained file, data embedded, so it opens with a double-click."""
    data = json.dumps(compact(payload), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", data, 1)


def digest(payload: dict, limit: int = 25) -> str:
    new = [b for b in payload["leads"] if b["first_seen"] == payload["date"]]
    lines = [f"# Business lead radar {payload['date']}", "",
             f"{len(payload['leads'])} businesses shown, {payload['new_today']} new since the last run, "
             f"{sum(1 for b in payload['leads'] if b['channels'].get('email', {}).get('allowed'))} that may be emailed.", ""]
    for b in new[:limit]:
        best = next((k for k in ("email", "phone", "visit", "letter") if b["channels"].get(k, {}).get("allowed")), "none")
        lines.append(f"- **{b['name']}** ({payload['segments'].get(b['segment'], {}).get('label', b['segment'])}, "
                     f"{b['city']}, score {b['score']}): {', '.join(b['offers']) or '-'}; contact by {best}.")
    if len(new) > limit:
        lines.append(f"- and {len(new) - limit} more in the dashboard")
    return "\n".join(lines) + "\n"


def notice(payload: dict, url: str = "") -> str:
    """The GitHub issue body: counts only. Names and contacts stay inside the encrypted page."""
    L = payload["leads"]
    em = sum(1 for b in L if b["channels"].get("email", {}).get("allowed"))
    new = [b for b in L if b["first_seen"] == payload["date"]]
    by_seg: dict[str, int] = {}
    by_reg: dict[str, int] = {}
    for b in new:
        by_seg[b["segment"]] = by_seg.get(b["segment"], 0) + 1
        r = b.get("region") or "unknown"
        by_reg[r] = by_reg.get(r, 0) + 1
    lines = [f"**{len(new):,} new** businesses since the last run, {len(L):,} shown, {em:,} may be emailed now.", ""]
    if url:
        lines += [f"Open the dashboard (passphrase needed): {url}", ""]
    if new:
        lines.append("New by kind: " + ", ".join(f"{payload['segments'].get(k, {}).get('label', k)} {n}"
                                                  for k, n in sorted(by_seg.items(), key=lambda x: -x[1])))
        lines.append("")
        lines.append("New by region: " + ", ".join(f"{k} {n}" for k, n in sorted(by_reg.items(), key=lambda x: -x[1])[:10]))
    w = payload.get("sites", {})
    lines += ["", f"Websites read this run: {w.get('read', 0)}, cached {w.get('cached', 0)}, failed {w.get('failed', 0)}.",
              "", "Names and contact details are only in the encrypted dashboard, never in this issue."]
    return "\n".join(lines) + "\n"
