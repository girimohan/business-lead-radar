"""Read each business's own website: the contact details it publishes, and what the site already has.

Only the business's own pages are read (homepage plus a few contact / booking / about pages), robots.txt is
respected, and results are cached so a site is read at most once per `refresh_days`.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import html as htmllib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from . import http
from .models import Business, Email
from .text import domain_of, fold, name_tokens, normalize_phone

LINK_WORDS = ("yhteys", "yhteystiedot", "ota-yhteytta", "contact", "kontakt", "ajanvaraus", "varaa", "booking",
              "tietoa", "meista", "about", "hinnasto", "palvelut", "info")
FREEMAIL = {"gmail.com", "hotmail.com", "hotmail.fi", "outlook.com", "outlook.fi", "live.com", "live.fi", "msn.com",
            "yahoo.com", "icloud.com", "me.com", "luukku.com", "suomi24.fi", "elisanet.fi", "kolumbus.fi",
            "saunalahti.fi", "welho.com", "netti.fi", "pp.inet.fi", "anvianet.fi", "dnainternet.net", "protonmail.com",
            "proton.me"}
GENERIC_LOCAL = {"info", "asiakaspalvelu", "ajanvaraus", "varaukset", "varaus", "booking", "bookings", "myynti",
                 "toimisto", "posti", "hello", "hei", "moi", "contact", "tilaukset", "tilaus", "palaute", "office",
                 "mail", "salon", "kahvila", "ravintola", "cafe", "restaurant", "studio", "sales", "support",
                 "laskutus", "kampaamo", "parturi", "hoitola", "yhteys", "kontakt", "reception", "catering"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+(?:@|\s?\(at\)\s?|\s?\[at\]\s?)[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# What the site already uses. Each value: list of substrings looked for in the HTML (lower case).
SIGNALS = {
    "booking": {"Timma": ["timma.fi"], "Varaa.com": ["varaa.com"], "Fresha": ["fresha.com"], "Vello": ["vello.fi"],
                "Booksy": ["booksy.com"], "Treatwell": ["treatwell."], "Phorest": ["phorest.com"],
                "Slotti": ["slotti.fi"], "Bokamera": ["bokamera."], "Getti": ["getti.fi"], "Calendly": ["calendly.com"],
                "Ajanvarauspalvelu": ["ajanvarauspalvelu.fi"], "Hairlinq": ["hairlinq"], "TableOnline": ["tableonline.fi"],
                "Dinnerbooking": ["dinnerbooking.com"], "OpenTable": ["opentable."], "Resy": ["resy.com"],
                "Eat.fi": ["eat.fi"]},
    "chat": {"Giosg": ["giosg.com"], "Ninchat": ["ninchat.com"], "Tawk.to": ["tawk.to"], "Tidio": ["tidio"],
             "Intercom": ["intercom.io", "widget.intercom"], "Crisp": ["crisp.chat"], "LiveChat": ["livechatinc.com"],
             "Zendesk": ["zdassets.com", "zopim"], "Smartsupp": ["smartsupp.com"], "Messenger chat": ["fb-customerchat"],
             "Chatbase": ["chatbase.co"], "Voiceflow": ["voiceflow.com"], "Botpress": ["botpress"], "Barmo": ["barmo.fi"],
             "WhatsApp button": ["wa.me/", "api.whatsapp.com/send"]},
    "delivery": {"Wolt": ["wolt.com"], "Foodora": ["foodora.fi"], "ResQ": ["resq-club", "resq.club"]},
    "platform": {"Shopify": ["cdn.shopify.com", "myshopify.com"], "WooCommerce": ["woocommerce"],
                 "Wix": ["wix.com", "wixstatic.com"], "Squarespace": ["squarespace.com", "sqsp.net"],
                 "WordPress": ["wp-content", "wp-includes"], "Webnode": ["webnode."], "Kotisivukone": ["kotisivukone"],
                 "Sivuviidakko": ["sivuviidakko"], "Yola": ["yola.com"], "Weebly": ["weebly.com"],
                 "Jimdo": ["jimdo"], "Duda": ["dudaone", "multiscreensite"], "Google Sites": ["sites.google.com"]},
}


TRADE_WORDS = ("salon", "hair", "hius", "kampaamo", "parturi", "barber", "beauty", "kauneus", "hoitola", "spa",
               "studio", "cafe", "kahvila", "ravintola", "restaurant", "pizza", "kebab", "sushi", "bistro", "bar",
               "baari", "nails", "kynsi", "ripsi", "lash", "brow", "hieronta", "massage", "fysio", "kitchen", "keittio")


def classify_email(addr: str, b: Business) -> str:
    local, _, dom = addr.lower().partition("@")
    lt = set(fold(local).split())
    if local in GENERIC_LOCAL or lt & GENERIC_LOCAL or any(w in local for w in TRADE_WORDS):
        return "generic"
    if lt & name_tokens(b.name, drop_noise=False) or (b.domain and dom == b.domain and local == b.domain.split(".")[0]):
        return "generic"     # salonaurora@..., named after the business
    return "personal"


def _emails(html: str) -> list[str]:
    found = set(m.group(1) for m in re.finditer(r'mailto:([^"\'?>\s]+)', html, re.I))
    text = re.sub(r"<[^>]+>", " ", html)
    for m in EMAIL_RE.finditer(htmllib.unescape(text)):
        found.add(re.sub(r"\s?[\(\[]at[\)\]]\s?", "@", m.group(0)))
    out = []
    for e in found:
        e = htmllib.unescape(e).strip(".,;:").lower()
        if re.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", e) and not e.endswith((".png", ".jpg", ".webp")):
            out.append(e)
    return out


def _links(base: str, html: str, domain: str) -> list[str]:
    out = []
    for href in re.findall(r'href=["\']([^"\'#]+)', html, re.I):
        u = urljoin(base, href)
        if domain_of(u) != domain or not u.startswith("http"):
            continue
        path = fold(urlsplit(u).path)
        if any(w.replace("-", " ") in path for w in LINK_WORDS) and u not in out:
            out.append(u)
    return out


def _safe(fn, fallback):
    """One broken website must never sink the run: any error counts as 'could not read'."""
    def run(b):
        try:
            return fn(b)
        except Exception:
            return dict(fallback) if isinstance(fallback, dict) else fallback
    return run


def read_site(b: Business, max_pages: int = 4) -> dict:
    """Returns a cache entry: emails with the page they were on, phones, form, signals, socials."""
    entry = {"read": dt.date.today().isoformat(), "ok": False, "emails": [], "phones": [], "form": "",
             "signals": {}, "instagram": "", "facebook": "", "pages": 0}
    first = http.page(b.website)
    if not first:
        entry["error"] = "site not reachable or robots.txt disallows"
        return entry
    final, html = first
    entry["ok"] = True
    entry["final_url"] = final
    domain = domain_of(final) or b.domain
    pages = [(final, html)]
    for u in _links(final, html, domain)[: max_pages - 1]:
        p = http.page(u)
        if p:
            pages.append(p)
    entry["pages"] = len(pages)
    blob = "\n".join(h for _, h in pages).lower()
    for url, h in pages:
        for e in _emails(h):
            dom = e.split("@")[1]
            if (dom == domain or dom.endswith("." + domain) or dom in FREEMAIL) and e not in [x["address"] for x in entry["emails"]]:
                entry["emails"].append({"address": e, "source_url": url})
        for t in re.findall(r'href=["\']tel:([^"\']+)', h, re.I):
            p = normalize_phone(htmllib.unescape(t))
            if p and p not in [x["number"] for x in entry["phones"]]:
                entry["phones"].append({"number": p, "source_url": url})
        if not entry["form"] and re.search(r"<form\b", h, re.I) and re.search(r"<textarea\b", h, re.I):
            entry["form"] = url
    sig = {}
    for group, names in SIGNALS.items():
        hits = [n for n, needles in names.items() if any(x in blob for x in needles)]
        if hits:
            sig[group] = hits
    sig["https"] = final.startswith("https://")
    sig["mobile"] = 'name="viewport"' in blob or "name=viewport" in blob
    sig["english"] = bool(re.search(r'hreflang=["\']en|/en/|lang=["\']en', blob))
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(20\d\d)", blob)]
    if years:
        sig["copyright_year"] = max(years)
    entry["signals"] = sig
    ig = re.search(r"instagram\.com/([A-Za-z0-9_.]+)", blob)
    fb = re.search(r"facebook\.com/([A-Za-z0-9_.-]+)", blob)
    entry["instagram"] = ig.group(1) if ig and ig.group(1) not in ("p", "explore", "sharer") else ""
    entry["facebook"] = fb.group(1) if fb and fb.group(1) not in ("sharer", "sharer.php", "tr", "plugins", "dialog") else ""
    return entry


def apply(b: Business, entry: dict) -> None:
    if not entry or not entry.get("ok"):
        b.signals["site_ok"] = False
        return
    b.signals["site_ok"] = True
    b.signals.update(entry.get("signals", {}))
    for e in entry.get("emails", []):
        b.emails.append(Email(address=e["address"], kind=classify_email(e["address"], b), source_url=e["source_url"]))
        b.note("email", "website", e["source_url"])
    phones = [(normalize_phone(p["number"]), p["source_url"]) for p in entry.get("phones", [])]
    phones = [p for p in phones if p[0]]
    if phones and not b.phone:
        b.phone, b.phone_source = phones[0][0], "own website"
        b.note("phone", "website", phones[0][1])
    if entry.get("form"):
        b.contact_form = entry["form"]
    b.instagram = b.instagram or entry.get("instagram", "")
    b.facebook = b.facebook or entry.get("facebook", "")
    b.emails.sort(key=lambda e: e.kind != "generic")


def _candidates(name: str) -> list[str]:
    from .text import FORM_WORDS
    toks = [t for t in fold(name).split() if t not in FORM_WORDS]
    if not toks:
        return []
    core = [t for t in toks if t not in ("ravintola", "kahvila", "restaurant", "cafe", "parturi", "kampaamo", "salon")] or toks
    out = []
    for parts in (toks, core):
        for sep in ("", "-"):
            stem = sep.join(parts)
            if 3 <= len(stem) <= 40:
                out += [f"{stem}.fi", f"{stem}.com"]
    return list(dict.fromkeys(out))[:4]


def guess_site(b: Business) -> str:
    """Try domains made from the name; accept one only if its homepage shows the business's distinctive name."""
    want = name_tokens(b.name)
    if not want:
        return ""
    for dom in _candidates(b.name):
        p = http.page(f"https://{dom}", timeout=(4, 8), max_bytes=400_000)
        if not p:
            continue
        text = fold(re.sub(r"<[^>]+>", " ", p[1]))
        if all(re.search(rf"\b{re.escape(t)}\b", text) for t in want):
            return p[0]
    return ""


