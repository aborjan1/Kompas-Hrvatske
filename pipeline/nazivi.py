"""Ujednačavanje naziva županija i gradova/općina iz različitih izvora.

Isti grad u izvorima izgleda različito: "Dugo Selo", "GRAD DUGO SELO", "Grad Dugo Selo".
Županija: "Zagrebačka", "ZAGREBAČKA ŽUPANIJA", "01 - ZAGREBAČKA ŽUPANIJA", "I ZAGREBAČKA".
Ove funkcije sve to svode na isti ključ, pa se podaci mogu spojiti po šifri.
"""

from __future__ import annotations

import difflib
import re
import unicodedata

from zupanije import ZUPANIJE

_RIMSKI = re.compile(r"^(?=[IVXL]+\s)[IVXL]+\s+")
_BROJ = re.compile(r"^\d{1,2}\s*[-–.]\s*")


def kljuc(naziv: str) -> str:
    """Ključ za usporedbu naziva grada ili općine: velika slova, bez prefiksa i razmaka."""
    s = unicodedata.normalize("NFC", str(naziv)).upper().strip()
    s = s.replace(".", "")
    # Crtica i razmak su isto: "Ivanić - Grad" = "Ivanić-Grad",
    # "Tar-Vabriga-Torre Abrega" = "Tar-Vabriga-Torre-Abrega"
    s = re.sub(r"[\s\-–—]+", " ", s)
    for prefiks in ("GRAD ", "OPĆINA ", "OPCINA "):
        if s.startswith(prefiks):
            s = s[len(prefiks) :]
    return s.strip()


def uskladi(izvor: list[str], cilj: list[str]) -> dict[str, str]:
    """Ključevi izvora → ključevi cilja (unutar iste županije).

    Prvo točno poklapanje, a za ostale jedinstveno poklapanje po prvim riječima.
    Primjer iz Porezne uprave: "KAŠTELIR LABINCI CASTELLIERE S D" →
    "KAŠTELIR LABINCI CASTELLIERE SANTA DOMENICA".
    """
    cilj_skup = set(cilj)
    out = {k: k for k in izvor if k in cilj_skup}
    slobodni = cilj_skup - set(out.values())
    for k in izvor:
        if k in out:
            continue
        rijeci = k.split()
        for n in range(min(len(rijeci), 3), 0, -1):
            pocetak = " ".join(rijeci[:n])
            kandidati = [c for c in slobodni if c == pocetak or c.startswith(pocetak + " ")]
            if len(kandidati) == 1:
                out[k] = kandidati[0]
                slobodni.discard(kandidati[0])
                break
    return out


def _kljuc_zupanije(naziv: str) -> str:
    s = unicodedata.normalize("NFC", str(naziv)).upper().strip()
    s = _BROJ.sub("", s)
    s = _RIMSKI.sub("", s)
    s = re.sub(r"\s*[-–—]\s*", "-", s)
    s = re.sub(r"\s+Ž[A-Z]*$", "", s)  # "ŽUPANIJA", ali i tipfeler "ŽUAPNIJA"
    return re.sub(r"\s+", " ", s).strip()


def _sazeto(k: str) -> str:
    return re.sub(r"[^A-ZČĆŽŠĐ]", "", k)


_ZUP = {_sazeto(_kljuc_zupanije(kratko)): sifra for sifra, (_, kratko) in ZUPANIJE.items()}


def sifra_zupanije(naziv: str) -> str | None:
    """Šifra županije ("01"–"21") iz bilo kojeg uobičajenog zapisa naziva, ili None.

    Podnosi razmak umjesto crtice ("DUBROVAČKO NERETVANSKA") i sitne tipfelere
    ("Varažinska") – oba se stvarno pojavljuju u izvorima.
    """
    if naziv is None or str(naziv).strip() == "":
        return None
    k = _sazeto(_kljuc_zupanije(naziv))
    if not k:
        return None
    if k in _ZUP:
        return _ZUP[k]
    if k in ("ZAGREB", "CITYOFZAGREB"):
        return "21"
    # Krnji zapisi ("KOPRIVNIČKO-KRIŽEVAČKA ŽUPAN"): jedinstveni početak
    pogodci = [s for z, s in _ZUP.items() if len(k) >= 6 and (z.startswith(k) or k.startswith(z))]
    if len(pogodci) == 1:
        return pogodci[0]
    # Tipfeleri: vrlo sličan naziv
    blizu = difflib.get_close_matches(k, list(_ZUP), n=1, cutoff=0.9)
    return _ZUP[blizu[0]] if blizu else None
