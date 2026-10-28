"""Obrada pravih podataka: iz data/raw/ napravi datoteke za kartu u web/public/data/.

Koraci (issues: spajanje po šifri, izvedeni pokazatelji, izvoz + provjere):
  1. šifrarnik područja (sifrarnik.py) → data/areas.csv
  2. čitanje svakog izvora (citaci.py) i spajanje po šifri županije / grada
  3. izvedeni pokazatelji: po stanovniku, rang, slična područja (izvoz.py)
  4. izvoz: meta.json, drzava.json, zupanije.json, jls.json, tocke/eu-projekti.geojson
  5. provjere: 21 županija, 556 JLS, zbroj županija = država

Uredne tablice za ručnu provjeru (otvaraju se u Excelu) spremaju se u data/obrada/.

Pokretanje (iz korijena repozitorija):
    python pipeline/build.py
"""

from __future__ import annotations

import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import citaci  # noqa: E402
import gradovi  # noqa: E402
import granice  # noqa: E402
import sifrarnik  # noqa: E402
from izvoz import IZLAZ, dodaj_rang, dodaj_slicne, spremi_json, zapis_podrucja  # noqa: E402
from nazivi import uskladi  # noqa: E402
from pokazatelji import POKAZATELJI, TEME  # noqa: E402
from zupanije import ZUPANIJE  # noqa: E402

KORIJEN = Path(__file__).resolve().parent.parent
OBRADA = KORIJEN / "data" / "obrada"
SVE = list(ZUPANIJE) + ["HR"]

# Izvori koji se sastoje od više skupova iz sources.csv
ZBIRNI_IZVORI = {
    "hbor-esif": [
        "hbor-rast-razvoj",
        "hbor-energetska",
        "hbor-rasvjeta",
        "hbor-ruralni-investicijski",
        "hbor-ruralni-obrtna",
    ],
}

# Granica Hrvatske (za odbacivanje očito pogrešnih koordinata)
BBOX = (13.2, 42.2, 19.5, 46.6)


def korak(tekst: str) -> None:
    print(f"\n== {tekst}")


# --------------------------------------------------------------------------- županije i država