class DomainGuesses:
    """data/domains.json: business id -> guessed website or "" (no personal data)."""

    def __init__(self, path: Path):
        self.path = path
        try:
            self.data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {}
        self.found = 0

    def run(self, businesses: list[Business], budget: int) -> None:
        # Storefronts on the map first: those are the ones a "no website" claim would be made about.
        todo = sorted((b for b in businesses if not b.website and b.id not in self.data), key=lambda b: not b.osm_ref)[:budget]
        with cf.ThreadPoolExecutor(16) as ex:
            for b, url in zip(todo, ex.map(_safe(guess_site, ""), todo)):
                self.data[b.id] = url
        for b in businesses:
            if b.id in self.data and not b.website:
                b.signals["site_searched"] = True
            url = self.data.get(b.id)
            if url and not b.website:
                b.website, b.domain = url, domain_of(url)
                b.note("website", "name_guess", url)
                self.found += 1

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")


class SiteCache:
    """private/sites.json: holds published contact details, so it lives with the other personal data."""

    def __init__(self, path: Path, refresh_days: int = 30):
        self.path, self.refresh = path, refresh_days
        try:
            self.data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {}
        self.stats = {"read": 0, "cached": 0, "failed": 0}

    def fresh(self, domain: str) -> bool:
        e = self.data.get(domain)
        if not e:
            return False
        age = (dt.date.today() - dt.date.fromisoformat(e["read"])).days
        return age < (self.refresh if e.get("ok") else 7)

    def crawl(self, businesses: list[Business], max_sites: int, max_pages: int) -> None:
        todo, seen = [], set()
        for b in businesses:
            if b.website and b.domain and b.domain not in seen:
                seen.add(b.domain)
                if self.fresh(b.domain):
                    self.stats["cached"] += 1
                else:
                    todo.append(b)
        # Registered companies first: their published generic address may be emailed (917/2014 § 202).
        todo.sort(key=lambda b: (b.legal_form_source != "prh", not b.osm_ref))
        todo = todo[:max_sites]
        with cf.ThreadPoolExecutor(16) as ex:
            failed = {"read": dt.date.today().isoformat(), "ok": False, "emails": [], "phones": [], "form": "",
                      "signals": {}, "instagram": "", "facebook": "", "pages": 0}
            for b, entry in zip(todo, ex.map(_safe(lambda x: read_site(x, max_pages), failed), todo)):
                self.data[b.domain] = entry
                self.stats["read" if entry["ok"] else "failed"] += 1

    def get(self, domain: str) -> dict | None:
        return self.data.get(domain)

    def prune(self, keep: set[str]) -> None:
        self.data = {k: v for k, v in self.data.items() if k in keep}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=0), encoding="utf-8")
