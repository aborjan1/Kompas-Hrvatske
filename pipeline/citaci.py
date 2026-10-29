"""Čitači izvora: svaki pretvara jednu preuzetu datoteku u urednu tablicu.

Svaka funkcija vraća pandas DataFrame sa stupcem `zupanija` (šifra "01"–"21", ili "HR"
za cijelu državu) ili `kljuc` (naziv grada/općine, vidi nazivi.kljuc), i stupcem
`godina` kad izvor ima više razdoblja. Tablice DZS-a i Porezne uprave nisu "uredne":
imaju naslove, dvojezična zaglavlja i fusnote, pa svaki čitač zna gdje mu je što.

Ako se raspored u izvoru promijeni, čitač javi jasnu grešku umjesto da tiho vrati
krive brojke.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from nazivi import kljuc, sifra_zupanije

KORIJEN = Path(__file__).resolve().parent.parent
RAW = KORIJEN / "data" / "raw"


# --------------------------------------------------------------------------- pomoćno


def nadji(mapa: str, uzorak: str = "") -> Path:
    """Datoteka u data/raw/<mapa>/: točno ime, inače prva (abecedno) čije ime sadrži uzorak.

    Točno ime ima prednost jer uzorak može biti dio drugog imena, npr.
    "prazni-poslovni-prostori-2024.xlsx" je dio "ne-uvjetni-prazni-poslovni-prostori-2024.xlsx".
    """
    if uzorak and (RAW / mapa / uzorak).is_file():
        return RAW / mapa / uzorak
    # bez uzorka "**" bi bio rekurzivni glob koji vraća samo mape
    obrazac = f"*{uzorak}*" if uzorak else "*"
    pogodci = sorted(
        p for p in (RAW / mapa).glob(obrazac) if p.is_file() and not p.name.startswith("_")
    )
    if not pogodci:
        raise FileNotFoundError(f"data/raw/{mapa}/*{uzorak}* ne postoji – pokreni download.py")
    return pogodci[0]


def excel(put: Path, list_=0) -> pd.DataFrame:
    """Cijeli list kao tekst, bez zaglavlja; prazne ćelije su ""."""
    return pd.read_excel(put, sheet_name=list_, header=None, dtype=str, engine="calamine").fillna(
        ""
    )


def broj(v) -> float | None:
    """'1.234,5' / '1234.5' / '-' / '...' / '3)' → float ili None."""
    if v is None:
        return None
    s = str(v).strip().replace(" ", "").replace(" ", "")
    if s in ("", "-", "–", "...", "…", "x", "z", "nan"):
        return None
    # Hrvatski zapis s točkom za tisućice: "1.234.567" ili "1.234,5". Pazi: "0.216" i
    # "1.333" su decimalni brojevi (tako ih zapisuje Excel), ne tisućice.
    if re.fullmatch(r"-?[1-9]\d{0,2}(\.\d{3}){2,}(,\d+)?", s) or re.fullmatch(
        r"-?[1-9]\d{0,2}(\.\d{3})+,\d+", s
    ):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def red_s(t: pd.DataFrame, tekst: str, stupac: int = 0) -> int:
    """Indeks prvog retka čija ćelija u stupcu počinje zadanim tekstom."""
    for i, v in enumerate(t[stupac]):
        if str(v).strip().startswith(tekst):
            return i
    raise ValueError(f"Redak koji počinje s '{tekst}' nije pronađen – promijenio se izvor?")


def _godina(zaglavlje: str) -> str:
    m = re.search(r"(19|20)\d\d", zaglavlje)
    return m.group(0) if m else zaglavlje.strip()


# --------------------------------------------------------------------------- Popis 2021.


def popis_kontingenti() -> pd.DataFrame:
    """Popis 2021., tablica 6.: stanovništvo i dob za državu, županije i gradove/općine.

    Stupci: razina (drzava|zupanija|jls), zupanija, vrsta, naziv, kljuc, stanovnistvo,
    st_0_14, st_65_plus, prosjecna_starost, indeks_starenja.
    """
    t = excel(nadji("dzs-popis2021", "po_gradovima_opcinama"), "6.")
    zag = red_s(t, "Županija")
    if not t.iloc[zag, 7].startswith("Ukupno") or not t.iloc[zag, 18].startswith("Prosječna"):
        raise ValueError("Popis, tablica 6.: stupci nisu na očekivanim mjestima")
    t = t[t[5].str.strip() == "sv."]  # zbroj oba spola
    redovi = []
    for _, r in t.iterrows():
        zup, vrsta, naziv = r[0].strip(), r[1].strip(), r[4].strip()
        if zup == "Republika Hrvatska":
            razina, sif = "drzava", "HR"
        elif naziv == "":
            # Redak županije. U izvoru Varaždinska ima pogrešno upisano "Općina".
            razina, vrsta, sif = "zupanija", "", sifra_zupanije(zup)
        elif vrsta in ("Grad", "Općina"):
            razina, sif = "jls", sifra_zupanije(zup)
        else:
            continue  # gradske četvrti Zagreba
        redovi.append(
            {
                "razina": razina,
                "zupanija": sif,
                "vrsta": {"Grad": "grad", "Općina": "opcina"}.get(vrsta, ""),
                "naziv": naziv,
                "kljuc": kljuc(naziv) if naziv else "",
                "stanovnistvo": broj(r[7]),
                "st_0_14": broj(r[9]),
                "st_65_plus": broj(r[16]),
                "prosjecna_starost": broj(r[18]),
                "indeks_starenja": broj(r[19]),
            }
        )
    return pd.DataFrame(redovi)


def popis_povrsina() -> pd.DataFrame:
    """Zbirni pregledi, tablica 1.: površina županija (km²). Stupci: zupanija, povrsina_km2."""
    t = excel(nadji("dzs-popis2021", "zbirni_pregledi"), "1.")
    pocetak = red_s(t, "Republika Hrvatska")
    redovi = []
    for i in range(pocetak, pocetak + 22):
        naziv = t.iloc[i, 0]
        sif = "HR" if naziv.startswith("Republika") else sifra_zupanije(naziv)
        redovi.append({"zupanija": sif, "povrsina_km2": broj(t.iloc[i, 2])})
    return pd.DataFrame(redovi)


# --------------------------------------------------------------------------- Plaće i zaposlenost


def _tablica_zupanija(t: pd.DataFrame, prvi_red: int, stupci: dict[str, int]) -> pd.DataFrame:
    """Redovi Republika Hrvatska + 21 županija od prvi_red; vrijednosti iz zadanih stupaca."""
    redovi = []
    for i in range(prvi_red, len(t)):
        naziv = t.iloc[i, 0].strip()
        sif = "HR" if naziv.startswith("Republika") else sifra_zupanije(naziv)
        if sif is None:
            if redovi:
                break
            continue
        redovi.append({"zupanija": sif, **{k: broj(t.iloc[i, j]) for k, j in stupci.items()}})
    df = pd.DataFrame(redovi).drop_duplicates("zupanija")
    if len(df) != 22:
        raise ValueError(f"Očekivano 22 retka (RH + 21 županija), pronađeno {len(df)}")
    return df


def place_zupanije() -> tuple[pd.DataFrame, str]:
    """Prosječna mjesečna neto plaća po županijama (EUR), zadnja cijela godina.

    Od 2024. DZS plaće po županijama objavljuje iz JOPPD-a u listu 9.4.9.;
    uzimamo stupac "Ø <godina>." i redak "Ukupno" svake županije.
    """
    t = excel(nadji("dzs-place", "pregled-po-zupanijama"), "9.4.9. NKD 2025.")
    zag = red_s(t, "Županija")
    godisnji = [(j, v) for j, v in enumerate(t.iloc[zag]) if re.fullmatch(r"Ø\s*\d{4}\.?\s*", v)]
    if not godisnji:
        raise ValueError("9.4.9.: nema stupca s godišnjim prosjekom (Ø godina)")
    j, zaglavlje = godisnji[-1]
    t = t[t[2].str.strip() == "Ukupno"].reset_index(drop=True)
    return _tablica_zupanija(t, 0, {"prosjecna_neto_placa": j}), _godina(zaglavlje)


def zaposleni_zupanije(godina: str = "2024") -> tuple[pd.DataFrame, str]:
    """Ukupno zaposleni po županijama, stanje 31. ožujka (administrativni izvori).

    Namjerno 2024., a ne 2025.: u 2025. DZS je promijenio obradu i serija ima lom
    (npr. Grad Zagreb pada s 472.598 na 377.586, a Zagrebačka raste za 32 %).
    """
    t = excel(nadji("dzs-place", "pregled-po-zupanijama"), "9.4.8.")
    zag = red_s(t, "Županija")
    j = [j for j, v in enumerate(t.iloc[zag]) if v.strip().startswith(f"{godina}.")][0]
    return _tablica_zupanija(t, zag + 1, {"zaposleni": j}), godina


def nezaposlenost_zupanije() -> tuple[pd.DataFrame, str]:
    """Stopa registrirane nezaposlenosti po županijama (%), zadnji objavljeni mjesec."""
    t = excel(nadji("dzs-place", "pregled-po-zupanijama"), "9.4.14.")
    zag = red_s(t, "Županija")
    ukupno = [(j, v) for j, v in enumerate(t.iloc[zag]) if "ukupno" in v.lower()]
    j, zaglavlje = ukupno[-1]
    razdoblje = re.sub(r"\s+", " ", zaglavlje.split("ukupno")[0]).strip()  # "VI. 2026."
    return _tablica_zupanija(t, zag + 1, {"stopa_nezaposlenosti": j}), razdoblje


# --------------------------------------------------------------------------- Porezna uprava


def kupoprodaje_zupanije() -> tuple[pd.DataFrame, str]:
    """Broj kupoprodaja nekretnina po županijama, zadnja cijela godina."""
    t = excel(nadji("pu-kupoprodaje"), 0)
    zag = red_s(t, "NAZIV ŽUPANIJE")
    godine = [(j, v) for j, v in enumerate(t.iloc[zag]) if re.fullmatch(r"\d{4}\.?", v.strip())]
    j, god = godine[-1]  # zadnja CIJELA godina (tekuća ima "stanje na dan", pa ne prolazi)
    redovi = []
    for i in range(zag + 1, len(t)):
        naziv = t.iloc[i, 0].strip()
        if naziv.upper().startswith("UKUPNO"):
            redovi.append({"zupanija": "HR", "kupoprodaje_nekretnina": broj(t.iloc[i, j])})
            break
        sif = sifra_zupanije(naziv)
        if sif:
            redovi.append({"zupanija": sif, "kupoprodaje_nekretnina": broj(t.iloc[i, j])})
    df = pd.DataFrame(redovi)
    if len(df) != 22:
        raise ValueError(f"Kupoprodaje: očekivano 22 retka, pronađeno {len(df)}")
    return df, _godina(god)


def dohodak_jls() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Neto dohodak stanovništva i porez na dohodak po gradovima/općinama (EUR).

    Vraća (jls, zupanije_i_drzava, godina). JLS: zupanija, kljuc, naziv, posloprimci,
    dohodak, porez, neto. Uzima najnoviji list "<godina> EUR".
    """
    put = nadji("pu-porez-dohodak", "neto-dohodak")
    for p in sorted((RAW / "pu-porez-dohodak").glob("*neto-dohodak*")):
        if "2022_2025" in p.name or p.stat().st_size > put.stat().st_size:
            put = p
    listovi = pd.ExcelFile(put, engine="calamine").sheet_names
    eur = sorted((s for s in listovi if s.strip().endswith("EUR")), key=_godina)
    list_ = eur[-1]
    t = excel(put, list_)
    zag = red_s(t, "Naziv županije")
    t = t.iloc[zag + 1 :]
    t = t[t[2].str.strip().str.startswith("UKUPNO")]
    stupci = {"posloprimci": 3, "dohodak": 6, "porez": 7, "neto": 8}
    jls, vise = [], []
    for _, r in t.iterrows():
        vrsta = r[2].strip()
        vr = {k: broj(r[j]) for k, j in stupci.items()}
        if vrsta == "UKUPNO OPĆINA":
            jls.append(
                {
                    "zupanija": sifra_zupanije(r[0]),
                    "naziv": r[1].strip(),
                    "kljuc": kljuc(r[1]),
                    **vr,
                }
            )
        elif vrsta == "UKUPNO ŽUPANIJA":
            vise.append({"zupanija": sifra_zupanije(r[0]), **vr})
        elif vrsta == "UKUPNO REPUBLIKA":
            vise.append({"zupanija": "HR", **vr})
    jls = pd.DataFrame(jls)
    vise = pd.DataFrame(vise)
    # Grad Zagreb nema zaseban "UKUPNO ŽUPANIJA": županija = grad
    if "21" not in set(vise["zupanija"]):
        zg = jls[jls["zupanija"] == "21"].drop(columns=["naziv", "kljuc"])
        vise = pd.concat([vise, zg], ignore_index=True)
    return jls, vise, _godina(list_)


