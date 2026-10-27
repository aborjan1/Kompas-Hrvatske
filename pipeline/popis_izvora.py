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
    ]
    for kljuc, naslov in FAZE.items():
        skupovi = po_fazi.get(kljuc, [])
        if not skupovi:
            continue
        out += [
            "",
            f"## {kljuc}. {naslov}",
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
        "## Izvori izvan data.gov.hr",
        "",
        "| Izvor | Izdavatelj | Napomena |",
        "| --- | --- | --- |",
    ]
    out += [f"| [{n}]({u}) | {i} | {o} |" for n, i, u, o in VANJSKI]
    out += [
        "",
        "## Pretrage lokalnih skupova",
        "",
        "Stotine skupova općina i gradova u različitim formatima. "
        "Za demo ih ne obrađujemo sve, nego samo po potrebi.",
        "",
    ]
    out += [f"- [{n}]({u})" for n, u in PRETRAGE]
    out += [
        "",
        "## Što nije u katalogu",
        "",
        "- EU sredstva 2021.–2027. i NPOO: izvor tek treba pronaći (issue #15).",
        "",
    ]

    IZLAZ.parent.mkdir(parents=True, exist_ok=True)
    IZLAZ.write_text("\n".join(out), encoding="utf-8")
    print(f"Spremljeno: {IZLAZ.relative_to(KORIJEN)} (skupova: {len(redovi)})")


if __name__ == "__main__":
    main()
