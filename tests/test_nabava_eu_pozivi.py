"""Javna nabava (naručitelji iz EOJN-a) i EU pozivi (uloga lokalne samouprave iz teksta plana)."""

import eu_pozivi
import nabava
import pandas as pd
import pytest

JLS = pd.DataFrame(
    [
        ("02917", "Novigrad-Cittanova", "grad", "18", "NOVIGRAD CITTANOVA"),
        ("05371", "Novigrad", "opcina", "13", "NOVIGRAD"),
        ("05355", "Otok", "grad", "16", "OTOK"),
        ("03140", "Otok", "opcina", "17", "OTOK"),
        ("05746", "Privlaka", "opcina", "13", "PRIVLAKA"),
        ("05835", "Privlaka", "opcina", "16", "PRIVLAKA"),
        ("04286", "Sveti Filip i Jakov", "opcina", "13", "SVETI FILIP I JAKOV"),
        ("05207", "Zadar", "grad", "13", "ZADAR"),
        ("04880", "Vinodolska općina", "opcina", "08", "VINODOLSKA OPĆINA"),
    ],
    columns=["sifra", "naziv", "vrsta", "zupanija", "kljuc"],
)


@pytest.mark.parametrize(
    "naziv, posta, sifra",
    [
        ("Grad Novigrad", "52466", "02917"),  # isti ključ postoji kao općina u Zadarskoj
        ("Općina Novigrad", "23312", "05371"),
        ("Grad Otok", "32252", "05355"),
        ("Općina Otok", "21238", "03140"),
        ("Općina Privlaka", "32251", "05835"),  # dvije općine istog imena: poštanski broj
        ("Općina Sv. Filip i Jakov", "23207", "04286"),
        ("GRAD ZADAR GRADSKO VIJEĆE", "23000", "05207"),
        ("VINODOLSKA OPĆINA", "51250", "04880"),
        ("Zadarska županija", "23000", "13"),
        ("Opća bolnica Zadar", "23000", None),  # ustanove se ne zbrajaju
        ("ZAVOD ZA HITNU MEDICINU ZADARSKE ŽUPANIJE", "23000", None),
    ],
)
def test_narucitelj(naziv, posta, sifra):
    assert nabava._Narucitelji(JLS).sifra(naziv, posta) == sifra


def test_iznos_u_eurima():
    p = {"contracts": [{"value": {"amount": 75345.0, "currency": "HRK"}}]}
    assert nabava._iznos(p) == pytest.approx(10000.0)
    assert nabava._iznos({"contracts": [{"value": {"amount": 5, "currency": "USD"}}]}) is None


@pytest.mark.parametrize(
    "tekst, jls, zup",
    [
        ("JLPRS", "prijavitelj", "prijavitelj"),
        ("Jedinice područne (regionalne) samouprave", None, "prijavitelj"),
        ("Osnivači osnovnih škola, ustanove koje obavljaju djelatnost", "prijavitelj", None),
        ("Prijavitelji: OCD-(udruge) Partneri: OCD, JLP(R)S, ustanove", "partner", "partner"),
        ("MSP-ovi", None, None),
        (
            "Prijavitelj: Ministarstvo zdravstva Partneri: Jedinice (lokalne)regionalne samouprave",
            None,
            "partner",
        ),
    ],
)
def test_uloga(tekst, jls, zup):
    assert eu_pozivi._uloga(tekst, eu_pozivi._JLS) == jls
    assert eu_pozivi._uloga(tekst, eu_pozivi._ZUP) == zup


def test_datum_i_podrucje():
    assert eu_pozivi._datum("2026-10-05 00:00:00") == ("2026-10-05", False)
    assert eu_pozivi._datum("listopad 2026.") == ("2026-10", True)
    assert eu_pozivi._datum("n/p") == (None, False)
    jed = eu_pozivi._Jedinice(JLS)
    assert eu_pozivi._podrucje("Republika Hrvatska", jed) == (None, [])
    assert eu_pozivi._podrucje("Jadranska Hrvatska", jed)[0] == [
        "08",
        "09",
        "13",
        "15",
        "17",
        "18",
        "19",
    ]
    assert eu_pozivi._podrucje("Gradovi - Zadar, Zadarska", jed) == (["13"], ["05207"])