# --------------------------------------------------------------------------- EU i HBOR


def eu_opkk() -> tuple[pd.DataFrame, str]:
    """Operacije OP Konkurentnost i kohezija 2014.–2020. (zadnji presjek).

    Stupci: sifra_projekta, fond, korisnik, oib, naziv, pocetak, kraj, ukupno_eur,
    esif_eur, mjesto, zupanija, lon, lat, kategorija.
    """
    put = nadji("eu-opkk-2014-2020")
    listovi = pd.ExcelFile(put, engine="calamine").sheet_names
    presjek = [s for s in listovi if s.upper().startswith("CUT OFF")][-1]
    t = excel(put, presjek)
    zag = red_s(t, "MIS kod")
    if not t.iloc[zag, 13].strip().startswith("Županija") or "ESIF" not in t.iloc[zag, 9]:
        raise ValueError("OPKK: stupci nisu na očekivanim mjestima")
    t = t.iloc[zag + 3 :]  # preskoči engleska zaglavlja i redak sa slovima a, b, c…
    t = t[t[0].str.strip() != ""]
    df = pd.DataFrame(
        {
            "sifra_projekta": t[0].str.strip(),
            "fond": t[1].str.strip(),
            "korisnik": t[2].str.strip(),
            "oib": t[3].str.strip(),
            "naziv": t[4].str.strip(),
            "pocetak": t[6].str[:10],
            "kraj": t[7].str[:10],
            "ukupno_eur": t[8].map(broj),
            "esif_eur": t[9].map(broj),
            "mjesto": t[11].str.strip(),
            "zupanija": t[13].map(sifra_zupanije),
            "lon": t[14].map(broj),
            "lat": t[15].map(broj),
            "kategorija": t[17].str.strip(),
        }
    )
    return df.reset_index(drop=True), presjek.replace("CUT OFF", "").strip()


