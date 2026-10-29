# Format podataka za kartu i sučelje

Ovaj dokument je dogovor između obrade podataka (David), karte (Boro) i sučelja (Rafael).
Sve datoteke nalaze se u `web/public/data/` i nastaju naredbom `python pipeline/build.py`.
**Te se datoteke nikad ne uređuju ručno.**

> **Stanje:** brojke su **prave** (`"probni_podaci": false`), a granice su **službene
> DGU granice** (`"probne_granice": false`) za županije i za svih 556 gradova i općina.
> Šifre gradova i općina su službene šifre iz Registra prostornih jedinica.

## Datoteke

| Datoteka | Što sadrži | Tko je koristi |
| --- | --- | --- |
| `meta.json` | Teme, katalog pokazatelja (naziv, jedinica, godina, izvor), popis izvora, napomene | Rafael, Boro |
| `drzava.json` | Brojke za cijelu Hrvatsku | Rafael |
| `zupanije.geojson` | Granice 21 županije (DGU), samo šifra i naziv | Boro |
| `zupanije.json` | Brojke, rangovi i slična područja za svaku županiju | Boro, Rafael |
| `jls.json` | Brojke, rangovi i slična područja za svih 556 gradova i općina | Boro, Rafael |
| `jls/<šifra županije>.geojson` | Granice gradova i općina jedne županije (21 datoteka, DGU) | Boro |
| `tocke/eu-projekti.geojson` | 8.355 EU projekata (OPKK 2014.–2020.) kao točke | Boro |
| `gradovi/…` | Prikaz Zagreba (17 gradskih četvrti, slojevi točaka) i Rijeke (proračun, prostori) | Boro, Rafael |

Granice i brojke su **namjerno odvojene**: granice se rijetko mijenjaju i preglednik ih
može dugo čuvati, a brojke se mijenjaju pri svakom pokretanju obrade.

## Opća pravila

- Kodiranje je **UTF-8**, a nazivi su s kvačicama („Varaždinska županija”).
- **Šifre su uvijek tekst**: `"05"`, a ne `5`.
  - Država: `"HR"`.
  - Županije: `"01"`–`"21"` (službene DZS šifre, iste kao ISO 3166-2:HR).
  - Gradovi i općine: službena 5-znamenkasta šifra iz Registra prostornih jedinica
    (DGU), npr. Andrijaševci `"00019"`, Grad Zagreb `"01333"`. Šifra **ne** sadrži
    županiju; županiju gradu ili općini daje polje `nadredeno` (ili `zupanija` u GeoJSON-u).
- **Brojevi su sirovi**, bez razmaka i oznaka valute: `2900000000`, a ne „2,9 mlrd €”.
  Formatiranje radi sučelje prema `jedinica` i `decimale` iz `meta.json`.
- **Podatak koji nedostaje je `null`**. Ključ uvijek postoji, ali se prikazuje kao
  „nema podatka”, ne kao 0.
- Koordinate su u **WGS84** (EPSG:4326) s najviše 5 decimala.

## `meta.json`

```json
{
  "verzija_formata": 1,
  "generirano": "2026-10-27T20:30:00+00:00",
  "probni_podaci": false,
  "probne_granice": true,
  "napomene": ["Granice županija su probne (Natural Earth) …"],
  "teme": { "ljudi": "Ljudi", "novac": "Novac", "porezi": "Porezi", "imovina": "Imovina" },
  "pokazatelji": {
    "neto_dohodak": {
      "naziv": "Neto dohodak stanovništva",
      "tema": "ljudi",
      "jedinica": "EUR",
      "decimale": 0,
      "po_stanovniku": { "mnozitelj": 1, "jedinica": "EUR po stanovniku" },
      "razine": ["drzava", "zupanija", "jls"],
      "izvor": "pu-porez-dohodak",
      "napomena": "Plaće, mirovine i ostali dohodak nakon poreza i doprinosa, za cijelu godinu.",
      "godina": "2025"
    }
  },
  "izvori": {
    "pu-porez-dohodak": {
      "naziv": "Porez na dohodak",
      "izdavatelj": "Porezna uprava",
      "poveznica": "https://data.gov.hr/ckan/dataset/…",
      "licenca": "Otvorena dozvola (OD)",
      "preuzeto": "2026-10-27",
      "dopunski": false
    }
  }
}
```

