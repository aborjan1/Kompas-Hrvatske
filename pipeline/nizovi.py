"""Vremenski nizovi za grafove u panelu (web/public/data/nizovi.json).

Za svaku temu po nekoliko pokazatelja kroz godine, na razinama na kojima ih izdavatelji
objavljuju: država (`HR`), županije (`01`–`21`) i, gdje postoje, gradovi i općine (službena
šifra). Vrijednosti su ukupni iznosi; sučelje ih po potrebi dijeli brojem stanovnika iz
Popisa 2021. (polje `po_stanovniku`, kao u katalogu pokazatelja).

Proračunski nizovi (Novac) i dalje su u proracuni.json; ovdje su samo ostale teme.
"""

from __future__ import annotations

import citaci
import pandas as pd
from nazivi import uskladi

_PO_ST_EUR = {"mnozitelj": 1, "jedinica": "EUR po stanovniku"}
_NA_1000 = {"mnozitelj": 1000, "jedinica": "na 1.000 stanovnika"}


def _serija(naziv, tema, jedinica, decimale, po_stanovniku, izvor, godine, razine, napomena):
    return {
        "naziv": naziv,
        "tema": tema,
        "jedinica": jedinica,
        "decimale": decimale,
        "po_stanovniku": po_stanovniku,
        "izvor": izvor,
        "godine": [int(g) for g in godine],
        "razine": razine,
        "napomena": napomena,
    }


def _sifre_dohotka(dj: pd.DataFrame, jls: pd.DataFrame) -> pd.Series:
    """Nazivi gradova i općina iz Porezne uprave → službene šifre, županiju po županiju."""
    sifre = {}
    for z, grupa in dj.groupby("zupanija"):
        cilj = jls[jls["zupanija"] == z]
        mapa = uskladi(list(grupa["kljuc"]), list(cilj["kljuc"]))
        po_kljucu = cilj.set_index("kljuc")["sifra"]
        for i, k in grupa["kljuc"].items():
            sifre[i] = po_kljucu.get(mapa.get(k, k))
    return pd.Series(sifre)


