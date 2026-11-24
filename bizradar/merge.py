"""Join OpenStreetMap places with PRH companies, so a place learns its business ID and company form."""
from __future__ import annotations

from .models import Business
from .text import name_similarity


def _score(place: Business, co: Business) -> float:
    if place.business_id and place.business_id == co.business_id:
        return 1.0
    if place.domain and co.domain and place.domain == co.domain:
        return 0.95
    sim = max([name_similarity(place.name, n) for n in [co.name] + co.other_names] or [0])
    if sim < 0.5:
        return 0.0
    same_post = place.postcode and co.postcode and place.postcode == co.postcode
    same_city = (place.city or "").lower() == (co.city or "").lower()
    if same_post:
        return min(0.9, 0.5 + sim / 2)
    if same_city and sim >= 0.75:
        return 0.7
    return 0.0


def absorb(co: Business, place: Business) -> Business:
    """PRH is the authority on identity; OSM on the place itself (phone, location, hours)."""
    co.osm_ref = place.osm_ref
    co.lat, co.lon = place.lat, place.lon
    co.opening_hours = co.opening_hours or place.opening_hours
    if not co.website and place.website:
        co.website, co.domain = place.website, place.domain
    if place.phone and not co.phone:
        co.phone, co.phone_source = place.phone, place.phone_source
    co.instagram = co.instagram or place.instagram
    co.facebook = co.facebook or place.facebook
    if place.name.lower() != co.name.lower() and place.name not in co.other_names:
        co.other_names.insert(0, place.name)   # the name on the door, often not the registered one
    co.signals.update({k: v for k, v in place.signals.items() if k not in co.signals})
    for p in place.provenance:
        co.note(p["field"], p["source"], p["ref"])
    return co


def merge(companies: list[Business], places: list[Business]) -> tuple[list[Business], dict]:
    by_post: dict[str, list[Business]] = {}
    for co in companies:
        by_post.setdefault(co.postcode or "?", []).append(co)
    by_domain = {co.domain: co for co in companies if co.domain}
    by_bid = {co.business_id: co for co in companies}
    used: set[str] = set()
    out: list[Business] = []
    stats = {"places": len(places), "companies": len(companies), "matched": 0}
    for p in places:
        cands = []
        if p.business_id in by_bid:
            cands.append(by_bid[p.business_id])
        if p.domain in by_domain:
            cands.append(by_domain[p.domain])
        cands += by_post.get(p.postcode, []) if p.postcode else [c for c in companies if c.city.lower() == p.city.lower()]
        best, best_s = None, 0.0
        for co in cands:
            if co.id in used:
                continue
            s = _score(p, co)
            if s > best_s:
                best, best_s = co, s
        if best and best_s >= 0.7:
            used.add(best.id)
            absorb(best, p)
            stats["matched"] += 1
        else:
            out.append(p)
    out.extend(companies)
    # Two OSM objects for one place (node + building): keep one per name+postcode.
    seen, dedup = set(), []
    for b in out:
        k = (b.business_id or b.name.lower(), b.postcode or b.city.lower())
        if k in seen:
            continue
        seen.add(k)
        dedup.append(b)
    stats["kept"] = len(dedup)
    return dedup, stats
