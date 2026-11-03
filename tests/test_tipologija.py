"""Tipologija gradova i općina: pet jasno različitih skupina dobiva pet pravih naziva."""

import numpy as np
import pandas as pd
import tipologija

# Profil svakog tipa: (stanovnika, dohodak po st., udio pomoći %, prihodi po st., dob)
PROFILI = {
    "sredista": (40000, 10000, 18, 1250, 44),
    "mali-stariji": (900, 7700, 50, 2000, 51),
    "samostalni": (2500, 9600, 11, 1950, 46.5),
    "ovisni": (2000, 6200, 60, 1100, 44.5),
    "prosjecni": (3400, 8000, 36, 1000, 44),
}


def _probni_jls(po_tipu: int = 20) -> tuple[pd.DataFrame, list[str]]:
    rng = np.random.default_rng(0)
    redovi, ocekivano = [], []
    for t, (st, doh, pom, pri, dob) in PROFILI.items():
        for _ in range(po_tipu):
            s = st * rng.uniform(0.9, 1.1)
            redovi.append(
                {
                    "sifra": f"{len(redovi):05d}",
                    "zupanija": "18" if t == "samostalni" else "05",
                    "stanovnistvo": round(s),
                    "neto_dohodak": doh * rng.uniform(0.97, 1.03) * s,
                    "udio_pomoci_u_prihodima": pom + rng.normal(0, 1),
                    "lokalni_prihodi": pri * rng.uniform(0.97, 1.03) * s,
                    "prosjecna_starost": dob + rng.normal(0, 0.3),
                }
            )
            ocekivano.append(t)
    return pd.DataFrame(redovi), ocekivano


def test_nazivi_tipova_prate_profil():
    jls, ocekivano = _probni_jls()
    r = tipologija.izracunaj(jls)
    assert [r["tip"][s] for s in jls["sifra"]] == ocekivano
    tipologija.provjeri(r, len(jls))
    assert r["meta"]["tipovi"]["samostalni"]["tipicno"]["udio_u_obalnim_zupanijama"] == 100


def test_slicni_po_profilu_su_iz_istog_tipa():
    jls, _ = _probni_jls()
    r = tipologija.izracunaj(jls)
    for s, slicni in r["slicni"].items():
        assert len(slicni) == tipologija.SLICNIH and s not in slicni
        assert {r["tip"][o] for o in slicni} == {r["tip"][s]}


def test_jedinice_bez_podatka_se_izostavljaju():
    jls, _ = _probni_jls()
    jls.loc[0, "lokalni_prihodi"] = np.nan
    r = tipologija.izracunaj(jls)
    assert "00000" not in r["tip"] and len(r["tip"]) == len(jls) - 1
