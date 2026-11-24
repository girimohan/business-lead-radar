from __future__ import annotations

import threading
import time
import urllib.robotparser
from urllib.parse import urlsplit

import requests

USER_AGENT = "business-lead-radar/0.1 (small-business prospecting tool; one visit per site per run)"
_local = threading.local()
_robots: dict[str, urllib.robotparser.RobotFileParser] = {}
_robots_lock = threading.Lock()


def session() -> requests.Session:
    if not hasattr(_local, "s"):
        _local.s = requests.Session()
        _local.s.headers["User-Agent"] = USER_AGENT
        _local.s.headers["Accept"] = "application/json, text/html;q=0.9, */*;q=0.5"
        _local.s.headers["Accept-Language"] = "fi, en;q=0.9, sv;q=0.8"
    return _local.s


class FetchError(Exception):
    pass


def request(method: str, url: str, *, as_json: bool = True, tries: int = 3, timeout=(8, 60), **kw):
    """GET/POST with polite retries. Returns None for 404/410; raises FetchError otherwise."""
    last = "no attempt"
    for attempt in range(tries):
        try:
            r = session().request(method, url, timeout=timeout, **kw)
        except requests.RequestException as e:
            last = type(e).__name__
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code in (404, 410):
            return None
        if r.status_code in (429, 504) or r.status_code >= 500:
            last = f"HTTP {r.status_code}"
            time.sleep(6 * (attempt + 1))
            continue
        if not r.ok:
            raise FetchError(f"HTTP {r.status_code} for {url}")
        if not as_json:
            return r.text
        try:
            return r.json()
        except ValueError as e:
            raise FetchError(f"bad JSON from {url}") from e
    raise FetchError(f"{last} for {url}")


def get(url: str, **kw):
    return request("GET", url, **kw)


def allowed(url: str) -> bool:
    """robots.txt check for business websites. A robots.txt that cannot be read is treated as allowing."""
    parts = urlsplit(url)
    base = f"{parts.scheme}://{parts.netloc}"
    with _robots_lock:
        rp = _robots.get(base)
    if rp is None:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = session().get(base + "/robots.txt", timeout=(5, 10))
            rp.parse(r.text.splitlines() if r.ok else [])
        except requests.RequestException:
            rp.parse([])
        with _robots_lock:
            _robots[base] = rp
    return rp.can_fetch(USER_AGENT, url)


def page(url: str, timeout=(6, 15), max_bytes: int = 1_500_000) -> tuple[str, str] | None:
    """Fetch an HTML page if robots.txt allows. Returns (final_url, html) or None."""
    if not allowed(url):
        return None
    try:
        r = session().get(url, timeout=timeout, allow_redirects=True, stream=True)
        if not r.ok or "html" not in r.headers.get("Content-Type", "html"):
            return None
        body = r.raw.read(max_bytes, decode_content=True)
        try:   # most Finnish sites are UTF-8 even when the header says otherwise
            return r.url, body.decode("utf-8")
        except UnicodeDecodeError:
            return r.url, body.decode(r.encoding or "cp1252", errors="replace")
    except (requests.RequestException, LookupError, OSError):
        return None
