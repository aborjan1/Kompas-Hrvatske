"""Javna nabava gradova, općina i županija iz registra ugovora EOJN RH (standard OCDS).

Izvor je registar ugovora Elektroničkog oglasnika javne nabave (Narodne novine d.d.) kako ga
objavljuje Open Contracting Data Registry: jedan redak JSON-a po postupku, s naručiteljem,
dobavljačima, vrijednošću ugovora i vrstom postupka.

Što računamo:
  * naručitelj je **uprava grada, općine ili županije** (npr. „Grad Karlovac”,
    „Općina Fažana”, „Zagrebačka županija”); njihove ustanove i trgovačka društva (vrtići,
    komunalna poduzeća, bolnice) imaju vlastite naručitelje i ovdje se ne zbrajaju;
  * vrijednost ugovora u eurima (ugovori u kunama preračunati tečajem 7,5345);
  * godina = godina potpisivanja ugovora; koristimo 2018.–2023., jer od listopada 2024.
    (prelazak na novi EOJN) registar u ovoj objavi nije potpun: mjesečni broj ugovora pada
    na četvrtinu i manje;
  * po županiji: uprava županije i svi njezini gradovi i općine, kao kod proračuna; država:
    sve lokalne uprave zajedno.

Pokazatelji (zadnjih pet cijelih godina, 2019.–2023.; mnoge male općine nemaju ugovor
svake godine, pa jedna godina ne bi bila usporediva):
  javna_nabava            vrijednost ugovora u pet godina (EUR)
  nabava_najveci_dobavljac udio najvećeg dobavljača u vrijednosti ugovora, 5 godina (%)
  nabava_bez_objave        udio vrijednosti ugovora sklopljenih bez prethodne objave, 5 godina (%)
Uz to za svako područje: niz po godinama i najveći dobavljači s vezama prema drugim gradovima i
općinama kod kojih isti dobavljač ima ugovore (graf veza).
"""

from __future__ import annotations

import gzip
import json
import re
from collections import defaultdict

import citaci
import pandas as pd
from nazivi import kljuc, sifra_zupanije, uskladi

KUNA_PO_EURU = 7.5345
PRVA, ZADNJA = 2018, 2023
RAZDOBLJE = 5  # godina za pokazatelje (2019.–2023.)
DOBAVLJACA = 8  # najvećih dobavljača po području
VEZA = 6  # drugih gradova i općina po dobavljaču

# Prva dva broja poštanskog broja → moguće županije; služi samo za razlikovanje istoimenih
# jedinica (Otok, Privlaka, Sveta Nedelja).
_POSTA = {
    "10": {"01", "21"},
    "20": {"19"},
    "21": {"17"},
    "22": {"15"},
    "23": {"13"},
    "31": {"14"},
    "32": {"16"},
    "33": {"10"},
    "34": {"11"},
    "35": {"12"},
    "40": {"20"},
    "42": {"05"},
    "43": {"07"},
    "44": {"03"},
    "47": {"04"},
    "48": {"06"},
    "49": {"02"},
    "51": {"08"},
    "52": {"18"},
    "53": {"09"},
}


def _iznos(postupak: dict) -> float | None:
    """Vrijednost ugovora (zbroj ugovora, inače dodjela) u eurima; strane valute izostavljamo."""
    stavke = postupak.get("contracts") or postupak.get("awards") or []
    ukupno = 0.0
    ima = False
    for s in stavke:
        v = s.get("value") or {}
        if v.get("amount") is None:
            continue
        valuta = v.get("currency")
        if valuta == "HRK":
            ukupno += v["amount"] / KUNA_PO_EURU
        elif valuta == "EUR":
            ukupno += v["amount"]
        else:
            continue
        ima = True
    return ukupno if ima else None


def _godina(postupak: dict) -> int | None:
    for c in postupak.get("contracts") or []:
        if c.get("dateSigned"):
            return int(c["dateSigned"][:4])
    datum = postupak.get("date") or ""
    return int(datum[:4]) if datum[:4].isdigit() else None


