"""Faze 5 i 6: detaljni prikaz Zagreba i Rijeke (issue #16).

Zagreb ima 17 gradskih četvrti sa službenim šiframa (RPJ, Grad Zagreb), pa se ostali
gradski skupovi na njih spajaju:
  - po nazivu četvrti (prazni prostori, stvarno korištenje površina),
  - po koordinatama (kapitalna ulaganja, smještajni objekti).

Rijeka nema otvorene granice mjesnih odbora ni koordinate prostora, pa za nju dajemo
gradske zbrojeve: proračun, poslovni prostori u zakupu i EU projekte.

Proračun obaju gradova svodi se na istu funkcijsku (COFOG) i ekonomsku klasifikaciju,
pa se može usporediti po stanovniku.

Izlaz: web/public/data/gradovi/ (opis u docs/format-podataka.md).
Pokretanje: python pipeline/gradovi.py  (ili kao dio build.py)
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from datetime import UTC, datetime

import geopandas as gpd
import pandas as pd
from citaci import RAW, TECAJ_HRK, broj, excel, nadji
from izvoz import IZLAZ, KORIJEN, dodaj_rang
from nazivi import kljuc

CILJ = IZLAZ / "gradovi"
HTRS = 3765  # HTRS96/TM, metrički sustav za površine
ZAGREB = "01333"
RIJEKA = "03735"

# Funkcijska klasifikacija (COFOG), razina odjeljka
FUNKCIJE = {
    "01": "Opće javne usluge",
    "02": "Obrana",
    "03": "Javni red i sigurnost",
    "04": "Ekonomski poslovi",
    "05": "Zaštita okoliša",
    "06": "Stanovanje i komunalni razvoj",
    "07": "Zdravstvo",
    "08": "Rekreacija, kultura i religija",
    "09": "Obrazovanje",
    "10": "Socijalna zaštita",
}

# Računski plan, skupine prihoda (razred 6 i 7)
PRIHODI = {
    "61": "Porezi",
    "63": "Pomoći (EU, država, drugi proračuni)",
    "64": "Prihodi od imovine",
    "65": "Pristojbe i naknade (komunalna naknada, doprinos…)",
    "66": "Prodaja usluga i donacije",
    "67": "Iz nadležnog proračuna i HZZO-a",
    "68": "Kazne i ostali prihodi",
    "71": "Prodaja zemljišta",
    "72": "Prodaja zgrada i opreme",
}

NAPOMENA_PRORACUN = {
    ZAGREB: "Grad Zagreb je ujedno i županija, pa njegov proračun uključuje i županijske "
    "poslove (bolnice, srednje škole, domove za starije). Zato su zdravstvo i obrazovanje "
    "po stanovniku znatno veći nego u drugim gradovima.",
    RIJEKA: "Plan Grada Rijeke s proračunskim korisnicima (vrtići, osnovne škole, ustanove "
    "u kulturi). Bolnice i srednje škole financira Primorsko-goranska županija.",
}

# Pokazatelji po gradskim četvrtima Zagreba
POKAZATELJI_CETVRTI: dict[str, dict] = {
    "povrsina": {
        "naziv": "Površina",
        "tema": "imovina",
        "jedinica": "km²",
        "decimale": 1,
        "izvor": "zg-cetvrti",
    },
    "kapitalna_ulaganja": {
        "naziv": "Kapitalna ulaganja Grada (plan)",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "izvor": "zg-kapitalna-2024",
        "napomena": "Plan kapitalnih ulaganja u objekte društvenih djelatnosti i obnovu "
        "nakon potresa; raspoređeno prema lokaciji objekta.",
    },
    "kapitalni_projekti": {
        "naziv": "Broj kapitalnih projekata",
        "tema": "novac",
        "jedinica": "broj",
        "decimale": 0,
        "izvor": "zg-kapitalna-2024",
    },
    "smjestajni_objekti": {
        "naziv": "Smještajni objekti (turizam)",
        "tema": "novac",
        "jedinica": "broj",
        "decimale": 0,
        "izvor": "zg-smjestajni-objekti",
        "napomena": "Hoteli, hosteli i smještaj u domaćinstvu.",
    },
    "prazni_poslovni_prostori": {
        "naziv": "Prazni gradski poslovni prostori",
        "tema": "imovina",
        "jedinica": "broj",
        "decimale": 0,
        "izvor": "zg-prazni-prostori",
        "napomena": "Prostori u vlasništvu Grada koji su slobodni za zakup, uključujući "
        "one koji ne ispunjavaju uvjete za korištenje.",
    },
    "prazni_poslovni_prostori_m2": {
        "naziv": "Površina praznih gradskih poslovnih prostora",
        "tema": "imovina",
        "jedinica": "m²",
        "decimale": 0,
        "izvor": "zg-prazni-prostori",
    },
    "prazne_garaze": {
        "naziv": "Prazne gradske garaže i parkirna mjesta",
        "tema": "imovina",
        "jedinica": "broj",
        "decimale": 0,
        "izvor": "zg-prazni-prostori",
    },
    "brownfield": {
        "naziv": "Brownfield (napuštene izgrađene površine)",
        "tema": "imovina",
        "jedinica": "ha",
        "decimale": 1,
        "izvor": "zg-stvarno-koristenje",
    },
    "udio_gospodarske_povrsine": {
        "naziv": "Udio gospodarskih površina",
        "tema": "imovina",
        "jedinica": "%",
        "decimale": 1,
        "izvor": "zg-stvarno-koristenje",
        "napomena": "Poslovne, proizvodne, trgovačke i ugostiteljske površine.",
    },
    "udio_stambene_povrsine": {
        "naziv": "Udio stambenih i mješovitih površina",
        "tema": "imovina",
        "jedinica": "%",
        "decimale": 1,
        "izvor": "zg-stvarno-koristenje",
    },
    "gospodarske_zone": {
        "naziv": "Gospodarske zone (prostorni planovi)",
        "tema": "imovina",
        "jedinica": "ha",
        "decimale": 1,
        "izvor": "zg-planirana-namjena",
        "napomena": "Površine koje prostorni planovi namjenjuju poslovnoj, proizvodnoj, "
        "trgovačkoj i ugostiteljsko-turističkoj djelatnosti.",
    },
    "gospodarske_zone_neizgradjene": {
        "naziv": "Neizgrađene gospodarske zone",
        "tema": "imovina",
        "jedinica": "ha",
        "decimale": 1,
        "izvor": "zg-planirana-namjena",
        "napomena": "Samo površine koje plan izričito označava kao neizgrađene ili "
        "planirane; za ostale planove izgrađenost nije poznata.",
    },
    "udio_zelene_povrsine": {
        "naziv": "Udio parkova i šuma",
        "tema": "imovina",
        "jedinica": "%",
        "decimale": 1,
        "izvor": "zg-stvarno-koristenje",
    },
}

IZVORI_GRADOVA = [
    "zg-cetvrti",
    "zg-kapitalna-2023",
    "zg-kapitalna-2024",
    "zg-smjestajni-objekti",
    "zg-prazni-prostori",
    "zg-stvarno-koristenje",
    "zg-brownfield",
    "zg-trznice",
    "zg-trgovacka-drustva",
    "zg-planirana-namjena",
    "zg-eu-projekti",
    "zg-proracun-2026",
    "ri-proracun",
    "ri-prostori-zakup",
    "ri-eu-projekti",
]


# --------------------------------------------------------------------------- pomoćno


def _geojson(put) -> gpd.GeoDataFrame:
    g = gpd.read_file(put)
    if g.crs is None:
        g = g.set_crs(4326)
    return g.to_crs(4326)


def _spremi(ime: str, podaci, uvlaka: int | None = None) -> None:
    put = CILJ / ime
    put.parent.mkdir(parents=True, exist_ok=True)
    put.write_text(json.dumps(podaci, ensure_ascii=False, indent=uvlaka), encoding="utf-8")
    print(f"  {put.relative_to(KORIJEN)}  ({put.stat().st_size / 1024:.0f} KB)")


def _tocke(g: gpd.GeoDataFrame, svojstva: list[str]) -> dict:
    """GeoDataFrame točaka → GeoJSON s koordinatama na 5 decimala (~1 m)."""
    znacajke = []
    for _, r in g.iterrows():
        znacajke.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(r.geometry.x, 5), round(r.geometry.y, 5)],
                },
                "properties": {k: _cisto(r.get(k)) for k in svojstva},
            }
        )
    return {"type": "FeatureCollection", "features": znacajke}


def _cisto(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, str):
        v = " ".join(v.split())
        return v or None
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _datum(v) -> str | None:
    s = str(v).strip()
    d = pd.to_datetime(s, errors="coerce", dayfirst=not re.match(r"\d{4}-", s))
    return None if pd.isna(d) else d.date().isoformat()


# --------------------------------------------------------------------------- Zagreb


def cetvrti() -> gpd.GeoDataFrame:
    """17 gradskih četvrti (RPJ_GC) u WGS84."""
    put = nadji("zg-cetvrti", ".zip")
    with zipfile.ZipFile(put) as z:
        shp = next(n for n in z.namelist() if n.lower().endswith(".shp"))
    g = gpd.read_file(f"zip://{put.as_posix()}!{shp}")
    g = g.rename(columns={"JMS_MB": "sifra", "JMS_IME": "naziv"})[["sifra", "naziv", "geometry"]]
    g["sifra"] = g["sifra"].astype(str).str.zfill(5)
    g["kljuc"] = g["naziv"].map(kljuc)
    g["povrsina"] = g.to_crs(HTRS).area / 1e6
    if len(g) != 17:
        raise ValueError(f"Očekujem 17 gradskih četvrti, a ima ih {len(g)}")
    return g.to_crs(4326)


def _u_cetvrt(g: gpd.GeoDataFrame, gc: gpd.GeoDataFrame, ime: str) -> gpd.GeoDataFrame:
    """Dodaje stupac `cetvrt` (šifra) prema položaju točke."""
    bez = g.geometry.isna() | g.geometry.is_empty
    if bez.any():
        print(f"  {ime}: {bez.sum()} zapisa bez koordinata – izostavljeno s karte")
    g = g[~bez]
    s = gpd.sjoin(g, gc[["sifra", "geometry"]], how="left", predicate="within")
    s = s[~s.index.duplicated()].rename(columns={"sifra": "cetvrt"}).drop(columns="index_right")
    van = s["cetvrt"].isna().sum()
    if van:
        print(f"  {ime}: {van} točaka izvan granica Grada Zagreba")
    return s


def kapitalna_ulaganja(gc: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    dijelovi, ukupno = [], {}
    for godina in ("2023", "2024"):
        g = _geojson(nadji(f"zg-kapitalna-{godina}", ".geojson"))
        stupac = next(c for c in g.columns if c.lower().startswith("plan"))
        ukupno[godina] = (len(g), float(pd.to_numeric(g[stupac]).sum()))
        g = g.rename(
            columns={
                stupac: "iznos",
                "Vrsta_objekta": "vrsta",
                "Adresa": "adresa",
                "Opis_radova": "opis",
                "Obveza": "obveza",
            }
        )
        g["godina"] = int(godina)
        g["vrsta"] = g["vrsta"].str.capitalize()
        dijelovi.append(_u_cetvrt(g, gc, f"kapitalna ulaganja {godina}"))
    return pd.concat(dijelovi, ignore_index=True), ukupno


def smjestaj(gc: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    g = _geojson(nadji("zg-smjestajni-objekti", ".geojson"))
    g = g.rename(columns={"NAZIV": "naziv", "ADRESA": "adresa", "vrsta_smjestaja": "vrsta"})
    g["vrsta"] = g["vrsta"].str.capitalize()
    return _u_cetvrt(g, gc, "smještajni objekti")


def prazni_prostori() -> pd.DataFrame:
    """Sve tablice 2024. (prostori, neuvjetni prostori, garaže, parkirna mjesta)."""
    vrste = {
        "prazni-poslovni-prostori-2024": "poslovni prostor",
        "ne-uvjetni-prazni-poslovni-prostori-2024": "poslovni prostor (ne ispunjava uvjete)",
        "prazne-garae-2024": "garaža",
        "prazna-garano-parkirna-mjesta-2024": "parkirno mjesto",
    }
    dijelovi = []
    for uzorak, vrsta in vrste.items():
        put = nadji("zg-prazni-prostori", f"{uzorak}.xlsx")
        if put.name != f"{uzorak}.xlsx":
            raise FileNotFoundError(f"data/raw/zg-prazni-prostori/{uzorak}.xlsx ne postoji")
        t = excel(put)
        zag = next(i for i, v in enumerate(t[0]) if str(v).startswith("R.br"))
        t.columns = [" ".join(str(c).split()).upper() for c in t.iloc[zag]]
        t = t.iloc[zag + 1 :]
        t = t[t["R.BR."].str.strip() != ""]
        povrsina = next(c for c in t.columns if c.startswith("POVRŠINA"))
        dijelovi.append(
            pd.DataFrame(
                {
                    "vrsta": vrsta,
                    "cetvrt_naziv": t["GRADSKA ČETVRT"].str.strip(),
                    "adresa": t["ADRESA"].str.strip(),
                    "povrsina": t[povrsina].map(broj),
                }
            )
        )
    p = pd.concat(dijelovi, ignore_index=True)
    if p.duplicated(["adresa", "povrsina", "vrsta"]).sum() > len(p) / 2:
        raise ValueError("Prazni prostori: tablice se ponavljaju – je li pročitana kriva datoteka?")
    p["kljuc"] = p["cetvrt_naziv"].map(kljuc)
    return p


def koristenje_povrsina() -> pd.DataFrame:
    """Stvarno korištenje 2020.: hektari po četvrti i vrsti korištenja."""
    t = pd.read_excel(nadji("zg-stvarno-koristenje", ".xlsx"), engine="calamine")
    t["ha"] = pd.to_numeric(t["povrsina_ha"], errors="coerce")
    t["kljuc"] = t["IME_GC"].map(kljuc)
    return t.pivot_table(index="kljuc", columns="Koristenje", values="ha", aggfunc="sum").fillna(0)


def brownfield_poligoni() -> dict:
    g = _geojson(nadji("zg-brownfield", ".geojson"))
    g["povrsina_ha"] = (g.to_crs(HTRS).area / 1e4).round(2)
    g = g.rename(
        columns={
            "Naziv": "naziv",
            "Prethodno_koristenje": "prethodno",
            "Privremeno_korištenje": "privremeno",
            "Vlasništvo": "vlasnistvo",
            "Nepokretna_kulturna_dobra": "kulturno_dobro",
            "Oznaka_planske_namjene": "planska_namjena",
        }
    )
    g = g[
        [
            "naziv",
            "prethodno",
            "privremeno",
            "vlasnistvo",
            "kulturno_dobro",
            "planska_namjena",
            "povrsina_ha",
            "geometry",
        ]
    ]
    g["geometry"] = g.geometry.set_precision(1e-5)
    return json.loads(g.to_json(drop_id=True))


def _vrsta_gospodarske(namjena: str) -> str:
    n = kljuc(namjena)
    proizvodna = any(r in n for r in ("PROIZVOD", "LOGISTI", "INDUSTRIJ", "ROBNI TERMINAL"))
    poslovna = any(r in n for r in ("POSLOV", "USLUŽ", "PODUZETN", "URED"))
    if any(r in n for r in ("UGOSTITELJ", "HOTEL", "LUGARNIC", "ŽELJEZNIČAR")):
        return "ugostiteljsko-turistička"
    if any(r in n for r in ("TRGOV", "TRŽNIC", "PRODAJE")) and not proizvodna:
        return "trgovačka"
    if proizvodna and poslovna:
        return "poslovna i proizvodna"
    if proizvodna:
        return "proizvodna"
    if poslovna:
        return "poslovna"
    return "gospodarska (općenito)"


def gospodarske_zone(gc: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Gospodarske površine iz Planirane namjene 2023. (GUP, PPGZ i urbanistički planovi)."""
    g = _geojson(nadji("zg-planirana-namjena", ".geojson"))
    g = g[g["Analitika"].str.strip() == "Gospodarska"].copy()
    if g.empty:
        raise ValueError("Planirana namjena: nema površina s analitikom 'Gospodarska'")
    m = g.to_crs(HTRS)
    m["geometry"] = m.make_valid().simplify(2)
    g = gpd.GeoDataFrame(
        {
            "vrsta": g["Namjena"].map(_vrsta_gospodarske),
            "namjena": g["Namjena"].str.strip(),
            "izgradjenost": g["Namjena"].map(
                lambda v: (
                    "neizgrađeno"
                    if re.search(r"neizgra|planiran", str(v), re.IGNORECASE)
                    else ("izgrađeno" if re.search(r"izgra", str(v), re.IGNORECASE) else None)
                )
            ),
            "plan": g["Naziv_plana"].str.strip(),
            "godina_plana": pd.to_numeric(g["Godina_zadnje_izmjene"], errors="coerce"),
            "povrsina_ha": (m.area / 1e4).round(2),
            "kljuc_namjene": g["Namjena"].map(kljuc),
        },
        geometry=m.geometry,
        crs=HTRS,
    )
    # četvrt prema točki unutar poligona (zone na granici četvrti idu u jednu od njih)
    tocke = g.copy()
    tocke["geometry"] = g.representative_point()
    s = gpd.sjoin(tocke, gc.to_crs(HTRS)[["sifra", "geometry"]], how="left", predicate="within")
    g["cetvrt"] = s.loc[~s.index.duplicated(), "sifra"]
    g = g.to_crs(4326)
    print(
        f"  gospodarske zone: {len(g)} površina, {g.povrsina_ha.sum():,.0f} ha; "
        f"neizgrađeno {g.loc[g.izgradjenost == 'neizgrađeno', 'povrsina_ha'].sum():,.0f} ha"
    )
    return g


