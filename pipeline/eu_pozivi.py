"""Planirani EU pozivi za gradove, općine i županije (web/public/data/eu-pozivi.json).

Izvor su indikativni planovi objave poziva Ministarstva regionalnoga razvoja i fondova EU za
2026.: Program Konkurentnost i kohezija (PKK), Integrirani teritorijalni program (ITP) i
Program Učinkoviti ljudski potencijali (ULJP). Svaki redak plana je jedan poziv s nazivom,
područjem, vrstom postupka, prihvatljivim prijaviteljima, iznosom i okvirnim datumima.

Za svaki poziv iz teksta zaključujemo:
  * smije li se prijaviti **grad ili općina** i/ili **županija**, kao prijavitelj ili kao
    partner (npr. „JLPRS”, „jedinica lokalne ili regionalne (područne) samouprave”,
    „Osnivači osnovnih škola”);
  * je li poziv **namijenjen određenom gradu ili općini** („Grad Zadar”, „Općina Sv. Petar u
    Šumi”) ili jedinicama iz obuhvata urbanog područja („JLS iz obuhvata UA Osijek”);
  * **područje**: cijela Hrvatska, županije ili NUTS 2 regije (Panonska, Jadranska,
    Sjeverna Hrvatska, Grad Zagreb).
Pozivi u kojima lokalna i regionalna samouprava nemaju ulogu (npr. samo poduzetnici ili
ministarstvo) ne ulaze u datoteku, ali se broje.

Ovo je tumačenje teksta plana, a ne službena odluka o prihvatljivosti: uvjeti su u samom
pozivu, pa sučelje uz svaki poziv navodi izvorni tekst o prijaviteljima.
"""

from __future__ import annotations

import re
from datetime import date

import citaci
import pandas as pd
from nazivi import kljuc, sifra_zupanije

# NUTS 2 regije (HR NUTS 2021) → županije
NUTS2 = {
    "PANONSKA": ["03", "04", "07", "10", "11", "12", "14", "16"],
    "JADRANSKA": ["08", "09", "13", "15", "17", "18", "19"],
    "SJEVERNA": ["01", "02", "05", "06", "20"],
    "GRAD ZAGREB": ["21"],
}
MJESECI = {
    "siječanj": 1, "veljača": 2, "ožujak": 3, "travanj": 4, "svibanj": 5, "lipanj": 6,
    "srpanj": 7, "kolovoz": 8, "rujan": 9, "listopad": 10, "studeni": 11, "prosinac": 12,
}  # fmt: skip

_JLS = re.compile(
    r"\bJLP\(?R\)?S\b|\bJLPRS\b|\bJLS\b|JLS-ov|jedinic\w*\s+lokaln|lokalne\s+ili\s+regionalne"
    r"|osnivači\s+osnovnih\s+škola",
    re.IGNORECASE,
)
_ZUP = re.compile(
    r"\bJLP\(?R\)?S\b|\bJLPRS\b|područne\s*\(regionalne\)|regionalne\s*\(područne\)"
    r"|\(lokalne\)\s*regionalne|jedinic\w*\s+područn",
    re.IGNORECASE,
)
_IMENOVANI = re.compile(
    r"\b(Grad|Općina)\s+([A-ZČĆŽŠĐ][\w.\-]*(?:\s+(?:[a-zčćžšđ]{1,2}|[A-ZČĆŽŠĐ][\w.\-]*))*)"
)
_OBUHVAT = re.compile(r"JLS(?:-ovi)?\s+iz\s+obuhvata\s+(U[AP])\s+([A-ZČĆŽŠĐ]\w+)", re.IGNORECASE)


def _datum(v: str) -> tuple[str | None, bool]:
    """'2026-10-05 00:00:00' → ('2026-10-05', False); 'listopad 2026.' → ('2026-10', True)."""
    v = (v or "").strip()
    if re.match(r"\d{4}-\d\d-\d\d", v):
        return v[:10], False
    m = re.match(r"([a-zčćžšđ]+)\s+(\d{4})", v.lower())
    if m and m[1] in MJESECI:
        return f"{m[2]}-{MJESECI[m[1]]:02d}", True
    return None, False


