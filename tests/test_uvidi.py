"""„Što je neobično ovdje” (pipeline/uvidi.py) na izmišljenim podacima."""

import pytest
from uvidi import PRAG, izracunaj, provjeri


def podrucje(tip, ulaganja, udio_pomoci, dohodak=8000.0):
    return {
        "tip": tip,
        "pokazatelji": {"udio_pomoci_u_prihodima": udio_pomoci},
        "po_stanovniku": {"lokalna_ulaganja": ulaganja, "neto_dohodak": dohodak},
    }


@pytest.fixture
def jls():
    # 30 sličnih općina oko 400 EUR ulaganja po stanovniku i 40 % pomoći
    d = {f"{i:05d}": podrucje("mali", 360 + 3 * i, 38 + i % 5, 7900 + 10 * i) for i in range(30)}
    d["99901"] = podrucje("mali", 4000.0, 40.0)  # deset puta više ulaganja
    d["99902"] = podrucje("mali", 40.0, 41.0)  # deset puta manje
    d["99903"] = podrucje("mali", 420.0, 75.0)  # udio pomoći znatno veći
    return d


def test_odstupanja_i_smjer(jls):
    r = izracunaj(jls)["podrucja"]
    vise = {u["kljuc"]: u for u in r["99901"]}
    assert vise["lokalna_ulaganja"]["smjer"] == "vise"
    assert vise["lokalna_ulaganja"]["z"] >= PRAG
    assert vise["lokalna_ulaganja"]["po_stanovniku"] is True
    assert r["99902"][0]["kljuc"] == "lokalna_ulaganja"
    assert r["99902"][0]["smjer"] == "manje"
    assert r["99903"][0]["kljuc"] == "udio_pomoci_u_prihodima"
    assert r["99903"][0]["slicni"] == pytest.approx(40, abs=2)


def test_obicni_nemaju_uvida_i_najvise_tri(jls):
    r = izracunaj(jls)["podrucja"]
    assert r["00015"] == []
    assert all(len(u) <= 3 for u in r.values())
    # najveće odstupanje prvo
    for u in r.values():
        assert [abs(x["z"]) for x in u] == sorted((abs(x["z"]) for x in u), reverse=True)


def test_mali_tip_i_nule_preskacu(jls):
    jls["88801"] = podrucje("rijetki", 9000.0, 90.0)  # tip s jednim članom: nema usporedbe
    jls["99904"] = podrucje("mali", 0.0, 40.0)  # nula na log ljestvici se preskače
    r = izracunaj(jls)["podrucja"]
    assert r["88801"] == []
    assert all(u["kljuc"] != "lokalna_ulaganja" for u in r["99904"])


def test_provjeri_broj(jls):
    r = izracunaj(jls)
    with pytest.raises(SystemExit):
        provjeri(r, len(jls) + 1)