def zagreb_cetvrti_pokazatelji(
    gc: gpd.GeoDataFrame,
    kap: gpd.GeoDataFrame,
    smj: gpd.GeoDataFrame,
    pp: pd.DataFrame,
    gz: gpd.GeoDataFrame,
) -> pd.DataFrame:
    t = gc.set_index("sifra")[["naziv", "kljuc", "povrsina"]].copy()

    k24 = kap[kap["godina"] == 2024]
    t["kapitalna_ulaganja"] = k24.groupby("cetvrt")["iznos"].sum()
    t["kapitalni_projekti"] = k24.groupby("cetvrt").size()
    t["smjestajni_objekti"] = smj.groupby("cetvrt").size()

    nepoznate = set(pp["kljuc"]) - set(t["kljuc"])
    if nepoznate:
        raise ValueError(f"Prazni prostori: nepoznate četvrti {sorted(nepoznate)}")
    po_k = t.reset_index().set_index("kljuc")["sifra"]
    pp = pp.assign(cetvrt=pp["kljuc"].map(po_k))
    prostori = pp[pp["vrsta"].str.startswith("poslovni")]
    garaze = pp[~pp["vrsta"].str.startswith("poslovni")]
    t["prazni_poslovni_prostori"] = prostori.groupby("cetvrt").size()
    t["prazni_poslovni_prostori_m2"] = prostori.groupby("cetvrt")["povrsina"].sum()
    t["prazne_garaze"] = garaze.groupby("cetvrt").size()

    kp = koristenje_povrsina()
    nepoznate = set(kp.index) - set(t["kljuc"])
    if nepoznate:
        raise ValueError(f"Korištenje površina: nepoznate četvrti {sorted(nepoznate)}")
    kp = kp.reindex(t["kljuc"]).set_axis(t.index)
    ukupno = kp.sum(axis=1)
    t["brownfield"] = kp["Brownfield površine"]
    t["udio_gospodarske_povrsine"] = kp["Gospodarstvo"] / ukupno * 100
    t["udio_stambene_povrsine"] = kp["Stambene i mješovite površine"] / ukupno * 100
    t["udio_zelene_povrsine"] = (kp["Javne zelene površine"] + kp["Šume"]) / ukupno * 100
    t["_povrsina_koristenje_km2"] = ukupno / 100

    t["gospodarske_zone"] = gz.groupby("cetvrt")["povrsina_ha"].sum()
    neizgr = gz[gz["izgradjenost"] == "neizgrađeno"]
    t["gospodarske_zone_neizgradjene"] = neizgr.groupby("cetvrt")["povrsina_ha"].sum()
    t[["gospodarske_zone", "gospodarske_zone_neizgradjene"]] = t[
        ["gospodarske_zone", "gospodarske_zone_neizgradjene"]
    ].fillna(0)

    brojevi = ["kapitalni_projekti", "smjestajni_objekti", "prazni_poslovni_prostori"]
    brojevi += ["prazne_garaze"]
    t[brojevi] = t[brojevi].fillna(0)
    t[["kapitalna_ulaganja", "prazni_poslovni_prostori_m2"]] = t[
        ["kapitalna_ulaganja", "prazni_poslovni_prostori_m2"]
    ].fillna(0)
    return t


