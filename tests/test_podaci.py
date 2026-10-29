"""Ugovor s kartom i sučeljem: datoteke u web/public/data/ moraju imati oblik opisan u
docs/format-podataka.md. Ovaj test se pokreće na GitHubu kod svakog pull requesta, pa
promjena koja pokvari podatke (npr. probni podaci preko pravih) odmah dobije crveni ✗.
"""

import csv
import json
import re
from pathlib import Path

import pytest

KORIJEN = Path(__file__).resolve().parent.parent
PODACI = KORIJEN / "web" / "public" / "data"

pytestmark = pytest.mark.skipif(
    not (PODACI / "meta.json").exists(), reason="nema web/public/data – pokreni build.py"
)


def ucitaj(ime: str):
    return json.loads((PODACI / ime).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def meta():
    return ucitaj("meta.json")


def test_meta_osnovno(meta):
    assert meta["verzija_formata"] == 1
    assert meta["probni_podaci"] is False, "u web/public/data su probni podaci"
    assert meta["probne_granice"] is False, "granice nisu službene DGU granice"
    for pid, p in meta["pokazatelji"].items():
        assert p["tema"] in meta["teme"], pid
        assert p["izvor"] in meta["izvori"], f"{pid}: izvor {p['izvor']} nije u meta.izvori"
        assert set(p["razine"]) <= {"drzava", "zupanija", "jls"}, pid
        assert p["godina"], f"{pid}: nema godine (izvor nije pročitan?)"


def _provjeri_podrucja(podrucja: dict, razina: str, meta: dict):
    trazeni = [p for p, d in meta["pokazatelji"].items() if razina in d["razine"]]
    for sifra, z in podrucja.items():
        assert z["sifra"] == sifra
        for p in trazeni:
            assert p in z["pokazatelji"], f"{sifra}: nema pokazatelja {p}"
        for kljuc in z["rang"]:
            assert kljuc.removesuffix("_po_stanovniku") in meta["pokazatelji"], kljuc
        assert all(s in podrucja for s in z["slicni"]), f"{sifra}: nepostojeće slično područje"


def test_drzava(meta):
    d = ucitaj("drzava.json")
    assert d["sifra"] == "HR"
    assert d["pokazatelji"]["stanovnistvo"] == 3871833


def test_zupanije(meta):
    z = ucitaj("zupanije.json")["podrucja"]
    assert sorted(z) == [f"{i:02d}" for i in range(1, 22)]
    _provjeri_podrucja(z, "zupanija", meta)
    assert sum(v["pokazatelji"]["stanovnistvo"] for v in z.values()) == 3871833


def test_gradovi_i_opcine(meta):
    j = ucitaj("jls.json")["podrucja"]
    assert len(j) == 556
    assert all(re.fullmatch(r"\d{5}", s) for s in j), "šifre JLS moraju biti 5 znamenki"
    assert sum(v["vrsta"] == "grad" for v in j.values()) == 128
    assert all(re.fullmatch(r"\d\d", v["nadredeno"]) for v in j.values())
    _provjeri_podrucja(j, "jls", meta)
    assert sum(v["pokazatelji"]["stanovnistvo"] for v in j.values()) == 3871833


def test_granice_odgovaraju_brojkama():
    zg = ucitaj("zupanije.geojson")
    assert {f["properties"]["sifra"] for f in zg["features"]} == {f"{i:02d}" for i in range(1, 22)}
    jls = ucitaj("jls.json")["podrucja"]
    sifre = set()
    for z in range(1, 22):
        g = ucitaj(f"jls/{z:02d}.geojson")
        for f in g["features"]:
            assert f["properties"]["zupanija"] == f"{z:02d}"
            sifre.add(f["properties"]["sifra"])
    assert sifre == set(jls), "granice JLS i jls.json nemaju iste šifre"


def test_koordinate_u_hrvatskoj():
    for f in ucitaj("tocke/eu-projekti.geojson")["features"]:
        lon, lat = f["geometry"]["coordinates"]
        assert 13.2 <= lon <= 19.5 and 42.2 <= lat <= 46.6


def test_proracuni():
    p = ucitaj("proracuni.json")
    n = len(p["godine"])
    jls = ucitaj("jls.json")["podrucja"]
    assert set(jls) | {"HR"} | {f"{i:02d}" for i in range(1, 22)} == set(p["podrucja"])
    for sifra, v in p["podrucja"].items():
        assert len(v["prihodi"]) == len(v["rashodi"]) == len(v["ulaganja"]) == n, sifra
        assert set(v["funkcije"]) == set(p["funkcije"]), sifra


def test_gradovi_meta_i_datoteke():
    m = ucitaj("gradovi/meta.json")
    for grad, g in m["gradovi"].items():
        for datoteka in [*g["slojevi"].values(), *g["tablice"]]:
            assert (PODACI / "gradovi" / grad / datoteka).exists(), f"{grad}/{datoteka}"
        for z in (g.get("zgrade_3d") or {}).values():
            assert (PODACI / "gradovi" / grad / z["datoteka"]).exists()
    c = ucitaj("gradovi/zagreb/cetvrti.json")["podrucja"]
    assert len(c) == 17
    for z in c.values():
        assert set(m["pokazatelji_cetvrti"]) <= set(z["pokazatelji"])


def test_izvori_u_sources_csv(meta):
    with (KORIJEN / "data" / "sources.csv").open(encoding="utf-8-sig", newline="") as f:
        redovi = list(csv.DictReader(f))
    ids = [r["id"] for r in redovi]
    assert len(ids) == len(set(ids)), "dupli id u sources.csv"
    zbirni = {"hbor-esif", "eu-2021-2027", "natural-earth-admin1"}
    for sid in meta["izvori"]:
        assert sid in ids or sid in zbirni, f"izvor {sid} nije u sources.csv"
