"""Šifrarnik područja: data/areas.csv (issue: šifrarnik + ujednačavanje naziva).

Izvori:
  - sifrarnik-jls: popis 556 gradova i općina s pripadajućom županijom (MPUDT)
  - dzs-popis2021: stanovništvo po gradovima/općinama, Popis 2021. (DZS, tablica 6.)

  - granice-upravne-jedinice: DGU Upravne jedinice INSPIRE (službene šifre JLS)

Šifre:
  - županija: službena šifra "01"–"21"
  - grad/općina: službena 5-znamenkasta šifra iz Registra prostornih jedinica (DGU),
    npr. Andrijaševci "00019", Grad Zagreb "01333".
    Ako DGU datoteke nema, dodjeljuje se PRIVREMENA šifra (županija + redni broj).

Pokretanje:  python pipeline/sifrarnik.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citaci import KORIJEN, nadji, popis_kontingenti  # noqa: E402
from nazivi import kljuc, sifra_zupanije, uskladi  # noqa: E402
from zupanije import ZUPANIJE  # noqa: E402

IZLAZ = KORIJEN / "data" / "areas.csv"


def dgu_sifre(sp: pd.DataFrame) -> pd.Series:
    """Službene DGU šifre gradova i općina, spojene po županiji i nazivu.

    DGU nazivi su ponekad duži ("Kaštelir-Labinci - Castelliere-S. Domenica"), pa se
    spajaju istom funkcijom kao i podaci Porezne uprave (nazivi.uskladi).
    """
    from granice import dgu_zip, ucitaj_au

    if dgu_zip() is None:
        print("  UPOZORENJE: nema DGU granica – šifre gradova i općina su PRIVREMENE")
        return sp["zupanija"] + (sp.groupby("zupanija").cumcount() + 1).map("{:03d}".format)

    d = ucitaj_au(razine=("2ndOrder", "3rdOrder"), geometrija=False)
    d = d[d.razina == "jls"].assign(kljuc=lambda x: x["naziv"].map(kljuc))
    sifre = pd.Series(index=sp.index, dtype=object)
    for z, grupa in sp.groupby("zupanija"):
        dz = d[d.zupanija == z]
        mapa = uskladi(list(dz["kljuc"]), list(grupa["kljuc"]))  # DGU ključ → naš ključ
        po_nasem = {nas: dz.loc[dz.kljuc == dgu, "sifra"].iloc[0] for dgu, nas in mapa.items()}
        sifre.loc[grupa.index] = grupa["kljuc"].map(po_nasem)
    if sifre.isna().any():
        bez = sp.loc[sifre.isna(), ["zupanija", "naziv"]]
        raise SystemExit(f"Gradovi/općine bez DGU šifre:\n{bez.to_string()}")
    return sifre


def napravi() -> pd.DataFrame:
    s = pd.read_excel(nadji("sifrarnik-jls", "opcine_gradovi"), dtype=str, engine="calamine")
    s.columns = ["zupanija_naziv", "vrsta", "naziv"]
    s["zupanija"] = s["zupanija_naziv"].map(sifra_zupanije)
    s["vrsta"] = s["vrsta"].str.strip().map({"Grad": "grad", "Općina": "opcina"})
    s["naziv"] = s["naziv"].str.strip()
    s["kljuc"] = s["naziv"].map(kljuc)
    if s[["zupanija", "vrsta"]].isna().any().any():
        raise SystemExit(f"Neprepoznati redovi u šifrarniku:\n{s[s.isna().any(axis=1)]}")

    popis = popis_kontingenti()
    pj = popis[popis.razina == "jls"]
    # Grad Zagreb je i županija i grad: u popisu postoji samo kao redak županije
    zg = popis[(popis.razina == "zupanija") & (popis.zupanija == "21")].assign(
        razina="jls", vrsta="grad", naziv="Zagreb", kljuc="ZAGREB"
    )
    pj = pd.concat([pj, zg])

    sp = s.merge(
        pj[["zupanija", "kljuc", "stanovnistvo"]],
        on=["zupanija", "kljuc"],
        how="outer",
        indicator=True,
    )
    nespojeno = sp[sp["_merge"] != "both"]
    if len(nespojeno):
        raise SystemExit(
            "Nazivi koji se ne poklapaju (šifrarnik ↔ popis):\n"
            + nespojeno[["zupanija", "naziv", "kljuc", "_merge"]].to_string()
        )

    sp = sp.sort_values(["zupanija", "kljuc"]).reset_index(drop=True)
    sp["sifra"] = dgu_sifre(sp)
    jls = sp[["sifra", "naziv", "vrsta", "zupanija", "kljuc"]].assign(
        stanovnistvo_2021=sp["stanovnistvo"].astype(int)
    )

    pz = popis[popis.razina == "zupanija"].set_index("zupanija")["stanovnistvo"]
    zup = pd.DataFrame(
        [
            {
                "sifra": sif,
                "naziv": puni,
                "vrsta": "zupanija",
                "zupanija": sif,
                "kljuc": kljuc(kratki),
                "stanovnistvo_2021": int(pz[sif]),
            }
            for sif, (puni, kratki) in ZUPANIJE.items()
        ]
    )
    return pd.concat([zup, jls], ignore_index=True)


def provjeri(a: pd.DataFrame) -> None:
    z, j = a[a.vrsta == "zupanija"], a[a.vrsta != "zupanija"]
    greske = []
    if len(z) != 21:
        greske.append(f"županija: {len(z)} (očekivano 21)")
    if len(j) != 556:
        greske.append(f"gradova i općina: {len(j)} (očekivano 556)")
    if (j.vrsta == "grad").sum() != 128:
        greske.append(f"gradova: {(j.vrsta == 'grad').sum()} (očekivano 128)")
    if a["sifra"].duplicated().any():
        greske.append("dvostruke šifre")
    zbroj = j.groupby("zupanija")["stanovnistvo_2021"].sum()
    for sif, st in z.set_index("sifra")["stanovnistvo_2021"].items():
        if zbroj.get(sif) != st:
            greske.append(f"županija {sif}: zbroj JLS {zbroj.get(sif)} ≠ {st}")
    if greske:
        raise SystemExit("Provjera šifrarnika NIJE prošla:\n  " + "\n  ".join(greske))
    ukupno = f"{j['stanovnistvo_2021'].sum():,}".replace(",", ".")
    print(
        f"Šifrarnik: 21 županija, {len(j)} gradova i općina "
        f"({(j.vrsta == 'grad').sum()} gradova), {ukupno} stanovnika – provjera prošla"
    )


def main() -> pd.DataFrame:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = napravi()
    provjeri(a)
    a.to_csv(IZLAZ, index=False, encoding="utf-8")
    print(f"  {IZLAZ.relative_to(KORIJEN)}")
    return a


if __name__ == "__main__":
    main()
