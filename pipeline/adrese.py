"""Adrese DGU (INSPIRE AD) i pretvaranje adresa u točke (geokodiranje).

DGU objavljuje sve kućne brojeve Hrvatske (oko 1,7 milijuna) u jednoj ZIP datoteci s četiri
GML-a: Address (kućni broj i točka), ThoroughfareName (ulice), AdminUnitName (naselja) i
PostalDescriptor (pošte). Adresa na ulicu i naselje pokazuje poveznicom (xlink).

Address.gml ima 2,6 GB, pa se ne čita XML parserom nego se prolazi kao tekst, zapis po
zapis, i zadržavaju se samo adrese unutar odabranih gradova. Rezultat se sprema u
data/raw/dgu-adrese/_adrese_gradovi.csv da sljedeće pokretanje traje sekundu.

Koordinate su u EPSG:3035 s redoslijedom osi sjever–istok (kao i granice), pa se okreću.
"""

from __future__ import annotations

import difflib
import json
import re
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from citaci import RAW
from izvoz import IZLAZ
from nazivi import kljuc

MAPA = RAW / "dgu-adrese"
PREDMEMORIJA = MAPA / "_adrese_gradovi.csv"

_ID = re.compile(r'gml:id="(?:ThoroughfareName|AdminUnitName|PostalDescriptor)\.(\d+)"')
_TEKST = re.compile(r"<gn:text>([^<]*)</gn:text>")
_POSTA = re.compile(r"<ad:postCode>([^<]*)</ad:postCode>")
_OZNAKA = re.compile(r"<ad:designator>([^<]*)</ad:designator><ad:type xlink:href=\"[^\"]*/(\w+)\"")
_DIO = re.compile(
    r'<ad:component xlink:href="#(ThoroughfareName|AdminUnitName|PostalDescriptor)\.(\d+)"'
)


def dgu_zip() -> Path | None:
    p = sorted(MAPA.glob("*.zip")) if MAPA.exists() else []
    return p[0] if p else None


def _nazivi(z: zipfile.ZipFile, ime: str, uzorak: re.Pattern = _TEKST) -> dict[str, str]:
    """gml:id → naziv (ulice, naselja) ili poštanski broj."""
    tekst = z.read(ime).decode("utf-8")
    out = {}
    for zapis in tekst.split("</wfs:member>"):
        m, n = _ID.search(zapis), uzorak.search(zapis)
        if m and n:
            out[m.group(1)] = n.group(1).strip()
    return out


def _poligoni(sifre: tuple[str, ...]) -> gpd.GeoDataFrame:
    """Granice traženih gradova iz web/public/data/jls/*.geojson (EPSG:3035)."""
    g = pd.concat([gpd.read_file(p) for p in sorted((IZLAZ / "jls").glob("*.geojson"))])
    g = g[g["sifra"].isin(sifre)][["sifra", "geometry"]]
    if len(g) != len(sifre):
        raise ValueError(f"Granice nisu pronađene za sve gradove: {sifre}")
    return gpd.GeoDataFrame(g, crs=4326).to_crs(3035)


def _izvadi(sifre: tuple[str, ...]) -> pd.DataFrame:
    put = dgu_zip()
    if put is None:
        raise FileNotFoundError(
            "nema data/raw/dgu-adrese/*.zip – python pipeline/download.py --samo dgu-adrese"
        )
    poligoni = _poligoni(sifre)
    # okvir oko gradova u (sjever, istok) poretku kako piše u GML-u
    x0, y0, x1, y1 = poligoni.total_bounds
    retci = []
    with zipfile.ZipFile(put) as z:
        ulice = _nazivi(z, "ThoroughfareName.gml")
        naselja = _nazivi(z, "AdminUnitName.gml")
        poste = _nazivi(z, "PostalDescriptor.gml", _POSTA)
        ostatak = ""
        with z.open("Address.gml") as f:
            while blok := f.read(64 * 1024 * 1024):
                ostatak += blok.decode("utf-8")
                zapisi = ostatak.split("</ad:Address>")
                ostatak = zapisi.pop()
                for d in zapisi:
                    i = d.find("<gml:pos>")
                    if i < 0:
                        continue
                    sjever, istok = map(float, d[i + 9 : d.find("</gml:pos>", i)].split())
                    if not (x0 <= istok <= x1 and y0 <= sjever <= y1):
                        continue
                    broj = dodatak = ""
                    for vrijednost, vrsta in _OZNAKA.findall(d):
                        if vrsta == "addressNumber":
                            broj = vrijednost
                        elif vrsta == "addressNumberExtension":
                            dodatak = vrijednost
                    dijelovi: dict[str, str] = {}
                    for vrsta, oznaka in _DIO.findall(d):
                        dijelovi.setdefault(vrsta, oznaka)  # prvo naselje, zatim država
                    retci.append(
                        (
                            istok,
                            sjever,
                            ulice.get(dijelovi.get("ThoroughfareName", ""), ""),
                            broj,
                            dodatak,
                            naselja.get(dijelovi.get("AdminUnitName", ""), ""),
                            poste.get(dijelovi.get("PostalDescriptor", ""), ""),
                        )
                    )
    t = pd.DataFrame(retci, columns=["x", "y", "ulica", "broj", "dodatak", "naselje", "posta"])
    g = gpd.GeoDataFrame(t, geometry=gpd.points_from_xy(t.x, t.y), crs=3035)
    g = gpd.sjoin(g, poligoni, how="inner", predicate="within").to_crs(4326)
    g["lon"] = g.geometry.x.round(6)
    g["lat"] = g.geometry.y.round(6)
    return pd.DataFrame(g[["sifra", "ulica", "broj", "dodatak", "naselje", "posta", "lon", "lat"]])


