"""Preuzimanje skupova podataka s data.gov.hr.

Popis skupova je u data/sources.csv (stupac `aktivno` = da). Za svaki skup skripta:
  1. pita CKAN API portala za opis skupa (package_show),
  2. sprema opis u data/raw/<id>/_metadata.json,
  3. preuzima sve datoteke podržanih formata u data/raw/<id>/,
  4. u sources.csv upisuje izdavatelja, licencu i datum preuzimanja.

Svaki pokušaj zapisuje se u data/raw/_dnevnik.csv.

Primjeri (iz korijena repozitorija, s uključenim .venv):
    python pipeline/download.py                      # svi aktivni skupovi
    python pipeline/download.py --samo dzs-bdp       # jedan skup
    python pipeline/download.py --samo dzs-bdp,dzs-place --ponovno
    python pipeline/download.py --popis              # samo ispiše što bi preuzeo
    python pipeline/download.py --faza 1,2,3         # samo kostur, Država i Županija

Faze (stupac `faza`): 1 Kostur, 2 Država, 3 Županija, 4 Grad, 5 Zagreb, 6 Rijeka.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

KORIJEN = Path(__file__).resolve().parent.parent
SOURCES = KORIJEN / "data" / "sources.csv"
RAW = KORIJEN / "data" / "raw"
DNEVNIK = RAW / "_dnevnik.csv"
API = "https://data.gov.hr/ckan/api/3/action"

# Formati koje preuzimamo. Ostalo (HTML stranice, WMS servisi, API poveznice) se preskače.
FORMATI = {"csv", "tsv", "txt", "xlsx", "xls", "ods", "json", "geojson", "xml", "gml", "zip"}


def napravi_sesiju() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "KompasHrvatske-datathon/1.0 (+github)"
    ponovi = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
    )
    s.mount("https://", HTTPAdapter(max_retries=ponovi))
    s.mount("http://", HTTPAdapter(max_retries=ponovi))
    return s


def ucitaj_izvore() -> tuple[list[str], list[dict]]:
    # utf-8-sig: datoteka se može otvoriti i spremiti u Excelu bez kvarenja kvačica
    with SOURCES.open(encoding="utf-8-sig", newline="") as f:
        citac = csv.DictReader(f)
        return list(citac.fieldnames or []), list(citac)


def spremi_izvore(stupci: list[str], redovi: list[dict]) -> bool:
    """Spremi sources.csv. Vraća False ako je datoteka zaključana (npr. otvorena u Excelu).

    Prvo piše u privremenu datoteku, pa je zamijeni: ako skripta pukne, sources.csv ostaje
    cijel. Na Windowsu zamjena ne uspije dok je datoteku otvorio drugi program, pa skripta
    pokuša nekoliko puta i onda samo upozori, umjesto da prekine preuzimanje.
    """
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", dir=SOURCES.parent, delete=False, suffix=".tmp"
    ) as f:
        pisac = csv.DictWriter(f, fieldnames=stupci)
        pisac.writeheader()
        pisac.writerows(redovi)
    privremena = Path(f.name)
    try:
        for pokusaj in range(5):
            try:
                privremena.replace(SOURCES)
                return True
            except PermissionError:
                time.sleep(0.5 * (pokusaj + 1))
        return False
    finally:
        privremena.unlink(missing_ok=True)


def zapisi_dnevnik(**zapis) -> None:
    novi = not DNEVNIK.exists()
    DNEVNIK.parent.mkdir(parents=True, exist_ok=True)
    stupci = ["vrijeme", "id", "resurs", "format", "status", "velicina_mb", "poruka", "url"]
    with DNEVNIK.open("a", encoding="utf-8", newline="") as f:
        pisac = csv.DictWriter(f, fieldnames=stupci)
        if novi:
            pisac.writeheader()
        if zapis.get("poruka"):
            zapis["poruka"] = str(zapis["poruka"])[:200]
        pisac.writerow({"vrijeme": datetime.now().isoformat(timespec="seconds"), **zapis})


def ime_datoteke(resurs: dict, fmt: str, zauzeta: set[str]) -> str:
    """Sigurno ime datoteke za Windows: bez kvačica, razmaka i posebnih znakova."""
    url_ime = unquote(Path(urlparse(resurs.get("url", "")).path).name)
    osnova = Path(url_ime).stem or resurs.get("name") or resurs.get("id", "datoteka")
    zamjene = str.maketrans("čćžšđČĆŽŠĐ", "cczsdCCZSD")
    osnova = re.sub(r"[^A-Za-z0-9._-]+", "_", osnova.translate(zamjene)).strip("._")[:80]
    ime = f"{osnova or 'datoteka'}.{fmt}"
    broj = 2
    while ime.lower() in zauzeta:
        ime = f"{osnova}_{broj}.{fmt}"
        broj += 1
    zauzeta.add(ime.lower())
    return ime


def format_resursa(resurs: dict) -> str:
    fmt = (resurs.get("format") or "").strip().lower().lstrip(".")
    if fmt not in FORMATI:
        nastavak = Path(urlparse(resurs.get("url", "")).path).suffix.lower().lstrip(".")
        if nastavak in FORMATI:
            fmt = nastavak
    return fmt


def preuzmi_datoteku(sesija, url: str, cilj: Path, max_mb: float) -> float:
    """Preuzme datoteku u dijelovima. Vraća veličinu u MB. Prekida ako prijeđe max_mb."""
    privremena = cilj.with_suffix(cilj.suffix + ".part")
    granica = max_mb * 1024 * 1024
    ukupno = 0
    try:
        with sesija.get(url, stream=True, timeout=(15, 180)) as r:
            r.raise_for_status()
            with privremena.open("wb") as f:
                for dio in r.iter_content(chunk_size=1024 * 256):
                    ukupno += len(dio)
                    if ukupno > granica:
                        raise ValueError(f"veće od {max_mb:.0f} MB (povećaj --max-mb)")
                    f.write(dio)
        privremena.replace(cilj)
    finally:
        privremena.unlink(missing_ok=True)
    return ukupno / 1024 / 1024


def potrazi_skup(sesija, api: str, naziv: str) -> dict | None:
    """Ako je skup na portalu dobio novu adresu, pronađi ga po nazivu (package_search)."""
    r = sesija.get(
        f"{api}/package_search", params={"q": f'title:"{naziv}"', "rows": 10}, timeout=(15, 60)
    )
    r.raise_for_status()
    rezultati = r.json().get("result", {}).get("results", [])
    tocno = [p for p in rezultati if p.get("title", "").strip().lower() == naziv.strip().lower()]
    return (tocno or rezultati or [None])[0]


def je_html(put: Path) -> bool:
    """Neki izvori umjesto datoteke vrate web stranicu (npr. istekla domena)."""
    with put.open("rb") as f:
        pocetak = f.read(512).lstrip().lower()
    return pocetak.startswith((b"<!doctype html", b"<html"))


def obradi_skup(sesija, red: dict, api: str, max_mb: float, ponovno: bool) -> bool:
    sid, slug = red["id"], red["slug"]
    print(f"\n[{sid}]")
    try:
        r = sesija.get(f"{api}/package_show", params={"id": slug}, timeout=(15, 60))
        if r.status_code == 404:
            paket = potrazi_skup(sesija, api, red["naziv"])
            if paket is None:
                raise LookupError("skup nije pronađen ni po adresi ni po nazivu")
            print(f"  skup je premješten; nova adresa: {paket['name']}")
            red["slug"] = paket["name"]
            red["poveznica"] = f"https://data.gov.hr/ckan/dataset/{paket['name']}"
        else:
            r.raise_for_status()
            odgovor = r.json()
            if not odgovor.get("success"):
                raise LookupError(f"API je vratio grešku: {odgovor.get('error')}")
            paket = odgovor["result"]
    except (requests.RequestException, LookupError, ValueError) as e:
        print(f"  GREŠKA: {e}")
        zapisi_dnevnik(id=sid, status="greska", poruka=str(e), url=slug)
        return False

    mapa = RAW / sid
    mapa.mkdir(parents=True, exist_ok=True)
    (mapa / "_metadata.json").write_text(
        json.dumps(paket, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Podaci iz portala imaju prednost pred onim što je ručno upisano.
    red["naziv"] = paket.get("title") or red["naziv"]
    red["izdavatelj"] = (paket.get("organization") or {}).get("title") or red["izdavatelj"]
    red["licenca"] = paket.get("license_title") or paket.get("license_id") or red["licenca"]

    resursi = paket.get("resources", [])
    zauzeta: set[str] = set()
    preuzeto = preskoceno = greske = 0
    for resurs in resursi:
        fmt = format_resursa(resurs)
        naziv = resurs.get("name") or resurs.get("id", "")
        url = resurs.get("url", "")
        if fmt not in FORMATI or not url:
            preskoceno += 1
            print(f"  preskačem  [{resurs.get('format') or '?'}] {naziv}")
            zapisi_dnevnik(
                id=sid,
                resurs=naziv,
                format=resurs.get("format"),
                status="preskoceno",
                poruka="nepodržan format",
                url=url,
            )
            continue

        cilj = mapa / ime_datoteke(resurs, fmt, zauzeta)
        if cilj.exists() and not ponovno:
            print(f"  postoji    {cilj.name}")
            zapisi_dnevnik(id=sid, resurs=naziv, format=fmt, status="postoji", url=url)
            preuzeto += 1
            continue
        try:
            mb = preuzmi_datoteku(sesija, url, cilj, max_mb)
            if fmt not in ("xml",) and je_html(cilj):
                cilj.unlink()
                raise ValueError("izvor je vratio web stranicu umjesto podataka")
            preuzeto += 1
            print(f"  preuzeto   {cilj.name} ({mb:.1f} MB)")
            zapisi_dnevnik(
                id=sid,
                resurs=naziv,
                format=fmt,
                status="preuzeto",
                velicina_mb=f"{mb:.2f}",
                url=url,
            )
        except (requests.RequestException, ValueError, OSError) as e:
            greske += 1
            print(f"  GREŠKA     {cilj.name}: {e}")
            zapisi_dnevnik(
                id=sid, resurs=naziv, format=fmt, status="greska", poruka=str(e), url=url
            )

    if preuzeto:
        red["datum_preuzimanja"] = date.today().isoformat()
    print(f"  ukupno: {preuzeto} preuzeto, {preskoceno} preskočeno, {greske} grešaka")
    return preuzeto > 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # kvačice u PowerShellu
    p = argparse.ArgumentParser(description="Preuzimanje skupova podataka s data.gov.hr")
    p.add_argument("--samo", help="id-jevi skupova odvojeni zarezom (stupac `id`)")
    p.add_argument("--ponovno", action="store_true", help="preuzmi i ono što već postoji")
    p.add_argument("--max-mb", type=float, default=300, help="najveća veličina datoteke")
    p.add_argument("--popis", action="store_true", help="samo ispiši skupove, ne preuzimaj")
    p.add_argument("--api", default=API, help="adresa CKAN API-ja")
    p.add_argument("--faza", help="brojevi faza odvojeni zarezom, npr. 1,2,3")
    a = p.parse_args()

    stupci, redovi = ucitaj_izvore()
    odabrani = [r for r in redovi if r.get("slug") and r.get("aktivno", "da").lower() == "da"]
    if a.faza:
        faze = {f.strip() for f in a.faza.split(",")}
        odabrani = [r for r in odabrani if r.get("faza", "").split(" ")[0] in faze]
    if a.samo:
        trazeni = {s.strip() for s in a.samo.split(",")}
        nepoznati = trazeni - {r["id"] for r in redovi}
        if nepoznati:
            print(f"Nepoznati id u --samo: {', '.join(sorted(nepoznati))}")
            return 2
        odabrani = [r for r in redovi if r["id"] in trazeni and r.get("slug")]

    if a.popis:
        for r in odabrani:
            print(f"{r.get('faza', ''):12} {r['id']:28} {r['naziv']}")
        print(f"\n{len(odabrani)} skupova")
        return 0

    print(f"Preuzimam {len(odabrani)} skupova u {RAW.relative_to(KORIJEN)}")
    sesija = napravi_sesiju()
    neuspjeli = []
    upozoren = False
    for red in odabrani:
        if not obradi_skup(sesija, red, a.api.rstrip("/"), a.max_mb, a.ponovno):
            neuspjeli.append(red["id"])
        # nakon svakog skupa, da se ništa ne izgubi
        if not spremi_izvore(stupci, redovi) and not upozoren:
            print("  UPOZORENJE: sources.csv je otvoren u drugom programu. Zatvori ga;")
            print("  preuzimanje se nastavlja, a datoteka se sprema čim se oslobodi.")
            upozoren = True

    print(f"\nGotovo: {len(odabrani) - len(neuspjeli)} od {len(odabrani)} skupova.")
    if not spremi_izvore(stupci, redovi):
        rezerva = SOURCES.with_name("sources.novi.csv")
        with rezerva.open("w", encoding="utf-8", newline="") as f:
            pisac = csv.DictWriter(f, fieldnames=stupci)
            pisac.writeheader()
            pisac.writerows(redovi)
        print(f"sources.csv je i dalje zaključan. Promjene su u {rezerva.relative_to(KORIJEN)}:")
        print("zatvori sources.csv, obriši ga i preimenuj sources.novi.csv u sources.csv.")
    if neuspjeli:
        print(f"Bez ijedne preuzete datoteke: {', '.join(neuspjeli)}")
        print(f"Detalji su u {DNEVNIK.relative_to(KORIJEN)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