- `godina` je razdoblje na koje se broj odnosi. Pokazatelji imaju **različite godine**
  (npr. stanovništvo 2021., plaće 2025.), pa godinu treba prikazati uz izvor.
  To je tekst, ne broj: može biti `"2025"`, `"VI. 2026."` ili `"stanje 31.05.2023"`.
- `napomena` je neobavezna rečenica za korisnika (npr. u oblačiću uz pokazatelj).
- `po_stanovniku` je `null` ako se pokazatelj ne preračunava po stanovniku (npr. stope u %).
  Prekidač „ukupno / po stanovniku” za takve pokazatelje treba biti onemogućen.
- `mnozitelj` je 1 za iznose u eurima („EUR po stanovniku”), a 1000 za brojeve
  („na 1.000 stanovnika”).
- `razine` govori gdje pokazatelj postoji. Npr. `inflacija` postoji samo na razini države.
- `izvor` je ključ u `izvori`. `hbor-esif` (5 skupova) i `eu-2021-2027` (3 popisa) su
  zbirni izvori s poljem `dijelovi`.
- **Navođenje izvora u sučelju** (uvjet organizatora): uz broj prikazati izdavatelja, naziv
  skupa i datum preuzimanja (`preuzeto`). Ako `licenca` počinje s „Otvorena dozvola”, dodati
  poveznicu https://data.gov.hr/otvorena-dozvola; ako dozvola nije navedena, napisati samo
  „javno objavljeno”. `dopunski: true` znači da skup nije s Portala otvorenih podataka nego sa
  službenih stranica tijela javne vlasti – takve izvore treba vidljivo odvojiti (npr. oznaka
  „dopunski izvor”).
- `napomene` su općenite napomene o podacima (npr. da su granice probne).

### Pokazatelji

| Ključ | Tema | Jedinica | Po stanovniku | Razine | Godina |
| --- | --- | --- | --- | --- | --- |
| `stanovnistvo` | ljudi | osoba | — | država, županija, JLS | 2021. |
| `gustoca_naseljenosti` | ljudi | st./km² | — | država, županija | 2021. |
| `prosjecna_starost` | ljudi | godina | — | država, županija, JLS | 2021. |
| `prosjecna_neto_placa` | ljudi | EUR | — | država, županija | 2025. |
| `zaposleni` | ljudi | osoba | na 1.000 st. | država, županija | 2024. |
| `stopa_nezaposlenosti` | ljudi | % | — | država, županija | IX. 2026. |
| `neto_dohodak` | ljudi | EUR | EUR po st. | država, županija, JLS | 2025. |
| `bdp` | novac | EUR | EUR po st. | država | 2023. |
| `bruto_dodana_vrijednost` | novac | EUR | EUR po st. | država, županija | 2023. |
| `eu_ugovoreno` | novac | EUR | EUR po st. | država, županija, JLS | 31. 5. 2023. |
| `eu_projekti` | novac | broj | na 1.000 st. | država, županija, JLS | 31. 5. 2023. |
| `eu_2127_ugovoreno` | novac | EUR | EUR po st. | država, županija**, JLS** | 30. 9. 2026. |
| `eu_2127_projekti` | novac | broj | na 1.000 st. | država, županija**, JLS** | 30. 9. 2026. |
| `hbor_krediti` | novac | EUR | EUR po st. | država, županija | 2018.–2023. |
| `lokalni_prihodi` | novac | EUR | EUR po st. | država***, županija***, JLS | 2025. |
| `lokalni_rashodi` | novac | EUR | EUR po st. | država***, županija***, JLS | 2025. |
| `lokalna_ulaganja` | novac | EUR | EUR po st. | država***, županija***, JLS | 2025. |
| `saldo_lokalnog_proracuna` | novac | EUR | EUR po st. | država***, županija***, JLS | 2025. |
| `udio_pomoci_u_prihodima` | novac | % | — | država***, županija***, JLS | 2025. |
| `inflacija` | novac | % | — | država | IX. 2026. |
| `saldo_proracuna` | novac | EUR | EUR po st. | država | 2025. |
| `javni_dug` | novac | EUR | EUR po st. | država | VI. 2026. |
| `porez_na_dohodak` | porezi | EUR | EUR po st. | država, županija, JLS | 2025. |
| `stopa_poreza_dohodak_niza` | porezi | % | — | država*, županija*, JLS | 2026. |
| `stopa_poreza_dohodak_visa` | porezi | % | — | država*, županija*, JLS | 2026. |
| `promjena_stope_niza` | porezi | p.b. | — | JLS | 2025.→2026. |
| `porez_na_potrosnju` | porezi | % | — | JLS | 2026. |
| `porez_na_nekretnine` | porezi | EUR/m² | — | JLS | 2026. |
| `kupoprodaje_nekretnina` | imovina | broj | na 1.000 st. | država, županija | 2025. |
| `pravne_osobe_aktivne` | imovina | broj | na 1.000 st. | država | I. 2022. |