HBOR = {
    "hbor-rast-razvoj": "ESIF krediti za rast i razvoj",
    "hbor-energetska": "ESIF krediti za energetsku učinkovitost",
    "hbor-rasvjeta": "ESIF krediti za javnu rasvjetu",
    "hbor-ruralni-investicijski": "Investicijski krediti za ruralni razvoj",
    "hbor-ruralni-obrtna": "Obrtna sredstva za ruralni razvoj",
}


TECAJ_HRK = 7.53450  # fiksni tečaj konverzije kune u euro


def _datum_objave(ime: str) -> int | None:
    """Godina iz imena datoteke: '..._16.01.2023.xlsx' ili '..._14072021-1.xlsx'."""
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(20\d\d)", ime) or re.search(r"\d{4}(20\d\d)", ime)
    return int(m.groups()[-1]) if m else None


def hbor_krediti() -> pd.DataFrame:
    """Korisnici HBOR-ovih ESIF kredita, svi programi. Stupci: program, korisnik,
    zupanija, projekt, iznos_eur, objava.

    Tablice ne navode valutu. Tablice objavljene prije 2023. su u kunama (preračunavamo
    fiksnim tečajem), a one iz 2023. u eurima. Provjereno: (1) program ESIF krediti za
    javne zgrade propisuje kunske kredite od 100 tisuća do 60 milijuna kuna, a tablica iz
    2021. ima iznose od ~0,5 do 25,7 milijuna; (2) iznosi u tablicama iz 2023. imaju dugačke
    decimale i pomnoženi s 7,53450 daju okrugle kune (javna rasvjeta 73 %, obrtna sredstva
    97 %), dakle to su kune preračunate u eure.
    """
    svi = []
    for mapa, program in HBOR.items():
        try:
            put = nadji(mapa, ".xls")
        except FileNotFoundError:
            continue
        t = excel(put, 0)
        objava = _datum_objave(put.name)
        u_kunama = objava is not None and objava < 2023
        zag = next(
            i for i in range(len(t)) if "Županija ulaganja" in [v.strip() for v in t.iloc[i]]
        )
        zaglavlje = [v.strip() for v in t.iloc[zag]]
        cz = zaglavlje.index("Županija ulaganja")
        ci = next(j for j, v in enumerate(zaglavlje) if v.startswith("Iznos kredita"))
        ck = next(j for j, v in enumerate(zaglavlje) if v.startswith("Naziv korisnika"))
        cp = next((j for j, v in enumerate(zaglavlje) if v.startswith("Naziv projekta")), None)
        for i in range(zag + 1, len(t)):
            iznos = broj(t.iloc[i, ci])
            if iznos is None or not t.iloc[i, ck].strip():
                continue
            svi.append(
                {
                    "program": program,
                    "korisnik": t.iloc[i, ck].strip(),
                    "zupanija": sifra_zupanije(t.iloc[i, cz]),
                    "projekt": t.iloc[i, cp].strip() if cp is not None else "",
                    "iznos_eur": round(iznos / TECAJ_HRK if u_kunama else iznos, 2),
                    "objava": objava,
                }
            )
    return pd.DataFrame(svi)


