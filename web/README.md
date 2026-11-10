# Kompas Hrvatske – web

Vite + Svelte aplikacija s Mapbox GL JS kartom.

```powershell
cd web
npm install
npm run dev      # http://localhost:5173
npm run build    # izlaz u web/dist/
npm run preview  # http://localhost:4173, objavljena verzija (s predmemorijom karte)
```

Podloga karte je Mapbox Outdoors (besplatno 50.000 učitavanja karte mjesečno).
Javni token s [account.mapbox.com](https://account.mapbox.com/access-tokens/), ograničen na
`http://localhost:5173` i `http://localhost:4173`, upiši u `web/.env.local` (ne ide u git),
po uzoru na `web/.env.example`:

```powershell
Copy-Item .env.example .env.local   # pa u .env.local upiši VITE_MAPBOX_TOKEN=...
```

Objava (GitHub Pages) koristi drugi token, ograničen na `https://aborjan1.github.io`, iz
GitHub tajne `VITE_MAPBOX_TOKEN` (`.github/workflows/pages.yaml`).

**Prije prezentacije:** `npm run build`, `npm run preview` pa otvori
`http://localhost:4173/?zagrij`. Karta skine cijelu Hrvatsku (~40 MB, 20–30 s) u predmemoriju
preglednika na 30 dana, pa se tijekom prezentacije ništa ne čeka s interneta.

## Struktura

- `src/map/` – karta (Mapbox slojevi i kamera). Neovisno o frameworku: UI poziva samo `createMap(container)`. Opis: [docs/karta.md](../docs/karta.md).
  - `config.js` – podloga (Mapbox Outdoors), uvodni let, granice Hrvatske, raspon zuma
  - `createMap.js` – stvara kartu (globus, oznake na hrvatskom, ograničenje kamere)
  - `odzumiravanje.js` – gumbi „+” i „−” s hrvatskim nazivima i izlazak razinu više: kad se županija ili grad odzumira ispod svog okvira (pinch, touchpad, kotačić, „−”), karta prijeđe na županiju ili Hrvatsku
  - `labels.js` – skriva nazive mjesta i zanimljivosti izvan Hrvatske
  - `warmUp.js` – zagrijavanje za prezentaciju (`?zagrij`)
  - `cityLayers.js` – gradski prikaz Zagreba i Rijeke: satelit i slojevi 4 filtra (ekonomska područja, poslovne zone, javna ulaganja, gradska imovina) iz `public/data/gradovi/`
  - `countyLayer.js` – choropleth županija: `createCountyLayer(map, geojson).setValues({ [sifra]: broj })`, 5 kvantilnih razreda
  - `legend.js` – legenda kao MapLibre kontrola
  - `hover.js` – isticanje granice i oblačić za bilo koji sloj poligona (`addHoverTooltip`)
  - `euLayer.js` – krugovi EU projekata, jedan po gradu ili općini, površina prema iznosu iz EU
  - `MapView.svelte` – tanki Svelte omotač: granice iz `public/data/zupanije.geojson`, boje iz storea `indicator` (`src/data/indicator.js`)
- `src/state.js` – zajedničko stanje (vidi dolje)
- `src/jezik.js` – jezik sučelja (hrvatski ili engleski): `t('Grafovi', 'Charts')`, lokalni format brojeva, `lang=en` u linku; izbor se pamti u pregledniku, a nikad se ne pogađa iz jezika preglednika. Paneli se pri promjeni jezika iscrtaju iznova (`App.svelte`), karta prati jezik sama (nazivi mjesta `name_en`, legenda, oblačići)
- `src/url.js` – stanje u URL-u: svaki pogled ima svoj link, Natrag i Naprijed rade (vidi dolje)
- `src/data/` – učitavanje podataka i pokazatelji
  - `podaci.js` – učitava `meta`, `drzava` i `zupanije` na startu, `jls.json` tek nakon izlaska s razine države
  - `teme.js` – koji pokazatelji pripadaju kojoj temi (karta i info panel)
  - `indicator.js` – pretvara razinu, temu i mjeru u brojke po šifri za kartu
  - `format.js` – formatiranje brojeva prema `jedinica` i `decimale` iz `meta.json`
  - `euProjekti.js` – EU projekti (2014.–2020.) zbrojeni po gradu ili općini, učitavaju se tek kad se uključi gumb „EU projekti”
  - `gradskiPrikaz.js` – koji grad ima koje filtre i koji su uključeni; gradski prikaz se otvara sam kad se odabere Zagreb ili Rijeka
  - `recenice.js` – rečenica info panela za svaku temu i razinu, od stvarnih brojeva; dio bez podatka se izostavlja (posebni predlošci za engleski)
  - `prijevod.js` – engleski tekstovi podataka iz `en.json` (nazivi i objašnjenja pokazatelja, županije, nizovi, funkcije proračuna, EU pozivi); učitavaju se tek kad se odabere EN i stavljaju se preko hrvatskih u storeovima `podaci`, `nizovi`, `proracuni`, `nabava` i `euPozivi`
  - `grafovi.js` – koje kartice s grafovima područje ima za temu; po tome se prikazuju desni stupac i kartica Grafovi
- `src/panels/` – paneli: putanja, info panel u karticama, teme i prekidač ukupno / po stanovniku; na širokom i položenom ekranu u stupcima koji se zatvaraju, a inače ladica odozdo (`src/raspored.css`, `ekran.js`)
  - `Kartice.svelte` – red kartica s tipkovnicom: u info panelu (Pregled, Usporedba, Grafovi, Priče) i među grafovima
  - `GrafUsporedbe.svelte` – u profilu županije: položaj među svih 21 županija (Chart.js), klik na stupac odabire županiju
  - `UsporedbaSlicnih.svelte` – u profilu grada ili općine: usporedba s 5 najsličnijih po broju stanovnika (`slicni` iz `jls.json`), klik odabire taj grad
  - `GrafStupci.svelte` – zajednički vodoravni stupčasti graf (Chart.js) za obje usporedbe
  - `IzvorPodatka.svelte` – izvor, godina i poveznica pokazatelja kojim je karta obojana, ispod tema
  - `Pretraga.svelte` – pretraga županija, gradova i općina (Fuse.js), radi i bez kvačica; logika u `src/data/pretraga.js`
  - `JezikGumb.svelte` – prekidač HR / EN pokraj pretrage
  - `PopisPrica.svelte` i `PricaKartica.svelte` – popis priča (u panelu za Hrvatsku) i priča preko cijelog ekrana: naslov, oblačić s rečenicom scene i kontrole s koracima
  - `EuProjektiPopis.svelte` – broj, iznos i 5 najvećih EU projekata odabranog grada, dok je sloj uključen
  - `GradskiFiltri.svelte` – gumbi za 4 filtra gradskog prikaza u profilu Zagreba ili Rijeke
  - `GrafVeza.svelte` – tema Nabava: graf veza (dobavljači i drugi gradovi i općine s istim dobavljačem) i popis dobavljača iz `nabava.json` (`src/data/nabava.js`)
  - `EuPozivi.svelte` – tema Novac: planirani i otvoreni EU pozivi za grad, općinu ili županiju i usporedba EU novca sa sličnima (`eu-pozivi.json`, `src/data/euPozivi.js`)
  - `GrafoviPanel.svelte` – desni stupac s grafovima za županiju, grad ili općinu, od 1100 px širine i 501 px visine
  - `GrafoviKartice.svelte` – grafovi teme u karticama (EU pozivi, Kamo ide novac, Kroz godine; Veze, Kroz godine), isti u desnom stupcu i u kartici Grafovi info panela
  - `TipOpcine.svelte` – u profilu grada ili općine: tip iz tipologije (strojno učenje, `pipeline/tipologija.py`) s objašnjenjem i 5 najsličnijih po profilu
  - `KamoIdeNovac.svelte` i `ProracunKrozGodine.svelte` – rashodi po namjeni (COFOG) i prihodi, rashodi i ulaganja 2019.–2025. iz `proracuni.json` (`src/data/proracuni.js`)
- `src/stories/` – priče (vidi dolje): `price.json` (scene), `scene.js` (scena → pogled i tekst), `player.js` (reprodukcija)
- `public/data/` – gotove GeoJSON/JSON datoteke iz `pipeline/` (format: `docs/format-podataka.md`)

## Zajedničko stanje (`src/state.js`)

Karta i paneli nikad ne zovu jedni druge. Oboje čitaju store `view`, a mijenjaju ga samo preko pomoćnih funkcija. Vrijednosti su iste kao u URL-u (`#/zupanija/05?tema=novac&mjera=po-stanovniku`, za JLS `#/jls/<sifra>`).

| Polje      | Vrijednosti                                | Početno    |
| ---------- | ------------------------------------------ | ---------- |
| `razina`   | `'drzava'` · `'zupanija'` · `'jls'`        | `'drzava'` |
| `podrucje` | šifra kao string (`'05'`), `null` za državu | `null`     |
| `tema`     | `'ljudi'` · `'novac'` · `'porezi'` · `'imovina'` | `'novac'`  |
| `mjera`    | `'ukupno'` · `'po-stanovniku'`             | `'ukupno'` |

| Funkcija                        | Tko je zove                                                        |
| ------------------------------- | ------------------------------------------------------------------ |
| `selectArea(razina, podrucje)`  | karta na klik, pretraga na odabir, putanja (`selectArea('drzava')`) |
| `setTema(tema)`, `setMjera(mjera)` | paneli                                                           |

Pravila:

- Funkcije bacaju grešku za nepoznatu vrijednost i za kriv par razine i šifre (`'drzava'` bez šifre, ostale razine sa šifrom kao stringom).
- Upis iste vrijednosti ne obavještava pretplatnike.
- Svaka promjena bilo kojeg polja obavještava sve pretplatnike. Karta zato pamti prethodne `razina` i `podrucje` i leti samo kad se oni promijene.
- Šifre su neprozirni stringovi iz Davidovih podataka. Za JLS se nadređena županija čita iz šifrarnika područja, ne sprema se u stanje.
- Hover i oblačić nisu u stanju, to je interni posao karte.

Karta čita `razina` i `podrucje` (kamera) te `indicator` iz `src/data/indicator.js` (boje), a ne temu i mjeru izravno. `indicator` je `{ kljuc, razina, title, unit, godina, izvor, poveznica, poStanovniku, imaPoStanovniku, values: { [sifra]: broj | null } }` ili `null` (podaci se učitavaju ili tema nema pokazatelj na toj razini). `razina` je `'zupanija'` za državu, a `'jls'` za odabranu županiju i grad ili općinu u njoj, s vrijednostima za gradove i općine te županije. Ako tema za gradove nema pokazatelj (Imovina), odabrana županija dobiva vrijednosti županija. Karta na razini države boja sve županije, za odabranu županiju njezine gradove i općine, a za odabrani grad i dalje cijelu županiju, s ostalim gradovima i općinama izblijeđenima i odabranim istaknutim obrubom. Koji pokazatelj pripada kojoj temi određuje `src/data/teme.js`.

U `.svelte` datotekama: `$view.tema`. U običnom JS-u: `view.subscribe((v) => …)`, koji vraća funkciju za odjavu.

## Stanje u URL-u (`src/url.js`)

Stanje se zrcali u hash, s istim vrijednostima:

| Pogled | Link |
| --- | --- |
| Hrvatska | `#/?tema=novac&mjera=ukupno` |
| Županija | `#/zupanija/05?tema=novac&mjera=po-stanovniku` |
| Grad ili općina | `#/jls/<sifra>?tema=porezi&mjera=ukupno` |
| Na engleskom | `#/?tema=novac&mjera=ukupno&lang=en` (hrvatski nema `lang`) |

- `main.js` pokreće `startUrlSync()` prije aplikacije, pa podijeljeni link odmah otvara taj pogled (i uvodni let karte sleti na njega).
- Osvježavanje stranice i ponovno otvoreni tab uvijek kreću od cijele Hrvatske (tema i mjera ostaju), bez obzira na područje u adresi. Samo otvoreni link vodi ravno na područje.
- Novo područje dodaje zapis u povijest preglednika, a nova tema ili mjera samo zamjenjuje trenutni, pa Natrag ide po područjima.
- Natrag, Naprijed i ručno upisan hash postavljaju stanje preko `setView()`.
- Nepoznata tema ili mjera zamijeni se trenutnom, a nepoznata šifra područja vraća na Hrvatsku čim se podaci učitaju. Link se pritom ispravi na mjestu.
- Hash, a ne putanja, pa GitHub Pages ne treba nikakvo podešavanje servera.
- Promjena jezika (prekidač HR / EN) zamjenjuje link na mjestu, pa se može poslati pogled na engleskom. Natrag i Naprijed ne mijenjaju odabrani jezik.

## Priče (`src/stories/`)

Priča je naslov i niz scena u `price.json`. Scena postavlja zajednički pogled, pa karta i paneli rade kao i inače:

```json
{
  "razina": "jls",
  "odabir": "najveci",
  "pokazatelj": "lokalna_ulaganja",
  "tema": "novac",
  "mjera": "po-stanovniku",
  "eu": false,
  "tekst": "U cijeloj Hrvatskoj po stanovniku najviše ulaže {naziv} ({zupanija}): {vrijednost}."
}
```

- Područje se bira pravilom (`"odabir": "najveci"` ili `"najmanji"` po `pokazatelj`) ili fiksnom šifrom (`"sifra"`). Za `drzava` ne treba ništa.
- U tekstu `{naziv}`, `{vrijednost}` (pokazatelj scene u mjeri scene) i `{zupanija}` popunjavaju se iz podataka, pa priča ostaje točna kad se podaci osvježe.
- `"eu": true` uključuje sloj EU projekata.
- Scene ne dodaju zapise u povijest preglednika, a „Završi” (ili Esc) vraća pogled i sloj od prije priče.

Priča se reproducira kao kratki film (`player.js`, polje `faza` u storeu `reprodukcija`):

| Faza | Što se vidi |
| --- | --- |
| `uvod` | Naslov priče preko karte, paneli se sklanjaju (`html[data-kino]`, `src/raspored.css`), kamera se nagne. |
| `odlazak` | Boje na karti se gase. |
| `let` | Scena postavlja pogled i kamera sporo leti na područje (`STORY_*` u `src/map/config.js`). |
| `prikaz` | Kamera je sletjela (`src/map/slijetanje.js`): boje se vraćaju, rečenica se pojavi u oblačiću riječ po riječ, a kamera polako prilazi i okreće se. |

- Priča sama ide dalje: scena traje dok se rečenica ne pročita (4–8 s prema duljini), a traka koraka pokazuje koliko je ostalo. Gumb pauze ili razmak je zaustavljaju, strelice lijevo i desno mijenjaju scenu, klik na korak otvara tu scenu.
- Za vrijeme priče kamerom upravlja priča: nema zumiranja ni klika na područja. Nagib postoji samo u priči (inače je karta ravna, `maxPitch: 0`).
- Boje se gase i pale preko feature-statea `fade` (`setFade` u `countyLayer.js` i `jlsLayer.js`), jer Mapbox ne može pretopiti jednu boju u drugu, a novi izraz za prozirnost u svakom frameu ponovno bi učitao sloj.
- Uz smanjeno kretanje priča ne ide sama, kamera skače umjesto da leti, a tekst se pojavi odjednom.

