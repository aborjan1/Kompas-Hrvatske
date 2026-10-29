"""Proračuni gradova, općina i županija (Ministarstvo financija, PR-RAS i RAS-funkcijski).

Pokazatelji za kartu računaju se za zadnju godinu, a vremenski niz 2019.–zadnja i
rashodi po funkcijama idu u web/public/data/proracuni.json za grafove u panelu.

Županija na karti = zbroj proračuna županije i svih njezinih gradova i općina (lokalna
razina na tom području); država = zbroj svih. Zbrojeve računamo sami iz pojedinačnih
proračuna, a zbirne listove Ministarstva koristimo samo za provjeru (vidi provjeri()).
"""

from __future__ import annotations

import citaci
import pandas as pd
from nazivi import uskladi
from zupanije import ZUPANIJE

FUNKCIJE = [f"{i:02d}" for i in range(1, 11)]


def _pokazatelji(p: pd.DataFrame) -> pd.DataFrame:
    """Iz stavki (stupci '6', '7', '3', '4', '63') u pokazatelje."""
    out = pd.DataFrame(index=p.index)
    out["lokalni_prihodi"] = p["6"] + p["7"]
    out["lokalni_rashodi"] = p["3"] + p["4"]
    out["lokalna_ulaganja"] = p["4"]
    out["saldo_lokalnog_proracuna"] = out["lokalni_prihodi"] - out["lokalni_rashodi"]
    out["udio_pomoci_u_prihodima"] = p["63"] / out["lokalni_prihodi"] * 100
    return out


def ucitaj(jls: pd.DataFrame) -> dict:
    """jls: tablica gradova i općina (sifra, zupanija, kljuc). Vraća rječnik s tablicama
    pokazatelja za JLS, županije i državu, vremenskim nizovima i godinom."""
    d, zadnja = citaci.lokalni_proracuni()
    jedinice = d[d["razina"].isin(["jls", "zupanija"])].copy()

    # nazivi listova ("GRAD GOSPIĆ") → službene šifre JLS, županiju po županiju
    lj = jedinice[jedinice["razina"] == "jls"][["zupanija", "kljuc"]].drop_duplicates()
    sifre = {}
    for z, grupa in lj.groupby("zupanija"):
        cilj = jls[jls["zupanija"] == z]
        mapa = uskladi(list(grupa["kljuc"]), list(cilj["kljuc"]))
        po_kljucu = cilj.set_index("kljuc")["sifra"]
        for k in grupa["kljuc"]:
            sifre[(z, k)] = po_kljucu.get(mapa.get(k, k))
    jedinice["sifra"] = [
        sifre.get((z, k)) if r == "jls" else z
        for z, k, r in zip(jedinice["zupanija"], jedinice["kljuc"], jedinice["razina"], strict=True)
    ]
    nespojeno = jedinice[(jedinice["razina"] == "jls") & jedinice["sifra"].isna()]
    if len(nespojeno):
        raise ValueError(f"Proračuni: nespojeni gradovi/općine {sorted(set(nespojeno['naziv']))}")

    siroko = jedinice.pivot_table(
        index=["razina", "zupanija", "sifra", "godina"],
        columns="stavka",
        values="iznos",
        aggfunc="sum",
    ).fillna(0)
    jl = siroko.xs("jls", level="razina").droplevel("zupanija")
    # županija = vlastiti proračun + svi gradovi i općine (Grad Zagreb nema zaseban županijski)
    po_zup = siroko.groupby(["zupanija", "godina"]).sum()
    drzava = siroko.groupby("godina").sum()

    return {
        "godina": zadnja,
        "jls": _pokazatelji(jl.xs(zadnja, level="godina")),
        "zupanije": _pokazatelji(po_zup.xs(zadnja, level="godina")),
        "drzava": _pokazatelji(drzava.loc[[zadnja]]).iloc[0],
        "nizovi": {"jls": jl, "zupanije": po_zup, "drzava": drzava},
        "zbirni": d[d["razina"].isin(["zupanija_ukupno", "drzava"])],
        "broj_jls": jl.index.get_level_values("sifra").nunique(),
    }


def provjeri(r: dict) -> list[str]:
    """Usporedba naših zbrojeva sa zbirnim listovima Ministarstva (zadnja godina)."""
    upozorenja = []
    z = r["zbirni"]
    z = z[z["godina"] == r["godina"]].pivot_table(
        index="zupanija", columns="stavka", values="iznos", aggfunc="sum"
    )
    nasi = r["nizovi"]["zupanije"].xs(r["godina"], level="godina")
    nasi.loc["HR"] = r["nizovi"]["drzava"].loc[r["godina"]]
    for stavka in ("6", "7", "3", "4", *FUNKCIJE):
        for oznaka in z.index:
            a, b = nasi.loc[oznaka, stavka], z.loc[oznaka, stavka]
            if b and abs(a - b) / abs(b) > 0.01:
                upozorenja.append(
                    f"{oznaka} {stavka}: zbroj jedinica {a / 1e6:,.1f} mil. ≠ zbirni list "
                    f"{b / 1e6:,.1f} mil. EUR"
                )
    return upozorenja


def json_nizovi(r: dict) -> dict:
    """Vremenski nizovi i funkcije za panel: {godine, podrucja: {sifra: {...}}}."""

    def zapis(t: pd.DataFrame) -> dict:
        t = t.sort_index()
        p = _pokazatelji(t)
        zadnji = t.iloc[-1]
        return {
            "prihodi": [round(v) for v in p["lokalni_prihodi"]],
            "rashodi": [round(v) for v in p["lokalni_rashodi"]],
            "ulaganja": [round(v) for v in p["lokalna_ulaganja"]],
            "funkcije": {f: round(zadnji.get(f, 0)) for f in FUNKCIJE},
        }

    nizovi = r["nizovi"]
    godine = sorted(nizovi["drzava"].index)
    podrucja = {"HR": zapis(nizovi["drzava"])}
    for z in ZUPANIJE:
        podrucja[z] = zapis(nizovi["zupanije"].xs(z, level="zupanija"))
    for s, t in nizovi["jls"].groupby(level="sifra"):
        podrucja[s] = zapis(t.droplevel("sifra"))
    return {
        "godine": [int(g) for g in godine],
        "napomena": "Ostvarenje (ne plan). Županija = proračun županije i svih njezinih "
        "gradova i općina; država = zbroj svih. Funkcije su za zadnju godinu i ne uključuju "
        "prijenose drugim proračunima, pa je njihov zbroj manji od ukupnih rashoda.",
        "funkcije": {
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
        },
        "podrucja": podrucja,
    }