# --------------------------------------------------------------------------- Država (HNB, DZS)


def hnb_inflacija() -> tuple[float, str]:
    """Godišnja inflacija (HIPC, %) za Hrvatsku, zadnji mjesec – iz Biltena HNB-a."""
    put = nadji("hnb-bilten")
    list_ = next(
        s for s in pd.ExcelFile(put, engine="calamine").sheet_names if s.startswith("Slika 5.4")
    )
    t = excel(put, list_)
    zag, cd = next(
        (i, j) for i in range(len(t)) for j in range(t.shape[1]) if t.iloc[i, j].strip() == "Date"
    )
    # stupci: Date | Datum | Hrvatska – HIPC ukupno | …
    if "HIPC ukupno" not in " ".join(t.iloc[: zag + 1, cd + 2]):
        raise ValueError("Bilten HNB-a: stupac 'Hrvatska – HIPC ukupno' nije na očekivanom mjestu")
    zadnji = None
    for i in range(zag + 1, len(t)):
        v = broj(t.iloc[i, cd + 2])
        if v is not None:
            zadnji = (v, t.iloc[i, cd][:7])
    if zadnji is None:
        raise ValueError("Bilten HNB-a: nema podataka o inflaciji")
    return zadnji


def hnb_dug() -> tuple[float, str]:
    """Ukupni dug opće države (mil. EUR), zadnji mjesec."""
    for p in sorted((RAW / "hnb-opca-drzava").glob("*.xlsx")):
        t = excel(p, 0)
        if "Dug opće države" not in " ".join(t.iloc[:3].values.ravel()):
            continue
        i = next(i for i in range(len(t)) if t.iloc[i, 1].strip().startswith("Ukupno dug"))
        datumi = t.iloc[5]
        j = max(j for j in range(len(datumi)) if broj(t.iloc[i, j]) is not None)
        return broj(t.iloc[i, j]), str(datumi.iloc[j])[:7]
    raise FileNotFoundError("Tablica I3 (dug opće države) nije pronađena")