class _Narucitelji:
    """Naziv naručitelja → šifra grada/općine ili županije (ili None)."""

    def __init__(self, jls: pd.DataFrame):
        self.po_kljucu: dict[str, list[dict]] = defaultdict(list)
        for r in jls.itertuples():
            self.po_kljucu[r.kljuc].append(
                {"sifra": r.sifra, "zupanija": r.zupanija, "vrsta": r.vrsta}
            )
        self.kljucevi = list(self.po_kljucu)
        self._predmemorija: dict[tuple, str | None] = {}

    def sifra(self, naziv: str, posta: str) -> str | None:
        kljuc_ = (naziv, posta[:2])
        if kljuc_ not in self._predmemorija:
            self._predmemorija[kljuc_] = self._trazi(naziv, posta[:2])
        return self._predmemorija[kljuc_]

    def _trazi(self, naziv: str, posta: str) -> str | None:
        gore = " ".join(naziv.strip().upper().split())
        if re.fullmatch(r"[A-ZČĆŽŠĐ\s\-–]+ŽUPANIJA", gore) and len(gore.split()) <= 4:
            return sifra_zupanije(gore)
        m = re.match(r"(GRAD|OPĆINA|OPCINA)\b", gore)
        if m:
            vrsta = "grad" if m[1] == "GRAD" else "opcina"
            k = kljuc(naziv)
        elif gore.endswith(" OPĆINA") and len(gore.split()) <= 3:  # "Vinodolska općina"
            vrsta, k = "opcina", kljuc(gore)
        else:
            return None
        k = re.sub(r"\bSV\b", "SVETI", k)
        # Isti ključ ili duži naziv koji njime počinje ("NOVIGRAD" → i "NOVIGRAD CITTANOVA"),
        # pa vrsta (grad/općina) i poštanski broj biraju pravu jedinicu.
        kandidati = list(self.po_kljucu.get(k, []))
        kandidati += [
            c for kk in self.kljucevi if kk.startswith(k + " ") for c in self.po_kljucu[kk]
        ]
        if not kandidati:
            k2 = uskladi([k], self.kljucevi).get(k)
            kandidati = list(self.po_kljucu.get(k2, [])) if k2 else []
        if len(kandidati) > 1:
            kandidati = [c for c in kandidati if c["vrsta"] == vrsta] or kandidati
        if len(kandidati) > 1 and posta in _POSTA:
            kandidati = [c for c in kandidati if c["zupanija"] in _POSTA[posta]] or kandidati
        if len(kandidati) > 1 and k in self.po_kljucu:
            tocni = [c for c in kandidati if c in self.po_kljucu[k]]
            kandidati = tocni if len(tocni) == 1 else kandidati
        return kandidati[0]["sifra"] if len(kandidati) == 1 else None


def ugovori(jls: pd.DataFrame) -> pd.DataFrame:
    """Jedan redak po (postupak, dobavljač): narucitelj (šifra), godina, iznos, dobavljac
    (id i naziv), bez_objave. Vrijednost postupka s više dobavljača dijeli se na jednake
    dijelove."""
    nar = _Narucitelji(jls)
    retci = []
    put = citaci.nadji("eojn-ugovori", ".jsonl.gz")
    with gzip.open(put, "rt", encoding="utf-8") as f:
        for redak in f:
            p = json.loads(redak)
            kupac = p.get("buyer") or {}
            stranke = {s.get("id"): s for s in p.get("parties") or []}
            posta = ((stranke.get(kupac.get("id")) or {}).get("address") or {}).get(
                "postalCode", ""
            )
            sifra = nar.sifra(kupac.get("name", ""), str(posta))
            if sifra is None:
                continue
            godina = _godina(p)
            iznos = _iznos(p)
            if godina is None or iznos is None or not PRVA <= godina <= ZADNJA:
                continue
            postupak = (p.get("tender") or {}).get("procurementMethodDetails") or ""
            bez_objave = "bez prethodne objave" in postupak.lower()
            dobavljaci = [s for a in p.get("awards") or [] for s in a.get("suppliers") or []]
            dobavljaci = dobavljaci or [{"id": None, "name": "(nepoznat)"}]
            dio = iznos / len(dobavljaci)
            for d in dobavljaci:
                retci.append(
                    (
                        sifra,
                        godina,
                        dio,
                        str(d.get("id")),
                        (d.get("name") or "").strip(),
                        bez_objave,
                    )
                )
    return pd.DataFrame(
        retci,
        columns=["narucitelj", "godina", "iznos", "dobavljac", "naziv_dobavljaca", "bez_objave"],
    )


