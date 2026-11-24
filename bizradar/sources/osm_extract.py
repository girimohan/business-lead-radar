"""OpenStreetMap from Geofabrik's daily Finland extract (data © OpenStreetMap contributors, ODbL 1.0).

For the whole country this replaces live Overpass queries, which the busy public servers often refuse
(HTTP 502/504, timeouts). The file (~780 MB) is downloaded at most once per `refresh_days` and read with
pyosmium; matches come out in the same shape as Overpass elements, so `osm.parse` handles both.
"""
from __future__ import annotations

import datetime as dt
import time
from pathlib import Path

from .. import http
from ..log import say

URL = "https://download.geofabrik.de/europe/finland-latest.osm.pbf"


def download(path: Path, refresh_days: int, url: str = URL) -> bool:
    """Fetch the extract unless the copy on disk is recent enough. True if a usable file is there."""
    if path.exists() and (time.time() - path.stat().st_mtime) < max(refresh_days, 1) * 86400:
        say(f"OSM: using the Finland map file from {dt.date.fromtimestamp(path.stat().st_mtime)}")
        return True
    say("OSM: downloading the Finland map file from Geofabrik (~780 MB)")
    part = path.with_suffix(".part")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with http.session().get(url, stream=True, timeout=(15, 120)) as r:
            r.raise_for_status()
            with part.open("wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
        part.replace(path)
        say(f"OSM: downloaded {path.stat().st_size / 1e6:,.0f} MB")
        return True
    except Exception as e:   # keep an older copy if there is one
        part.unlink(missing_ok=True)
        say(f"OSM: download failed ({type(e).__name__}: {e})" + ("; using the older copy" if path.exists() else ""))
        return path.exists()


def scan(path: Path, segments: dict) -> list[dict]:
    """Named places with any of the segments' tags, as Overpass-style elements (nodes and ways with a centre;
    relations without one, located later by their address)."""
    import osmium   # imported here so the rest of the radar runs without it

    pairs = [tuple(t.split("=", 1)) for s in segments.values() for t in s.get("osm", [])]
    if not pairs:
        return []
    fp = osmium.FileProcessor(str(path)).with_locations().with_filter(osmium.filter.TagFilter(*pairs))
    out = []
    for o in fp:
        tags = {t.k: t.v for t in o.tags}
        if not tags.get("name"):
            continue
        if o.is_node():
            if not o.location.valid():
                continue
            el = {"type": "node", "id": o.id, "lat": round(o.location.lat, 6), "lon": round(o.location.lon, 6)}
        elif o.is_way():
            pts = [(n.location.lat, n.location.lon) for n in o.nodes if n.location.valid()]
            el = {"type": "way", "id": o.id}
            if pts:
                el["center"] = {"lat": round(sum(p[0] for p in pts) / len(pts), 6),
                                "lon": round(sum(p[1] for p in pts) / len(pts), 6)}
        else:
            el = {"type": "relation", "id": o.id}
        el["tags"] = tags
        out.append(el)
    return out