def _uloga(tekst: str, uzorak: re.Pattern) -> str | None:
    """'prijavitelj' ako se jedinica spominje među prijaviteljima, 'partner' ako samo među
    partnerima, inače None."""
    dijelovi = re.split(r"Partner\w*\s*:", tekst, maxsplit=1, flags=re.IGNORECASE)
    if uzorak.search(dijelovi[0]):
        return "prijavitelj"
    if len(dijelovi) > 1 and uzorak.search(dijelovi[1]):
        return "partner"
    return None


class _Jedinice:
    def __init__(self, jls: pd.DataFrame):
        self.jls = jls
        self.po_kljucu = {}
        for r in jls.itertuples():
            self.po_kljucu.setdefault(r.kljuc, []).append(r)

    def nadji(self, vrsta: str | None, naziv: str) -> str | None:
        k = re.sub(r"\bSV\b", "SVETI", kljuc(naziv))
        kandidati = list(self.po_kljucu.get(k, []))
        kandidati += [r for kk, rr in self.po_kljucu.items() if kk.startswith(k + " ") for r in rr]
        if vrsta and len(kandidati) > 1:
            kandidati = [r for r in kandidati if r.vrsta == vrsta] or kandidati
        return kandidati[0].sifra if len(kandidati) == 1 else None

    def zupanija(self, sifra: str) -> str:
        return self.jls.set_index("sifra").loc[sifra, "zupanija"]


def _podrucje(tekst: str, jed: _Jedinice) -> tuple[list[str] | None, list[str]]:
    """(županije ili None za cijelu Hrvatsku, imenovani gradovi iz „Gradovi - X”)."""
    t = " ".join((tekst or "").split())
    gore = t.upper()
    if not t or gore in ("REPUBLIKA HRVATSKA", "HR0", "HRVATSKA") or "POTPOMOGNUT" in gore:
        return None, []
    gradovi = []
    if gore.startswith("GRADOVI"):
        dio = re.sub(r"^GRADOVI\s*-\s*", "", t, flags=re.IGNORECASE)
        zupanije = []
        for d in re.split(r",", dio):
            z = sifra_zupanije(d)
            if z:
                zupanije.append(z)
            else:
                s = jed.nadji("grad", d)
                if s:
                    gradovi.append(s)
        zupanije = zupanije or [jed.zupanija(s) for s in gradovi]
        return sorted(set(zupanije)), gradovi
    zupanije = []
    for regija, z in NUTS2.items():
        if regija in gore and ("HRVATSK" in gore or regija == "GRAD ZAGREB"):
            zupanije += z
    for d in re.split(r",|\si\s", t):
        z = sifra_zupanije(d)
        if z:
            zupanije.append(z)
    return (sorted(set(zupanije)) or None), gradovi


def _redovi() -> list[dict]:
    """Svi pozivi iz tri plana u istom obliku."""
    out = []
    for sid, program in (("eu-pozivi-pkk-2026", "PKK"), ("eu-pozivi-itp-2026", "ITP")):
        put = citaci.nadji(sid, ".xlsx")
        t = pd.read_excel(put, 0, header=None, dtype=str, engine="calamine").fillna("")
        zag = next(i for i in range(len(t)) if t.iloc[i, 0].strip().startswith("Redni broj"))
        for i in range(zag + 1, len(t)):
            r = t.iloc[i]
            if not r[1].strip():
                continue
            out.append(
                {
                    "program": program,
                    "naziv": r[1],
                    "podrucje": r[2],
                    "vrsta": r[6],
                    "aktivnosti": r[7],
                    "prijavitelji": r[8],
                    "iznos": citaci.broj(r[9]),
                    "pocetak": r[11],
                    "kraj": r[12],
                    "izvor": sid,
                }
            )
    put = citaci.nadji("eu-pozivi-uljp-2026", ".xlsx")
    for list_ in pd.ExcelFile(put, engine="calamine").sheet_names:
        t = pd.read_excel(put, list_, header=None, dtype=str, engine="calamine").fillna("")
        zag = next(i for i in range(len(t)) if t.iloc[i, 0].strip().startswith("Br."))
        for i in range(zag + 1, len(t)):
            r = t.iloc[i]
            if not r[1].strip():
                continue
            out.append(
                {
                    "program": "ULJP",
                    "naziv": r[1],
                    "podrucje": r[14],
                    "vrsta": r[5],
                    "aktivnosti": r[7],
                    "prijavitelji": r[9] if r[9].strip() not in ("", "n/p") else r[8],
                    "iznos": citaci.broj(r[10]),
                    "pocetak": r[15],
                    "kraj": "",  # plan ULJP-a daje datum objave rezultata, ne kraj poziva
                    "izvor": "eu-pozivi-uljp-2026",
                }
            )
    return out


