"""PRH / YTJ open data (avoindata.prh.fi, API v3, CC BY 4.0). Companies by industry code, for the
whole country or for chosen municipalities.

What it gives: business ID, names, company form, industry (TOL 2025), visiting and postal address, website
(about 40% of records). No phone numbers and no email addresses. Sole traders (toiminimi) are not in this
dataset; they are found through OpenStreetMap and matched by name instead.
"""
from __future__ import annotations

import concurrent.futures as cf

from .. import http
from ..log import say
from ..models import Business
from ..text import domain_of, normalize_url
from . import SourceResult

API = "https://avoindata.prh.fi/opendata-ytj-api/v3/companies"
FORMS = {"16": "oy", "17": "oy", "13": "ky", "5": "ay", "14": "osk", "19": "other"}
# Liquidation, bankruptcy, restructuring, dissolution: not a business to approach.
BAD_SITUATIONS = {"SELTILA", "KONK", "YRUSAN", "SANEER", "PURK"}


def _name(c: dict) -> tuple[str, list[str]]:
    live = [n for n in c.get("names", []) if not n.get("endDate")]
    main = next((n["name"] for n in live if n.get("type") == "1"), live[0]["name"] if live else "")
    return main, [n["name"] for n in live if n["name"] != main]


def _desc(obj: dict, lang: str = "1") -> str:
    for d in obj.get("descriptions", []):
        if d.get("languageCode") == lang:
            return d.get("description", "")
    return ""


def parse(c: dict, segment: str) -> Business | None:
    if c.get("endDate") or c.get("tradeRegisterStatus") not in ("1", None):
        return None
    if any(s.get("type") in BAD_SITUATIONS for s in c.get("companySituations", [])):
        return None
    name, others = _name(c)
    if not name:
        return None
    bid = c["businessId"]["value"]
    form_code = (c.get("companyForms") or [{}])[0].get("type", "")
    mbl = c.get("mainBusinessLine") or {}
    b = Business(id=f"prh:{bid}", name=name, segment=segment, business_id=bid,
                 legal_form=FORMS.get(form_code, "other"), legal_form_source="prh",
                 industry_code=mbl.get("type", ""), industry=_desc(mbl), other_names=others,
                 registered=(c.get("registrationDate") or ""))
    # Visiting address (type 1) first, then postal (type 2).
    for a in sorted(c.get("addresses", []), key=lambda a: a.get("type", 9)):
        if a.get("street"):
            city = next((p["city"] for p in a.get("postOffices", []) if p.get("languageCode") == "1"), "")
            b.street = " ".join(x for x in (a.get("street"), a.get("buildingNumber"), a.get("entrance")) if x)
            b.postcode, b.city = a.get("postCode", ""), city.title()
            b.note("address", "prh", bid)
            break
    site = (c.get("website") or {}).get("url", "")
    if site:
        b.website, b.domain = normalize_url(site), domain_of(site)
        b.note("website", "prh", bid)
    b.note("business_id", "prh", bid)
    b.note("legal_form", "prh", bid)
    return b


def _page(location: str | None, code: str, page: int) -> dict:
    params = {"mainBusinessLine": code, "page": page}
    if location:
        params["location"] = location
    return http.get(API, params=params) or {}


def fetch(municipalities: list[str] | None, segments: dict) -> SourceResult:
    """One query per (municipality, industry code), or per code for the whole country when municipalities is None.

    Records are kept only if their main line is one of the codes (the location filter also matches postal
    addresses elsewhere; the pipeline filters by place afterwards). Pages after the first are fetched in parallel.
    """
    places = municipalities or [None]
    jobs = [(m, code, seg) for m in places for seg, s in segments.items() for code in s.get("tol", [])]
    res = SourceResult(name="prh")
    seen: set[str] = set()
    errors: list[str] = []
    pages = 0

    def take(rows: list[dict], code: str, seg: str) -> None:
        for c in rows:
            bid = c.get("businessId", {}).get("value")
            if not bid or bid in seen or (c.get("mainBusinessLine") or {}).get("type") != code:
                continue
            b = parse(c, seg)
            if b:
                seen.add(bid)
                res.items.append(b)

    with cf.ThreadPoolExecutor(6) as ex:
        first = {ex.submit(_page, m, code, 1): (m, code, seg) for m, code, seg in jobs}
        more = {}
        for f in cf.as_completed(first):
            m, code, seg = first[f]
            try:
                d = f.result()
            except http.FetchError as e:
                errors.append(f"{m or 'FI'}/{code}: {e}")
                continue
            pages += 1
            take(d.get("companies", []), code, seg)
            total = d.get("totalResults") or 0
            for p in range(2, min(-(-total // 100), 400) + 1):
                more[ex.submit(_page, m, code, p)] = (m, code, seg)
        say(f"PRH: {len(jobs)} industry codes queried, {len(more):,} more pages to fetch")
        for n, f in enumerate(cf.as_completed(more), 1):
            if n % 100 == 0:
                say(f"PRH: {n:,}/{len(more):,} pages")
            m, code, seg = more[f]
            try:
                take(f.result().get("companies", []), code, seg)
                pages += 1
            except http.FetchError as e:
                errors.append(f"{m or 'FI'}/{code}: {e}")
    say(f"PRH: {len(res.items):,} companies from {pages:,} pages" + (f", {len(errors)} errors" if errors else ""))
    res.ok = pages > 0 and len(errors) <= pages
    res.error = "; ".join(errors[:3]) + (f" (+{len(errors) - 3} more)" if len(errors) > 3 else "")
    res.detail = f"{pages} pages, {'whole country' if not municipalities else f'{len(municipalities)} municipalities'}"
    return res
