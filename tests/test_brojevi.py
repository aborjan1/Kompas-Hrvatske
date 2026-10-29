"""Čitanje brojeva i iznosa iz hrvatskih tablica i tekstova."""

import gradovi
import pytest
from citaci import _lokacije, _najvise, broj


@pytest.mark.parametrize(
    "tekst, broj_",
    [
        ("1.234.567", 1234567.0),
        ("1.234,5", 1234.5),
        ("12,5", 12.5),
        ("2 900 000", 2900000.0),
        # Excel zapisuje decimale točkom: "0.216" nije 216 (greška pronađena u fazi 4)
        ("0.216", 0.216),
        ("1.333", 1.333),
        ("-", None),
        ("", None),
    ],
)
def test_broj(tekst, broj_):
    assert broj(tekst) == broj_


def test_najvise_iz_raspona():
    assert _najvise("0,60 do 3,7") == 3.7
    assert _najvise("1,00-3,00%") == 3.0


def test_lokacije_projekta_s_udjelima():
    assert _lokacije("Grad Zagreb (90.00%), Zadarska županija (10.00%)") == {
        "21": 0.9,
        "13": 0.1,
    }
    # izvor ponekad ne daje 100 %: iznos se dijeli razmjerno
    assert _lokacije("Grad Zagreb (50.00%)") == {"21": 1.0}
    assert _lokacije("") == {}


@pytest.mark.parametrize(
    "tekst, eur",
    [
        ("1.872.533,00 eura", 1872533.0),
        ("55.000 eura", 55000.0),
        ("1.865.065,60 kn", 247536.74),  # kune → euri po fiksnom tečaju
    ],
)
def test_iznos_iz_teksta(tekst, eur):
    assert gradovi._iznos_teksta(tekst) == eur
