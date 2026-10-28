# Provjera preuzetih skupova (faze 1–6)

Stanje: 27. 10. 2026., nakon `python pipeline/download.py --faza 1,2,3`.

Od 24 skupa preuzeta su 23. Za prvi demo koristimo **14**, dva su **neispravna na izvoru**,
a ostali su preuzeti, ali se zasad ne koriste (stari, samo na razini države ili bez veze
s područjem). BDP je naknadno uzet iz PDF priopćenja DZS-a (vidi dolje).

## Što koristimo

| Skup (mapa) | Datoteka i list | Razina | Razdoblje | Pokazatelj |
| --- | --- | --- | --- | --- |
| `sifrarnik-jls` | `…opcine_gradovi_RH.xls` | JLS | – | šifrarnik: 556 JLS i njihove županije |
| `dzs-popis2021` | `…po_gradovima_opcinama.xlsx`, tab. 6. | država, županija, JLS | 2021. | stanovništvo, prosječna starost |
| `dzs-popis2021` | `…zbirni_pregledi.xlsx`, tab. 1. | država, županija | 2021. | površina → gustoća naseljenosti |
| `dzs-place` | `…pregled-po-zupanijama.xlsx`, 9.4.9. NKD 2025. | država, županija | 2025. | prosječna neto plaća |
| `dzs-place` | isto, 9.4.8. | država, županija | 2024. | zaposleni |
| `dzs-place` | isto, 9.4.14. | država, županija | lipanj 2026. | stopa registrirane nezaposlenosti |
| `pu-porez-dohodak` | `pk_neto-dohodak…2022_2025….xlsx`, list „2025 EUR” | država, županija, **JLS** | 2025. | neto dohodak, uplaćeni porez na dohodak |
| `pu-kupoprodaje` | `pk_ppn_pregled…po-upanijama….xlsx` | država, županija | 2025. | kupoprodaje nekretnina |
| `eu-opkk-2014-2020` | `popis-operacija-opkk-31.5.2023.xlsx`, „CUT OFF 31.05.2023” | država, županija, **točke** | presjek 31. 5. 2023. | ugovorena EU sredstva, broj projekata, karta projekata |
| `hbor-*` (5 skupova) | po jedna tablica korisnika | država, županija | 2018.–2023. | HBOR krediti iz EU fondova |
| `dzs-bdp-regije` | priopćenje NR-2026-2-1 (PDF), tablice 1. i 2. | država; županija | 2023. | BDP (država), bruto dodana vrijednost (županije) |
| `granice-upravne-jedinice` | `INSPIRE_Administrative_Units_(AU).zip` (GML, 600 MB) | županija, JLS | stanje 25. 10. 2026. | granice za kartu, službene šifre JLS, EU projekti po JLS |
| `hnb-bilten` | list „Slika 5.4.” | država | rujan 2026. | inflacija (HIPC) |
| `hnb-opca-drzava` | tablica I2 | država | 2025. | saldo opće države |
| `hnb-opca-drzava` | tablica I3 | država | lipanj 2026. | dug opće države |
| `dzs-rps` | `MSI_REGISTAR.xlsx`, 11.1.1. | država | siječanj 2022. | aktivne pravne osobe |

Najvrjedniji je skup Porezne uprave o neto dohotku: jedini daje novčani podatak za **svih
556 gradova i općina**, pa razina Grad nije prazna.

## Neispravni izvori

| Skup | Problem | Prijedlog |
| --- | --- | --- |
| `aik-poslovne-zone` | Domena aik-invest.hr je istekla; poveznica vraća oglasnu stranicu, ne JSON | Tražiti zamjenski izvor poslovnih zona (npr. registar poduzetničke infrastrukture) |
| `pu-fiskalizacija` | Poveznica vodi na web aplikaciju, ne na tablicu | Ne koristiti |
| `dzs-bdp` | Skup premješten na portalu, a preuzeta tablica je prazna: od 27. 2. 2026. DZS BDP objavljuje samo u PC-Axis bazi; tablica BDP-a po županijama vraća 404 | Zamijenjeno ručno preuzetim priopćenjem DZS-a (`dzs-bdp-regije`) |

