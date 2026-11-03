"""Tipologija gradova i općina strojnim učenjem (k-means).

Svih 556 gradova i općina grupira se prema pet obilježja koja zajedno opisuju kakva je
sredina: veličina, dohodak stanovnika, ovisnost proračuna o pomoćima, prihodi proračuna po
stanovniku i prosječna dob. Rezultat su tipovi poput „Općine nižeg dohotka, ovisne o
pomoćima” i, za svaku jedinicu, pet najsličnijih po cijelom profilu (ne samo po broju
stanovnika).

Zašto ovih pet: postoje za sve gradove i općine i stabilni su iz godine u godinu. EU sredstva
i ulaganja ne ulaze u grupiranje jer jedan veliki projekt preokrene sliku jedne godine;
prikazuju se uz tip kao opis.

Metoda:
  1. obilježja: log(stanovništvo), log(neto dohodak po stanovniku), udio pomoći u prihodima
     (%), log(prihodi proračuna po stanovniku), prosječna dob; log ublažava velike razlike
     (Zagreb ima 767.000 stanovnika, najmanja općina 171);
  2. standardizacija (svako obilježje na prosjek 0 i standardnu devijaciju 1), da nijedno
     ne prevlada samo zbog svoje jedinice;
  3. k-means s K = 5 skupina (50 pokretanja, fiksno sjeme, pa je rezultat ponovljiv);
  4. nazivi tipova iz središta skupina prema pravilima u NAZIVI (najveći, najstariji, ...),
     pa ne ovise o redoslijedu skupina; ako pravila ne daju pet različitih tipova, obrada
     staje s porukom;
  5. slični po profilu: pet najbližih u istom standardiziranom prostoru.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

K = 5
SJEME = 42
SLICNIH = 5

OBILJEZJA = {
    "velicina": "broj stanovnika (log)",
    "dohodak": "neto dohodak po stanovniku (log)",
    "pomoci": "udio pomoći u prihodima proračuna",
    "prihodi": "prihodi proračuna po stanovniku (log)",
    "dob": "prosječna dob stanovnika",
}

# Tip → naziv i kratko objašnjenje. Redoslijed je redoslijed dodjele: svaki tip uzima
# skupinu koja najviše odgovara pravilu među još neimenovanima.
NAZIVI = {
    "sredista": (
        "Veći gradovi i središta",
        "Najveće sredine s višim dohotkom; proračun se većinom puni vlastitim prihodima.",
    ),
    "mali-stariji": (
        "Male općine sa starijim stanovništvom",
        "Vrlo male i najstarije sredine; zbog malo stanovnika proračun po stanovniku je visok, "
        "ali velik dio dolazi iz pomoći.",
    ),
    "samostalni": (
        "Financijski samostalne sredine",
        "Visok dohodak i visoki vlastiti prihodi proračuna, a pomoći su mali dio.",
    ),
    "ovisni": (
        "Sredine nižeg dohotka, ovisne o pomoćima",
        "Najniži dohodak stanovnika; više od polovice proračuna dolazi iz državnog proračuna, "
        "EU i drugih pomoći.",
    ),
    "prosjecni": (
        "Prosječni manji gradovi i općine",
        "Blizu hrvatskog prosjeka po dohotku i ovisnosti o pomoćima, s najnižim prihodima "
        "proračuna po stanovniku.",
    ),
}

OBALNE_ZUPANIJE = {"08", "09", "13", "15", "17", "18", "19"}


def obiljezja(jls: pd.DataFrame) -> pd.DataFrame:
    """Tablica obilježja po šifri; jedinice bez nekog od podataka se izostavljaju."""
    st = jls["stanovnistvo"]
    x = pd.DataFrame(
        {
            "velicina": np.log(st),
            "dohodak": np.log(jls["neto_dohodak"] / st),
            "pomoci": jls["udio_pomoci_u_prihodima"],
            "prihodi": np.log(jls["lokalni_prihodi"] / st),
            "dob": jls["prosjecna_starost"],
        }
    )
    x.index = jls["sifra"].to_numpy()
    return x.replace([np.inf, -np.inf], np.nan).dropna()


def _imenuj(sredista: pd.DataFrame) -> dict[int, str]:
    """Skupina → id tipa, iz standardiziranih središta skupina."""
    slobodne = set(sredista.index)
    oznake: dict[int, str] = {}

    def uzmi(tip: str, mjera: pd.Series) -> None:
        izbor = mjera.loc[sorted(slobodne)].idxmax()
        oznake[izbor] = tip
        slobodne.discard(izbor)

    s = sredista
    uzmi("sredista", s["velicina"])
    uzmi("mali-stariji", s["dob"] - s["velicina"])
    uzmi("samostalni", -s["pomoci"] + s["dohodak"])
    uzmi("ovisni", s["pomoci"] - s["dohodak"])
    uzmi("prosjecni", -s["prihodi"])
    if len(set(oznake.values())) != K or slobodne:
        raise SystemExit(f"Tipologija: pravila nisu dala {K} različitih tipova ({oznake}).")
    return oznake


def izracunaj(jls: pd.DataFrame) -> dict:
    """jls: tablica gradova i općina iz build.py (sifra, zupanija i pokazatelji).

    Vraća {"tip": {sifra: id}, "slicni": {sifra: [sifre]}, "meta": {...}} za izvoz."""
    x = obiljezja(jls)
    z = StandardScaler().fit_transform(x)
    km = KMeans(n_clusters=K, n_init=50, random_state=SJEME).fit(z)
    sredista = pd.DataFrame(km.cluster_centers_, columns=list(OBILJEZJA))
    oznake = _imenuj(sredista)
    tip = pd.Series([oznake[k] for k in km.labels_], index=x.index)

    # Pet najbližih po cijelom profilu (euklidska udaljenost u standardiziranom prostoru).
    udaljenosti = ((z[:, None, :] - z[None, :, :]) ** 2).sum(axis=2)
    np.fill_diagonal(udaljenosti, np.inf)
    sifre = x.index.to_numpy()
    slicni = {
        s: [str(sifre[j]) for j in np.argsort(udaljenosti[i])[:SLICNIH]]
        for i, s in enumerate(sifre)
    }

    zupanija = jls.set_index("sifra")["zupanija"]
    st = jls.set_index("sifra")["stanovnistvo"]
    tipovi = {}
    for t, (naziv, opis) in NAZIVI.items():
        clanovi = tip.index[tip == t]
        sirovo = x.loc[clanovi]
        obalnih = zupanija.loc[clanovi].isin(OBALNE_ZUPANIJE).mean() * 100
        tipovi[t] = {
            "naziv": naziv,
            "opis": opis,
            "broj": int(len(clanovi)),
            "tipicno": {
                "stanovnika": int(st.loc[clanovi].median()),
                "dohodak_po_stanovniku": int(round(np.exp(sirovo["dohodak"].median()), -1)),
                "udio_pomoci": round(float(sirovo["pomoci"].median()), 1),
                "prihodi_po_stanovniku": int(round(np.exp(sirovo["prihodi"].median()), -1)),
                "prosjecna_dob": round(float(sirovo["dob"].median()), 1),
                "udio_u_obalnim_zupanijama": round(float(obalnih)),
            },
        }

    meta = {
        "naziv": "Tip grada ili općine",
        "metoda": (
            f"Strojno učenje (k-means, {K} skupina) nad pet obilježja svih gradova i općina: "
            + ", ".join(OBILJEZJA.values())
            + ". Obilježja su standardizirana; slični po profilu su pet najbližih u istom "
            "prostoru."
        ),
        "obiljezja": OBILJEZJA,
        "silhouette": round(float(silhouette_score(z, km.labels_)), 3),
        "tipovi": tipovi,
    }
    return {"tip": tip.to_dict(), "slicni": slicni, "meta": meta}


def provjeri(r: dict, broj_jls: int) -> None:
    """Svaka jedinica ima tip i pet sličnih; nijedan tip nije prazan ni prevelik."""
    if len(r["tip"]) != broj_jls:
        raise SystemExit(f"Tipologija: tip ima {len(r['tip'])} od {broj_jls} gradova i općina.")
    for t, d in r["meta"]["tipovi"].items():
        if not 0.03 * broj_jls <= d["broj"] <= 0.6 * broj_jls:
            raise SystemExit(f"Tipologija: tip {t} ima {d['broj']} jedinica (neuobičajeno).")
