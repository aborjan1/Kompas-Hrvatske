"""Pretvaranje adresa u točke (adrese DGU-a)."""

import pandas as pd
import pytest
from adrese import geokodiraj, kljuc_ulice, posvojni, razdvoji_broj


@pytest.mark.parametrize(
    "adresa, dijelovi",
    [
        ("ILICA 0297", ("ILICA", "297", "")),
        ("ALEJA LIPA 0001/A", ("ALEJA LIPA", "1", "A")),
        ("ILICA 0001/1", ("ILICA", "1", "")),  # broj stana se zanemaruje
        ("TOMAŠIĆEVA 0006 DV", ("TOMAŠIĆEVA", "6", "")),  # ulaz iz dvorišta
        ("VATROGASNA 0000/BB", ("VATROGASNA", "", "")),  # bez broja
        ("VRBIK X. 0017", ("VRBIK X.", "17", "")),
    ],
)
def test_razdvoji_broj(adresa, dijelovi):
    assert razdvoji_broj(adresa) == dijelovi


def test_posvojni_oblik():
    assert posvojni("Barčića") == "BARČIĆEVA"
    assert posvojni("Heinzela") == "HEINZELOVA"
    assert posvojni("Slavenskoga") == "SLAVENSKOG"


def test_kljuc_ulice_ne_ovisi_o_redoslijedu_i_rijeci_ulica():
    assert kljuc_ulice("Ulica grada Vukovara") == kljuc_ulice("GRADA VUKOVARA")


def test_geokodiraj():
    adrese = pd.DataFrame(
        {
            "sifra": ["01333"] * 4,
            "ulica": ["Ulica Erazma Barčića", "Ulica Erazma Barčića", "Ilica", "Ilica"],
            "broj": ["8", "10", "1", "1"],
            "dodatak": ["", "", "", "A"],
            "naselje": ["Zagreb"] * 4,
            "posta": ["10000"] * 4,
            "lon": [15.97, 15.98, 15.90, 15.91],
            "lat": [45.80, 45.81, 45.80, 45.81],
        }
    )
    t = pd.DataFrame(
        {
            "ulica": ["BARČIĆEVA", "ILICA", "ILICA", "BARČIĆEVA", "NEPOSTOJEĆA"],
            "broj": ["8", "1", "1", "", "5"],
            "dodatak": ["", "A", "B", "", ""],
        }
    )
    g = geokodiraj(t, adrese, "01333")
    assert list(g["nacin"]) == ["tocno", "tocno", "bez dodatka", "ulica", None]
    assert (g.loc[0, "lon"], g.loc[0, "lat"]) == (15.97, 45.80)
    assert g.loc[1, "lon"] == 15.91  # Ilica 1A, ne Ilica 1
