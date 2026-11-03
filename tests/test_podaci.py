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
        assert p.get("objasnjenje"), f"{pid}: nema objašnjenja za korisnika"


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


def test_nizovi(meta):
    n = ucitaj("nizovi.json")
    jls = ucitaj("jls.json")["podrucja"]
    zupanije = [f"{i:02d}" for i in range(1, 22)]
    for sid, s in n["serije"].items():
        assert s["tema"] in meta["teme"], sid
        assert s["izvor"] in meta["izvori"], f"{sid}: izvor {s['izvor']} nije u meta.izvori"
        assert s["godine"] == sorted(s["godine"]) and len(s["godine"]) >= 3, sid
        for sifra in ["HR", *zupanije]:
            assert len(n["podrucja"][sifra][sid]) == len(s["godine"]), f"{sid} {sifra}"
    for sifra, nizovi in n["podrucja"].items():
        razina = "drzava" if sifra == "HR" else "zupanija" if len(sifra) == 2 else "jls"
        assert razina != "jls" or sifra in jls, f"nepoznata šifra {sifra}"
        for sid, vrijednosti in nizovi.items():
            assert razina in n["serije"][sid]["razine"], f"{sid} ne postoji za {razina}"
            assert len(vrijednosti) == len(n["serije"][sid]["godine"]), f"{sid} {sifra}"


def test_nabava_i_eu_pozivi(meta):
    jls = ucitaj("jls.json")["podrucja"]
    n = ucitaj("nabava.json")["podrucja"]
    assert set(jls) <= set(n) and "HR" in n, "nabava.json mora imati sve JLS i državu"
    for sifra, z in n.items():
        for d in z["dobavljaci"]:
            assert d["naziv"] and d["iznos"] > 0, sifra
            assert all(s in jls for s in d["drugi"]), f"{sifra}: nepostojeća veza"
    e = ucitaj("eu-pozivi.json")
    assert e["pozivi"], "nema EU poziva za lokalnu samoupravu"
    for p in e["pozivi"]:
        assert p["jls"] in (None, "prijavitelj", "partner"), p["id"]
        assert p["zupanija"] in (None, "prijavitelj", "partner"), p["id"]
        assert p["jls"] or p["zupanija"] or p["imenovani"], p["id"]
        assert all(s in jls for s in p["imenovani"]), p["id"]
        assert p["zupanije"] is None or all(re.fullmatch(r"\d\d", z) for z in p["zupanije"])


def test_engleski_tekstovi(meta):
    en = ucitaj("en.json")
    assert set(en["pokazatelji"]) == set(meta["pokazatelji"]), "en.json ne prati meta.json"
    for pid, p in en["pokazatelji"].items():
        assert p["naziv"] and p["objasnjenje"], pid
        assert not re.search(r"[čćžšđ]", p["objasnjenje"].lower()), f"{pid}: hrvatski tekst?"
    assert set(en["teme"]) == set(meta["teme"])
    assert set(en["tipologija"]["tipovi"]) == set(meta["tipologija"]["tipovi"])
    assert len(en["zupanije"]) == 21
    assert set(en["serije"]) == set(ucitaj("nizovi.json")["serije"])
    assert set(en["eu_pozivi"]["pozivi"]) == {p["id"] for p in ucitaj("eu-pozivi.json")["pozivi"]}


def test_tipologija(meta):
    j = ucitaj("jls.json")["podrucja"]
    tipovi = meta["tipologija"]["tipovi"]
    for s, v in j.items():
        assert v["tip"] in tipovi, f"{s}: nepoznat tip {v['tip']}"
        assert len(v["slicni_profil"]) == 5 and s not in v["slicni_profil"]
        assert all(o in j for o in v["slicni_profil"]), f"{s}: nepostojeće slično područje"
    assert sum(t["broj"] for t in tipovi.values()) == len(j)
    for t_id, t in tipovi.items():
        assert t["broj"] == sum(v["tip"] == t_id for v in j.values()), t_id


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
    zbirni = {"hbor-esif", "eu-2021-2027", "eu-pozivi-2026", "natural-earth-admin1"}
    for sid in meta["izvori"]:
        assert sid in ids or sid in zbirni, f"izvor {sid} nije u sources.csv"
