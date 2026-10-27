"""PROBNE granice županija: web/public/data/zupanije.geojson iz Natural Eartha.

Koriste se dok ne obradimo službene DGU granice (Upravne jedinice INSPIRE, issue #12).
Natural Earth je javna domena, ali granice su pojednostavljene (~200 m) i nema gradova
ni općina.

Pokretanje (samo ako zupanije.geojson ne postoji ili ga želiš ponovno napraviti):
    python pipeline/granice.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import requests
import shapely

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zupanije import ZUPANIJE  # noqa: E402

KORIJEN = Path(__file__).resolve().parent.parent
IZLAZ = KORIJEN / "web" / "public" / "data" / "zupanije.geojson"
CACHE = KORIJEN / "data" / "raw" / "_natural_earth" / "ne_10m_admin_1.geojson"
NE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_10m_admin_1_states_provinces.geojson"
)


def zupanije() -> gpd.GeoDataFrame:
    if not CACHE.exists():
        print("Preuzimam Natural Earth granice (oko 40 MB, samo prvi put)...")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(NE_URL, timeout=(10, 300))
        r.raise_for_status()
        CACHE.write_bytes(r.content)

    g = gpd.read_file(CACHE)
    hr = g[g["adm0_a3"] == "HRV"].copy()
    # Greška u Natural Earthu: Požeško-slavonska je upisana kao HR-12 (Brodsko-posavska).
    # Prepoznajemo je po FIPS oznaci HR11.
    hr.loc[hr["fips"] == "HR11", "iso_3166_2"] = "HR-11"
    hr["sifra"] = hr["iso_3166_2"].str.replace("HR-", "", regex=False)
    if sorted(hr["sifra"]) != sorted(ZUPANIJE):
        raise SystemExit(f"Neočekivane šifre županija: {sorted(hr['sifra'])}")
    hr["naziv"] = hr["sifra"].map(lambda s: ZUPANIJE[s][0])
    hr["kratki_naziv"] = hr["sifra"].map(lambda s: ZUPANIJE[s][1])
    hr = hr[["sifra", "naziv", "kratki_naziv", "geometry"]].sort_values("sifra")
    hr["geometry"] = hr.geometry.simplify(0.002, preserve_topology=True)
    hr["geometry"] = shapely.set_precision(hr.geometry.values, grid_size=1e-5)
    return hr.to_crs(4326)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    IZLAZ.parent.mkdir(parents=True, exist_ok=True)
    IZLAZ.write_text(zupanije().to_json(drop_id=True, ensure_ascii=False), encoding="utf-8")
    print(f"  {IZLAZ.relative_to(KORIJEN)}  ({IZLAZ.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
