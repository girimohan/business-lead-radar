"""Municipality and region for every lead, so the whole of Finland can be filtered by region and town.

Data: Statistics Finland (Tilastokeskus) open data, CC BY 4.0: postcode areas 2026 (postcode -> municipality),
municipality borders 1:4.5M 2026, and the municipality -> region (maakunta) classification. `python -m bizradar
geo` downloads it once into data/geo.json (public statistics, no personal data, committed with the code).

Lookup order: postcode, then the map point (OpenStreetMap places), then the town name.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import http

WFS = "https://geo.stat.fi/geoserver/{ns}/wfs"
CLASS = "https://data.stat.fi/api/classifications/v2"
YEAR = "2026"


def download(path: Path) -> dict:
    pno = http.get(WFS.format(ns="postialue"), params={
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeName": f"postialue:pno_{YEAR}",
        "outputFormat": "json", "propertyName": "posti_alue,kunta"})
    kunta = http.get(WFS.format(ns="tilastointialueet"), params={
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeName": f"tilastointialueet:kunta4500k_{YEAR}", "outputFormat": "json", "srsName": "EPSG:4326"})
    maps = http.get(f"{CLASS}/correspondenceTables/kunta_1_{YEAR}0101%23maakunta_1_{YEAR}0101/maps",
                    params={"content": "data", "meta": "min", "lang": "fi"})
    regions = http.get(f"{CLASS}/classifications/maakunta_1_{YEAR}0101/classificationItems",
                       params={"content": "data", "meta": "min", "lang": "fi"})
    if not (pno and kunta and maps and regions):
        raise RuntimeError("Statistics Finland download failed")
    region_of = {m["sourceLocalId"].split("/")[-1]: m["targetLocalId"].split("/")[-1] for m in maps}
    out = {
        "source": "Statistics Finland (Tilastokeskus), CC BY 4.0: postcode areas, municipality borders, regions "
                  + YEAR,
        "regions": {r["code"]: r["classificationItemNames"][0]["name"] for r in regions},
        "municipalities": {}, "postcodes": {}, "shapes": {},
    }
    for f in kunta["features"]:
        p, g = f["properties"], f["geometry"]
        out["municipalities"][p["kunta"]] = [p["nimi"], p["namn"], region_of.get(p["kunta"], "")]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        out["shapes"][p["kunta"]] = [[[[round(x, 4), round(y, 4)] for x, y in ring] for ring in poly] for poly in polys]
    for f in pno["features"]:
        p = f["properties"]
        out["postcodes"][p["posti_alue"]] = p["kunta"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out


def _inside(x: float, y: float, rings: list) -> bool:
    hit = False
    for ring in rings:                       # even-odd over outer ring and holes
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi = ring[i]
            xj, yj = ring[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                hit = not hit
            j = i
    return hit


class Geo:
    def __init__(self, path: Path):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            d = {"regions": {}, "municipalities": {}, "postcodes": {}, "shapes": {}}
        self.ok = bool(d["municipalities"])
        self.regions = d["regions"]
        self.munis = d["municipalities"]
        self.postcodes = d["postcodes"]
        self.by_name = {}
        for code, (fi, sv, _) in self.munis.items():
            self.by_name[fi.lower()] = code
            self.by_name[sv.lower()] = code
        self.boxes = []
        for code, polys in d["shapes"].items():
            for poly in polys:
                xs = [p[0] for p in poly[0]]
                ys = [p[1] for p in poly[0]]
                self.boxes.append((min(xs), min(ys), max(xs), max(ys), code, poly))

    def code_at(self, lat: float, lon: float) -> str:
        for x0, y0, x1, y1, code, poly in self.boxes:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and _inside(lon, lat, poly):
                return code
        return ""

    def locate(self, postcode: str = "", lat: float | None = None, lon: float | None = None, city: str = "") -> str:
        """Municipality code, or "" if nothing matches."""
        code = self.postcodes.get((postcode or "").strip())
        if not code and lat is not None and lon is not None:
            code = self.code_at(lat, lon)
        if not code and city:
            code = self.by_name.get(city.strip().lower(), "")
        return code or ""

    def names(self, code: str) -> tuple[str, str]:
        """(municipality, region) in Finnish."""
        m = self.munis.get(code)
        if not m:
            return "", ""
        return m[0], self.regions.get(m[2], "")

    def is_municipality(self, name: str) -> bool:
        return name.strip().lower() in self.by_name

    def region_boxes(self) -> dict[str, tuple[float, float, float, float]]:
        """Region name -> (south, west, north, east), the box around its municipalities (for map queries)."""
        out: dict[str, list[float]] = {}
        for x0, y0, x1, y1, code, _ in self.boxes:
            r = self.names(code)[1]
            if not r:
                continue
            b = out.setdefault(r, [y0, x0, y1, x1])
            b[:] = [min(b[0], y0), min(b[1], x0), max(b[2], y1), max(b[3], x1)]
        return {r: tuple(round(v, 3) for v in b) for r, b in sorted(out.items())}

    def is_region(self, name: str) -> bool:
        return name.strip().lower() in {r.lower() for r in self.regions.values()}