def hnb_saldo() -> tuple[float, str]:
    """Neto pozajmljivanje (+) / zaduživanje (–) opće države (mil. EUR), zadnja godina."""
    for p in sorted((RAW / "hnb-opca-drzava").glob("*.xlsx")):
        t = excel(p, 0)
        if "Glavni makro-agregati" not in " ".join(t.iloc[:3].values.ravel()):
            continue
        god = next(
            i for i in range(10) if any(re.fullmatch(r"\d{4}\.", v.strip()) for v in t.iloc[i])
        )
        i = next(i for i in range(len(t)) if "Neto pozajmljivanje" in " ".join(t.iloc[i, :3]))
        j = max(j for j in range(t.shape[1]) if broj(t.iloc[i, j]) is not None)
        return broj(t.iloc[i, j]), _godina(t.iloc[god, j])
    raise FileNotFoundError("Tablica I2 (makro-agregati opće države) nije pronađena")


def _pdf_retci(stranica, tolerancija: float = 1.5) -> list[tuple[float, list[dict]]]:
    """Riječi PDF stranice grupirane u retke (po visini), slijeva nadesno."""
    rijeci = sorted(stranica.extract_words(x_tolerance=1.5), key=lambda w: (w["top"], w["x0"]))
    retci: list[tuple[float, list[dict]]] = []
    for w in rijeci:
        if retci and abs(retci[-1][0] - w["top"]) <= tolerancija:
            retci[-1][1].append(w)
        else:
            retci.append((w["top"], [w]))
    return [(t, sorted(ws, key=lambda w: w["x0"])) for t, ws in retci]


def _pdf_brojevi(rijeci: list[dict], razmak: float = 4.0) -> list[float]:
    """DZS piše tisućice s razmakom ("79 186"). Brojke bliže od `razmak` točaka su jedan
    broj; stupci tablice su međusobno udaljeni 20+ točaka."""
    brojevi, trenutni, kraj = [], "", None
    for w in rijeci:
        t = w["text"].replace(",", ".")
        if not re.fullmatch(r"-?[\d.]+", t):
            continue
        if trenutni and w["x0"] - kraj < razmak:
            trenutni += t
        else:
            if trenutni:
                brojevi.append(float(trenutni))
            trenutni = t
        kraj = w["x1"]
    if trenutni:
        brojevi.append(float(trenutni))
    return brojevi


def bdp_regije() -> tuple[pd.DataFrame, dict, str]:
    """DZS priopćenje „BDP za RH, HR NUTS 2 i županije” (PDF).

    Vraća (zupanije, drzava, godina):
      zupanije: zupanija, bdv_eur – bruto dodana vrijednost po županijama (tablica 2.)
      drzava:   bdp_eur, bdp_po_stanovniku – BDP Republike Hrvatske (tablica 1.)
    Po županijama DZS objavljuje bruto DODANU vrijednost, ne BDP: razlika su porezi na
    proizvode minus subvencije, koji se ne raspoređuju po županijama.
    """
    import logging

    import pdfplumber  # samo za ovaj izvor

    logging.getLogger("pdfminer").setLevel(logging.ERROR)  # bezopasna upozorenja o fontovima

    put = nadji("dzs-bdp-regije", ".pdf")
    with pdfplumber.open(put) as pdf:
        tekst = " ".join((s.extract_text() or "") for s in pdf.pages[:4])
        m = re.search(r"ŽUPANIJ[AE]\s+U\s+(\d{4})", tekst)
        if not m:
            raise ValueError("BDP PDF: godina u naslovu nije pronađena")
        godina = m.group(1)

        # Tablica 1.: redak "<godina>." ispod zaglavlja "BDP, mil. EUR"
        drzava = None
        for s in pdf.pages:
            retci = _pdf_retci(s)
            u_eur = False
            for _, ws in retci:
                red = " ".join(w["text"] for w in ws)
                if "mil. EUR" in red:
                    u_eur = True
                elif u_eur and ws[0]["text"] == f"{godina}.":
                    b = _pdf_brojevi(ws[1:])
                    if len(b) != 10:
                        raise ValueError(f"BDP PDF, tablica 1.: očekivano 10 brojeva, a ima {b}")
                    drzava = {"bdp_eur": b[0] * 1e6, "bdp_po_stanovniku": b[5]}
                    break
            if drzava:
                break
        if drzava is None:
            raise ValueError("BDP PDF: redak s BDP-om u eurima nije pronađen")

        # Tablica 2.: zadnji broj u retku je ukupna bruto dodana vrijednost.
        # Naziv županije može biti u dva retka ("Bjelovarsko-" / "bilogorska") iznad i
        # ispod brojeva, pa ga skupljamo iz lijevog stupca u pojasu ±7 točaka.
        s = next(s for s in pdf.pages if "BRUTO DODANA VRIJEDNOST" in (s.extract_text() or ""))
        rijeci = s.extract_words(x_tolerance=1.5)
        redovi = []
        for top, ws in _pdf_retci(s):
            b = _pdf_brojevi(ws)
            if len(b) < 11:
                continue
            ime = [
                w
                for w in rijeci
                if w["x1"] < 120
                and abs(w["top"] - top) <= 7
                and not re.fullmatch(r"[\d.,]+", w["text"])
            ]
            ime = sorted(ime, key=lambda w: (w["top"], w["x0"]))
            naziv = ""
            for w in ime:
                naziv += w["text"] if naziv.endswith("-") or not naziv else " " + w["text"]
            sif = "HR" if naziv.startswith("Republika") else sifra_zupanije(naziv)
            if sif:
                redovi.append({"zupanija": sif, "bdv_eur": b[-1] * 1e6})
    zup = pd.DataFrame(redovi).drop_duplicates("zupanija")
    if len(zup) != 22:
        raise ValueError(f"BDP PDF, tablica 2.: očekivano 22 retka (RH + 21), a ima {len(zup)}")
    return zup, drzava, godina