def zupanije_i_drzava(godine: dict) -> pd.DataFrame:
    """Jedna tablica: redak po županiji + redak 'HR', stupac po pokazatelju."""
    t = pd.DataFrame(index=pd.Index(SVE, name="zupanija"))

    pop = citaci.popis_kontingenti()
    pz = pop[pop.razina.isin(["zupanija", "drzava"])].set_index("zupanija")
    t["stanovnistvo"] = pz["stanovnistvo"]
    t["prosjecna_starost"] = pz["prosjecna_starost"]
    t["gustoca_naseljenosti"] = (
        t["stanovnistvo"] / citaci.popis_povrsina().set_index("zupanija")["povrsina_km2"]
    )
    for p in ("stanovnistvo", "prosjecna_starost", "gustoca_naseljenosti"):
        godine[p] = "2021"
    print("  stanovništvo i dob (Popis 2021.)")

    for citac, opis in [
        (citaci.place_zupanije, "neto plaće"),
        (citaci.zaposleni_zupanije, "zaposleni"),
        (citaci.nezaposlenost_zupanije, "nezaposlenost"),
        (citaci.kupoprodaje_zupanije, "kupoprodaje nekretnina"),
    ]:
        df, god = citac()
        stupac = [c for c in df.columns if c != "zupanija"][0]
        t[stupac] = df.set_index("zupanija")[stupac]
        godine[stupac] = god
        print(f"  {opis} ({god})")

    _, dz, god = citaci.dohodak_jls()
    dz = dz.set_index("zupanija")
    t["neto_dohodak"] = dz["neto"]
    t["porez_na_dohodak"] = dz["porez"]
    godine["neto_dohodak"] = godine["porez_na_dohodak"] = god
    print(f"  neto dohodak i porez na dohodak ({god})")

    eu, presjek = citaci.eu_opkk()
    po_z = eu.groupby("zupanija")["esif_eur"].agg(["sum", "count"])
    t["eu_ugovoreno"] = po_z["sum"]
    t["eu_projekti"] = po_z["count"]
    t.loc["HR", "eu_ugovoreno"] = eu["esif_eur"].sum()
    t.loc["HR", "eu_projekti"] = len(eu)
    godine["eu_ugovoreno"] = godine["eu_projekti"] = f"stanje {presjek}"
    bez = eu[eu.zupanija.isna()]
    print(
        f"  EU projekti OPKK ({len(eu)} operacija, presjek {presjek}); "
        f"{len(bez)} bez županije ({bez.esif_eur.sum() / 1e6:,.0f} mil. EUR) "
        "ulazi samo u zbroj države"
    )

    hb = citaci.hbor_krediti()
    t["hbor_krediti"] = hb.groupby("zupanija")["iznos_eur"].sum()
    t.loc[ZUPANIJE.keys(), "hbor_krediti"] = t.loc[list(ZUPANIJE), "hbor_krediti"].fillna(0)
    t.loc["HR", "hbor_krediti"] = hb["iznos_eur"].sum()
    godine["hbor_krediti"] = "2018.–2023."
    print(f"  HBOR ESIF krediti ({len(hb)} korisnika)")

    try:
        bdv, bdp, god = citaci.bdp_regije()
        t["bruto_dodana_vrijednost"] = bdv.set_index("zupanija")["bdv_eur"]
        t.loc["HR", "bdp"] = bdp["bdp_eur"]
        godine["bdp"] = godine["bruto_dodana_vrijednost"] = god
        print(f"  BDP (država) i bruto dodana vrijednost (županije) ({god})")
    except FileNotFoundError:
        print("  UPOZORENJE: nema PDF-a s regionalnim BDP-om u data/raw/dzs-bdp-regije/")

    v, god = citaci.hnb_inflacija()
    t.loc["HR", "inflacija"] = v
    godine["inflacija"] = god
    v, god = citaci.hnb_saldo()
    t.loc["HR", "saldo_proracuna"] = v * 1e6
    godine["saldo_proracuna"] = god
    v, god = citaci.hnb_dug()
    t.loc["HR", "javni_dug"] = v * 1e6
    godine["javni_dug"] = god
    v, god = citaci.aktivne_pravne_osobe()
    t.loc["HR", "pravne_osobe_aktivne"] = v
    godine["pravne_osobe_aktivne"] = god
    print("  država: inflacija, saldo, dug, pravne osobe (HNB, DZS)")
    return t


# --------------------------------------------------------------------------- gradovi i općine


def uskladi_po_zupanijama(izvor: pd.DataFrame, cilj: pd.DataFrame) -> pd.Series:
    """Ključevi naziva iz izvora prevedeni na ključeve šifrarnika, županiju po županiju."""
    novi = izvor["kljuc"].copy()
    for z, grupa in izvor.groupby("zupanija"):
        mapa = uskladi(list(grupa["kljuc"]), list(cilj.loc[cilj.zupanija == z, "kljuc"]))
        novi.loc[grupa.index] = grupa["kljuc"].map(mapa).fillna(grupa["kljuc"])
    return novi


def eu_po_jls(poligoni: gpd.GeoDataFrame | None) -> pd.DataFrame | None:
    """EU projekti raspoređeni po gradovima/općinama prema koordinatama projekta."""
    if poligoni is None:
        return None
    eu, _ = citaci.eu_opkk()
    eu = eu.dropna(subset=["lon", "lat"])
    tocke = gpd.GeoDataFrame(eu, geometry=gpd.points_from_xy(eu.lon, eu.lat), crs=4326)
    sp = gpd.sjoin(
        tocke,
        poligoni[["sifra", "geometry"]].rename(columns={"sifra": "jls"}),
        how="left",
        predicate="within",
    )
    sp = sp[~sp.index.duplicated()]
    return sp


