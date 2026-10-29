"""Zajedničke funkcije za izradu datoteka u web/public/data/ (format: docs/format-podataka.md).

Koriste ih build.py (pravi podaci) i probni_podaci.py (izmišljeni podaci), pa obje
skripte uvijek daju isti oblik datoteka.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from pokazatelji import POKAZATELJI

KORIJEN = Path(__file__).resolve().parent.parent
IZLAZ = KORIJEN / "web" / "public" / "data"


def _cisto(v):
    """NaN → None, cijeli brojevi bez .0, ostalo zaokruženo na 2 decimale."""
    if v is None:
        return None
    try:
        if math.isnan(v):
            return None
    except TypeError:
        return v
    return int(v) if float(v).is_integer() else round(float(v), 2)


def zapis_podrucja(
    sifra: str, naziv: str, vrsta: str, nadredeno: str | None, vrijednosti: dict
) -> dict:
    """Jedno područje u dogovorenom obliku; po_stanovniku se računa iz stanovništva."""
    vrijednosti = {k: _cisto(v) for k, v in vrijednosti.items()}
    stan = vrijednosti.get("stanovnistvo")
    po_st = {}
    for pid, v in vrijednosti.items():
        ps = POKAZATELJI[pid]["po_stanovniku"]
        if ps:
            po_st[pid] = round(v / stan * ps["mnozitelj"], 2) if v is not None and stan else None
    return {
        "sifra": sifra,
        "naziv": naziv,
        "vrsta": vrsta,
        "nadredeno": nadredeno,
        "pokazatelji": vrijednosti,
        "po_stanovniku": po_st,
        "rang": {},
        "slicni": [],
    }


def dodaj_rang(podrucja: dict[str, dict]) -> None:
    """Rang 1 = najveća vrijednost, samo među područjima koja imaju podatak."""
    if not podrucja:
        return
    prvo = next(iter(podrucja.values()))
    for dio in ("pokazatelji", "po_stanovniku"):
        for pid in prvo[dio]:
            vr = {s: z[dio][pid] for s, z in podrucja.items() if z[dio].get(pid) is not None}
            poredak = sorted(vr, key=lambda s: vr[s], reverse=True)
            mjesto = {s: i + 1 for i, s in enumerate(poredak)}
            kljuc = pid if dio == "pokazatelji" else f"{pid}_po_stanovniku"
            for s, z in podrucja.items():
                z["rang"][kljuc] = mjesto.get(s)


def dodaj_slicne(podrucja: dict[str, dict], koliko: int = 5) -> None:
    """Slična područja = najbliža po broju stanovnika (iste razine)."""
    stan = {s: z["pokazatelji"].get("stanovnistvo") for s, z in podrucja.items()}
    imaju = [s for s in podrucja if stan[s] is not None]
    for s in imaju:
        ostali = sorted((o for o in imaju if o != s), key=lambda o: abs(stan[o] - stan[s]))
        podrucja[s]["slicni"] = ostali[:koliko]


def spremi_json(ime: str, podaci, uvlaka: int | None = 2) -> Path:
    put = IZLAZ / ime
    put.parent.mkdir(parents=True, exist_ok=True)
    put.write_text(json.dumps(podaci, ensure_ascii=False, indent=uvlaka), encoding="utf-8")
    print(f"  {put.relative_to(KORIJEN)}  ({put.stat().st_size / 1024:.0f} KB)")
    return put
