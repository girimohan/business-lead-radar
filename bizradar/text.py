from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit

# Words that say what kind of company it is, not which one. Dropped when names are compared.
FORM_WORDS = {"oy", "oyj", "ab", "ky", "ay", "tmi", "toiminimi", "osk", "osuuskunta", "ltd", "kb", "ab", "inc",
              "kommandiittiyhtio", "osakeyhtio", "avoin", "yhtio", "co", "company", "tmi."}
NOISE_WORDS = {"parturi", "kampaamo", "parturikampaamo", "parturi-kampaamo", "ravintola", "kahvila", "cafe", "kafe",
               "restaurant", "salon", "salong", "studio", "hius", "hiusstudio", "kauneushoitola", "kauneus", "beauty",
               "hair", "barber", "barbershop", "pizzeria", "kebab", "grill", "bar", "baari", "the", "and", "ja", "&"}


def fold(s: str) -> str:
    """Lower case, accents off (ä->a, ö->o), punctuation to spaces."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def name_tokens(name: str, drop_noise: bool = True) -> set[str]:
    toks = set(fold(name).split()) - FORM_WORDS
    if drop_noise:
        core = toks - NOISE_WORDS
        return core or toks
    return toks


def name_similarity(a: str, b: str) -> float:
    """Jaccard similarity of the distinctive words of two business names (0..1)."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def legal_form_from_name(name: str) -> str:
    """Company form from the name's suffix. A missing suffix proves nothing (signs rarely say 'Oy')."""
    toks = fold(name).split()
    if not toks:
        return "unknown"
    if any(t in ("oy", "oyj", "ab", "osakeyhtio") for t in toks):
        return "oy"
    if any(t in ("ky", "kommandiittiyhtio") for t in toks):
        return "ky"
    if "ay" in toks or "avoin yhtio" in fold(name):
        return "ay"
    if any(t in ("osk", "osuuskunta") for t in toks):
        return "osk"
    if any(t in ("tmi", "toiminimi") for t in toks):
        return "tmi"
    return "unknown"


def domain_of(url: str) -> str:
    if not url:
        return ""
    if "://" not in url:
        url = "http://" + url
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url.lstrip("/")
    return url


def normalize_phone(p: str) -> str:
    """Finnish numbers to +358 form; other text returned trimmed."""
    p = (p or "").split(";")[0].strip()
    digits = re.sub(r"[^\d+]", "", p)
    if digits.startswith("00358"):
        digits = "+" + digits[2:]
    elif digits.startswith("0") and len(digits) >= 7:
        digits = "+358" + digits[1:]
    elif digits.startswith("358"):
        digits = "+" + digits
    n = len(digits) - 1
    if not digits.startswith("+") or n < 8 or n > 15 or (digits.startswith("+358") and not 9 <= n <= 13):
        return ""
    return digits
