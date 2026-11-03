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
  napomena       kako je broj izračunat, za one koji žele točnu definiciju (neobavezno)
  objasnjenje    što broj znači, jednostavnim riječima, za panel i legendu (obavezno)

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
        "objasnjenje": "Koliko ljudi ovdje živi prema Popisu stanovništva 2021. Tim brojem "
        "dijelimo sve iznose po stanovniku.",
    },
    "stanovnistvo_procjena": {
        "naziv": "Stanovništvo (procjena DZS-a)",
        "tema": "ljudi",
        "jedinica": "osoba",
        "decimale": 0,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija"],
        "izvor": "dzs-procjena-stanovnistva",
        "napomena": "Procjena sredinom godine. Iznosi po stanovniku i dalje se računaju iz "
        "Popisa 2021., jer za gradove i općine novije procjene nema.",
        "objasnjenje": "Koliko ljudi ovdje živi sredinom 2025. prema procjeni Državnog zavoda za "
        "statistiku, s doseljenima, odseljenima, rođenima i umrlima nakon popisa.",
    },
    "promjena_stanovnistva": {
        "naziv": "Promjena broja stanovnika",
        "tema": "ljudi",
        "jedinica": "%",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija"],
        "izvor": "dzs-procjena-stanovnistva",
        "napomena": "Promjena procjene sredinom godine u odnosu na sredinu 2021. "
        "(useljavanje i iseljavanje te rođeni i umrli).",
        "objasnjenje": "Za koliko se posto promijenio broj stanovnika od 2021. do 2025. Minus "
        "znači da je više ljudi umrlo ili odselilo nego što se rodilo ili "
        "doselilo.",
    },
    "gustoca_naseljenosti": {
        "naziv": "Gustoća naseljenosti",
        "tema": "ljudi",
        "jedinica": "st./km²",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija"],
        "izvor": "dzs-popis2021",
        "objasnjenje": "Koliko ljudi u prosjeku živi na jednom četvornom kilometru. Velik broj "
        "znači gusto naseljen kraj, malen rijetko naseljen.",
    },
    "prosjecna_starost": {
        "naziv": "Prosječna starost",
        "tema": "ljudi",
        "jedinica": "godina",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "dzs-popis2021",
        "objasnjenje": "Prosječna dob svih stanovnika. Veći broj znači stariju sredinu, s više "
        "umirovljenika i manje djece.",
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
        "objasnjenje": "Koliko zaposleni u tvrtkama i ustanovama prosječno dobiju na ruke "
        "mjesečno, nakon poreza i doprinosa. Ne uključuje obrte.",
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
        "objasnjenje": "Koliko ljudi ima posao. Po stanovniku pokazuje koliko je zaposlenih na "
        "svakih 1.000 stanovnika.",
    },
    "stopa_nezaposlenosti": {
        "naziv": "Stopa registrirane nezaposlenosti",
        "tema": "ljudi",
        "jedinica": "%",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija"],
        "izvor": "dzs-place",
        "objasnjenje": "Koliko je od 100 ljudi koji rade ili traže posao prijavljeno na Zavodu "
        "za zapošljavanje kao nezaposleno.",
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
        "objasnjenje": "Koliko su svi stanovnici zajedno primili u godini nakon poreza i "
        "doprinosa: plaće, mirovine i ostalo. Po stanovniku je to prosjek po "
        "osobi, računajući i djecu.",
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
        "objasnjenje": "Vrijednost svega što je u Hrvatskoj proizvedeno u godini. Najčešća mjera "
        "veličine gospodarstva.",
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
        "objasnjenje": "Koliko vrijednosti u godini stvore tvrtke, obrti i javne službe u "
        "županiji. Slično BDP-u, ali bez poreza na proizvode poput PDV-a.",
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
        "objasnjenje": "Koliko je novca iz EU fondova ugovoreno za projekte ovdje u razdoblju "
        "2014.–2020. Ugovoreno ne znači i isplaćeno.",
    },
    "eu_projekti": {
        "naziv": "Broj EU projekata (OPKK 2014.–2020.)",
        "tema": "novac",
        "jedinica": "broj",
        "decimale": 0,
        "po_stanovniku": _NA_1000,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "eu-opkk-2014-2020",
        "objasnjenje": "Koliko je projekata s novcem iz EU fondova ugovoreno ovdje u razdoblju "
        "2014.–2020.",
    },
    "eu_2127_ugovoreno": {
        "naziv": "Ugovorena EU sredstva 2021.–2027.",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "eu-2021-2027",
        "napomena": "EU dio ugovorenih projekata iz programa Konkurentnost i kohezija, "
        "Integrirani teritorijalni program i Učinkoviti ljudski potencijali. Županije prema "
        "lokaciji projekta (ULJP prema sjedištu korisnika); gradovi i općine prema sjedištu "
        "korisnika. Projekti državnih tijela i projekti bez lokacije ulaze samo u zbroj države.",
        "objasnjenje": "Koliko je novca iz EU fondova do sada ugovoreno za projekte ovdje u "
        "razdoblju 2021.–2027. Razdoblje još traje, a ugovoreno ne znači i "
        "isplaćeno.",
    },
    "eu_2127_projekti": {
        "naziv": "Broj EU projekata 2021.–2027.",
        "tema": "novac",
        "jedinica": "broj",
        "decimale": 0,
        "po_stanovniku": _NA_1000,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "eu-2021-2027",
        "napomena": "Projekt koji se provodi u više županija broji se u svakoj od njih.",
        "objasnjenje": "Koliko je projekata s novcem iz EU fondova do sada ugovoreno ovdje u "
        "razdoblju 2021.–2027.",
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
        "objasnjenje": "Koliko su tvrtke, poljoprivrednici i javni sektor dobili povoljnih "
        "kredita HBOR-a koji se financiraju iz EU fondova.",
    },
    "inflacija": {
        "naziv": "Inflacija (godišnja, HIPC)",
        "tema": "novac",
        "jedinica": "%",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava"],
        "izvor": "hnb-bilten",
        "objasnjenje": "Koliko su cijene porasle u godinu dana. Na primjer, 4 % znači da ono što "
        "je lani stajalo 100 € sada stoji 104 €.",
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
        "objasnjenje": "Razlika između prihoda i rashoda cijele države, s gradovima, općinama i "
        "fondovima. Minus znači da država troši više nego što prikupi i razliku "
        "posuđuje.",
    },
    "javni_dug": {
        "naziv": "Dug opće države",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava"],
        "izvor": "hnb-opca-drzava",
        "objasnjenje": "Koliko država ukupno duguje kroz kredite i obveznice, zajedno s "
        "gradovima, općinama i javnim fondovima.",
    },
    "lokalni_prihodi": {
        "naziv": "Prihodi lokalnog proračuna",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "mfin-lokalni-proracuni",
        "napomena": "Ostvarenje proračuna (ne plan), zadnja godina. Za županiju: proračun "
        "županije i svih njezinih gradova i općina; za državu: zbroj svih lokalnih proračuna.",
        "objasnjenje": "Sav novac koji je grad ili općina primila u godini: porezi, naknade, "
        "pomoći države i EU te prodaja imovine. Za županiju zbrajamo i sve "
        "njezine gradove i općine.",
    },
    "lokalni_rashodi": {
        "naziv": "Rashodi lokalnog proračuna",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "mfin-lokalni-proracuni",
        "napomena": "Ostvarenje proračuna (ne plan), zadnja godina. Za županiju: proračun "
        "županije i svih njezinih gradova i općina; za državu: zbroj svih lokalnih proračuna.",
        "objasnjenje": "Sav novac koji je grad ili općina potrošila u godini: plaće, materijal, "
        "usluge, pomoći građanima i ulaganja.",
    },
    "lokalna_ulaganja": {
        "naziv": "Ulaganja lokalnog proračuna",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "mfin-lokalni-proracuni",
        "napomena": "Rashodi za nabavu nefinancijske imovine (ceste, zgrade, oprema).",
        "objasnjenje": "Dio rashoda koji je otišao u trajnu imovinu: ceste, zgrade, vrtiće, "
        "opremu. Pokazuje koliko se gradi, a ne samo troši.",
    },
    "saldo_lokalnog_proracuna": {
        "naziv": "Višak ili manjak lokalnog proračuna",
        "tema": "novac",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "mfin-lokalni-proracuni",
        "napomena": "Prihodi minus rashodi u godini (bez zaduživanja i prenesenog viška).",
        "objasnjenje": "Prihodi minus rashodi u godini. Plus je višak, a minus znači da je "
        "potrošeno više nego primljeno, pa se razlika pokriva kreditom ili "
        "ušteđevinom.",
    },
    "udio_pomoci_u_prihodima": {
        "naziv": "Udio pomoći u prihodima proračuna",
        "tema": "novac",
        "jedinica": "%",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "mfin-lokalni-proracuni",
        "napomena": "Pomoći iz državnog proračuna, EU i drugih proračuna (skupina 63) u "
        "ukupnim prihodima (skupine 6 i 7).",
        "objasnjenje": "Od svakih 100 € prihoda, koliko je grad ili općina dobila od države, EU "
        "ili drugih proračuna, a nije prikupila sama. Visok udio znači veću "
        "ovisnost o tuđem novcu, ali uključuje i EU novac za projekte.",
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
        "objasnjenje": "Koliko su stanovnici platili poreza na plaće, mirovine i druga primanja. "
        "Taj porez pripada gradu ili općini u kojoj žive i njihov je glavni "
        "vlastiti prihod.",
    },
    "stopa_poreza_dohodak_niza": {
        "naziv": "Niža stopa poreza na dohodak",
        "tema": "porezi",
        "jedinica": "%",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "pu-porezne-stope-jls",
        "napomena": "Stopu određuje grad ili općina. Za županiju i državu: prosjek "
        "gradova i općina ponderiran brojem stanovnika.",
        "objasnjenje": "Postotak poreza na primanja do granice višeg razreda, koji plaća većina "
        "zaposlenih. Određuje ga grad ili općina, pa niža stopa znači više na "
        "ruke.",
    },
    "stopa_poreza_dohodak_visa": {
        "naziv": "Viša stopa poreza na dohodak",
        "tema": "porezi",
        "jedinica": "%",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "pu-porezne-stope-jls",
        "napomena": "Stopu određuje grad ili općina. Za županiju i državu: prosjek "
        "gradova i općina ponderiran brojem stanovnika.",
        "objasnjenje": "Postotak poreza na dio primanja iznad granice višeg razreda, tj. na veće "
        "plaće. I njega određuje grad ili općina.",
    },
    "promjena_stope_niza": {
        "naziv": "Promjena niže stope poreza na dohodak",
        "tema": "porezi",
        "jedinica": "p.b.",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["jls"],
        "izvor": "pu-porezne-stope-jls",
        "napomena": "Razlika u odnosu na prošlu godinu, u postotnim bodovima.",
        "objasnjenje": "Je li grad ili općina ove godine promijenila nižu stopu poreza na "
        "dohodak i za koliko postotnih bodova. Minus znači da je porez smanjen.",
    },
    "porez_na_potrosnju": {
        "naziv": "Porez na potrošnju",
        "tema": "porezi",
        "jedinica": "%",
        "decimale": 1,
        "po_stanovniku": None,
        "razine": ["jls"],
        "izvor": "pu-porezne-stope-jls",
        "napomena": "Lokalni porez na pića u ugostiteljstvu; najviša stopa ako je propisan raspon.",
        "objasnjenje": "Lokalni porez na pića koja se prodaju u kafićima i restoranima. Novac "
        "ide gradu ili općini.",
    },
    "porez_na_nekretnine": {
        "naziv": "Porez na nekretnine",
        "tema": "porezi",
        "jedinica": "EUR/m²",
        "decimale": 2,
        "po_stanovniku": None,
        "razine": ["jls"],
        "izvor": "pu-porezne-stope-jls",
        "napomena": "Godišnji iznos po m²; najviši iznos ako je propisan raspon.",
        "objasnjenje": "Koliko vlasnik godišnje plaća po kvadratu stana ili kuće u kojoj nitko "
        "ne živi stalno i koja nije u dugoročnom najmu, npr. vikendice.",
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
        "objasnjenje": "Koliko je nekretnina (stanova, kuća, zemljišta) prodano u godini. "
        "Pokazuje koliko je živo tržište nekretnina.",
    },
    "porez_na_promet_nekretnina": {
        "naziv": "Porez na promet nekretnina (prihod proračuna)",
        "tema": "imovina",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "mfin-lokalni-proracuni",
        "napomena": "Ostvarenje proračuna, račun 6134 (povremeni porezi na imovinu), koji kod "
        "gradova i općina čini porez na promet nekretnina. Za županiju: županija i svi njezini "
        "gradovi i općine.",
        "objasnjenje": "Koliko je grad ili općina dobila od poreza koji plaća kupac nekretnine "
        "na njezinu području. Što se više nekretnina proda i što su skuplje, to je iznos veći.",
    },
    "prihodi_od_imovine": {
        "naziv": "Prihodi od nefinancijske imovine",
        "tema": "imovina",
        "jedinica": "EUR",
        "decimale": 0,
        "po_stanovniku": _PO_ST_EUR,
        "razine": ["drzava", "zupanija", "jls"],
        "izvor": "mfin-lokalni-proracuni",
        "napomena": "Ostvarenje proračuna, skupina 642: naknade za koncesije, zakup i najam "
        "imovine, naknade za korištenje imovine i ostalo. Za županiju: županija i svi njezini "
        "gradovi i općine.",
        "objasnjenje": "Koliko grad ili općina zaradi od svoje imovine: zakupa i najma prostora i "
        "zemljišta, koncesija i naknada za korištenje.",
    },
    "pravne_osobe_aktivne": {
        "naziv": "Aktivne pravne osobe",
        "tema": "imovina",
        "jedinica": "broj",
        "decimale": 0,
        "po_stanovniku": _NA_1000,
        "razine": ["drzava"],
        "izvor": "dzs-rps",
        "objasnjenje": "Koliko je aktivnih tvrtki, udruga, ustanova i drugih pravnih osoba. "
        "Obrti nisu uključeni.",
    },
}

for _id, _p in POKAZATELJI.items():
    assert _p["tema"] in TEME, _id
    assert _p.get("objasnjenje"), f"{_id}: nema objašnjenja"