Sva tri skupa su u `sources.csv` označena s `aktivno = ne`.

## Preuzeto, ali se zasad ne koristi

| Skup | Zašto |
| --- | --- |
| `dzs-cijene` | Indeksi potrošačkih cijena premješteni su u drugu publikaciju; inflaciju uzimamo iz Biltena HNB-a |
| `dzs-poduzeca`, `dzs-rps` (ostali listovi) | Samo razina države, po djelatnostima |
| `dzs-turizam` | Noćenja po županijama postoje samo do 2021. (godina pandemije) |
| `hzz-slobodna-mjesta` | RSS s oglasima (npr. 173 za Zagrebačku); nije ukupan broj slobodnih mjesta |
| `udruge-financiranje` | Podaci samo za 2013.–2016. |
| `registar-udruga` | Isti podaci u tri formata (oko 550 MB); trebat će tek za sjedišta udruga |
| `dzs-nkd` | Šifrarnik djelatnosti; trebat će uz Sudski registar |
| `hnb-opca-drzava` (G8a, G8b) | Kamatne stope; nisu u planu |

## Granice (DGU)

- Poveznica na ATOM uslugu na data.gov.hr je **prazna**; ispravna adresa je https://geoportal.dgu.hr/services/atom/au/xml.
- Zaglavlje GML-a tvrdi da sadrži 10.000 od 50.194 jedinica, ali stvarno sadrži svih 50.194 (21 županija, 556 JLS, 6.759 naselja, statistički i popisni krugovi).
- Koordinate su u EPSG:3035 s redoslijedom osi sjever–istok; obrada ih okreće.
- Svih 556 gradova i općina iz DGU-a spojeno je sa šifrarnikom po nazivu; time JLS imaju službene šifre.
- ATOM usluga navodi „ograničenje javnog pristupa prema čl. 13. st. 1. t. (e) INSPIRE Direktive”, a data.gov.hr isti skup vodi pod Otvorenom dozvolom. **Prije predaje provjeriti uvjete korištenja s DGU-om.**
- EU projekti raspoređeni po JLS prema koordinatama: 54 od 8.355 točaka leži u drugoj županiji od one upisane u izvoru, a 11 izvan kopna.

## Faza 4 (razina Grad)

| Skup | Stanje |
| --- | --- |
| `pu-porezne-stope-jls` | ✔ Koristi se. Tablice imaju **službenu šifru JLS**, pa se spajaju izravno (556/556). Niža stopa 15–23 %, viša 25–33 %. Porez na potrošnju i nekretnine: kod raspona („3,00 do 5,00”) uzima se najviši iznos. Paušalni porez je po naseljima, pa se zasad ne koristi. |
| `dzs-gradovi-opcine` | Preuzeto; samo 128 gradova (bez općina). Kandidat za procjenu stanovništva i prirodno kretanje. |
| `turisticki-objekti` | Preuzeto; samo zbirni podaci iz 2019., bez adresa. Ne koristi se. |
| `komunalni-projekti` | **Neispravan**: datoteke su na staroj domeni www.mgipu.hr, koja prekida vezu. |

## Faze 5 i 6 (Zagreb i Rijeka)

Stanje: 28. 10. 2026., nakon `python pipeline/download.py --faza 5,6` (20 od 22 skupa).