def gradovi_i_opcine(
    areas: pd.DataFrame, godine: dict, eu_jls: pd.DataFrame | None = None
) -> pd.DataFrame:
    jls = areas[areas.vrsta != "zupanija"].set_index(["zupanija", "kljuc"])

    pop = citaci.popis_kontingenti()
    pj = pop[pop.razina == "jls"].set_index(["zupanija", "kljuc"])
    zg = pop[(pop.razina == "zupanija") & (pop.zupanija == "21")].assign(kljuc="ZAGREB")
    pj = pd.concat([pj, zg.set_index(["zupanija", "kljuc"])])
    jls["stanovnistvo"] = jls["stanovnistvo_2021"]
    jls["prosjecna_starost"] = pj["prosjecna_starost"]

    dj, _, _ = citaci.dohodak_jls()
    dj["kljuc"] = uskladi_po_zupanijama(dj, jls.reset_index())
    dj = dj.set_index(["zupanija", "kljuc"])
    nespojeno = dj.index.difference(jls.index)
    if len(nespojeno):
        print(f"  UPOZORENJE: {len(nespojeno)} JLS iz Porezne uprave nije spojeno:")
        for z, k in nespojeno:
            print(f"    {z} {k}")
    jls["neto_dohodak"] = dj["neto"]
    jls["porez_na_dohodak"] = dj["porez"]
    jls = jls.reset_index()
    stope, god = citaci.porezne_stope_jls()
    jls = jls.merge(stope, on="sifra", how="left")
    for p in (
        "stopa_poreza_dohodak_niza",
        "stopa_poreza_dohodak_visa",
        "porez_na_potrosnju",
        "porez_na_nekretnine",
    ):
        godine[p] = god
    godine["promjena_stope_niza"] = f"{int(god) - 1}.→{god}."
    opis = "stanovništvo, dob, dohodak, porez, porezne stope"
    if eu_jls is not None:
        po = eu_jls.groupby("jls")["esif_eur"].agg(["sum", "count"])
        jls["eu_ugovoreno"] = jls["sifra"].map(po["sum"]).fillna(0)
        jls["eu_projekti"] = jls["sifra"].map(po["count"]).fillna(0)
        izvan = eu_jls["jls"].isna().sum()
        opis += f", EU projekti ({izvan} točaka izvan granica JLS, npr. na moru)"
    print(f"  {len(jls)} gradova i općina: {opis}")
    return jls


def ponderirane_stope(t: pd.DataFrame, jls: pd.DataFrame) -> None:
    """Stope poreza za županije i državu: prosjek JLS ponderiran stanovništvom."""
    for p in ("stopa_poreza_dohodak_niza", "stopa_poreza_dohodak_visa"):
        tez = jls["stanovnistvo"] * jls[p]
        po_z = tez.groupby(jls["zupanija"]).sum() / jls.groupby("zupanija")["stanovnistvo"].sum()
        t[p] = po_z.round(2)
        t.loc["HR", p] = round(tez.sum() / jls["stanovnistvo"].sum(), 2)


# --------------------------------------------------------------------------- točke


def eu_tocke(eu_jls: pd.DataFrame | None = None) -> dict:
    eu, presjek = citaci.eu_opkk()
    if eu_jls is not None:
        eu["jls"] = eu_jls["jls"].reindex(eu.index)
    else:
        eu["jls"] = None
    x0, y0, x1, y1 = BBOX
    u_hr = eu["lon"].between(x0, x1) & eu["lat"].between(y0, y1)
    print(f"  {u_hr.sum()} od {len(eu)} EU projekata ima ispravne koordinate")
    znacajke = []
    for _, r in eu[u_hr].iterrows():
        znacajke.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(r.lon, 5), round(r.lat, 5)]},
                "properties": {
                    "sifra": r.sifra_projekta,
                    "naziv": r.naziv[:160],
                    "korisnik": r.korisnik,
                    "esif_eur": round(r.esif_eur or 0),
                    "ukupno_eur": round(r.ukupno_eur or 0),
                    "zupanija": r.zupanija,
                    "jls": r.jls if isinstance(r.jls, str) else None,
                    "mjesto": r.mjesto,
                    "fond": r.fond,
                    "pocetak": r.pocetak,
                    "kraj": r.kraj,
                    "kategorija": r.kategorija[:3],
                },
            }
        )
    return {"type": "FeatureCollection", "presjek": presjek, "features": znacajke}