def aktivne_pravne_osobe() -> tuple[float, str]:
    """Broj aktivnih pravnih osoba u RH (Statistički registar), najnovije stanje."""
    t = excel(nadji("dzs-rps"), "11.1.1.")
    i = red_s(t, "STANJE")  # najnovije stanje je prvo u tablici
    stanje = t.iloc[i, 0].replace("STANJE", "").strip().rstrip(".").lower()
    for k in range(i + 1, i + 6):
        if t.iloc[k, 0].strip() == "aktivne":
            return broj(t.iloc[k, 2]), stanje
    raise ValueError("Registar: redak 'aktivne' nije pronađen")


# --------------------------------------------------------------------------- porezne stope (JLS)


def _najvise(v) -> float | None:
    """'0,60 do 3,7' / '1,00-3,00%' / '2' → najviši broj u zapisu (ili None)."""
    brojevi = [broj(x) for x in re.findall(r"\d+(?:[.,]\d+)?", str(v))]
    brojevi = [b for b in brojevi if b is not None]
    return max(brojevi) if brojevi else None


def porezne_stope_jls() -> tuple[pd.DataFrame, str]:
    """Porezne stope i iznosi po gradovima/općinama (Porezna uprava), spojeno po šifri.

    Šifra u tablicama Porezne uprave je službena šifra JLS bez vodećih nula (19 = "00019").
    Stupci: sifra, stopa_poreza_dohodak_niza, stopa_poreza_dohodak_visa (%),
    promjena_stope_niza (postotni bodovi u odnosu na prošlu godinu),
    porez_na_potrosnju (%), porez_na_nekretnine (EUR/m², najviši iznos ako je raspon).
    """
    mapa = "pu-porezne-stope-jls"
    t = pd.read_excel(nadji(mapa, "tablica-poreznih-stopa"), dtype=str, engine="calamine")
    stupci = [c.strip() for c in t.columns]
    if not (stupci[1].startswith("Šifra") and stupci[5].startswith("Niža stopa")):
        raise ValueError("Tablica poreznih stopa: stupci nisu na očekivanim mjestima")
    godina = _godina(stupci[5])
    df = pd.DataFrame(
        {
            "sifra": t.iloc[:, 1].str.strip().str.zfill(5),
            "stopa_poreza_dohodak_niza": t.iloc[:, 5].map(broj) * 100,
            "stopa_poreza_dohodak_visa": t.iloc[:, 6].map(broj) * 100,
        }
    )

    # Usporedba s prošlom godinom: isti redoslijed redaka, ali bez šifre – provjeri nazive
    u = pd.read_excel(nadji(mapa, "usporedba-2025"), dtype=str, engine="calamine")
    if (u.iloc[:, 1].str.strip().values != t.iloc[:, 2].str.strip().values).any():
        raise ValueError("Usporedba stopa: redoslijed gradova/općina se ne poklapa s tablicom")
    df["promjena_stope_niza"] = ((u.iloc[:, 2].map(broj) - u.iloc[:, 4].map(broj)) * 100).round(2)

    p = pd.read_excel(nadji(mapa, "potronju"), dtype=str, engine="calamine")
    stupac = next(j for j, c in enumerate(p.columns) if str(c).strip() == godina)
    df = df.merge(
        pd.DataFrame(
            {
                "sifra": p.iloc[:, 1].str.strip().str.zfill(5),
                "porez_na_potrosnju": p.iloc[:, stupac].map(_najvise),
            }
        ),
        on="sifra",
        how="left",
    )
    # Stope poreza na potrošnju su upisane kao udio (0.03), a rasponi kao postotak ("1,00-3,00%")
    df["porez_na_potrosnju"] = df["porez_na_potrosnju"].map(
        lambda v: v * 100 if v is not None and v < 1 else v
    )

    n = pd.read_excel(nadji(mapa, "nekretnine"), dtype=str, engine="calamine")
    stupac = next(j for j, c in enumerate(n.columns) if godina in str(c))
    df = df.merge(
        pd.DataFrame(
            {
                "sifra": n.iloc[:, 1].str.strip().str.zfill(5),
                "porez_na_nekretnine": n.iloc[:, stupac].map(_najvise),
            }
        ),
        on="sifra",
        how="left",
    )
    return df, godina


# --------------------------------------------------------------------------- EU 2021.–2027.

# Korisnici čiji projekti pokrivaju cijelu državu (ministarstva, državne agencije, HZZ…):
# sjedište im je u Zagrebu, ali novac nije "zagrebački", pa ulaze samo u zbroj države.
DRZAVNA_TIJELA = re.compile(
    r"^(Ministarstvo|Agencija|Hrvatsk[ai] (zavod|agencija|akademska)|HRVATSKI ZAVOD|"
    r"Ured |Akademija socijalne|Nacionalni centar|Središnji državni)",
    re.IGNORECASE,
)