def izracunaj(jls: pd.DataFrame, pr: dict, nab: dict | None = None) -> dict:
    """jls: gradovi i općine (sifra, zupanija, kljuc); pr: rezultat proracuni.ucitaj();
    nab: rezultat nabava.izracunaj() (neobavezno).

    Vraća {"serije": {id: opis}, "podrucja": {sifra: {id: [vrijednost po godini]}}}."""
    serije: dict[str, dict] = {}
    podrucja: dict[str, dict[str, list]] = {}

    def upisi(sid: str, tablica: pd.DataFrame) -> None:
        """tablica: redak po šifri područja, stupac po godini (redom kao u seriji)."""
        for sifra, red in tablica.iterrows():
            vrijednosti = [None if pd.isna(v) else round(float(v), 2) for v in red]
            if any(v is not None for v in vrijednosti):
                podrucja.setdefault(str(sifra), {})[sid] = vrijednosti

    # --- Ljudi
    pr_st, _, _ = citaci.procjena_stanovnistva()
    serije["stanovnistvo"] = _serija(
        "Broj stanovnika (procjena DZS-a)", "ljudi", "osoba", 0, None,
        "dzs-procjena-stanovnistva", pr_st.columns, ["drzava", "zupanija"],
        "Procjena sredinom godine; uključuje doseljene i odseljene te rođene i umrle.",
    )  # fmt: skip
    upisi("stanovnistvo", pr_st)

    nz = citaci.nezaposlenost_po_godinama()
    serije["nezaposlenost"] = _serija(
        "Stopa registrirane nezaposlenosti", "ljudi", "%", 1, None, "dzs-place", nz.columns,
        ["drzava", "zupanija"], "Godišnji prosjek mjesečnih stopa.",
    )  # fmt: skip
    upisi("nezaposlenost", nz)

    # Dohodak i porez: jedan list Porezne uprave po godini (2022. u kunama → EUR).
    listovi = citaci.dohodak_listovi()
    godine = [citaci._godina(s) for s in listovi]
    neto, porez = {}, {}
    for list_, god in zip(listovi, godine, strict=True):
        dj, vise, _ = citaci.dohodak_jls(list_)
        dj["sifra"] = _sifre_dohotka(dj, jls)
        dj = dj.dropna(subset=["sifra"]).set_index("sifra")
        vise = vise.set_index("zupanija")
        neto[god] = pd.concat([dj["neto"], vise["neto"]])
        porez[god] = pd.concat([dj["porez"], vise["porez"]])
    razine_sve = ["drzava", "zupanija", "jls"]
    serije["neto_dohodak"] = _serija(
        "Ukupna primanja stanovnika", "ljudi", "EUR", 0, _PO_ST_EUR, "pu-porez-dohodak",
        godine, razine_sve,
        "Neto dohodak (plaće, mirovine i ostalo nakon poreza i doprinosa); 2022. preračunata "
        "iz kuna fiksnim tečajem 7,5345.",
    )  # fmt: skip
    upisi("neto_dohodak", pd.DataFrame(neto))

    # --- Porezi
    serije["porez_na_dohodak"] = _serija(
        "Plaćeni porez na plaće", "porezi", "EUR", 0, _PO_ST_EUR, "pu-porez-dohodak", godine,
        razine_sve, "Porez na dohodak po prebivalištu obveznika; pripada gradu ili općini.",
    )  # fmt: skip
    upisi("porez_na_dohodak", pd.DataFrame(porez))

    # --- Imovina
    kp = citaci.kupoprodaje_po_godinama()
    serije["kupoprodaje_nekretnina"] = _serija(
        "Prodane nekretnine", "imovina", "broj", 0, _NA_1000, "pu-kupoprodaje", kp.columns,
        ["drzava", "zupanija"], "Broj kupoprodaja po godini (cijele godine).",
    )  # fmt: skip
    upisi("kupoprodaje_nekretnina", kp)

    # Proračunski nizovi: zbroj po godinama iz proracuni.ucitaj (jls, županije, država).
    n = pr["nizovi"]
    god_pr = sorted(n["drzava"].index)

    def proracunski(stavka: str) -> pd.DataFrame:
        jl = n["jls"][stavka].unstack("godina")
        zu = n["zupanije"][stavka].unstack("godina")
        hr = n["drzava"][[stavka]].T.rename(index={stavka: "HR"})
        return pd.concat([jl, zu, hr])[god_pr]

    for sid, stavka, naziv, napomena in [
        (
            "porez_na_promet_nekretnina",
            "6134",
            "Porez od prodaje nekretnina",
            "Porez na promet nekretnina u proračunu (račun 6134). Za županiju: zbroj "
            "županije i njezinih gradova i općina.",
        ),
        (
            "prihodi_od_imovine",
            "642",
            "Prihodi od zakupa i koncesija",
            "Prihodi od nefinancijske imovine u proračunu (skupina 642). Za županiju: zbroj "
            "županije i njezinih gradova i općina.",
        ),
    ]:
        serije[sid] = _serija(
            naziv, "imovina", "EUR", 0, _PO_ST_EUR, "mfin-lokalni-proracuni", god_pr,
            razine_sve, napomena,
        )  # fmt: skip
        upisi(sid, proracunski(stavka))

    # --- Nabava
    if nab is not None:
        serije["javna_nabava"] = _serija(
            "Ugovori javne nabave", "nabava", "EUR", 0, _PO_ST_EUR, "eojn-ugovori",
            nab["godine"], razine_sve,
            "Vrijednost ugovora uprave grada, općine ili županije po godini potpisivanja "
            "(registar ugovora EOJN RH).",
        )  # fmt: skip
        upisi("javna_nabava", pd.DataFrame(nab["nizovi"]).T)

    return {"serije": serije, "podrucja": podrucja}


def provjeri(r: dict, broj_jls: int) -> None:
    """Svaka serija ima podatke za državu i sve županije, a JLS serije za (gotovo) sve JLS."""
    p = r["podrucja"]
    zupanije = [f"{i:02d}" for i in range(1, 22)]
    for sid, s in r["serije"].items():
        for sifra in ["HR", *zupanije]:
            v = p.get(sifra, {}).get(sid)
            if v is None or len(v) != len(s["godine"]):
                raise SystemExit(f"Nizovi: {sid} nema {len(s['godine'])} godina za {sifra}.")
        if "jls" in s["razine"]:
            imaju = sum(1 for k, d in p.items() if len(k) == 5 and sid in d)
            if imaju < broj_jls - 2:
                raise SystemExit(f"Nizovi: {sid} ima samo {imaju} od {broj_jls} JLS.")
