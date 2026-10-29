"""Granice županija i gradova/općina iz DGU-a (Upravne jedinice INSPIRE, issue #12).

Izvor: data/raw/granice-upravne-jedinice/INSPIRE_Administrative_Units_(AU).zip
       (ATOM: https://geoportal.dgu.hr/services/atom/au/xml)
U ZIP-u je jedan GML (~600 MB) s 50.194 jedinice: država, 21 županija, 556 gradova
i općina, naselja te statistički i popisni krugovi, u projekciji ETRS89/LAEA (EPSG:3035).

GML se čita u jednom prolazu (iterparse), bez učitavanja cijele datoteke u memoriju,
i uzimaju se samo razine koje trebamo. Granice se pojednostavljuju kao CJELINA
(shapely.coverage_simplify): susjedne jedinice i dalje dijele istu granicu, bez rupa
i preklapanja između njih.

Ako DGU datoteke nema, koriste se probne granice županija iz Natural Eartha.

Pokretanje (samo granice):  python pipeline/granice.py
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import shapely
from shapely.geometry import MultiPolygon, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zupanije import ZUPANIJE  # noqa: E402

KORIJEN = Path(__file__).resolve().parent.parent
IZLAZ = KORIJEN / "web" / "public" / "data"
DGU_ZIP = KORIJEN / "data" / "raw" / "granice-upravne-jedinice"
NE_CACHE = KORIJEN / "data" / "raw" / "_natural_earth" / "ne_10m_admin_1.geojson"
NE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_10m_admin_1_states_provinces.geojson"
)

# Tolerancija pojednostavljenja u metrima (projekcija EPSG:3035)
TOL_ZUPANIJE = 400
TOL_JLS = 80

_AU = "{http://inspire.ec.europa.eu/schemas/au/4.0}"
_GN = "{http://inspire.ec.europa.eu/schemas/gn/4.0}"
_GML = "{http://www.opengis.net/gml/3.2}"
_XL = "{http://www.w3.org/1999/xlink}href"
RAZINE = {"1stOrder": "drzava", "2ndOrder": "zupanija", "3rdOrder": "jls"}


# --------------------------------------------------------------------------- čitanje DGU GML-a


def dgu_zip() -> Path | None:
    zipovi = sorted(DGU_ZIP.glob("*.zip")) if DGU_ZIP.exists() else []
    return zipovi[0] if zipovi else None


def _prsten(el) -> np.ndarray:
    # EPSG:3035 u GML-u ima redoslijed osi sjever, istok (N E), a shapely očekuje x, y (E N)
    return np.array(el.text.split(), dtype=float).reshape(-1, 2)[:, ::-1]


def _geometrija(el) -> MultiPolygon:
    poligoni = []
    for p in el.iter(_GML + "Polygon"):
        vanjski = p.find(f"{_GML}exterior/{_GML}LinearRing/{_GML}posList")
        unutarnji = [
            _prsten(r) for r in p.findall(f"{_GML}interior/{_GML}LinearRing/{_GML}posList")
        ]
        poligoni.append(Polygon(_prsten(vanjski), unutarnji))
    return MultiPolygon(poligoni)


def ucitaj_au(razine=("2ndOrder", "3rdOrder"), geometrija: bool = True) -> gpd.GeoDataFrame:
    """Upravne jedinice zadanih razina. Stupci: gml_id, razina, sifra, naziv, nadredeni_id,
    zupanija (šifra županije za JLS), geometry (EPSG:3035)."""
    put = dgu_zip()
    if put is None:
        raise FileNotFoundError("Nema DGU ZIP-a u data/raw/granice-upravne-jedinice/")
    redovi, geom = [], []
    with zipfile.ZipFile(put) as z:
        gml = next(n for n in z.namelist() if n.lower().endswith(".gml"))
        with z.open(gml) as f:
            for _, el in ET.iterparse(f, events=("end",)):
                if el.tag != _AU + "AdministrativeUnit":
                    continue
                lvl = el.find(_AU + "nationalLevel")
                lvl = lvl.get(_XL).rsplit("/", 1)[-1] if lvl is not None else ""
                if lvl in razine:
                    ime = el.find(
                        f"{_AU}name/{_GN}GeographicalName/{_GN}spelling/"
                        f"{_GN}SpellingOfName/{_GN}text"
                    )
                    gore = el.find(_AU + "upperLevelUnit")
                    redovi.append(
                        {
                            "gml_id": el.get(_GML + "id"),
                            "razina": RAZINE[lvl],
                            "sifra": el.findtext(_AU + "nationalCode", "").strip(),
                            "naziv": (ime.text or "").strip() if ime is not None else "",
                            "nadredeni_id": (gore.get(_XL) or "").lstrip("#")
                            if gore is not None
                            else "",
                        }
                    )
                    geom.append(_geometrija(el) if geometrija else None)
                el.clear()
    g = gpd.GeoDataFrame(redovi, geometry=geom, crs=3035)
    # Šifra županije za svaki grad/općinu, preko nadređene jedinice
    zup = dict(
        zip(
            g.loc[g.razina == "zupanija", "gml_id"],
            g.loc[g.razina == "zupanija", "sifra"],
            strict=True,
        )
    )
    g["zupanija"] = np.where(g.razina == "zupanija", g.sifra, g.nadredeni_id.map(zup))
    return g


def provjeri_au(g: gpd.GeoDataFrame) -> None:
    z, j = g[g.razina == "zupanija"], g[g.razina == "jls"]
    greske = []
    if sorted(z.sifra) != sorted(ZUPANIJE):
        greske.append(f"šifre županija: {sorted(z.sifra)}")
    if len(j) != 556 or j.sifra.duplicated().any():
        greske.append(f"JLS: {len(j)}, dvostruke šifre: {j.sifra.duplicated().sum()}")
    if j.zupanija.isna().any():
        greske.append(f"JLS bez županije: {j.zupanija.isna().sum()}")
    if greske:
        raise SystemExit("DGU granice – provjera nije prošla:\n  " + "\n  ".join(greske))


# --------------------------------------------------------------------------- obrada


def _pojednostavi(g: gpd.GeoDataFrame, tolerancija: float) -> gpd.GeoDataFrame:
    g = g.copy()
    g["geometry"] = shapely.make_valid(g.geometry.values)
    try:
        g["geometry"] = shapely.coverage_simplify(g.geometry.values, tolerancija)
    except Exception as e:  # npr. nevaljana pokrivenost – pojednostavi svaku zasebno
        print(f"  UPOZORENJE: coverage_simplify nije uspio ({e}); pojednostavljujem zasebno")
        g["geometry"] = g.geometry.simplify(tolerancija, preserve_topology=True)
    g = g.to_crs(4326)
    g["geometry"] = shapely.set_precision(g.geometry.values, grid_size=1e-5)
    return g


def _spremi(g: gpd.GeoDataFrame, ime: str) -> Path:
    put = IZLAZ / ime
    put.parent.mkdir(parents=True, exist_ok=True)
    put.write_text(g.to_json(drop_id=True, ensure_ascii=False), encoding="utf-8")
    return put


def izvezi_dgu(areas: pd.DataFrame | None = None) -> dict:
    """zupanije.geojson + jls/<zz>.geojson iz DGU podataka. Vraća sažetak za ispis."""
    g = ucitaj_au()
    provjeri_au(g)

    z = g[g.razina == "zupanija"].copy()
    z["naziv"] = z.sifra.map(lambda s: ZUPANIJE[s][0])
    z["kratki_naziv"] = z.sifra.map(lambda s: ZUPANIJE[s][1])
    z = _pojednostavi(
        z[["sifra", "naziv", "kratki_naziv", "geometry"]].sort_values("sifra"), TOL_ZUPANIJE
    )
    put = _spremi(z, "zupanije.geojson")
    print(f"  {put.relative_to(KORIJEN)}  ({put.stat().st_size / 1024:.0f} KB)")

    j = g[g.razina == "jls"].copy()
    j["vrsta"] = None
    if areas is not None:  # nazivi i vrsta (grad/općina) iz šifrarnika
        a = areas[areas.vrsta != "zupanija"].set_index("sifra")
        j["vrsta"] = j.sifra.map(a["vrsta"])
        j["naziv"] = j.sifra.map(a["naziv"]).fillna(j["naziv"])
    j = _pojednostavi(j[["sifra", "naziv", "vrsta", "zupanija", "geometry"]], TOL_JLS)
    ukupno = 0
    for sif, dio in j.groupby("zupanija"):
        put = _spremi(dio.sort_values("sifra"), f"jls/{sif}.geojson")
        ukupno += put.stat().st_size
    print(f"  web/public/data/jls/01–21.geojson  (21 datoteka, ukupno {ukupno / 1024:.0f} KB)")
    return {"zupanija": len(z), "jls": len(j)}


# --------------------------------------------------------------------------- probne granice


def zupanije_natural_earth() -> gpd.GeoDataFrame:
    """PROBNE granice županija (Natural Earth), samo ako DGU datoteke nema."""
    if not NE_CACHE.exists():
        print("Preuzimam Natural Earth granice (oko 40 MB, samo prvi put)...")
        NE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(NE_URL, timeout=(10, 300))
        r.raise_for_status()
        NE_CACHE.write_bytes(r.content)
    g = gpd.read_file(NE_CACHE)
    hr = g[g["adm0_a3"] == "HRV"].copy()
    # Greška u Natural Earthu: Požeško-slavonska je upisana kao HR-12. Prepoznaje se po FIPS HR11.
    hr.loc[hr["fips"] == "HR11", "iso_3166_2"] = "HR-11"
    hr["sifra"] = hr["iso_3166_2"].str.replace("HR-", "", regex=False)
    hr["naziv"] = hr["sifra"].map(lambda s: ZUPANIJE[s][0])
    hr["kratki_naziv"] = hr["sifra"].map(lambda s: ZUPANIJE[s][1])
    hr = hr[["sifra", "naziv", "kratki_naziv", "geometry"]].sort_values("sifra")
    hr["geometry"] = hr.geometry.simplify(0.002, preserve_topology=True)
    hr["geometry"] = shapely.set_precision(hr.geometry.values, grid_size=1e-5)
    return hr.to_crs(4326)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if dgu_zip():
        print("Granice iz DGU-a (Upravne jedinice INSPIRE)")
        izvezi_dgu()
    else:
        print("Nema DGU granica – radim PROBNE granice županija (Natural Earth)")
        put = _spremi(zupanije_natural_earth(), "zupanije.geojson")
        print(f"  {put.relative_to(KORIJEN)}")


if __name__ == "__main__":
    main()