def eu_projekti_zagreb() -> list[dict]:
    t = excel(nadji("zg-eu-projekti", ".xlsx"))
    zag = next(i for i, v in enumerate(t[0]) if str(v).startswith("Redni"))
    t = t.iloc[zag + 1 :]
    t = t[t[1].str.strip() != ""]
    out = []
    for _, r in t.iterrows():
        out.append(
            {
                "naziv": _cisto(r[1]),
                "nositelj": _cisto(r[2]),
                "program": _cisto(r[3]),
                "skupina_programa": _skupina_programa(r[3]),
                "pocetak": _datum(r[4]),
                "vrijednost_eur": _broj2(r[5]),
                "bespovratno_eur": _broj2(r[6]),
            }
        )
    return out


def _broj2(v) -> float | None:
    b = broj(v)
    return None if b is None else round(b, 2)


def _skupina_programa(v: str) -> str:
    s = kljuc(v)
    pravila = [
        ("ERASMUS", "Erasmus+"),
        ("KONKURENTNOST I KOHEZIJA", "OP Konkurentnost i kohezija 2014.–2020."),
        ("LJUDSKI POTENCIJALI", "OP Učinkoviti ljudski potencijali 2014.–2020."),
        ("OPORAVKA I OTPORNOSTI", "Nacionalni plan oporavka i otpornosti"),
        ("OBZOR", "Obzor 2020 / Obzor Europa"),
        ("HORIZON", "Obzor 2020 / Obzor Europa"),
        ("SOLIDARNOSTI", "Fond solidarnosti EU"),
        ("INTERREG", "Interreg"),
        ("URBACT", "Interreg"),
        ("KONKURENTNOST", "Program Konkurentnost i kohezija 2021.–2027."),
        ("UČINKOVITI LJUDSKI", "Program Učinkoviti ljudski potencijali 2021.–2027."),
    ]
    for uzorak, skupina in pravila:
        if uzorak in s:
            return skupina
    return "Ostali programi"