| Skup | Stanje |
| --- | --- |
| `zg-cetvrti` | ✔ 17 četvrti sa službenim šiframa; EPSG:3765 → WGS84. Osnova prikaza Zagreba. |
| `zg-stvarno-koristenje` | ✔ 33.497 površina s nazivom četvrti; zbroj po četvrti odgovara površini poligona (razlika najviše 0,5 %). |
| `zg-kapitalna-2023`, `zg-kapitalna-2024` | ✔ Točke s planiranim iznosom. 2 i 4 projekta nemaju koordinate („Ostali školski objekti” i sl.), pa nisu na karti (0,9 % iznosa 2024.). |
| `zg-smjestajni-objekti` | ✔ 2.702 točke, stanje 2023. |
| `zg-prazni-prostori` | ✔ Tablice 2024. imaju naziv četvrti, pa se spajaju po nazivu (sve 17 prepoznato). Bez koordinata. |
| `zg-brownfield`, `zg-trznice`, `zg-trgovacka-drustva` | ✔ Slojevi na karti. 2 gradska društva imaju sjedište izvan Zagreba. |
| `zg-eu-projekti` | ✔ 299 projekata (437 mil. EUR bespovratno), bez lokacije. Nazivi programa pisani na više načina („Erasmus+”, „Erasmus +”), pa se grupiraju u skupine. |
| `zg-proracun-2026` | ✔ Konsolidirani plan; rashodi (razredi 3 i 4) po funkcijskoj klasifikaciji = 3,08 mlrd. EUR. |
| `ri-proracun` | ✔ Plan 2025.; zbroj funkcija = „UKUPNO RASHODI” (220,9 mil. EUR). |
| `ri-prostori-zakup` | ✔ 1.296 prostora; zbrojeno po zoni zakupnine i području djelatnosti (NKD). Bez koordinata. |
| `ri-eu-projekti` | ✔ 16 projekata u slobodnom tekstu (ne u tablici); dva iznosa u kunama preračunata u EUR. |
| `zg-planirana-namjena` | ✔ 8.999 površina bez preklapanja pokriva cijeli Grad (64.124 ha). Uzete su 553 gospodarske površine (2.384 ha). Izgrađenost navode samo neki planovi: 237 ha izričito „neizgrađeno” ili „planirano” (PPGZ, Sesvetski Kraljevec), za ostale nije poznata. Zona se pripisuje četvrti prema točki unutar poligona. |
| `zg-prometnice`, `zg-zakup-prostora`, `zg-zakup-zemljista`, `zg-proracun-2022-2025`, `ri-prihodi-poduzetnika` | Preuzeto, ne koristi se (bez lokacije, stariji ili premali). |
| `ri-slobodni-prostori` | **Neispravan**: poslužitelj e-usluge3.rijeka.hr ima nepotpun SSL certifikat. |
| `ri-subvencije` | **Neispravan**: datoteke na data.rijeka.hr vraćaju 404. |

**Usporedba proračuna:** Grad Zagreb je ujedno i županija, pa njegov proračun
uključuje bolnice, srednje škole i domove za starije. Zdravstvo po stanovniku je u Zagrebu
455 EUR, a u Rijeci 35 EUR. Ta se napomena izvozi uz podatke.

## EU 2021.–2027. (#15)