def _cisto(s: str) -> str:
    return " ".join(str(s).replace("\n", " ").split())


def izracunaj(jls: pd.DataFrame) -> dict:
    jed = _Jedinice(jls)
    pozivi, bez_uloge = [], 0
    redni: dict[str, int] = {}
    for r in _redovi():
        redni[r["program"]] = n = redni.get(r["program"], 0) + 1
        prij = _cisto(r["prijavitelji"])
        uloga_jls = _uloga(prij, _JLS)
        uloga_zup = _uloga(prij, _ZUP)
        imenovani = []
        dio_prij = re.split(r"Partner\w*\s*:", prij, maxsplit=1, flags=re.IGNORECASE)[0]
        for vrsta, naziv in _IMENOVANI.findall(dio_prij):
            s = jed.nadji("grad" if vrsta == "Grad" else "opcina", naziv)
            if s:
                imenovani.append(s)
        zupanije, gradovi = _podrucje(r["podrucje"], jed)
        napomena = None
        m = _OBUHVAT.search(prij)
        if m:
            napomena = (
                f"Samo za gradove i općine iz obuhvata "
                f"{'urbane aglomeracije' if m[1].upper() == 'UA' else 'urbanog područja'} {m[2]}."
            )
            uloga_jls = uloga_jls or "prijavitelj"
            imenovani += gradovi  # središte urbanog područja
            if gradovi and not zupanije:
                zupanije = sorted({jed.zupanija(s) for s in gradovi})
        if not (uloga_jls or uloga_zup or imenovani):
            bez_uloge += 1
            continue
        pocetak, mj_p = _datum(r["pocetak"])
        kraj, mj_k = _datum(r["kraj"])
        pozivi.append(
            {
                "id": f"{r['program']}-{n}",
                "program": r["program"],
                "naziv": _cisto(r["naziv"]),
                "vrsta": _cisto(r["vrsta"]).capitalize(),
                "iznos": r["iznos"],
                "pocetak": pocetak,
                "kraj": kraj,
                "samo_mjesec": mj_p or mj_k,
                "podrucje": _cisto(r["podrucje"]) or "Republika Hrvatska",
                "zupanije": zupanije,  # None = cijela Hrvatska
                "jls": uloga_jls,
                "zupanija": uloga_zup,
                "imenovani": sorted(set(imenovani)),
                "prijavitelji": prij[:400],
                "napomena": napomena,
                "izvor": r["izvor"],
            }
        )
    pozivi.sort(key=lambda p: (p["pocetak"] or "9999", p["naziv"]))
    return {
        "azurirano": date.today().isoformat(),
        "napomena": "Indikativni planovi objave poziva za 2026. (PKK, ITP: listopad 2026.; ULJP: "
        "III. izmjena). Prihvatljivost je zaključena iz teksta plana; točni uvjeti su u pozivu.",
        "ukupno_poziva": len(pozivi) + bez_uloge,
        "bez_lokalne_samouprave": bez_uloge,
        "pozivi": pozivi,
    }


def provjeri(r: dict) -> None:
    if not r["pozivi"]:
        raise SystemExit("EU pozivi: nijedan poziv za gradove, općine ili županije.")
    if r["ukupno_poziva"] < 20:
        raise SystemExit(
            f"EU pozivi: samo {r['ukupno_poziva']} poziva u planovima (očekivano 40+)."
        )