# --------------------------------------------------------------------------- proračun


def _stavke(iznosi: dict[str, float], nazivi: dict[str, str], stan: int) -> list[dict]:
    ukupno = sum(iznosi.values())
    return [
        {
            "sifra": s,
            "naziv": nazivi.get(s, s),
            "iznos": round(v),
            "po_stanovniku": round(v / stan, 2),
            "udio": round(v / ukupno * 100, 2),
        }
        for s, v in sorted(iznosi.items())
        if v
    ]


def _proracun(grad, sifra, stan, godina, vrsta, izvor, funkcije, prihodi) -> dict:
    return {
        "grad": grad,
        "sifra": sifra,
        "godina": godina,
        "vrsta": vrsta,
        "izvor": izvor,
        "stanovnistvo": stan,
        "rashodi_ukupno": round(sum(funkcije.values())),
        "rashodi_po_stanovniku": round(sum(funkcije.values()) / stan, 2),
        "prihodi_ukupno": round(sum(prihodi.values())),
        "prihodi_po_stanovniku": round(sum(prihodi.values()) / stan, 2),
        "rashodi_po_funkciji": _stavke(funkcije, FUNKCIJE, stan),
        "napomena": NAPOMENA_PRORACUN.get(sifra),
        "prihodi_po_vrsti": _stavke(prihodi, PRIHODI, stan),
    }


