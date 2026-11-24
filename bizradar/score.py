"""Which Barmo product fits each business, and how good a lead it is (0-100). Every point has a stated reason."""
from __future__ import annotations

import datetime as dt

from .models import Business

SELF_SERVE_BOOKING = {"Timma", "Varaa.com", "Fresha", "Vello", "Booksy", "Treatwell", "Phorest", "Slotti", "Bokamera",
                      "Getti", "Calendly", "Ajanvarauspalvelu", "Hairlinq", "TableOnline", "Dinnerbooking",
                      "OpenTable", "Resy", "Eat.fi"}
DIY_BUILDERS = {"Wix", "Webnode", "Kotisivukone", "Yola", "Weebly", "Jimdo", "Google Sites", "Sivuviidakko"}


def offers_for(b: Business, cfg: dict) -> list[tuple[str, str, str]]:
    """[(offer_key, why_en, why_fi)] in the order the segment prefers, only where the evidence supports it.

    The why texts are written to the business ("your website ..."), so drafts can use them as they are.
    """
    seg = cfg["segments"].get(b.segment, {})
    s = b.signals
    site_ok = s.get("site_ok")
    year = dt.date.today().year
    out = []
    for key in seg.get("offers", []):
        en = fi = ""
        if key == "receptionist":
            if site_ok and not s.get("chat"):
                if set(s.get("booking", [])) & SELF_SERVE_BOOKING:
                    en = "your website has online booking but no chat for customers' questions"
                    fi = "verkkosivuillanne on ajanvaraus, mutta ei chattia asiakkaiden kysymyksille"
                else:
                    en = "your website has no chat and no online booking"
                    fi = "verkkosivuillanne ei ole chattia eikä verkkoajanvarausta"
        elif key == "website":
            # Claims about a website are made only from evidence: a mapped storefront with no site anywhere,
            # or a site the radar actually read. A site that failed to load proves nothing (robots, outage).
            if not b.website and s.get("site_searched") and b.osm_ref:
                en, fi = "I could not find a website for you", "en löytänyt teille verkkosivuja"
            elif not site_ok:
                pass
            elif not s.get("mobile"):
                en, fi = "your website does not adapt to phones", "verkkosivunne eivät mukaudu puhelimen näytölle"
            elif not s.get("https"):
                en, fi = "your website has no secure https connection", "verkkosivuillanne ei ole suojattua https-yhteyttä"
            elif s.get("copyright_year") and s["copyright_year"] <= year - 6:
                en = f"the copyright line on your website still says {s['copyright_year']}"
                fi = f"verkkosivujenne alalaidassa lukee yhä vuosi {s['copyright_year']}"
        elif key == "accounts":
            if b.legal_form in ("tmi", "unknown"):
                en, fi = "you run your business as a sole trader", "toimitte toiminimellä"
            elif b.legal_form in ("ay", "ky"):
                en, fi = "you run a small partnership", "olette pieni henkilöyhtiö"
        elif key == "shopify_faq":
            if "Shopify" in s.get("platform", []):
                en, fi = "you sell through a Shopify store", "myytte Shopify-verkkokaupassa"
        elif key == "automation":
            used = s.get("delivery", []) + s.get("booking", [])
            if used:
                en = "you already use " + ", ".join(used)
                fi = "käytätte jo palveluita " + ", ".join(used)
        if en:
            out.append((key, en, fi))
    return out


def score(b: Business, cfg: dict, today: dt.date | None = None) -> None:
    today = today or dt.date.today()
    pts, reasons = 0, []
    offers = offers_for(b, cfg)
    b.offers = [k for k, _, _ in offers]
    b.offer_why = {k: {"en": en, "fi": fi} for k, en, fi in offers}
    if offers:
        pts += 30 + 8 * (len(offers) - 1)
        reasons += [f"{cfg['offers'][k]['name']}: {en}" for k, en, _ in offers]
    else:
        reasons.append("no clear gap Barmo fills")
    ch = b.channels or {}
    if ch.get("email", {}).get("allowed"):
        pts += 25
        reasons.append("can be emailed")
    elif ch.get("phone", {}).get("allowed") or ch.get("letter", {}).get("allowed"):
        pts += 12
    if b.phone:
        pts += 8
    if b.business_id:
        pts += 5
    if b.registered:
        try:
            age = (today - dt.date.fromisoformat(b.registered[:10])).days / 365
            if age < 2:
                pts += 10
                reasons.append("registered in the last two years: still setting things up")
        except ValueError:
            pass
    if b.signals.get("platform") and set(b.signals["platform"]) & DIY_BUILDERS:
        pts += 5
        reasons.append("site built on " + ", ".join(sorted(set(b.signals["platform"]) & DIY_BUILDERS)))
    if b.signals.get("english") is False and b.signals.get("site_ok"):
        pts += 3
    b.score = max(0, min(100, pts))
    b.reasons = reasons