\* Stope određuju gradovi i općine; za županiju i državu to je prosjek ponderiran
brojem stanovnika (Hrvatska: niža 20,6 %, viša 30,5 %). `promjena_stope_niza` je dobra
„priča”: 13 gradova i općina promijenilo je nižu stopu za 2026., od −5 do +2,5 postotna boda.

\*\* EU 2021.–2027. (programi Konkurentnost i kohezija, Integrirani teritorijalni
program i Učinkoviti ljudski potencijali; 3.717 projekata, 7,13 mlrd. EUR EU sredstava).
Županija = lokacija projekta (projekt u više županija dijeli se po udjelima), grad/općina =
sjedište korisnika. Projekti ministarstava, HZZ-a i drugih državnih tijela (1,74 mlrd. EUR)
ulaze samo u zbroj države, pa zbroj županija nije jednak državi. Dobra „priča” za kartu:
u razdoblju 2014.–2020. Zagreb je dobio 3,8 mlrd. EUR, a sada po stanovniku vode Karlovačka i
Ličko-senjska županija.

\*\*\* Proračuni (Ministarstvo financija, ostvarenje): za grad ili općinu to je njezin
proračun, za županiju zbroj proračuna županije i svih njezinih gradova i općina, a za
državu zbroj svih lokalnih proračuna. Raspodjela je jako nejednaka (prihodi po stanovniku od
641 do 15.959 EUR; Ervenik ima neuobičajeno velike prihode), pa za boje karte treba koristiti
kvantile, a ne linearnu skalu. `udio_pomoci_u_prihodima` je dobra „priča”: u polovici
općina pomoći čine više od 40 % prihoda, a u nekima više od 80 %.

Prijedlog za panel Država (najviše 4 broja): stanovništvo, BDP, prosječna neto plaća
i inflacija.

Po županijama DZS ne objavljuje BDP, nego **bruto dodanu vrijednost** (BDP bez poreza na
proizvode). Za usporedbu županija koristi `bruto_dodana_vrijednost`, uz napomenu iz `meta.json`.

Popis će rasti (porezne stope po JLS, poslovne zone). Sučelje zato ne smije imati
nazive ni jedinice upisane u kodu, nego ih uvijek čita iz `meta.json`.

## `drzava.json`, `zupanije.json` i `jls.json`

Svako područje ima isti oblik. `drzava.json` je jedan takav zapis, a `zupanije.json` i
`jls.json` ih imaju više pod ključem `podrucja`, gdje je ključ šifra područja.

```json
{
  "generirano": "2026-10-27T20:30:00+00:00",
  "podrucja": {
    "05": {
      "sifra": "05",
      "naziv": "Varaždinska županija",
      "vrsta": "zupanija",
      "nadredeno": "HR",
      "pokazatelji":   { "stanovnistvo": 159487, "neto_dohodak": 1418652273.93 },
      "po_stanovniku": { "neto_dohodak": 8895.1 },
      "rang":          { "stanovnistvo": 8, "neto_dohodak_po_stanovniku": 10 },
      "slicni": ["13", "16", "03", "12", "18"]
    }
  }
}
```