def proracun_zagreb(stan: int) -> dict:
    r = pd.read_excel(
        nadji("zg-proracun-2026", "plan-rashodi-2026.xlsx"), dtype=str, engine="calamine"
    )
    p = pd.read_excel(
        nadji("zg-proracun-2026", "plan-prihodi-2026.xlsx"), dtype=str, engine="calamine"
    )
    for t in (r, p):
        t["Plan"] = pd.to_numeric(t["Plan"])
    # rashodi = razredi 3 i 4 (bez izdataka za otplatu zajmova, razred 5)
    r = r[r["OznakaOdjeljka"].str[0].isin(["3", "4"])]
    funkcije = r.groupby(r["OznakaPodskupine"].str[:2])["Plan"].sum().to_dict()
    p = p[p["OznakaOdjeljka"].str[0].isin(["6", "7"])]
    prihodi = p.groupby(p["OznakaOdjeljka"].str[:2])["Plan"].sum().to_dict()
    return _proracun("Zagreb", ZAGREB, stan, 2026, "plan", "zg-proracun-2026", funkcije, prihodi)


def proracun_rijeka(stan: int) -> dict:
    put = nadji("ri-proracun", "2025.-godinu-i-projekcije")
    listovi = pd.ExcelFile(put, engine="calamine").sheet_names

    def iz_lista(dio: str, uzorak: str, raspon: tuple[int, int]) -> dict[str, float]:
        t = excel(put, next(s for s in listovi if dio in s))
        out = {}
        for naziv, iznos in zip(t[0], t[1], strict=True):
            m = re.match(uzorak, str(naziv).strip())
            if m and raspon[0] <= int(m.group(1)[0]) <= raspon[1]:
                out[m.group(1)] = broj(iznos) or 0
        return out

    funkcije = iz_lista("funkcijska", r"^(\d\d) ", (0, 1))
    prihodi = iz_lista("ekonomska", r"^(\d\d) ", (6, 7))
    t = excel(put, next(s for s in listovi if "funkcijska" in s))
    ukupno = broj(t[1][red_ukupno(t, "UKUPNO RASHODI")])
    if abs(sum(funkcije.values()) - ukupno) > 1:
        raise ValueError("Rijeka: zbroj funkcija ≠ UKUPNO RASHODI")
    godina = int(re.search(r"za (20\d\d)", put.name.replace("-", " ").replace(".", " ")).group(1))
    return _proracun("Rijeka", RIJEKA, stan, godina, "plan", "ri-proracun", funkcije, prihodi)