# --------------------------------------------------------------------------- meta


def meta_izvori(potrebni: set[str], dgu: bool) -> dict:
    with (KORIJEN / "data" / "sources.csv").open(encoding="utf-8-sig", newline="") as f:
        izvori = {r["id"]: r for r in csv.DictReader(f)}

    def opis(sid: str) -> dict:
        r = izvori[sid]
        return {
            "naziv": r["naziv"],
            "izdavatelj": r["izdavatelj"],
            "poveznica": r["poveznica"],
            "licenca": r.get("licenca") or None,
            "preuzeto": r.get("datum_preuzimanja") or None,
        }

    out = {}
    for sid in sorted(potrebni):
        if sid in ZBIRNI_IZVORI:
            dijelovi = [opis(d) for d in ZBIRNI_IZVORI[sid] if d in izvori]
            out[sid] = {
                "naziv": "HBOR – korisnici ESIF kredita (5 skupova)",
                "izdavatelj": "HBOR",
                "poveznica": dijelovi[0]["poveznica"],
                "licenca": dijelovi[0]["licenca"],
                "dijelovi": dijelovi,
            }
        else:
            out[sid] = opis(sid)
    granice_id = "granice-upravne-jedinice" if dgu else "natural-earth-admin1"
    out[granice_id] = opis(granice_id)
    return out


# --------------------------------------------------------------------------- provjere


def provjere(t: pd.DataFrame, jls: pd.DataFrame) -> None:
    korak("Provjere")
    greske = []
    z = t.loc[list(ZUPANIJE)]
    if len(z) != 21 or z["stanovnistvo"].isna().any():
        greske.append("nema stanovništva za svih 21 županiju")
    if len(jls) != 556:
        greske.append(f"JLS: {len(jls)} (očekivano 556)")
    print(f"  {'pokazatelj':26} {'zbroj županija':>18} {'država':>18}  razlika")
    for p in (
        "stanovnistvo",
        "zaposleni",
        "kupoprodaje_nekretnina",
        "neto_dohodak",
        "porez_na_dohodak",
        "bruto_dodana_vrijednost",
        "eu_ugovoreno",
        "hbor_krediti",
    ):
        if p not in t:
            continue
        zbroj, hr = z[p].sum(), t.loc["HR", p]
        razlika = (zbroj - hr) / hr * 100 if hr else 0
        oznaka = "ok" if abs(razlika) < 0.5 else "≠"
        print(f"  {p:26} {zbroj:>18,.0f} {hr:>18,.0f}  {razlika:+.2f} % {oznaka}")
        if p == "stanovnistvo" and abs(razlika) > 0:
            greske.append("zbroj stanovnika županija ≠ država")
    for p in ("neto_dohodak", "porez_na_dohodak"):
        zz = jls.groupby("zupanija")[p].sum()
        r = ((zz - z[p]) / z[p] * 100).abs().max()
        print(f"  {p}: najveća razlika zbroj JLS ↔ županija {r:.2f} %")
    for p in ("stopa_poreza_dohodak_niza", "stopa_poreza_dohodak_visa"):
        if jls[p].isna().any() or not jls[p].between(10, 40).all():
            greske.append(f"{p}: nedostaje ili je izvan raspona 10–40 %")
    if jls["neto_dohodak"].isna().any():
        print(f"  JLS bez podatka o dohotku: {jls['neto_dohodak'].isna().sum()}")
    if greske:
        raise SystemExit("PROVJERE NISU PROŠLE:\n  " + "\n  ".join(greske))
    print("  Sve ključne provjere su prošle.")