| Polje | Značenje |
| --- | --- |
| `vrsta` | `drzava`, `zupanija`, `grad` ili `opcina` |
| `nadredeno` | Šifra područja iznad (za županiju `"HR"`, za grad ili općinu šifra županije) |
| `pokazatelji` | Ukupne vrijednosti, za svaki pokazatelj koji postoji na ovoj razini |
| `po_stanovniku` | Vrijednosti po stanovniku, samo za pokazatelje kojima to ima smisla |
| `rang` | Mjesto među područjima iste razine (21 županija ili 556 JLS); **1 = najveća vrijednost**. Za mjeru po stanovniku ključ ima nastavak `_po_stanovniku`. `null` ako nema podatka |
| `slicni` | 5 šifri područja iste razine najsličnijih po broju stanovnika |

Rang je samo poredak, ne ocjena. Je li veća vrijednost bolja (plaća) ili lošija
(nezaposlenost), odlučuje rečenica u sučelju.

`jls.json` je spremljen bez uvlaka (282 KB), pa ga ne treba otvarati ručno. Za pregled
postoji `data/obrada/jls.csv`, koji se otvara u Excelu.

## `proracuni.json`

Vremenski niz proračuna za graf u panelu, za državu (`"HR"`), županije (`"01"`–`"21"`) i
sve gradove i općine (službena šifra):

```json
{
  "godine": [2019, 2020, 2021, 2022, 2023, 2024, 2025],
  "funkcije": {"01": "Opće javne usluge", "09": "Obrazovanje", "...": "..."},
  "podrucja": {
    "01333": {
      "prihodi": [1012503810, 973008626, "…"],
      "rashodi": ["…"],
      "ulaganja": ["…"],
      "funkcije": {"01": 123456789, "...": "…"}
    }
  }
}
```

`prihodi`, `rashodi` i `ulaganja` imaju po jednu vrijednost za svaku godinu iz `godine`
(EUR, ostvarenje). `funkcije` su rashodi po namjeni za zadnju godinu; ne uključuju prijenose
drugim proračunima, pa je njihov zbroj manji od rashoda. Datoteka ima oko 220 KB.

## `zupanije.geojson`

Standardni GeoJSON (`FeatureCollection`) s 21 poligonom. Svojstva (`properties`):

```json
{ "sifra": "05", "naziv": "Varaždinska županija", "kratki_naziv": "Varaždinska" }
```

Brojke **nisu** u GeoJSON-u. Karta ih spaja sa `zupanije.json` preko šifre.

Granice su službene DGU granice, pojednostavljene za prikaz (županije oko 400 m, općine
oko 80 m) tako da susjedi i dalje dijele istu granicu: nema rupa ni preklapanja.

## `jls/<šifra županije>.geojson`

21 datoteka, po jedna za svaku županiju (`jls/05.geojson` = gradovi i općine
Varaždinske županije), ukupno oko 2,4 MB. Učitava se samo datoteka županije u koju
korisnik uđe. Svojstva:

```json
{ "sifra": "00019", "naziv": "Andrijaševci", "vrsta": "opcina", "zupanija": "16" }
```

Brojke su u `jls.json` pod istom šifrom. Za MapLibre vrijedi isti savjet kao za
županije (`promoteId: "sifra"`).

**Savjet za MapLibre (Boro):** kod dodavanja izvora koristi `promoteId: "sifra"`. Tada se
za svaku županiju može postaviti `setFeatureState({ source, id: "05" }, { vrijednost })`
i bojati izrazom `["feature-state", "vrijednost"]`. Kad se promijeni tema ili mjera,
mijenja se samo stanje, a granice se ne učitavaju ponovno.

## `tocke/eu-projekti.geojson`

`FeatureCollection` točaka, uz polje `presjek` (datum stanja podataka). Svojstva:

```json
{
  "sifra": "KK.01.1.1.01.0001",
  "naziv": "Potpora vrhunskim istraživanjima Centra izvrsnosti …",
  "korisnik": "Institut Ruđer Bošković",
  "esif_eur": 4285859,
  "ukupno_eur": 5042187,
  "zupanija": "21",
  "jls": "01333",
  "mjesto": "Zagreb",
  "fond": "EFRR",
  "pocetak": "2017-11-01",
  "kraj": "2023-11-30",
  "kategorija": "060"
}
```

`jls` je šifra grada ili općine u kojoj točka leži (prema granicama DGU-a); `null` za
11 točaka izvan kopna (npr. na moru). Datoteka ima oko 3,6 MB, pa je treba učitati tek kad korisnik uključi sloj, a točke
grupirati (`cluster: true`). Za 3D stupce teme Novac koristi se `esif_eur`.