def red_ukupno(t: pd.DataFrame, tekst: str) -> int:
    return next(i for i, v in enumerate(t[0]) if str(v).strip() == tekst)


# --------------------------------------------------------------------------- Rijeka


# NKD 2007.: odjeljak (prve dvije znamenke) → područje
NKD_PODRUCJA = [
    (1, 3, "Poljoprivreda, šumarstvo i ribarstvo"),
    (5, 9, "Rudarstvo"),
    (10, 33, "Prerađivačka industrija"),
    (35, 39, "Energija, voda i otpad"),
    (41, 43, "Građevinarstvo"),
    (45, 47, "Trgovina"),
    (49, 53, "Prijevoz i skladištenje"),
    (55, 56, "Smještaj i ugostiteljstvo"),
    (58, 63, "Informacije i komunikacije"),
    (64, 66, "Financije i osiguranje"),
    (68, 68, "Poslovanje nekretninama"),
    (69, 75, "Stručne i znanstvene djelatnosti"),
    (77, 82, "Administrativne i pomoćne usluge"),
    (84, 84, "Javna uprava"),
    (85, 85, "Obrazovanje"),
    (86, 88, "Zdravstvo i socijalna skrb"),
    (90, 93, "Umjetnost, zabava i rekreacija"),
    (94, 94, "Udruge i organizacije"),
    (95, 96, "Popravci i osobne usluge"),
]


def nkd_podrucje(sifra) -> str:
    m = re.match(r"\s*(\d\d)", str(sifra or ""))
    if m:
        o = int(m.group(1))
        for od, do, naziv in NKD_PODRUCJA:
            if od <= o <= do:
                return naziv
    return "Nije navedeno"