Stanje: 28. 10. 2026. Popisi operacija nisu na data.gov.hr, nego na
[eufondovi.gov.hr/popisi-projekata](https://eufondovi.gov.hr/popisi-projekata/)
(Ministarstvo regionalnoga razvoja i fondova EU). `download.py` ih preuzima izravno
(`nacin = url` u `sources.csv`). Kod nove tromjesečne objave treba zamijeniti poveznicu.

| Skup | Operacija | EU sredstva | Napomena |
| --- | --- | --- | --- |
| `eu-pkk-2021-2027` | 1.861 | 4,36 mlrd. EUR | Datoteka ima list za svaki presjek; čita se najnoviji (30. 9. 2026.). Lokacija projekta po županijama s udjelima. |
| `eu-itp-2021-2027` | 351 | 1,05 mlrd. EUR | Isti oblik kao PKK. |
| `eu-uljp-2021-2027` | 1.505 | 1,72 mlrd. EUR | Drugačiji oblik: samo sjedište korisnika (grad, županija, koordinate). |

- **Državni projekti:** 66 operacija (1,74 mlrd. EUR) nemaju lokaciju ili ih provode
  ministarstva, HZZ i državne agencije (popis u `citaci.DRZAVNA_TIJELA`). Ulaze samo u zbroj
  države; inače bi Grad Zagreb „dobio” npr. 566 mil. EUR HZZ-ovih mjera zapošljavanja.
- **Udjeli lokacija:** kod 32 mala PKK projekta (ukupno 2,5 mil. EUR) navedeni udjeli ne daju
  100 % (npr. samo „Grad Zagreb (50.00%)”); iznos se dijeli razmjerno navedenim udjelima.
- **Gradovi i općine:** prema sjedištu korisnika, samo za projekte koji se provode u županiji
  sjedišta. 5 projekata (8,5 mil. EUR) ima naselje umjesto grada ili općine („Rokovci
  Andrijaševci”, „Sigetec Ludbreški”) ili grad koji ne pripada upisanoj županiji.
- Provjera: zbroj županija + državni projekti = ukupno za državu (do 1 EUR).

## Greške u izvorima koje obrada ispravlja

Sve su ispravljene u kodu, a ne ručno u datotekama, pa se popravak ponavlja pri svakom pokretanju.

- **Popis 2021., tab. 6.:** redak Varaždinske županije ima pogrešno upisano „Općina” u stupcu vrste.
- **Natural Earth (rezervne probne granice):** Požeško-slavonska ima šifru Brodsko-posavske (HR-12).
- **Nazivi županija:** „Varažinska”, „BJELOVARSKO-BILOGORSKA ŽUAPNIJA”, „DUBROVAČKO NERETVANSKA” (bez crtice).
- **Nazivi općina:** Porezna uprava piše „KAŠTELIR LABINCI CASTELLIERE S D”; šifrarnik „Kaštelir-Labinci – Castelliere-S. Domenica”.

## Odluke i pretpostavke

- **BDP:** po županijama DZS objavljuje samo bruto dodanu vrijednost (BDP bez poreza na proizvode minus subvencije). Na razini države prikazujemo BDP, a na razini županija bruto dodanu vrijednost.

- **Plaće:** do 2023. DZS ih objavljuje iz istraživanja RAD-1G, a od 2024. iz JOPPD-a (list 9.4.9.). Serije nisu usporedive, pa koristimo samo 2025.
- **Zaposleni:** koristimo 2024., a ne 2025. U 2025. serija ima lom: Grad Zagreb pada s 472.598 na 377.586, a Zagrebačka raste za 32 %.
- **HBOR krediti:** tablice ne navode valutu. Pretpostavljamo da su tablice objavljene prije 2023. u kunama (preračun 7,53450) i da su one iz 2023. u eurima. **Treba provjeriti na stranicama HBOR-a.**
- **EU projekti:** 10 projekata (726 mil. EUR) nema županiju; ulaze samo u zbroj države. Ukupna ugovorena ESIF sredstva (9,34 mlrd. EUR) premašuju alokaciju programa jer se ugovaralo više od 100 %.
- **Po stanovniku:** svi pokazatelji dijele se sa stanovništvom iz Popisa 2021., jer novijih podataka po JLS nema.
- **Licence:** portal za dio skupova ne navodi licencu (npr. `dzs-place`). Prije predaje treba ih provjeriti na stranici skupa.

## Provjere u `build.py`

| Provjera | Rezultat |
| --- | --- |
| 21 županija, 556 JLS, 128 gradova | ✔ |
| Zbroj stanovnika JLS = županija = država (3.871.833) | ✔ |
| Zbroj županija = država: zaposleni, kupoprodaje, neto dohodak, porez, HBOR | ✔ (razlika 0,00 %) |
| Zbroj županija = država: bruto dodana vrijednost | ✔ (66.252 ↔ 66.251 mil. EUR, zaokruživanje) |
| Zbroj JLS = županija: neto dohodak, porez | ✔ (razlika 0,00 %) |
| Svih 556 JLS spojeno s podacima Porezne uprave | ✔ |
| EU projekti s ispravnim koordinatama | 8.355 od 8.365 |