def _presjek_lista(ime: str) -> tuple[int, int, int]:
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", ime)
    return (int(m[3]), int(m[2]), int(m[1])) if m else (0, 0, 0)


def _lokacije(v: str) -> dict[str, float]:
    """'Grad Zagreb (90.00%), Zadarska županija (10.00%)' → {'21': 0.9, '13': 0.1}."""
    out: dict[str, float] = {}
    for naziv, pct in re.findall(r"([^,(]+?)\s*\((\d+(?:[.,]\d+)?)\s*%\)", str(v)):
        z = sifra_zupanije(naziv)
        if z:
            out[z] = out.get(z, 0) + float(pct.replace(",", ".")) / 100
    # Kod ~30 malih projekata udjeli u izvoru ne daju 100 % (npr. samo "Grad Zagreb (50.00%)").
    # Iznos se tada dijeli razmjerno navedenim udjelima.
    ukupno = sum(out.values())
    return {z: u / ukupno for z, u in out.items()} if ukupno else {}


def _eu_pkk_itp(mapa: str, program: str) -> tuple[pd.DataFrame, str]:
    put = nadji(mapa, ".xlsx")
    listovi = pd.ExcelFile(put, engine="calamine").sheet_names
    zadnji = max(listovi, key=_presjek_lista)
    t = excel(put, zadnji)
    zag = red_s(t, "No.")
    t.columns = [" ".join(str(c).split()) for c in t.iloc[zag]]
    t = t.iloc[zag + 2 :]  # preskoči englesko zaglavlje
    t = t[t["MIS kod projekta"].str.strip() != ""]
    potrebni = [
        "Županija (lokacija projekta)",
        "EU sredstva (EUR)",
        "Općina/grad (sjedište korisnika)",
    ]
    if any(c not in t.columns for c in potrebni):
        raise ValueError(f"{program}: nema očekivanih stupaca {potrebni}")
    ukupno = next(c for c in t.columns if c.startswith("Ukupni prihvatljivi"))
    df = pd.DataFrame(
        {
            "program": program,
            "sifra_projekta": t["MIS kod projekta"].str.strip(),
            "korisnik": t["Naziv korisnika"].str.strip(),
            "naziv": t["Naziv operacije"].str.strip(),
            "fond": t["Fond"].str.strip(),
            "status": t.get("Status projekta", pd.Series("", index=t.index)).str.strip(),
            "pocetak": t["Datum početka ugovora"].str[:10],
            "kraj": t["Očekivani ili stvarni datum završetka operacije"].str[:10],
            "ukupno_eur": t[ukupno].map(broj),
            "eu_eur": t["EU sredstva (EUR)"].map(broj),
            "mjesto": t["Općina/grad (sjedište korisnika)"].str.strip(),
            "zupanija_sjedista": t["Županija (sjedište korisnika)"].map(sifra_zupanije),
            "lokacija": t["Županija (lokacija projekta)"].map(_lokacije),
        }
    )
    return df, re.search(r"\d{1,2}\.\d{1,2}\.\d{4}", zadnji).group(0)


def _eu_uljp() -> tuple[pd.DataFrame, str]:
    put = nadji("eu-uljp-2021-2027", ".xlsx")
    t = excel(put)
    t.columns = [" ".join(str(c).split()) for c in t.iloc[0]]
    t = t.iloc[2:]  # preskoči englesko zaglavlje
    t = t[t["ŠIFRA UGOVORA"].str.strip() != ""]
    korisnik = next(c for c in t.columns if c.startswith("NAZIV KORISNIKA"))
    zup = t["LOKACIJA KORISNIKA/ŽUPANIJA"].map(sifra_zupanije)
    drzavno = t[korisnik].str.strip().str.match(DRZAVNA_TIJELA)
    lokacija = [{} if (d or pd.isna(z)) else {z: 1.0} for d, z in zip(drzavno, zup, strict=True)]
    df = pd.DataFrame(
        {
            "program": "ULJP",
            "sifra_projekta": t["ŠIFRA UGOVORA"].str.strip(),
            "korisnik": t[korisnik].str.strip(),
            "naziv": t["NAZIV OPERACIJE"].str.strip(),
            "fond": t["FOND"].str.strip(),
            "status": t["STATUS PROVEDBE"].str.strip(),
            "pocetak": t["DATUM POČETKA OPERACIJE"].str[:10],
            "kraj": t[next(c for c in t.columns if c.startswith("OČEKIVANI DATUM"))].str[:10],
            "ukupno_eur": t["UKUPNI TROŠAK OPERACIJE (EUR)"].map(broj),
            "eu_eur": t["EU IZNOS SUFINANCIRANJA"].map(broj),
            "mjesto": t["LOKACIJA KORISNIKA"].str.strip(),
            "zupanija_sjedista": zup,
            "lokacija": lokacija,
        }
    )
    m = re.search(r"(\d{2})(\d{2})(\d{4})", put.name)
    presjek = f"{int(m[1])}.{int(m[2])}.{m[3]}" if m else ""
    return df, presjek