## Gradovi: `gradovi/`

Prikaz grada otvara se kad korisnik na razini Grad odabere Zagreb (`01333`) ili Rijeku
(`03735`). Sve datoteke nastaju u `pipeline/gradovi.py` (korak 4 u `build.py`).

```text
gradovi/
  meta.json                         katalog slojeva i pokazatelja četvrti, nazivi funkcija, izvori
  zagreb/cetvrti.geojson            17 gradskih četvrti (poligoni: sifra, naziv)
  zagreb/cetvrti.json               brojke i rangovi po četvrtima (isti oblik kao zupanije.json)
  zagreb/kapitalna-ulaganja.geojson točke: planirana gradska ulaganja 2023. i 2024.
  zagreb/brownfield.geojson         poligoni: 43 napuštene površine
  zagreb/gospodarske-zone.geojson   poligoni: 553 gospodarske zone iz prostornih planova
  zagreb/zgrade-3d/<šifra>.geojson  3D zgrade (ZG3D) za Donji grad, Gornji grad–Medveščak i Trnje
  zagreb/prazni-prostori.geojson    točke: 733 prazna gradska prostora i garaže (po adresi)
  zagreb/smjestaj.geojson           točke: 2.702 smještajna objekta (hotel, hostel, domaćinstvo)
  zagreb/trznice.geojson            točke: 31 gradska tržnica
  zagreb/gradska-drustva.geojson    točke: 33 gradska trgovačka društva
  zagreb/eu-projekti.json           popis 299 EU projekata Grada (bez lokacije)
  zagreb/proracun.json              proračun 2026. po funkcijama i vrstama prihoda
  rijeka/proracun.json              proračun 2025., isti oblik kao za Zagreb
  rijeka/poslovni-prostori.json     1.296 gradskih prostora u zakupu po zonama i djelatnostima
  rijeka/eu-projekti.json           popis 16 EU projekata Grada (2013.–2017.)
  rijeka/poslovni-prostori.geojson  točke: 1.295 gradskih prostora u zakupu (po adresi)
```

**Četvrti.** Šifra četvrti je službena 5-znamenkasta šifra iz Registra prostornih
jedinica (npr. Donji grad `"00116"`), a `nadredeno` je `"01333"`. Pokazatelji su opisani
u `gradovi/meta.json` → `pokazatelji_cetvrti` (naziv, tema, jedinica, decimale, godina,
izvor), istim poljima kao u glavnom `meta.json`. Po četvrtima nema stanovništva, pa nema
ni vrijednosti po stanovniku (`po_stanovniku` je prazan).

| Ključ | Tema | Jedinica | Godina |
| --- | --- | --- | --- |
| `povrsina` | imovina | km² | 2025. |
| `kapitalna_ulaganja` | novac | EUR | 2024. |
| `kapitalni_projekti` | novac | broj | 2024. |
| `smjestajni_objekti` | novac | broj | 2023. |
| `prazni_poslovni_prostori` | imovina | broj | 2024. |
| `prazni_poslovni_prostori_m2` | imovina | m² | 2024. |
| `prazne_garaze` | imovina | broj | 2024. |
| `brownfield` | imovina | ha | 2020. |
| `udio_gospodarske_povrsine` | imovina | % | 2020. |
| `udio_stambene_povrsine` | imovina | % | 2020. |
| `udio_zelene_povrsine` | imovina | % | 2020. |
| `gospodarske_zone` | imovina | ha | 2023. |
| `gospodarske_zone_neizgradjene` | imovina | ha | 2023. |

**Gospodarske zone** (`gospodarske-zone.geojson`, oko 300 KB) imaju svojstva `vrsta`
(poslovna, proizvodna, poslovna i proizvodna, trgovačka, ugostiteljsko-turistička,
gospodarska (općenito)), `namjena` (izvorni naziv iz plana), `izgradjenost`
(`"neizgrađeno"`, `"izgrađeno"` ili `null` kad plan to ne navodi), `plan`, `godina_plana`,
`povrsina_ha` i `cetvrt`. Za kartu: boja prema `vrsta`, a neizgrađene zone istaknuti
(npr. iscrtkani rub) jer su to površine spremne za nova ulaganja.