def adrese_gradova(sifre: tuple[str, ...]) -> pd.DataFrame:
    """Sve adrese u zadanim gradovima/općinama (šifre JLS). Rezultat se pamti na disku."""
    put = dgu_zip()
    if put is None:
        raise FileNotFoundError(
            "nema data/raw/dgu-adrese/*.zip – python pipeline/download.py --samo dgu-adrese"
        )
    potpis = {"zip": put.name, "velicina": put.stat().st_size, "sifre": sorted(sifre)}
    opis = PREDMEMORIJA.with_suffix(".json")
    if PREDMEMORIJA.exists() and opis.exists() and json.loads(opis.read_text()) == potpis:
        return pd.read_csv(PREDMEMORIJA, dtype=str, keep_default_na=False).astype(
            {"lon": float, "lat": float}
        )
    print("  adrese DGU: prvo čitanje Address.gml (2,6 GB), oko pola minute…")
    t = _izvadi(sifre)
    t.to_csv(PREDMEMORIJA, index=False, encoding="utf-8")
    opis.write_text(json.dumps(potpis))
    return t


# --------------------------------------------------------------------------- spajanje


_SKRATI = {
    "ULICA": "",
    "UL": "",
    "TRG": "TRG",
    "SV": "SVETOG",
    "SVETOG": "SVETOG",
    "SVETE": "SVETE",
    "BRAĆE": "BRAĆE",
    "DR": "",
}


def kljuc_ulice(naziv: str) -> str:
    """Ulica bez riječi 'ulica', točaka i redoslijeda riječi: 'Ulica grada Vukovara' =
    'GRADA VUKOVARA ULICA' = 'ULICA GRADA VUKOVARA'."""
    s = kljuc(re.sub(r"[.,]", " ", str(naziv)))
    rijeci = [_SKRATI.get(r, r) for r in s.split()]
    return " ".join(sorted(r for r in rijeci if r))


def posvojni(genitiv: str) -> str:
    """Prezime u genitivu → posvojni pridjev: 'Barčića' → 'BARČIĆEVA', 'Heinzela' →
    'HEINZELOVA'. Tako 'Ulica Erazma Barčića' (DGU) odgovara 'BARČIĆEVA' (Grad Zagreb)."""
    s = kljuc(genitiv)
    if s.endswith("OGA"):
        return s[:-1]  # Slavenskoga → SLAVENSKOG
    if not s.endswith("A") or len(s) < 4:
        return ""
    korijen = s[:-1]
    meki = korijen.endswith(("Č", "Ć", "Š", "Ž", "J", "C", "DŽ", "Đ", "LJ", "NJ"))
    return korijen + ("EVA" if meki else "OVA")


def _kljucevi_ulice(naziv: str) -> list[str]:
    kljucevi = [kljuc_ulice(naziv)]
    rijeci = str(naziv).split()
    if len(rijeci) >= 2 and kljuc(rijeci[0]) in ("ULICA", "TRG"):
        p = posvojni(rijeci[-1])
        if p:
            kljucevi.append(kljuc_ulice(("TRG " if kljuc(rijeci[0]) == "TRG" else "") + p))
    if kljuc(rijeci[-1]) == "ULICA" and len(rijeci) == 2:
        p = posvojni(rijeci[0])
        if p:
            kljucevi.append(kljuc_ulice(p))
    return kljucevi


def _najbliza_ulica(k: str, poznate: list[str]) -> str | None:
    """Kratice ('TRG HRV. BRANITELJA DOM. RATA') i sitne razlike u pisanju ('KENNEDYA')."""
    rijeci = k.split()
    for p in poznate:
        pr = p.split()
        if len(pr) == len(rijeci) and all(
            a == b or (len(a) >= 3 and b.startswith(a)) for a, b in zip(rijeci, pr, strict=True)
        ):
            return p
    slicne = difflib.get_close_matches(k, poznate, n=1, cutoff=0.88)
    return slicne[0] if slicne else None