def poslovni_prostori_rijeka() -> dict:
    d = json.loads(nadji("ri-prostori-zakup", ".json").read_text(encoding="utf-8"))
    t = pd.DataFrame(d)
    t["povrsina"] = t["POVRSINA_PROSTORA"].map(broj)
    t["cijena"] = t["JEDINICNA_CIJENA_EUR"].map(broj)
    t["mjesecno"] = t["povrsina"] * t["cijena"]
    t["djelatnost"] = t["DJELATNOST_NKD"].map(nkd_podrucje)
    t["zona"] = t["ZONA"].fillna("").str.strip()

    def zbroj(g: pd.DataFrame) -> dict:
        return {
            "broj": int(len(g)),
            "povrsina_m2": round(float(g["povrsina"].sum())),
            "zakupnina_mjesecno_eur": round(float(g["mjesecno"].sum())),
            "prosjecna_cijena_eur_m2": round(float(g["mjesecno"].sum() / g["povrsina"].sum()), 2),
        }

    return {
        "grad": "Rijeka",
        "sifra": RIJEKA,
        "izvor": "ri-prostori-zakup",
        "ukupno": zbroj(t),
        "po_zoni": {z: zbroj(g) for z, g in sorted(t.groupby("zona"))},
        "po_djelatnosti": dict(
            sorted(
                ((dj, zbroj(g)) for dj, g in t.groupby("djelatnost")),
                key=lambda x: -x[1]["broj"],
            )
        ),
        "napomena": "Zakupnina je mjesečna (površina × jedinična cijena po m²). Zone su "
        "zone zakupnine Grada Rijeke; zona 0 ima najvišu cijenu (središte grada). Izvor nema "
        "koordinate, samo adrese.",
    }


def eu_projekti_rijeka() -> list[dict]:
    tekst = nadji("ri-eu-projekti", ".csv").read_text(encoding="utf-8-sig")
    retci = [r.rstrip(";").strip() for r in tekst.splitlines()]
    projekti, tren = [], None
    for r in retci:
        m = re.match(r"^(\d+)\.\s*(.+)", r)
        if m and int(m.group(1)) == len(projekti) + 1:
            tren = {"naziv": m.group(2).strip(), "trajanje": None, "program": None}
            tren["vrijednost_eur"] = None
            projekti.append(tren)
        elif tren:
            kl, _, vr = r.strip('"').partition(":")
            kl = kl.strip().lower()
            if kl.startswith("trajanje"):
                tren["trajanje"] = vr.strip()
            elif kl.startswith("program iz kojeg"):
                tren["program"] = vr.strip()
            elif kl.startswith("ukupna vrijednost"):
                tren["vrijednost_eur"] = _iznos_teksta(vr)
    return projekti


def _iznos_teksta(v: str) -> float | None:
    """'1.872.533,00 eura' / '55.000 eura' / '1.865.065,60 kn' → EUR."""
    m = re.search(r"\d[\d.]*(,\d+)?", v)
    if not m:
        return None
    iznos = float(m.group(0).replace(".", "").replace(",", "."))
    if re.search(r"\bk(n|una)\b", v.lower()):
        iznos /= TECAJ_HRK
    return round(iznos, 2)


# --------------------------------------------------------------------------- glavno


def _meta_izvori() -> dict:
    import csv

    with (KORIJEN / "data" / "sources.csv").open(encoding="utf-8-sig", newline="") as f:
        izvori = {r["id"]: r for r in csv.DictReader(f)}
    return {
        sid: {
            "naziv": izvori[sid]["naziv"],
            "izdavatelj": izvori[sid]["izdavatelj"],
            "poveznica": izvori[sid]["poveznica"],
            "licenca": izvori[sid].get("licenca") or None,
        }
        for sid in IZVORI_GRADOVA
        if sid in izvori
    }


def provjere(t: pd.DataFrame, kap: gpd.GeoDataFrame, kap_ukupno: dict) -> None:
    greske = []
    razlika = (t["povrsina"] - t["_povrsina_koristenje_km2"]).abs() / t["povrsina"]
    if (razlika > 0.02).any():
        greske.append(f"Površina četvrti ≠ korištenje površina: {razlika.max():.1%}")
    else:
        print(
            "  ✔ Površine četvrti = zbroj korištenja površina "
            f"(najveća razlika {razlika.max():.2%})"
        )
    n, iznos = kap_ukupno["2024"]
    na_karti = kap[kap["godina"] == 2024]
    print(
        f"  ✔ Kapitalna ulaganja 2024.: {len(na_karti)} od {n} projekata na karti, "
        f"{na_karti['iznos'].sum() / iznos:.1%} iznosa"
    )
    if greske:
        raise SystemExit("Provjere gradova nisu prošle:\n  " + "\n  ".join(greske))


