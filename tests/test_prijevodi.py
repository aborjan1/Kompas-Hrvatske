"""Engleski tekstovi za sučelje (pipeline/prijevodi.py)."""

import pytest
from pokazatelji import POKAZATELJI, TEME
from prijevodi import POKAZATELJI as EN
from prijevodi import TEME as TEME_EN
from prijevodi import godina_en, napomena_poziva_en


@pytest.mark.parametrize(
    ("hr", "en"),
    [
        ("2025", "2025"),
        ("2019.–2023.", "2019–2023"),
        ("2021.→2025.", "2021→2025"),
        ("sredina 2025.", "mid-2025"),
        ("stanje 31.05.2023", "as of 31 May 2023"),
        ("stanje 30.9.2026", "as of 30 Sep 2026"),
        ("IX. 2026.", "Sep 2026"),
        ("XII. 2026.", "Dec 2026"),
        ("31. siječnja 2022", "31 Jan 2022"),
        ("2026-09", "2026-09"),
        (None, None),
    ],
)
def test_godina_en(hr, en):
    assert godina_en(hr) == en


def test_napomena_poziva():
    assert napomena_poziva_en(None) is None
    assert napomena_poziva_en(
        "Samo za gradove i općine iz obuhvata urbane aglomeracije Osijek."
    ) == ("Only for cities and municipalities within the Osijek urban agglomeration.")
    with pytest.raises(SystemExit):
        napomena_poziva_en("Nešto novo.")


def test_svaki_pokazatelj_ima_prijevod():
    assert set(TEME_EN) == set(TEME)
    for pid, p in POKAZATELJI.items():
        assert pid in EN, f"{pid}: nema engleskog naziva"
        assert EN[pid]["naziv"] and EN[pid]["objasnjenje"], pid
        if p.get("napomena"):
            assert EN[pid].get("napomena"), f"{pid}: nema engleske napomene"
        if p.get("objasnjenje_zupanija"):
            assert EN[pid].get("objasnjenje_zupanija"), f"{pid}: nema objašnjenja za županiju"
