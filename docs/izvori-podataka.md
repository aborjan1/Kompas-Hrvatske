# Izvori podataka – Kompas Hrvatske

Ova datoteka nastaje automatski iz `data/sources.csv` (`python pipeline/popis_izvora.py`). Ne uređuj je ručno.

Broj skupova: **69**. Skripta `pipeline/download.py` preuzima njih **51**, a ostali se preuzimaju ručno, koriste kao servis izravno na karti ili traže API registraciju.

Mapa u koju se skup sprema je `data/raw/<id>/`.

## 1. Kostur: granice i šifrarnici

| id (mapa) | Skup | Izdavatelj | Formati | Način | Issue | Napomena |
| --- | --- | --- | --- | --- | --- | --- |
| `granice-upravne-jedinice` | [Upravne jedinice INSPIRE (granice države, županija, općina, naselja)](https://data.gov.hr/ckan/dataset/upravne-jedinice-inspire) | Državna geodetska uprava | GML (ZIP) | ručno | #12 | Ručno: https://geoportal.dgu.hr/services/atom/INSPIRE_Administrative_Units_(AU).zip (ATOM https://geoportal.dgu.hr/services/atom/au/xml; poveznica na data.gov.hr je prazna). EPSG:3035. |
| `sifrarnik-jls` | [Popis županija, gradova i općina](https://data.gov.hr/ckan/dataset/popis-zupanija-gradova-i-opcina) | Ministarstvo pravosuđa, uprave i digitalne transformacije | HTML, XLS | skripta | #9 | Osnova za areas.csv |
| `dzs-nkd` | [Nacionalna klasifikacija djelatnosti 2007.](https://data.gov.hr/ckan/dataset/nacionalna-klasifikacija-djelatnosti-2007) | Državni zavod za statistiku | JSON, PDF | skripta | #10 | Grupiranje tvrtki po djelatnosti |
| `sudreg` | [Sudski registar (REST API, uz besplatnu registraciju)](https://data.gov.hr/ckan/dataset/sudski-registar) | Ministarstvo pravosuđa, uprave i digitalne transformacije | API | API (registracija) | #4 | Besplatna registracija na sudreg-data.gov.hr (OAuth) |
| `natural-earth-admin1` | [Natural Earth – Admin 1 States and Provinces (1:10m)](https://www.naturalearthdata.com/) | Natural Earth | GeoJSON | ručno | #6 | Samo probne granice; zamjenjuju se DGU granicama |

## 2. Razina Država

| id (mapa) | Skup | Izdavatelj | Formati | Način | Issue | Napomena |
| --- | --- | --- | --- | --- | --- | --- |
| `dzs-popis2021` | [Statistika u nizu: Popis stanovništva, kućanstava i stanova 2021.  - stanovništvo](https://data.gov.hr/ckan/dataset/statistika-u-nizu-popis-stanovnistva-kucanstava-i-stanova-2021) | Državni zavod za statistiku | XLSX | skripta | #7 | Zamjena za INSPIRE servise stanovništva |
| `dzs-place` | [Statistika u nizu: Zaposlenost i plaće](https://data.gov.hr/ckan/dataset/statistika-u-nizu-zaposlenost-i-pla-e) | Državni zavod za statistiku | XLSX, XLS | skripta | #7 | Provjeriti razinu županija |
| `dzs-bdp` | [Statistika u nizu:  Bruto domaći proizvod](https://data.gov.hr/ckan/dataset/statistika-u-nizu-bruto-doma-i-proizvod) | Državni zavod za statistiku | XLS, XLSX | skripta | #7 | Prazno: od 27. 2. 2026. DZS tromjesečni BDP objavljuje samo u PC-Axis bazi. Koristimo dzs-bdp-regije. |
| `dzs-bdp-regije` | [Bruto domaći proizvod za Republiku Hrvatsku, HR_NUTS 2021. – HR NUTS 2 i županije u 2023. (priopćenje NR-2026-2-1)](https://podaci.dzs.hr/media/mmwmg1dv/nr-2026-2-1-bruto-domaći-proizvod-za-republiku-hrvatsku-hr_nuts-2021-hr-nuts-2-i-županije-u-2023.pdf) | Državni zavod za statistiku | PDF | ručno | #7 | Ručno preuzet PDF (izvan data.gov.hr, izdavatelj DZS). BDP za RH i bruto dodana vrijednost po županijama. |
| `dzs-cijene` | [Statistika u nizu:  Cijene](https://data.gov.hr/ckan/dataset/statistika-u-nizu-cijene) | Državni zavod za statistiku | XLSX | skripta | #7 | Inflacija |
| `dzs-rps` | [Statistika u nizu:  Registar poslovnih subjekata](https://data.gov.hr/ckan/dataset/statistika-u-nizu-registar-poslovnih-subjekata) | Državni zavod za statistiku | XLSX | skripta | #7 |  |
| `hnb-opca-drzava` | [Sektor opće države](https://data.gov.hr/ckan/dataset/op-a-dr-ava) | Hrvatska narodna banka | XLSX | skripta | #7 | Državni proračun: prihodi, rashodi, dug |
| `hnb-bilten` | [Bilten HNB-a – dodatni gospodarski, financijski i monetarni pokazatelji](https://data.gov.hr/ckan/dataset/bilten-hnb-a) | Hrvatska narodna banka | XLSX | skripta | #7 | Krediti |
| `pu-porez-dohodak` | [Porez na dohodak](https://data.gov.hr/ckan/dataset/https-porezna-uprava-gov-hr-hr-porez-na-dohodak-4763-4763) | Porezna uprava | XLSX | skripta | #7 |  |
| `pu-fiskalizacija` | [Fiskalizacija](https://data.gov.hr/ckan/dataset/https-porezna-gov-hr-fiskalizacija-izvjestaji) | Porezna uprava | XLSX | skripta | #8 | NEISPRAVAN: poveznica vodi na web aplikaciju (HTML), ne na tablicu. |
| `eu-opkk-2014-2020` | [Popis operacija financiranih u okviru Programa „Konkurentnost i kohezija 2014.-2020.“](https://data.gov.hr/ckan/dataset/popis-operacija-financiranih-u-okviru-programa-konkurentnost-i-kohezija-2014-2020) | Ministarstvo regionalnoga razvoja i fondova Europske unije  | XLSX | skripta | #7 | Zbrajanje po sjedištu korisnika |
| `eu-pkk-2021-2027` | [Popis operacija – Program Konkurentnost i kohezija 2021.–2027.](https://eufondovi.gov.hr/wp-content/uploads/2026/10/Popis-operacija-PKK-30.9.2026.xlsx) | Ministarstvo regionalnoga razvoja i fondova Europske unije | XLSX | url | #15 | Izvan data.gov.hr: službeni popis operacija (čl. 49. Uredbe (EU) 2021/1060) na eufondovi.gov.hr/popisi-projekata. Kod nove objave promijeniti poveznicu. |
| `eu-itp-2021-2027` | [Popis operacija – Integrirani teritorijalni program 2021.–2027.](https://eufondovi.gov.hr/wp-content/uploads/2026/10/Popis-operacija-ITP-30.9.2026.xlsx) | Ministarstvo regionalnoga razvoja i fondova Europske unije | XLSX | url | #15 | Izvan data.gov.hr: službeni popis operacija (čl. 49. Uredbe (EU) 2021/1060) na eufondovi.gov.hr/popisi-projekata. Kod nove objave promijeniti poveznicu. |
| `eu-uljp-2021-2027` | [Popis operacija – Program Učinkoviti ljudski potencijali 2021.–2027.](https://eufondovi.gov.hr/wp-content/uploads/2026/10/Popis-operacija-u-okviru-PULJP-2021.-2027-final-table_30092026.xlsx) | Ministarstvo regionalnoga razvoja i fondova Europske unije | XLSX | url | #15 | Izvan data.gov.hr: službeni popis operacija (čl. 49. Uredbe (EU) 2021/1060) na eufondovi.gov.hr/popisi-projekata. Kod nove objave promijeniti poveznicu. |
| `srdi-financijska` | [Središnji registar državne imovine – financijska imovina](https://data.gov.hr/ckan/dataset/sredisnji-registar-drzavne-imovine-financijska-imovina) | Ministarstvo pravosuđa, uprave i digitalne transformacije | CSV, JSON, API | API (registracija) | #4 | Državni udjeli u tvrtkama |

## 3. Razina Županija

| id (mapa) | Skup | Izdavatelj | Formati | Način | Issue | Napomena |
| --- | --- | --- | --- | --- | --- | --- |
| `hzz-slobodna-mjesta` | [Slobodna radna mjesta po županijama u Hrvatskoj i u Europskoj uniji](https://data.gov.hr/ckan/dataset/slobodna-radna-mjesta-po-zupanijama-u-rh-i-eu) | Hrvatski zavod za zapošljavanje | XML | skripta | #7 | XML |
| `dzs-poduzeca` | [Statistika u nizu: Poduzeća](https://data.gov.hr/ckan/dataset/statistika-u-nizu-poduzeca) | Državni zavod za statistiku | XLSX | skripta | #7 | Provjeriti razinu županija |
| `dzs-turizam` | [Statistika u nizu:  Turizam](https://data.gov.hr/ckan/dataset/statistika-u-nizu-turizam) | Državni zavod za statistiku | XLSX | skripta | #7 |  |
| `pu-kupoprodaje` | [Pregled broja kupoprodaja nekretnina po stjecateljima po županijama i ukupno za RH od 2016.-2026.](https://data.gov.hr/ckan/dataset/pregled-broja-kupoprodaja-nekretnina-po-stjecateljima-po-zupanijama-i-ukupno-za-rh-od-2016-2026) | Porezna uprava | XLSX | skripta | #7 |  |
| `aik-poslovne-zone` | [Poslovne zone u Republici Hrvatskoj](https://data.gov.hr/ckan/dataset/poslovne-zone-u-republici-hrvatskoj) | Agencija za investicije i konkurentnost (NEAKTIVAN) | HTML, JSON | skripta | #14 | NEISPRAVAN: domena aik-invest.hr je istekla, poveznica vraća oglasnu stranicu. Tražiti zamjenski izvor poslovnih zona. Za Zagreb zamijenjeno skupom zg-planirana-namjena; za ostatak Hrvatske zamjene još nema. |
| `udruge-financiranje` | [Podaci o financiranju udruga](https://data.gov.hr/ckan/dataset/podaci-o-financiranju-udruga) | Ured za udruge | XLS | skripta | #7 | Spaja se s Registrom udruga |
| `registar-udruga` | [Registar udruga Republike Hrvatske](https://data.gov.hr/ckan/dataset/registar-udruga) | Ministarstvo pravosuđa, uprave i digitalne transformacije | HTML, JSON, XML, CSV | skripta | #7 | Sjedište udruge |
| `hbor-rast-razvoj` | [Financijski instrument "ESIF krediti za rast i razvoj"](https://data.gov.hr/ckan/dataset/financijski-instrument-esif-krediti-za-rast-i-razvoj) | Hrvatska banka za obnovu i razvitak | XLSX | skripta | #7 | Korisnici HBOR kredita |
| `hbor-energetska` | [Financijski instrument "ESIF krediti za energetsku učinkovitost"](https://data.gov.hr/ckan/dataset/financijski-instrument-esif-krediti-za-energetsku-ucinkovitost) | Hrvatska banka za obnovu i razvitak | XLSX | skripta | #7 | Korisnici HBOR kredita |
| `hbor-rasvjeta` | [Financijski instrument "ESIF krediti za javnu rasvjetu"](https://data.gov.hr/ckan/dataset/financijski-instrument-esif-krediti-za-javnu-rasvjetu) | Hrvatska banka za obnovu i razvitak | XLSX | skripta | #7 | Korisnici HBOR kredita |
| `hbor-ruralni-investicijski` | [Financijski instrument "Investicijski krediti za ruralni razvoj"](https://data.gov.hr/ckan/dataset/financijski-instrument-investicijski-krediti-za-ruralni-razvoj) | Hrvatska banka za obnovu i razvitak | XLSX | skripta | #7 | Korisnici HBOR kredita |
| `hbor-ruralni-obrtna` | [Financijski instrument "Obrtna sredstva za ruralni razvoj"](https://data.gov.hr/ckan/dataset/financijski-instrument-obrtna-sredstva-za-ruralni-razvoj) | Hrvatska banka za obnovu i razvitak | XLSX | skripta | #7 | Korisnici HBOR kredita |
| `srdi-nekretnine` | [Središnji registar državne imovine – nekretnine](https://data.gov.hr/ckan/dataset/sredisnji-registar-drzavne-imovine-nekretnine) | Ministarstvo pravosuđa, uprave i digitalne transformacije | CSV, JSON, API | API (registracija) | #4 | Zbrojiti po županiji i JLS |
| `popis2021-zupanije` | [Stanovništvo po dobi i spolu po županijama (Popis 2021.) INSPIRE](https://data.gov.hr/ckan/dataset/raspodjela-stanovnitva-prema-dobnim-skupinama-i-spolu-na-razini-upanija-iz-popisa-stanovnitva-2) | Državna geodetska uprava | WFS, WMS | servis (WMS/WFS) | #8 | Samo WFS; koristimo dzs-popis2021 |

## 4. Razina Grad

| id (mapa) | Skup | Izdavatelj | Formati | Način | Issue | Napomena |
| --- | --- | --- | --- | --- | --- | --- |
| `dzs-gradovi-opcine` | [Statistika u nizu:  Gradovi i općine u statistici](https://data.gov.hr/ckan/dataset/statistika-u-nizu-gradovi-u-statistici) | Državni zavod za statistiku | XLSX | skripta | #7 | Samo 128 gradova (bez općina): procjena stanovništva, prirodno kretanje, migracije; kandidat za kasnije. |
| `pu-porezne-stope-jls` | [Usporedba poreznih stopa prema odlukama jedinica lokalne samouprave u Republici Hrvatskoj](https://data.gov.hr/ckan/dataset/https-porezna-uprava-gov-hr-hr-odluke-jls-4009) | Porezna uprava | XLSX | skripta | #14 | Spaja se po službenoj šifri JLS. Stope poreza na dohodak, porez na potrošnju i na nekretnine; paušalni porez (po naseljima) zasad se ne koristi. |
| `komunalni-projekti` | [Financiranje projekata za poticanje razvoja komunalnog gospodarstva i komunalnog standarda](https://data.gov.hr/ckan/dataset/financiranje-projekata-komunalnog-gospodarstva-i-standarda) | Ministarstvo graditeljstva i prostornoga uređenja (NEAKTIVAN) | CSV | skripta | #14 | NEISPRAVAN: datoteke su na staroj domeni www.mgipu.hr koja prekida vezu (2014.–2017.). |
| `turisticki-objekti` | [Popis kategoriziranih turističkih objekata u Republici Hrvatskoj](https://data.gov.hr/ckan/dataset/popis-kategoriziranih-turistickih-objekata) | Ministarstvo turizma i sporta | XLSX | skripta | #14 | Samo zbirni podaci iz 2019. bez adresa; zasad se ne koristi. |
| `popis2021-jls` | [Stanovništvo po dobi i spolu po gradovima/općinama (Popis 2021.) INSPIRE](https://data.gov.hr/ckan/dataset/raspodjela-stanovnitva-prema-dobnim-skupinama-i-spolu-na-razni-gradova-opina-iz-popisa-stanovni) | Državna geodetska uprava | WFS, WMS | servis (WMS/WFS) | #8 | Samo WFS; koristimo dzs-popis2021 |

## 5. Gradski prikaz: Zagreb

| id (mapa) | Skup | Izdavatelj | Formati | Način | Issue | Napomena |
| --- | --- | --- | --- | --- | --- | --- |
| `dgu-adrese` | [Adrese INSPIRE (kućni brojevi cijele Hrvatske)](https://geoportal.dgu.hr/services/atom/INSPIRE_Addresses_(AD).zip) | Državna geodetska uprava | GML (ZIP) | url | #16 | ATOM https://geoportal.dgu.hr/services/atom/ad/xml (skup "adrese" na data.gov.hr). EPSG:3035, 84 MB. Adrese praznih prostora Zagreba i prostora u zakupu Rijeke u točke. |
| `dgu-ortofoto-2024` | [Digitalni ortofoto 1:5000 2024. (+ 2011.–2023., LIDAR 2022./23., 1:500 i 1:1000 – zasebni skupovi)](https://data.gov.hr/ckan/dataset/digitalni-ortofoto-u-mjerilu-1-5000-2024-godina) | Državna geodetska uprava | WMS, WMTS | servis (WMS/WFS) | #16 | WMTS: karta ga učitava uživo, ne preuzima se |
| `zg3d` | [ZG3D 2022 – 3D model Grada Zagreba (+ 17 gradskih četvrti)](https://data.gov.hr/ckan/dataset/zg3d-2022-3d-model-gz) | Grad Zagreb | CSV, GeoJSON, XLSX, FGDB | ručno | #17 | Zamijenjeno skupovima po četvrtima (zg3d-donji-grad, zg3d-gornji-grad, zg3d-trnje). |
| `zg3d-donji-grad` | [ZG3D Gradska četvrt Donji Grad 2022](https://data.gov.hr/ckan/dataset/zg3d-gradska-cetvrt-donji-grad-2022) | Grad Zagreb | GeoJSON | skripta | #17 | 3D zgrade (LoD 2.2) za 3D prikaz središta Zagreba; koristi se GeoJSON (visina = Z_Delta). |
| `zg3d-gornji-grad` | [ZG3D Gradska četvrt Gornji Grad 2022](https://data.gov.hr/ckan/dataset/zg3d-gradska-cetvrt-gornji-grad-2022) | Grad Zagreb | GeoJSON | skripta | #17 | 3D zgrade (LoD 2.2) za 3D prikaz središta Zagreba; koristi se GeoJSON (visina = Z_Delta). |
| `zg3d-trnje` | [ZG3D Gradska četvrt Trnje 2022](https://data.gov.hr/ckan/dataset/zg3d-gradska-cetvrt-trnje-2022) | Grad Zagreb | GeoJSON | skripta | #17 | 3D zgrade (LoD 2.2) za 3D prikaz središta Zagreba; koristi se GeoJSON (visina = Z_Delta). |
| `zg-cetvrti` | [Gradske četvrti - prostorna jedinica mjesne samouprave za područje Grada Zagreba](https://data.gov.hr/ckan/dataset/gradske-cetvrti-prostorna-jedinica-mjesne-samouprave-za-podrucje-grada-zagreba) | Grad Zagreb | SHP | skripta | #16 | 17 četvrti sa šiframa RPJ (EPSG:3765). Osnova za prikaz Zagreba. |
| `zg-planirana-namjena` | [Geoportal planirana namjena 2023](https://data.gov.hr/ckan/dataset/geoportal-planirana-namjena-2023) | Grad Zagreb | CSV, SHP, GeoJSON, KML | skripta | #14 | Gospodarske zone (553 površine, 2.384 ha) i neizgrađene gospodarske zone po četvrtima. GeoJSON 35 MB. |
| `zg-stvarno-koristenje` | [Stvarno korištenje površina 2020.](https://data.gov.hr/ckan/dataset/stvarno-koristenje-povrsina-2020) | Grad Zagreb | CSV, XLSX | skripta | #16 | Hektari po četvrti (IME_GC): brownfield, udio gospodarskih, stambenih i zelenih površina. |
| `zg-smjestajni-objekti` | [Geoportal Smještajni objekti](https://data.gov.hr/ckan/dataset/geoportal-smjestajni-objekti) | Grad Zagreb | CSV, SHP, GeoJSON, KML | skripta | #16 | 2.702 točke (hoteli, hosteli, domaćinstva). |
| `zg-trgovacka-drustva` | [Geoportal gradska trgovačka društva](https://data.gov.hr/ckan/dataset/geoportal-gradska-trgovacka-drustva) | Grad Zagreb | CSV, KML, SHP, GeoJSON | skripta | #16 |  |
| `zg-trznice` | [Geoportal gradske tržnice](https://data.gov.hr/ckan/dataset/geoportal-gradske-trznice) | Grad Zagreb | CSV, KML, SHP, GeoJSON | skripta | #16 |  |
| `zg-brownfield` | [Brownfield površine](https://data.gov.hr/ckan/dataset/brownfield-povrsine) | Grad Zagreb | CSV, KML, SHP, GeoJSON | skripta | #16 |  |
| `zg-kapitalna-2023` | [Kapitalna ulaganja 2023](https://data.gov.hr/ckan/dataset/kapitalna-ulaganja-2023) | Grad Zagreb | CSV, KML, SHP, GeoJSON | skripta | #16 | Točke s planiranim iznosom; 2 bez koordinata. |
| `zg-kapitalna-2024` | [Kapitalna ulaganja 2024.](https://data.gov.hr/ckan/dataset/kapitalna-ulaganja-2024) | Grad Zagreb | CSV, SHP, GeoJSON, KML | skripta | #16 | Točke s planiranim iznosom; 4 bez koordinata. Pokazatelj po četvrtima. |
| `zg-prometnice` | [Izgrađene prometnice u Gradu Zagrebu](https://data.gov.hr/ckan/dataset/izgradene-ceste-u-gradu-zagrebu) | Grad Zagreb | XLSX, CSV | skripta | #16 | Popis cesta bez koordinata; ne koristi se. |
| `zg-eu-projekti` | [Projekti Europske Unije u provedbi](https://data.gov.hr/ckan/dataset/projekti-europske-unije) | Grad Zagreb | CSV, XLSX | skripta | #16 | 299 projekata Grada i ustanova; bez lokacije. |
| `zg-vrtici-skole` | [Dječji vrtići, osnovne i srednje škole Grada Zagreba INSPIRE](https://data.gov.hr/ckan/dataset/djeji-vrtii-osnovne-i-srednje-kole-grada-zagreba-inspire) | Državna geodetska uprava | WFS, WMS | servis (WMS/WFS) | #16 | WFS: za priču o vrtićima |
| `zg-prazni-prostori` | [Prazni poslovni prostori](https://data.gov.hr/ckan/dataset/prazni-poslovni-prostori) | Grad Zagreb | XLSX, CSV | skripta | #16 | Tablice 2024. imaju stupac GRADSKA ČETVRT; spaja se po nazivu. Adrese bez koordinata. |
| `zg-zakup-prostora` | [Registar ugovora o zakupu / korištenju poslovnih prostora](https://data.gov.hr/ckan/dataset/registar-ugovora-o-zakupu-koristenju-poslovnih-prostora) | Grad Zagreb | XLSX, CSV | skripta | #16 | Adrese bez četvrti i koordinata; ne koristi se. |
| `zg-zakup-zemljista` | [Ugovori o zakupu zemljišta](https://data.gov.hr/ckan/dataset/ugovori-o-zakupu-zemljista-2022) | Grad Zagreb | XLSX, CSV | skripta | #16 | Mali broj ugovora; ne koristi se. |
| `zg-proracun-2026` | [Proračun Grada Zagreba 2026.](https://data.gov.hr/ckan/dataset/proracun-grada-zagreba-2026) | Grad Zagreb | XLSX, CSV | skripta | #16 | Konsolidirani plan; rashodi po funkcijskoj klasifikaciji (OznakaPodskupine). |
| `zg-proracun-2022-2025` | [Proračun Grada Zagreba 2022. - 2025.](https://data.gov.hr/ckan/dataset/proracun) | Grad Zagreb | XLSX, CSV | skripta | #16 | Starije verzije proračuna; zasad se koristi samo zg-proracun-2026. |

## 6. Gradski prikaz: Rijeka

| id (mapa) | Skup | Izdavatelj | Formati | Način | Issue | Napomena |
| --- | --- | --- | --- | --- | --- | --- |
| `ri-proracun` | [Proračun Grada Rijeke na 4.razini i Izvršenja na 5.razini konta](https://data.gov.hr/ckan/dataset/proracun-grada-rijeke-na-4-razini-konta) | Grad Rijeka | XLS, XLSX | skripta | #16 | Plan 2025. (funkcijska i ekonomska klasifikacija); 35 datoteka od 2015. |
| `ri-slobodni-prostori` | [Poslovni prostori Grada Rijeke - SLOBODNI](https://data.gov.hr/ckan/dataset/https-e-usluge3-rijeka-hr-apex-f-p-150-7) | Grad Rijeka | HTML, JSON | skripta | #16 | NEISPRAVAN: e-usluge3.rijeka.hr ima nepotpun SSL certifikat (preuzimanje odbijeno). |
| `ri-prostori-zakup` | [Poslovni prostori Grada Rijeke - U ZAKUPU](https://data.gov.hr/ckan/dataset/poslovni-prostori-u-zakupu) | Grad Rijeka | JSON, CSV | skripta | #16 | 1.296 prostora s adresom, zonom, površinom i cijenom; bez koordinata. |
| `ri-eu-projekti` | [EU projekti u kojima je nositelj ili partner Grad Rijeka](https://data.gov.hr/ckan/dataset/eu-projekti-od-2013-godine) | Grad Rijeka | CSV | skripta | #16 | 16 projekata u slobodnom tekstu; iznosi u kunama preračunati u EUR. |
| `ri-subvencije` | [Subvencije poduzetnicima Grada Rijeke - Lista korisnika](https://data.gov.hr/ckan/dataset/subvencije-poduzetnicima-grada-rijeke-lista-korisnika) | Grad Rijeka | XLS, CSV | skripta | #16 | NEISPRAVAN: datoteke na data.rijeka.hr vraćaju 404. |
| `ri-prihodi-poduzetnika` | [Prihodi poslovanja poduzetnika prema djelatnostima](https://data.gov.hr/ckan/dataset/prihodi-poslovanja-poduzetnika-prema-djelatnostima) | Grad Rijeka | XLS | skripta | #16 | Samo do 2018.; ne koristi se. |
| `ri-gis` | [GIS Grada Rijeke](https://data.gov.hr/ckan/dataset/gis-grad-rijeka) | Grad Rijeka | WMS | servis (WMS/WFS) | #16 | WMS servis |

## Izvori izvan data.gov.hr

| Izvor | Izdavatelj | Napomena |
| --- | --- | --- |
| [Upit o trošenju sredstava državnog proračuna](https://www.drzavna-riznica.hr/trosenje_sredstava_DP/Pretraga/OpcaPretraga) | Ministarstvo financija | Isplate iz državnog proračuna po primatelju |
| [Sudski registar – portal za razvojne programere](https://sudreg-data.gov.hr/) | MPUDT | REST API, besplatna registracija |
| [SRDI – javni API](https://srdi.gov.hr/api/docs) | MPUDT | Državna imovina, API dokumentacija |
| [DZS – statističke baze i publikacije](https://podaci.dzs.hr/hr/) | DZS | Ako neka tablica fali u „Statistici u nizu” |
| [Geoportal DGU](https://geoportal.dgu.hr/) | Državna geodetska uprava | Preglednik i servisi prostornih podataka |
| [Portal otvorenih podataka Grada Zagreba](https://data.zagreb.hr/) | Grad Zagreb | Izvorni portal za skupove Grada Zagreba |

## Pretrage lokalnih skupova

Stotine skupova općina i gradova u različitim formatima. Za demo ih ne obrađujemo sve, nego samo po potrebi.

- [Proračuni općina, gradova i županija](https://data.gov.hr/ckan/dataset?q=prora%C4%8Dun)
- [Financijski izvještaji JLS](https://data.gov.hr/ckan/dataset?q=financijski+izvje%C5%A1taj)
- [Isplate iz proračuna (iTransparentnost)](https://data.gov.hr/ckan/dataset?q=isplate)
- [Poslovni prostori i zakupnine](https://data.gov.hr/ckan/dataset?q=poslovni+prostor)

## Što nije u katalogu

- EU sredstva 2021.–2027. i NPOO: izvor tek treba pronaći (issue #15).
