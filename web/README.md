# Kompas Hrvatske – web

Vite + Svelte aplikacija s MapLibre kartom.

```powershell
cd web
npm install
npm run dev      # http://localhost:5173
npm run build    # izlaz u web/dist/
```

Podloga karte je MapTiler (besplatni plan: nekomercijalno, 5.000 učitavanja karte mjesečno).
Ključ s [cloud.maptiler.com](https://cloud.maptiler.com/account/keys/) upiši u `web/.env.local`
(ne ide u git), po uzoru na `web/.env.example`:

```powershell
Copy-Item .env.example .env.local   # pa u .env.local upiši VITE_MAPTILER_KEY=...
```
## Struktura

- `src/map/` – karta (MapLibre slojevi i kamera). Neovisno o frameworku: UI poziva samo `createMap(container)`.
  - `config.js` – podloga (MapTiler Landscape), uvodni let, granice Hrvatske, raspon zuma
  - `createMap.js` – stvara kartu (globus, oznake na hrvatskom, MapTiler logo, ograničenje kamere)
  - `labels.js` – skriva nazive mjesta izvan Hrvatske
  - `countyLayer.js` – choropleth županija: `createCountyLayer(map, geojson).setValues({ [sifra]: broj })`, 5 kvantilnih razreda
  - `legend.js` – legenda kao MapLibre kontrola
  - `hover.js` – isticanje granice i oblačić za bilo koji sloj poligona (`addHoverTooltip`)
  - `euLayer.js` – krugovi EU projekata, jedan po gradu ili općini, površina prema iznosu iz EU
  - `MapView.svelte` – tanki Svelte omotač: granice iz `public/data/zupanije.geojson`, boje iz storea `indicator` (`src/data/indicator.js`)
- `src/state.js` – zajedničko stanje (vidi dolje)
- `src/url.js` – stanje u URL-u: svaki pogled ima svoj link, Natrag i Naprijed rade (vidi dolje)
- `src/data/` – učitavanje podataka i pokazatelji
  - `podaci.js` – učitava `meta`, `drzava` i `zupanije` na startu, `jls.json` tek nakon izlaska s razine države
  - `teme.js` – koji pokazatelji pripadaju kojoj temi (karta i info panel)
  - `indicator.js` – pretvara razinu, temu i mjeru u brojke po šifri za kartu
  - `format.js` – formatiranje brojeva prema `jedinica` i `decimale` iz `meta.json`
  - `euProjekti.js` – EU projekti (2014.–2020.) zbrojeni po gradu ili općini, učitavaju se tek kad se uključi gumb „EU projekti”
- `src/panels/` – lebdeći paneli: putanja, info panel, teme i prekidač ukupno / po stanovniku
  - `GrafUsporedbe.svelte` – u profilu županije: položaj među svih 21 županija (Chart.js), klik na stupac odabire županiju
  - `UsporedbaSlicnih.svelte` – u profilu grada ili općine: usporedba s 5 najsličnijih po broju stanovnika (`slicni` iz `jls.json`), klik odabire taj grad
  - `GrafStupci.svelte` – zajednički vodoravni stupčasti graf (Chart.js) za obje usporedbe
  - `IzvorPodatka.svelte` – izvor, godina i poveznica pokazatelja kojim je karta obojana, ispod tema
  - `Pretraga.svelte` – pretraga županija, gradova i općina (Fuse.js), radi i bez kvačica; logika u `src/data/pretraga.js`
  - `PopisPrica.svelte` i `PricaKartica.svelte` – popis priča (u panelu za Hrvatsku) i kartica priče koja za vrijeme priče zamjenjuje traku s temama
- `src/data/recenice.js` – rečenica info panela za svaku temu i razinu, od stvarnih brojeva; dio bez podatka se izostavlja
  - `EuProjektiPopis.svelte` – broj, iznos i 5 najvećih EU projekata odabranog grada, dok je sloj uključen
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

- `main.js` pokreće `startUrlSync()` prije aplikacije, pa podijeljeni link odmah otvara taj pogled (i uvodni let karte sleti na njega).
- Novo područje dodaje zapis u povijest preglednika, a nova tema ili mjera samo zamjenjuje trenutni, pa Natrag ide po područjima.
- Natrag, Naprijed i ručno upisan hash postavljaju stanje preko `setView()`.
- Nepoznata tema ili mjera zamijeni se trenutnom, a nepoznata šifra područja vraća na Hrvatsku čim se podaci učitaju. Link se pritom ispravi na mjestu.
- Hash, a ne putanja, pa GitHub Pages ne treba nikakvo podešavanje servera.

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
- Scene ne dodaju zapise u povijest preglednika, a „Završi” (ili Esc) vraća pogled i sloj od prije priče. Strelice lijevo i desno mijenjaju scenu, a „Automatski” ih mijenja sam (za snimanje videa; ne nudi se uz smanjeno kretanje).