**3D zgrade** (`zgrade-3d/00116.geojson`, `00159`, `00680`; 2–4 MB svaka) su tlocrti
dijelova zgrada iz modela ZG3D (LoD 2.2) sa svojstvima `visina` (m) i `godina` (godina
snimanja: 2008., 2019. ili 2022.). Popis datoteka i sažetak (broj dijelova, prosječna i
najveća visina) su u `gradovi/meta.json` → `gradovi.zagreb.zgrade_3d`. Za kartu:

```js
map.addLayer({
  id: "zgrade-3d", type: "fill-extrusion", source: "zgrade-00116", minzoom: 14,
  paint: {
    "fill-extrusion-height": ["get", "visina"],
    "fill-extrusion-base": 0,
    "fill-extrusion-color": ["interpolate", ["linear"], ["get", "visina"],
      0, "#d9d9d9", 20, "#8c8c8c", 60, "#3b3b3b"]
  }
});
```

Datoteke učitati tek kad korisnik u prikazu Zagreba približi kartu (zoom 14 ili više),
jer su zajedno oko 8,5 MB.

**Prostori po adresi** nastaju spajanjem adrese iz gradske tablice s registrom adresa
DGU-a. Svojstvo `tocnost` kaže koliko je točka pouzdana: `"tocno"` (ista ulica, broj i
slovo), `"bez dodatka"` (ista ulica i broj) ili `"ulica"` (samo ulica, točka je sredina
ulice, npr. za adrese „bez broja”). Zagreb (`prazni-prostori.geojson`): `vrsta` (poslovni
prostor, poslovni prostor (ne ispunjava uvjete), garaža, parkirno mjesto), `adresa`,
`povrsina` (m²), `cetvrt`. Rijeka (`poslovni-prostori.geojson`): `adresa`, `zona` (0 =
najskuplja, središte; III = rub grada), `povrsina`, `djelatnost`, `cijena_eur_m2`,
`zakupnina_mjesecno` (EUR). Imena zakupnika se namjerno ne prikazuju. Na istoj adresi može
biti više prostora (npr. garaže u istoj zgradi), pa točke treba grupirati.

**Točke** imaju svojstvo `cetvrt` (šifra četvrti u kojoj leže; `null` izvan grada).
Kapitalna ulaganja imaju `godina` (2023 ili 2024) i `iznos` (EUR), pa sloj treba
filtrirati po godini, npr. `["==", ["get", "godina"], 2024]`. Smještaj (oko 600 KB)
učitati tek kad se sloj uključi i grupirati točke.

**Proračun** (`proracun.json`) ima isti oblik za oba grada, pa se mogu staviti jedan
uz drugi:

```json
{
  "grad": "Zagreb", "sifra": "01333", "godina": 2026, "vrsta": "plan",
  "stanovnistvo": 767131,
  "rashodi_ukupno": 3077158730, "rashodi_po_stanovniku": 4011.26,
  "prihodi_ukupno": 2931223940, "prihodi_po_stanovniku": 3821.02,
  "rashodi_po_funkciji": [
    {"sifra": "09", "naziv": "Obrazovanje", "iznos": 1023466120, "po_stanovniku": 1334.15, "udio": 33.26}
  ],
  "prihodi_po_vrsti": [
    {"sifra": "61", "naziv": "Porezi", "iznos": 1633130000, "po_stanovniku": 2128.88, "udio": 55.71}
  ],
  "napomena": "Grad Zagreb je ujedno i županija …"
}
```

`napomena` treba prikazati uz usporedbu: Zagreb kao grad i županija financira i bolnice
i srednje škole, pa njegov proračun po stanovniku nije izravno usporediv s Rijekom.

**Rijeka** nema otvorene granice mjesnih odbora. Na karti se prikazuje granica grada iz
`jls/08.geojson` (šifra `03735`) i točke prostora u zakupu, a zbrojevi u panelu.

## Kako se mijenja ovaj format

1. Promjenu predloži u issue-u ili pull requestu i označi ostalu dvojicu.
2. Ako se ključ preimenuje ili ukloni, poveća se `verzija_formata` u `meta.json`.
3. Novi pokazatelj ne mijenja verziju: dovoljno ga je dodati u `pipeline/pokazatelji.py`.