def izracunaj(jls: pd.DataFrame) -> dict:
    """Pokazatelji po području, nizovi po godinama i najveći dobavljači s vezama."""
    u = ugovori(jls)
    zup_jls = jls.set_index("sifra")["zupanija"]
    # područje → popis naručitelja koji mu pripadaju (JLS: sam; županija: uprava + JLS; HR: svi)
    u["zupanija"] = [n if len(n) == 2 else zup_jls.get(n) for n in u["narucitelj"]]
    godine = list(range(PRVA, ZADNJA + 1))
    od = ZADNJA - RAZDOBLJE + 1

    # naziv dobavljača: najčešći zapis za isti id
    nazivi = u.groupby("dobavljac")["naziv_dobavljaca"].agg(lambda s: s.value_counts().index[0])
    # kod kojih sve gradova i općina dobavljač ima ugovore (5 godina), s iznosom
    jls_u = u[(u["narucitelj"].str.len() == 5) & (u["godina"] >= od)]
    kupci_dobavljaca = jls_u.groupby(["dobavljac", "narucitelj"])["iznos"].sum()

    def opis(dio: pd.DataFrame) -> dict:
        po_godini = dio.groupby("godina")["iznos"].sum().reindex(godine, fill_value=0)
        zadnjih = dio[dio["godina"] >= od]
        ukupno = zadnjih["iznos"].sum()
        po_dob = zadnjih.groupby("dobavljac")["iznos"].sum().sort_values(ascending=False)
        po_dob = po_dob.drop("None", errors="ignore")
        po_dob = po_dob[po_dob > 0]  # ugovori s iznosom 0 (npr. okvirni sporazumi)
        return {
            "pokazatelji": {
                "javna_nabava": float(ukupno),
                "nabava_najveci_dobavljac": float(po_dob.iloc[0] / ukupno * 100)
                if ukupno and len(po_dob)
                else None,
                "nabava_bez_objave": float(
                    zadnjih.loc[zadnjih["bez_objave"], "iznos"].sum() / ukupno * 100
                )
                if ukupno
                else None,
            },
            "niz": [round(float(v), 2) for v in po_godini],
            "po_dob": po_dob,
            "ukupno": ukupno,
            "ugovora": int(zadnjih["iznos"].count()),
        }

    def dobavljaci(o: dict, sifra: str | None) -> list[dict]:
        out = []
        for dob, iznos in o["po_dob"].head(DOBAVLJACA).items():
            drugi = kupci_dobavljaca.get(dob, pd.Series(dtype=float))
            if sifra is not None:
                drugi = drugi.drop(sifra, errors="ignore")
            drugi = drugi.sort_values(ascending=False)
            out.append(
                {
                    "naziv": nazivi.get(dob, dob),
                    "iznos": round(float(iznos), 2),
                    "udio": round(float(iznos / o["ukupno"] * 100), 1) if o["ukupno"] else None,
                    "drugih_jls": int(len(drugi)),
                    "drugi": [str(s) for s in drugi.head(VEZA).index],
                }
            )
        return out

    pokazatelji, nizovi, veze = {}, {}, {}
    for sifra, dio in u.groupby("narucitelj"):
        if len(sifra) != 5:
            continue
        o = opis(dio)
        pokazatelji[sifra] = o["pokazatelji"]
        nizovi[sifra] = o["niz"]
        veze[sifra] = {"ugovora": o["ugovora"], "dobavljaci": dobavljaci(o, sifra)}
    for z, dio in u.groupby("zupanija"):
        o = opis(dio)
        pokazatelji[z] = o["pokazatelji"]
        nizovi[z] = o["niz"]
        veze[z] = {"ugovora": o["ugovora"], "dobavljaci": dobavljaci(o, None)}
    # Gradovi i općine bez ijednog ugovora u registru (male općine često nabavljaju samo
    # jednostavnom nabavom ispod pragova, koja nije u EOJN-u): nula, bez udjela.
    for sifra in jls["sifra"]:
        if sifra not in pokazatelji:
            pokazatelji[sifra] = {
                "javna_nabava": 0.0,
                "nabava_najveci_dobavljac": None,
                "nabava_bez_objave": None,
            }
            nizovi[sifra] = [0.0] * len(godine)
            veze[sifra] = {"ugovora": 0, "dobavljaci": []}
    o = opis(u)
    pokazatelji["HR"] = o["pokazatelji"]
    nizovi["HR"] = o["niz"]
    veze["HR"] = {"ugovora": o["ugovora"], "dobavljaci": dobavljaci(o, None)}

    return {
        "pokazatelji": pokazatelji,
        "nizovi": nizovi,
        "godine": godine,
        "veze": veze,
        "razdoblje": f"{od}.–{ZADNJA}.",
        "broj_narucitelja": int(u["narucitelj"].nunique()),
        "broj_ugovora": int(len(u)),
    }


def json_veze(r: dict) -> dict:
    """nabava.json za panel: najveći dobavljači i veze po području."""
    return {
        "razdoblje": r["razdoblje"],
        "napomena": "Ugovori uprave grada, općine ili županije iz registra ugovora EOJN RH "
        "(bez njihovih ustanova i trgovačkih društava). Županija: uprava županije i svi njezini "
        "gradovi i općine. Iznosi u EUR, kune preračunate tečajem 7,5345.",
        "podrucja": r["veze"],
    }


def provjeri(r: dict, broj_jls: int) -> None:
    if r["broj_narucitelja"] < 0.9 * broj_jls:
        raise SystemExit(
            f"Nabava: samo {r['broj_narucitelja']} naručitelja spojeno (očekivano barem 90 % JLS)."
        )
    for sifra in ["HR", *[f"{i:02d}" for i in range(1, 22)]]:
        if sifra not in r["pokazatelji"]:
            raise SystemExit(f"Nabava: nema podataka za {sifra}.")