# --------------------------------------------------------------------------- glavno


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sada = datetime.now(UTC).isoformat(timespec="seconds")
    godine: dict[str, str] = {}

    korak("1. Šifrarnik")
    areas = sifrarnik.main()

    korak("1. Granice")
    dgu = granice.dgu_zip() is not None
    poligoni = None
    if dgu:
        granice.izvezi_dgu(areas)
        poligoni = pd.concat(
            [gpd.read_file(p) for p in sorted((IZLAZ / "jls").glob("*.geojson"))],
            ignore_index=True,
        )
    else:
        print("  Nema DGU granica – koristim postojeći (probni) zupanije.geojson")
        if not (IZLAZ / "zupanije.geojson").exists():
            granice.main()
    eu_jls = eu_po_jls(poligoni)

    korak("2. Čitanje izvora: država i županije")
    t = zupanije_i_drzava(godine)
    korak("2. Čitanje izvora: gradovi i općine")
    jls = gradovi_i_opcine(areas, godine, eu_jls)
    ponderirane_stope(t, jls)

    provjere(t, jls)

    OBRADA.mkdir(parents=True, exist_ok=True)
    t.round(2).to_csv(OBRADA / "zupanije.csv", encoding="utf-8-sig")
    jls.drop(columns=["stanovnistvo_2021"]).round(2).to_csv(
        OBRADA / "jls.csv", index=False, encoding="utf-8-sig"
    )

    korak("3. Izvoz u web/public/data/")

    def vrijednosti(red: pd.Series, razina: str) -> dict:
        return {p: red.get(p) for p, d in POKAZATELJI.items() if razina in d["razine"]}

    drzava = zapis_podrucja(
        "HR", "Republika Hrvatska", "drzava", None, vrijednosti(t.loc["HR"], "drzava")
    )
    spremi_json("drzava.json", {"generirano": sada, **drzava})

    podrucja = {}
    for sif, (naziv, _) in ZUPANIJE.items():
        podrucja[sif] = zapis_podrucja(
            sif, naziv, "zupanija", "HR", vrijednosti(t.loc[sif], "zupanija")
        )
    dodaj_rang(podrucja)
    dodaj_slicne(podrucja)
    spremi_json("zupanije.json", {"generirano": sada, "podrucja": podrucja})

    pj = {}
    for _, r in jls.sort_values("sifra").iterrows():
        pj[r.sifra] = zapis_podrucja(r.sifra, r.naziv, r.vrsta, r.zupanija, vrijednosti(r, "jls"))
    dodaj_rang(pj)
    dodaj_slicne(pj)
    spremi_json("jls.json", {"generirano": sada, "podrucja": pj}, uvlaka=None)

    spremi_json("tocke/eu-projekti.geojson", eu_tocke(eu_jls), uvlaka=None)

    pokazatelji = {p: {**d, "godina": godine.get(p)} for p, d in POKAZATELJI.items()}
    meta = {
        "verzija_formata": 1,
        "generirano": sada,
        "probni_podaci": False,
        "probne_granice": not dgu,
        "napomene": (
            [
                "Granice su pojednostavljene za prikaz (županije ~400 m, općine ~80 m).",
                "EU projekti po gradovima i općinama raspoređeni su prema koordinatama "
                "projekta, a po županijama prema županiji navedenoj u izvoru.",
            ]
            if dgu
            else [
                "Granice županija su probne (Natural Earth) dok ne obradimo DGU granice.",
                "Šifre gradova i općina su privremene (vidi data/areas.csv).",
            ]
        ),
        "teme": TEME,
        "pokazatelji": pokazatelji,
        "izvori": meta_izvori({d["izvor"] for d in POKAZATELJI.values()}, dgu),
    }
    spremi_json("meta.json", meta)

    korak("4. Gradovi: Zagreb (četvrti) i Rijeka")
    gradovi.main(sada)

    nedostaje = [p for p in POKAZATELJI if p not in godine]
    if nedostaje:
        print(f"\nPokazatelji bez podataka: {', '.join(nedostaje)}")
    print("\nGotovo.")


if __name__ == "__main__":
    main()
