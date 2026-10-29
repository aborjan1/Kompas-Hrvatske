"""Iz data/sources.csv napravi docs/izvori-podataka.md – popis poveznica po fazama.

Ista datoteka služi kao popis izvora u dokumentaciji za predaju.
Pokretanje (iz korijena repozitorija):
    python pipeline/popis_izvora.py
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

KORIJEN = Path(__file__).resolve().parent.parent
SOURCES = KORIJEN / "data" / "sources.csv"
IZLAZ = KORIJEN / "docs" / "izvori-podataka.md"

FAZE = {
    "1": "Kostur: granice i šifrarnici",
    "2": "Razina Država",
    "3": "Razina Županija",
    "4": "Razina Grad",
    "5": "Gradski prikaz: Zagreb",
    "6": "Gradski prikaz: Rijeka",
}

NACIN = {
    "preuzimanje": "skripta",
    "rucno": "ručno",
    "url": "skripta (izravna poveznica)",
    "servis": "servis (WMS/WFS)",
    "api": "API (registracija)",
}

# Izvori izvan data.gov.hr (iz lista "Izvori izvan portala" u katalogu)
VANJSKI = [
    (
        "Upit o trošenju sredstava državnog proračuna",
        "Ministarstvo financija",
        "https://www.drzavna-riznica.hr/trosenje_sredstava_DP/Pretraga/OpcaPretraga",
        "Isplate iz državnog proračuna po primatelju",
    ),
    (
        "Sudski registar – portal za razvojne programere",
        "MPUDT",
        "https://sudreg-data.gov.hr/",
        "REST API, besplatna registracija",
    ),
    (
        "SRDI – javni API",
        "MPUDT",
        "https://srdi.gov.hr/api/docs",
        "Državna imovina, API dokumentacija",
    ),
    (
        "DZS – statističke baze i publikacije",
        "DZS",
        "https://podaci.dzs.hr/hr/",
        "Ako neka tablica fali u „Statistici u nizu”",
    ),
    (
        "Geoportal DGU",
        "Državna geodetska uprava",
        "https://geoportal.dgu.hr/",
        "Preglednik i servisi prostornih podataka",
    ),
    (
        "Portal otvorenih podataka Grada Zagreba",
        "Grad Zagreb",
        "https://data.zagreb.hr/",
        "Izvorni portal za skupove Grada Zagreba",
    ),
]

# Pretrage lokalnih skupova (previše ih je za pojedinačno navođenje)
PRETRAGE = [
    ("Proračuni općina, gradova i županija", "https://data.gov.hr/ckan/dataset?q=prora%C4%8Dun"),
    ("Financijski izvještaji JLS", "https://data.gov.hr/ckan/dataset?q=financijski+izvje%C5%A1taj"),
    ("Isplate iz proračuna (iTransparentnost)", "https://data.gov.hr/ckan/dataset?q=isplate"),
    ("Poslovni prostori i zakupnine", "https://data.gov.hr/ckan/dataset?q=poslovni+prostor"),
]


OD = "https://data.gov.hr/otvorena-dozvola"


def je_dopunski(r: dict) -> bool:
    """Skup koji nije objavljen na data.gov.hr (nema adrese skupa na portalu)."""
    return not r.get("slug")


def stranica(r: dict) -> str:
    if je_dopunski(r):
        return r["poveznica"]
    return f"https://data.gov.hr/ckan/dataset/{r['slug']}"


def dozvola(r: dict) -> str:
    lic = r.get("licenca") or "nije navedena"
    if lic.startswith("Otvorena dozvola"):
        return f"[Otvorena dozvola]({OD})"
    if lic.startswith("Creative Commons Imenovanje 4.0"):
        return "[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.hr)"
    return lic


def tablica_koristenih(skupovi: list[dict]) -> list[str]:
    out = [
        "| Skup | Izdavatelj | Dozvola | Preuzeto | id (mapa) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in skupovi:
        out.append(
            f"| [{r['naziv'].strip()}]({stranica(r)}) | {r['izdavatelj'].strip()} | {dozvola(r)} "
            f"| {r.get('datum_preuzimanja') or '–'} | `{r['id']}` |"
        )
    return out


def korisceni_dio(redovi: list[dict]) -> list[str]:
    aktivni = [r for r in redovi if r["aktivno"] == "da"]
    portal = [r for r in aktivni if not je_dopunski(r)]
    dopunski = [r for r in aktivni if je_dopunski(r)]
    return [
        "## Korišteni skupovi",
        "",
        f"Obrada (`pipeline/build.py`) koristi **{len(aktivni)}** skupova: **{len(portal)}** s "
        f"Portala otvorenih podataka i **{len(dopunski)}** dopunskih izvora tijela javne vlasti. "
        "Sve ih preuzima `python pipeline/download.py`.",
        "",
        "**Kako navoditi izvor.** Za skupove pod Otvorenom dozvolom navodi se izdavatelj, naziv "
        f"skupa, datum preuzimanja i poveznica na [Otvorenu dozvolu]({OD}). Za skupove bez "
        "navedene dozvole (npr. dio skupova DZS-a) navodi se samo izvor uz napomenu da su "
        "javno objavljeni na Portalu (prema odgovoru organizatora datathona, 29. 10. 2026.).",
        "",
        "### A. Portal otvorenih podataka (data.gov.hr)",
        "",
        *tablica_koristenih(portal),
        "",
        "### B. Dopunski izvori tijela javne vlasti",
        "",
        "Pravila datathona dopuštaju dopunu podacima iz drugih javno dostupnih izvora tijela "
        "javne vlasti, uz jasno navođenje izvora.",
        "",
        *tablica_koristenih(dopunski),
        "",
    ]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with SOURCES.open(encoding="utf-8-sig", newline="") as f:
        redovi = list(csv.DictReader(f))

    po_fazi: dict[str, list[dict]] = defaultdict(list)
    for r in redovi:
        po_fazi[r.get("faza", "").split(" ")[0]].append(r)

    n_skripta = sum(r["aktivno"] == "da" for r in redovi)
    out = [
        "# Izvori podataka – Kompas Hrvatske",
        "",
        "Ova datoteka nastaje automatski iz `data/sources.csv` "
        "(`python pipeline/popis_izvora.py`). Ne uređuj je ručno.",
        "",
        f"Broj skupova: **{len(redovi)}**. Skripta "
        f"`pipeline/download.py` preuzima njih **{n_skripta}**, a ostali se preuzimaju "
        "ručno, koriste kao servis izravno na karti ili traže API registraciju.",
        "",
        "Mapa u koju se skup sprema je `data/raw/<id>/`.",
        "",
        *korisceni_dio(redovi),
        "## Svi pregledani skupovi po fazama",
        "",
        "Uključuje i skupove koji su pregledani, ali se ne koriste, te neispravne izvore "
        "(stupac Napomena).",
    ]
    for kljuc, naslov in FAZE.items():
        skupovi = po_fazi.get(kljuc, [])
        if not skupovi:
            continue
        out += [
            "",
            f"### {kljuc}. {naslov}",
            "",
            "| id (mapa) | Skup | Izdavatelj | Formati | Način | Issue | Napomena |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for r in skupovi:
            out.append(
                f"| `{r['id']}` | [{r['naziv']}]({r['poveznica']}) | {r['izdavatelj']} "
                f"| {r.get('formati', '')} | {NACIN.get(r.get('nacin', ''), r.get('nacin', ''))} "
                f"| {r.get('issue', '')} | {r.get('napomena', '')} |"
            )
    out += [
        "",
        "## Ostali korisni izvori (nisu korišteni)",
        "",
        "| Izvor | Izdavatelj | Napomena |",
        "| --- | --- | --- |",
    ]
    out += [f"| [{n}]({u}) | {i} | {o} |" for n, i, u, o in VANJSKI]
    out += [
        "",
        "## Pretrage lokalnih skupova na portalu",
        "",
        "Stotine skupova općina i gradova u različitim formatima. "
        "Za demo ih ne obrađujemo sve, nego samo po potrebi.",
        "",
    ]
    out += [f"- [{n}]({u})" for n, u in PRETRAGE]
    out += [
        "",
    ]

    IZLAZ.parent.mkdir(parents=True, exist_ok=True)
    IZLAZ.write_text("\n".join(out), encoding="utf-8")
    print(f"Spremljeno: {IZLAZ.relative_to(KORIJEN)} (skupova: {len(redovi)})")


if __name__ == "__main__":
    main()
