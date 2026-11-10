"""„Što je neobično ovdje”: po čemu grad ili općina najviše odstupa od sličnih.

Slični su gradovi i općine istog tipa iz tipologije (tipologija.py, k-means), pa se mala
općina uspoređuje s malim općinama, a veliki grad s velikim gradovima. Za svaki pokazatelj
s popisa POKAZATELJI računa se robusni z: (x − medijan) / (1,4826 · MAD) unutar tipa, za
iznose na logaritamskoj ljestvici (iznosi po stanovniku jako su nakošeni). Pokazatelji s
|z| ≥ PRAG ulaze u uvide, najviše NAJVISE po području, najveće odstupanje prvo. Za
postotke i godine razlika mora biti i barem MIN_RAZLIKA (postotni bod, godina), da mala
razlika u uskoj raspodjeli ne ispadne „neobična”.

Uvid nije ocjena: više ulaganja ili veći udio jednog dobavljača može biti i dobro i loše.
Sučelje od brojeva slaže rečenicu na hrvatskom ili engleskom (Neobicno.svelte).
"""

from __future__ import annotations

import math
from statistics import median

PRAG = 2.0  # |z| od kojeg je odstupanje „neobično”
NAJVISE = 3  # uvida po gradu ili općini
NAJMANJE_SLICNIH = 20  # manji tip nema pouzdan medijan
MIN_RAZLIKA = 1.0  # za pokazatelje bez logaritma: postotni bod ili godina

# pokazatelj: (po stanovniku?, logaritamska ljestvica?)
POKAZATELJI: dict[str, tuple[bool, bool]] = {
    "neto_dohodak": (True, True),
    "prosjecna_starost": (False, False),
    "lokalni_prihodi": (True, True),
    "lokalna_ulaganja": (True, True),
    "udio_pomoci_u_prihodima": (False, False),
    "porez_na_dohodak": (True, True),
    "porez_na_promet_nekretnina": (True, True),
    "prihodi_od_imovine": (True, True),
    "eu_2127_ugovoreno": (True, True),
    "javna_nabava": (True, True),
    "nabava_najveci_dobavljac": (False, False),
    "nabava_bez_objave": (False, False),
}


def _vrijednost(podrucje: dict, kljuc: str, po_st: bool) -> float | None:
    v = (podrucje["po_stanovniku"] if po_st else podrucje["pokazatelji"]).get(kljuc)
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)


def _ljestvica(v: float, log: bool) -> float | None:
    if not log:
        return v
    return math.log(v) if v > 0 else None


def izracunaj(jls: dict[str, dict]) -> dict:
    """jls: zapisi gradova i općina iz izvoza (pokazatelji, po_stanovniku, tip).

    Vraća {"prag", "podrucja": {sifra: [uvid, …]}, "tipovi": {tip: broj}}; uvid je
    {kljuc, po_stanovniku, vrijednost, slicni (medijan tipa), z, smjer: "vise"|"manje"}."""
    po_tipu: dict[str, list[str]] = {}
    for sifra, p in jls.items():
        if p.get("tip"):
            po_tipu.setdefault(p["tip"], []).append(sifra)

    # medijan i MAD po tipu i pokazatelju (na ljestvici usporedbe)
    stat: dict[tuple[str, str], tuple[float, float, float]] = {}
    for tip, sifre in po_tipu.items():
        if len(sifre) < NAJMANJE_SLICNIH:
            continue
        for kljuc, (po_st, log) in POKAZATELJI.items():
            sirovo = [_vrijednost(jls[s], kljuc, po_st) for s in sifre]
            sirovo = [v for v in sirovo if v is not None]
            skala = [x for x in (_ljestvica(v, log) for v in sirovo) if x is not None]
            if len(skala) < NAJMANJE_SLICNIH:
                continue
            m = median(skala)
            mad = median(abs(x - m) for x in skala)
            if mad > 0:
                stat[(tip, kljuc)] = (m, 1.4826 * mad, median(sirovo))

    podrucja: dict[str, list[dict]] = {}
    for sifra, p in jls.items():
        uvidi = []
        for kljuc, (po_st, log) in POKAZATELJI.items():
            s = stat.get((p.get("tip"), kljuc))
            v = _vrijednost(p, kljuc, po_st)
            x = None if v is None else _ljestvica(v, log)
            if s is None or x is None:
                continue
            z = (x - s[0]) / s[1]
            if not log and abs(v - s[2]) < MIN_RAZLIKA:
                continue
            if abs(z) >= PRAG:
                uvidi.append(
                    {
                        "kljuc": kljuc,
                        "po_stanovniku": po_st,
                        "vrijednost": round(v, 2),
                        "slicni": round(s[2], 2),
                        "z": round(z, 2),
                        "smjer": "vise" if z > 0 else "manje",
                    }
                )
        uvidi.sort(key=lambda u: -abs(u["z"]))
        podrucja[sifra] = uvidi[:NAJVISE]

    return {
        "prag": PRAG,
        "tipovi": {t: len(s) for t, s in po_tipu.items()},
        "podrucja": podrucja,
    }


def provjeri(r: dict, broj_jls: int) -> None:
    if len(r["podrucja"]) != broj_jls:
        raise SystemExit(f"Uvidi: {len(r['podrucja'])} od {broj_jls} gradova i općina.")
    imaju = sum(1 for u in r["podrucja"].values() if u)
    if not 0.2 * broj_jls <= imaju <= 0.95 * broj_jls:
        raise SystemExit(f"Uvidi: neobičan broj područja s uvidima ({imaju} od {broj_jls}).")