def eu_2021_2027() -> tuple[pd.DataFrame, str]:
    """Operacije PKK, ITP i ULJP 2021.–2027. u jednoj tablici.

    `lokacija` je {šifra županije: udio}: za PKK i ITP prema lokaciji projekta (projekt
    može biti u više županija), za ULJP prema sjedištu korisnika. Prazno = projekt na
    razini države (npr. fondovi, ministarstva, HZZ) – ulazi samo u zbroj države.
    """
    dijelovi, presjeci = [], set()
    for mapa, program in (("eu-pkk-2021-2027", "PKK"), ("eu-itp-2021-2027", "ITP")):
        df, p = _eu_pkk_itp(mapa, program)
        dijelovi.append(df)
        presjeci.add(p)
    df, p = _eu_uljp()
    dijelovi.append(df)
    presjeci.add(p)
    sve = pd.concat(dijelovi, ignore_index=True)
    presjek = " / ".join(sorted(presjeci))
    return sve, presjek


# --------------------------------------------------------------------------- proračuni JLP(R)S

# Stavke koje zadržavamo iz obrazaca PR-RAS (računski plan) i RAS-funkcijski (01–10)
STAVKE_PRORACUNA = {
    "6": "prihodi poslovanja",
    "7": "prihodi od prodaje nefinancijske imovine",
    "61": "porezi",
    "63": "pomoći",
    "3": "rashodi poslovanja",
    "31": "rashodi za zaposlene",
    "4": "rashodi za nabavu nefinancijske imovine",
    **{f"{i:02d}": f"funkcija {i:02d}" for i in range(1, 11)},
}


def lokalni_proracuni() -> tuple[pd.DataFrame, str]:
    """Ostvarenje proračuna svih gradova, općina i županija (Ministarstvo financija).

    ZIP sadrži jednu radnu knjigu po županiji (01–21) i jednu za cijelu državu (22). Svaki
    list je jedna jedinica ("GRAD GOSPIĆ", "OPĆINA BRINJE", "LIČKO-SENJSKA ŽUPANIJA") ili
    zbroj ("SVEUKUPNO OPĆ_GRAD_ŽUPANIJA"). Stupci "Ostvareno u <godina>".

    Vraća dugu tablicu: zupanija, razina (jls | zupanija | zupanija_ukupno | drzava),
    naziv, kljuc, godina, stavka, iznos.
    """
    import io
    import zipfile

    put = nadji("mfin-lokalni-proracuni", ".zip")
    retci = []
    with zipfile.ZipFile(put) as z:
        datoteke: dict[str, zipfile.ZipInfo] = {}
        for info in z.infolist():
            m = re.match(r"(\d\d)\s", info.filename)
            if not m:
                continue
            # kod dvije verzije iste županije prednost ima "ispravak"
            if m[1] not in datoteke or "ispravak" in info.filename.lower():
                datoteke[m[1]] = info
        for oznaka, info in sorted(datoteke.items()):
            knjiga = pd.ExcelFile(io.BytesIO(z.read(info)), engine="calamine")
            for list_ in knjiga.sheet_names:
                ime = " ".join(list_.split()).upper()
                if oznaka == "22":
                    if not ime.startswith("SVEUKUPNO OPĆ_GRAD_ŽUPANIJA"):
                        continue
                    zup, razina = "HR", "drzava"
                elif oznaka == "21":
                    zup, razina = "21", "jls"  # Grad Zagreb je i grad i županija
                elif ime.startswith("SVEUKUPNO"):
                    zup, razina = oznaka, "zupanija_ukupno"
                elif ime.startswith("UKUPNO"):
                    continue
                elif ime.endswith("ŽUPANIJA"):
                    zup, razina = oznaka, "zupanija"
                else:
                    zup, razina = oznaka, "jls"
                t = pd.read_excel(knjiga, list_, header=None, dtype=str).fillna("")
                zag = next(i for i, v in enumerate(t[3]) if str(v).startswith("Ostvareno u"))
                godine = {
                    c: _godina(str(t.iloc[zag, c]))
                    for c in t.columns
                    if str(t.iloc[zag, c]).startswith("Ostvareno u")
                }
                tijelo = t.iloc[zag + 2 :]  # preskoči redak s brojevima stupaca "1 2 3 4…"
                tijelo = tijelo[tijelo[2].str.strip().isin(STAVKE_PRORACUNA)]
                tijelo = tijelo.drop_duplicates(2)  # ista oznaka zna se ponoviti niže
                k = kljuc(ime)
                for c, god in godine.items():
                    for stavka, v in zip(tijelo[2].str.strip(), tijelo[c], strict=True):
                        retci.append((zup, razina, ime, k, god, stavka, broj(v)))
    df = pd.DataFrame(
        retci, columns=["zupanija", "razina", "naziv", "kljuc", "godina", "stavka", "iznos"]
    )
    # ista stavka može se pojaviti dvaput (npr. "01" u PR-RAS i u RAS-funkc): uzima se prva
    df = df.drop_duplicates(["zupanija", "razina", "naziv", "godina", "stavka"])
    zadnja = max(df["godina"])
    return df, zadnja
