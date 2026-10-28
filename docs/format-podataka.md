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
| `zagreb/`, `rijeka/` | Slojevi gradskog prikaza *(dolazi kasnije)* | Boro |

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
      "preuzeto": "2026-10-27"
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
- `izvor` je ključ u `izvori`. `hbor-esif` je zbirni izvor s poljem `dijelovi` (5 skupova).
- `napomene` su općenite napomene o podacima (npr. da su granice probne).

### Pokazatelji

| Ključ | Tema | Jedinica | Po stanovniku | Razine | Godina |
| --- | --- | --- | --- | --- | --- |
| `stanovnistvo` | ljudi | osoba | — | država, županija, JLS | 2021. |
| `gustoca_naseljenosti` | ljudi | st./km² | — | država, županija | 2021. |
| `prosjecna_starost` | ljudi | godina | — | država, županija, JLS | 2021. |
| `prosjecna_neto_placa` | ljudi | EUR | — | država, županija | 2025. |
| `zaposleni` | ljudi | osoba | na 1.000 st. | država, županija | 2024. |
| `stopa_nezaposlenosti` | ljudi | % | — | država, županija | VI. 2026. |
| `neto_dohodak` | ljudi | EUR | EUR po st. | država, županija, JLS | 2025. |
| `bdp` | novac | EUR | EUR po st. | država | 2023. |
| `bruto_dodana_vrijednost` | novac | EUR | EUR po st. | država, županija | 2023. |
| `eu_ugovoreno` | novac | EUR | EUR po st. | država, županija, JLS | 31. 5. 2023. |
| `eu_projekti` | novac | broj | na 1.000 st. | država, županija, JLS | 31. 5. 2023. |
| `hbor_krediti` | novac | EUR | EUR po st. | država, županija | 2018.–2023. |
| `inflacija` | novac | % | — | država | IX. 2026. |
| `saldo_proracuna` | novac | EUR | EUR po st. | država | 2025. |
| `javni_dug` | novac | EUR | EUR po st. | država | VI. 2026. |
| `porez_na_dohodak` | porezi | EUR | EUR po st. | država, županija, JLS | 2025. |
| `kupoprodaje_nekretnina` | imovina | broj | na 1.000 st. | država, županija | 2025. |
| `pravne_osobe_aktivne` | imovina | broj | na 1.000 st. | država | I. 2022. |

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

## Kako se mijenja ovaj format

1. Promjenu predloži u issue-u ili pull requestu i označi ostalu dvojicu.
2. Ako se ključ preimenuje ili ukloni, poveća se `verzija_formata` u `meta.json`.
3. Novi pokazatelj ne mijenja verziju: dovoljno ga je dodati u `pipeline/pokazatelji.py`.
