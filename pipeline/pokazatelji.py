"""Katalog pokazatelja koje aplikacija prikazuje.

Ovo je jedino mjesto gdje se pokazatelj definira. Iz njega nastaje dio
`pokazatelji` u web/public/data/meta.json, pa karta i paneli iz meta.json
znaju naziv, temu, jedinicu, godinu i izvor svakog broja.

Polja:
  naziv          tekst za korisnika
  tema           ljudi | novac | porezi | imovina
  jedinica       jedinica ukupne vrijednosti
  decimale       koliko decimala prikazati
  po_stanovniku  None ili {"mnozitelj": 1 | 1000, "jedinica": "..."}:
                 vrijednost / stanovništvo * mnozitelj
  razine         na kojim razinama postoji: drzava, zupanija, jls
  izvor          id skupa iz data/sources.csv (ili zbirni id, vidi build.ZBIRNI_IZVORI)
  napomena       kratko objašnjenje za korisnika (neobavezno)

Godinu svakog pokazatelja upisuje build.py iz samog izvora (polje `godina` u meta.json).
"""

TEME = {
    "ljudi": "Ljudi",
    "novac": "Novac",
    "porezi": "Porezi",
    "imovina": "Imovina",
}

_PO_ST_EUR = {"mnozitelj": 1, "jedinica": "EUR po stanovniku"}
_NA_1000 = {"mnozitelj": 1000, "jedinica": "na 1.000 stanovnika"}

POKAZATELJI: dict[str, dict] = {
    # --- Ljudi ---
    "stanovnistvo": {
        "naziv": "Stanovništvo",
        "tema": "ljudi",
        "jedinica": "osoba",
        "decimale": 0,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "dzs-popis2021",
    },
    "gustoca_naseljenosti": {
        "naziv": "Gustoća naseljenosti",
        "tema": "ljudi",
        "jedinica": "st./km²",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija"],
        "izvor": "dzs-popis2021",
    },
    "prosjecna_starost": {
        "naziv": "Prosječna starost",
        "tema": "ljudi",
        "jedinica": "godina",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "dzs-popis2021",
    },
    "prosjecna_neto_placa": {
        "naziv": "Prosječna neto plaća",
        "tema": "ljudi",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija"],
        "izvor": "dzs-place",
        "napomena": "Mjesečni prosjek u pravnim osobama, prema JOPPD obrascu.",
    },
    "zaposleni": {
        "naziv": "Zaposleni",
        "tema": "ljudi",
        "jedinica": "osoba",
        "decimale": 0,
        "po_stanovniku": _NA_1000,
        "razine": ["drzava", "zupanija"],
        "izvor": "dzs-place",
        "napomena": "Stanje 31. ožujka, administrativni izvori.",
    },
    "stopa_nezaposlenosti": {
        "naziv": "Stopa registrirane nezaposlenosti",
        "tema": "ljudi",
        "jedinica": "%",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija"],
        "izvor": "dzs-place",
    },
    "neto_dohodak": {
        "naziv": "Neto dohodak stanovništva",
        "tema": "ljudi",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "pu-porez-dohodak",
        "napomena": "Plaće, mirovine i ostali dohodak nakon poreza i doprinosa, za cijelu godinu.",
    },
    # --- Novac ---
    "bdp": {
        "naziv": "Bruto domaći proizvod",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava"],
        "izvor": "dzs-bdp-regije",
    },
    "bruto_dodana_vrijednost": {
        "naziv": "Bruto dodana vrijednost",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija"],
        "izvor": "dzs-bdp-regije",
        "napomena": "Vrijednost proizvodnje u županiji; BDP bez poreza na proizvode. "
        "Po županijama DZS ne objavljuje BDP.",
    },
    "eu_ugovoreno": {
        "naziv": "Ugovorena EU sredstva (OPKK 2014.–2020.)",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "eu-opkk-2014-2020",
        "napomena": "ESIF dio ugovorenih projekata, prema mjestu provedbe projekta.",
    },
    "eu_projekti": {
        "naziv": "Broj EU projekata (OPKK 2014.–2020.)",
        "tema": "novac",
        "jedinica": "broj",
        "decimale": 0,
        "po_stanovniku": _NA_1000,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "eu-opkk-2014-2020",
    },
    "hbor_krediti": {
        "naziv": "HBOR krediti iz EU fondova",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija"],
        "izvor": "hbor-esif",
        "napomena": "Pet ESIF programa HBOR-a, po županiji ulaganja.",
    },
    "inflacija": {
        "naziv": "Inflacija (godišnja, HIPC)",
        "tema": "novac",
        "jedinica": "%",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava"],
        "izvor": "hnb-bilten",
    },
    "saldo_proracuna": {
        "naziv": "Saldo opće države",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava"],
        "izvor": "hnb-opca-drzava",
        "napomena": "Negativno = deficit (neto zaduživanje), ESA 2010.",
    },
    "javni_dug": {
        "naziv": "Dug opće države",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava"],
        "izvor": "hnb-opca-drzava",
    },
    # --- Porezi ---
    "porez_na_dohodak": {
        "naziv": "Uplaćeni porez na dohodak",
        "tema": "porezi",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "pu-porez-dohodak",
        "napomena": "Pripada gradovima i općinama; po prebivalištu obveznika.",
    },
    # --- Imovina ---
    "kupoprodaje_nekretnina": {
        "naziv": "Kupoprodaje nekretnina",
        "tema": "imovina",
        "jedinica": "broj",
        "decimale": 0,
        "po_stanovniku": _NA_1000,
        "razine": ["drzava", "zupanija"],
        "izvor": "pu-kupoprodaje",
    },
    "pravne_osobe_aktivne": {
        "naziv": "Aktivne pravne osobe",
        "tema": "imovina",
        "jedinica": "broj",
        "decimale": 0,
        "po_stanovniku": _NA_1000,
        "razine": ["drzava"],
        "izvor": "dzs-rps",
    },
}

for _id, _p in POKAZATELJI.items():
    assert _p["tema"] in TEME, _id