def razdvoji_broj(tekst: str) -> tuple[str, str, str]:
    """'ILICA 0297' → ('ILICA', '297', ''); 'ALEJA LIPA 0001/A' → ('ALEJA LIPA', '1', 'A');
    'VRBIK X. 0004' → ('VRBIK X.', '4', '')."""
    t = re.sub(r"\s+DV\.?$", "", str(tekst).strip())  # "DV" = ulaz iz dvorišta
    t = re.sub(r"/\s*(\d+|BB)$", "", t)  # broj stana ili "bez broja"
    m = re.match(r"^(.*?)[ ,]+0*(\d*)\s*/?\s*([A-ZČĆŽŠĐa-zčćžšđ]?)\s*$", t)
    if not m:
        return t, "", ""
    return m.group(1).strip(), m.group(2), m.group(3).upper()


def geokodiraj(
    tablica: pd.DataFrame,
    adrese: pd.DataFrame,
    jls: str,
    cetvrti: gpd.GeoDataFrame | None = None,
) -> pd.DataFrame:
    """Dodaje stupce lon, lat i nacin tablici sa stupcima ulica, broj, dodatak (i po želji
    cetvrt = šifra gradske četvrti).

    Ulica se prvo prevodi na DGU naziv (isti ključ, posvojni oblik, kratica ili sitna
    razlika u pisanju), a zatim se traži:
      "tocno"        – ista ulica, broj i slovo,
      "bez dodatka"  – ista ulica i broj (izvor ili DGU nema slovo),
      "ulica"        – samo ulica (broj ne postoji ili je "bez broja"): sredina ulice.
    Ako ista adresa postoji u više naselja grada, bira se ona u istoj četvrti.
    """
    a = adrese[adrese["sifra"] == jls].copy()
    a["naziv"] = a["ulica"].where(a["ulica"] != "", a["naselje"])
    a["broj"] = a["broj"].str.lstrip("0")
    a["dodatak"] = a["dodatak"].str.upper()
    if cetvrti is not None:
        tg = gpd.GeoDataFrame(a, geometry=gpd.points_from_xy(a.lon, a.lat), crs=4326)
        c = cetvrti[["sifra", "geometry"]].rename(columns={"sifra": "cetvrt_a"})
        s = gpd.sjoin(tg, c, how="left", predicate="within")
        a["cetvrt_a"] = s.loc[~s.index.duplicated(), "cetvrt_a"]
    else:
        a["cetvrt_a"] = None
    # jedna DGU ulica može imati više ključeva (puni naziv i posvojni oblik)
    nazivi = {n: _kljucevi_ulice(n) for n in a["naziv"].unique()}
    a = a.assign(k=a["naziv"].map(nazivi)).explode("k")
    poznate = sorted(set(a["k"]))
    skup = set(poznate)

    t = tablica.copy()
    t["k0"] = t["ulica"].fillna("").map(kljuc_ulice)
    prijevod = {k: (k if k in skup else _najbliza_ulica(k, poznate)) for k in t["k0"].unique()}
    t["k"] = t["k0"].map(prijevod)
    t["broj"] = t["broj"].fillna("").astype(str).str.lstrip("0")
    t["dodatak"] = t["dodatak"].fillna("").astype(str).str.upper()
    if "cetvrt" not in t:
        t["cetvrt"] = None
    t["lon"] = t["lat"] = float("nan")
    t["nacin"] = None

    def upisi(spoj: pd.DataFrame, nacin: str) -> None:
        spoj = spoj.assign(ista=spoj["cetvrt"] == spoj["cetvrt_a"])
        spoj = spoj.sort_values("ista", ascending=False).drop_duplicates("index")
        spoj = spoj.set_index("index")
        t.loc[spoj.index, ["lon", "lat"]] = spoj[["lon_a", "lat_a"]].to_numpy()
        t.loc[spoj.index, "nacin"] = nacin

    for nacin, kljucevi in (("tocno", ["k", "broj", "dodatak"]), ("bez dodatka", ["k", "broj"])):
        ostali = t[t["nacin"].isna() & t["k"].notna() & (t["broj"] != "")].reset_index()
        kand = a.drop_duplicates(kljucevi + ["cetvrt_a"])[
            kljucevi + ["cetvrt_a", "lon", "lat"]
        ].rename(columns={"lon": "lon_a", "lat": "lat_a"})
        upisi(ostali[["index", "cetvrt", *kljucevi]].merge(kand, on=kljucevi), nacin)

    ostali = t[t["nacin"].isna() & t["k"].notna()].reset_index()
    sredine = (
        a.groupby(["k", "cetvrt_a"], dropna=False)[["lon", "lat"]]
        .median()
        .reset_index()
        .rename(columns={"lon": "lon_a", "lat": "lat_a"})
    )
    upisi(ostali[["index", "cetvrt", "k"]].merge(sredine, on="k"), "ulica")
    return t.drop(columns=["k", "k0"])
