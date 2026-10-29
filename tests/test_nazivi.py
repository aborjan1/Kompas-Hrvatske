"""Usklađivanje naziva: greške pronađene u stvarnim izvorima ne smiju se vratiti."""

import pytest
from nazivi import kljuc, sifra_zupanije, uskladi


@pytest.mark.parametrize(
    "naziv, ocekivano",
    [
        ("Grad Zagreb", "ZAGREB"),
        ("OPĆINA BRINJE", "BRINJE"),
        # crtica i razmak su isto (Porezna uprava i šifrarnik pišu različito)
        ("Tar-Vabriga-Torre Abrega", "TAR VABRIGA TORRE ABREGA"),
        ("Tar-Vabriga – Torre-Abrega", "TAR VABRIGA TORRE ABREGA"),
        ("Sv. Ivan Zelina", "SV IVAN ZELINA"),
    ],
)
def test_kljuc(naziv, ocekivano):
    assert kljuc(naziv) == ocekivano


@pytest.mark.parametrize(
    "naziv, sifra",
    [
        ("Varažinska", "05"),  # tipfeler u izvoru
        ("BJELOVARSKO-BILOGORSKA ŽUAPNIJA", "07"),  # tipfeler u izvoru
        ("DUBROVAČKO NERETVANSKA", "19"),  # bez crtice
        ("I. Zagrebačka županija", "01"),  # redni broj ispred
        ("Grad Zagreb", "21"),
        ("Osječko-baranjska županija (100.00%)", "14"),
        ("RH", None),
    ],
)
def test_sifra_zupanije(naziv, sifra):
    assert sifra_zupanije(naziv) == sifra


def test_uskladi_skraceni_naziv():
    cilj = [kljuc("Kaštelir-Labinci – Castelliere-S. Domenica"), "ZAGREB", "BRINJE"]
    mapa = uskladi(["KAŠTELIR LABINCI CASTELLIERE S D", "ZAGREB"], cilj)
    assert mapa["KAŠTELIR LABINCI CASTELLIERE S D"] == cilj[0]
    assert mapa["ZAGREB"] == "ZAGREB"