def main(sada: str | None = None) -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sada = sada or datetime.now(UTC).isoformat(timespec="seconds")
    if not (RAW / "zg-cetvrti").exists():
        print("  Nema podataka faza 5 i 6 – pokreni: python pipeline/download.py --faza 5,6")
        return

    areas = pd.read_csv(KORIJEN / "data" / "areas.csv", dtype=str)
    stan = areas.set_index("sifra")["stanovnistvo_2021"].astype(int)

    print("  Zagreb: četvrti i slojevi")
    gc = cetvrti()
    kap, kap_ukupno = kapitalna_ulaganja(gc)
    smj = smjestaj(gc)
    pp = prazni_prostori()
    gz = gospodarske_zone(gc)
    t = zagreb_cetvrti_pokazatelji(gc, kap, smj, pp, gz)
    provjere(t, kap, kap_ukupno)

    podrucja = {}
    for sif, r in t.iterrows():
        podrucja[sif] = {
            "sifra": sif,
            "naziv": r["naziv"],
            "vrsta": "cetvrt",
            "nadredeno": ZAGREB,
            "pokazatelji": {p: _cisto(round(float(r[p]), 2)) for p in POKAZATELJI_CETVRTI},
            "po_stanovniku": {},
            "rang": {},
            "slicni": [],
        }
    dodaj_rang(podrucja)

    g = gc[["sifra", "naziv", "geometry"]].copy()
    g["geometry"] = g.geometry.simplify(0.00005).set_precision(1e-5)
    _spremi("zagreb/cetvrti.geojson", json.loads(g.to_json(drop_id=True)))
    _spremi("zagreb/cetvrti.json", {"generirano": sada, "podrucja": podrucja}, uvlaka=2)

    kap["iznos"] = pd.to_numeric(kap["iznos"])
    _spremi(
        "zagreb/kapitalna-ulaganja.geojson",
        _tocke(kap, ["naziv", "vrsta", "adresa", "opis", "obveza", "iznos", "godina", "cetvrt"]),
    )
    _spremi("zagreb/smjestaj.geojson", _tocke(smj, ["naziv", "vrsta", "adresa", "cetvrt"]))
    for mapa, ime in (("zg-trznice", "trznice"), ("zg-trgovacka-drustva", "gradska-drustva")):
        tg = _u_cetvrt(_geojson(nadji(mapa, ".geojson")), gc, ime)
        svojstva = [c for c in ("naziv", "adresa", "web", "vrsta", "udjeli") if c in tg.columns]
        _spremi(f"zagreb/{ime}.geojson", _tocke(tg, svojstva + ["cetvrt"]))
    _spremi("zagreb/brownfield.geojson", brownfield_poligoni())
    gz_izvoz = gz.drop(columns=["kljuc_namjene"]).copy()
    gz_izvoz["geometry"] = gz_izvoz.geometry.set_precision(1e-5)
    _spremi("zagreb/gospodarske-zone.geojson", json.loads(gz_izvoz.to_json(drop_id=True)))
    _spremi(
        "zagreb/eu-projekti.json", {"izvor": "zg-eu-projekti", "projekti": eu_projekti_zagreb()}
    )
    _spremi("zagreb/proracun.json", proracun_zagreb(int(stan[ZAGREB])), uvlaka=2)

    print("  Rijeka")
    _spremi("rijeka/proracun.json", proracun_rijeka(int(stan[RIJEKA])), uvlaka=2)
    _spremi("rijeka/poslovni-prostori.json", poslovni_prostori_rijeka(), uvlaka=2)
    _spremi(
        "rijeka/eu-projekti.json", {"izvor": "ri-eu-projekti", "projekti": eu_projekti_rijeka()}
    )

    meta = {
        "generirano": sada,
        "gradovi": {
            "zagreb": {
                "sifra": ZAGREB,
                "naziv": "Zagreb",
                "podrucja": "cetvrti",
                "slojevi": {
                    "cetvrti": "cetvrti.geojson",
                    "kapitalna-ulaganja": "kapitalna-ulaganja.geojson",
                    "smjestaj": "smjestaj.geojson",
                    "trznice": "trznice.geojson",
                    "gradska-drustva": "gradska-drustva.geojson",
                    "brownfield": "brownfield.geojson",
                    "gospodarske-zone": "gospodarske-zone.geojson",
                },
                "tablice": ["cetvrti.json", "proracun.json", "eu-projekti.json"],
            },
            "rijeka": {
                "sifra": RIJEKA,
                "naziv": "Rijeka",
                "podrucja": None,
                "slojevi": {},
                "tablice": ["proracun.json", "poslovni-prostori.json", "eu-projekti.json"],
                "napomena": "Rijeka nema otvorene granice mjesnih odbora; granica grada je "
                "u jls/08.geojson (šifra 03735).",
            },
        },
        "pokazatelji_cetvrti": {
            p: {**d, "godina": _GODINE_CETVRTI[p]} for p, d in POKAZATELJI_CETVRTI.items()
        },
        "funkcije": FUNKCIJE,
        "vrste_prihoda": PRIHODI,
        "izvori": _meta_izvori(),
    }
    _spremi("meta.json", meta, uvlaka=2)


_GODINE_CETVRTI = {
    "povrsina": "2025",
    "kapitalna_ulaganja": "2024",
    "kapitalni_projekti": "2024",
    "smjestajni_objekti": "2023",
    "prazni_poslovni_prostori": "2024",
    "prazni_poslovni_prostori_m2": "2024",
    "prazne_garaze": "2024",
    "brownfield": "2020",
    "udio_gospodarske_povrsine": "2020",
    "udio_stambene_povrsine": "2020",
    "udio_zelene_povrsine": "2020",
    "gospodarske_zone": "2023",
    "gospodarske_zone_neizgradjene": "2023",
}


if __name__ == "__main__":
    main()
