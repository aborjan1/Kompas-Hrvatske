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
  - `MapView.svelte` – tanki Svelte omotač: granice iz `public/data/zupanije.geojson`, boje iz storea `indicator` (`src/data/indicator.js`)
- `src/state.js` – zajedničko stanje (vidi dolje)
- `src/data/` – učitavanje podataka i pokazatelji
  - `podaci.js` – učitava `meta`, `drzava` i `zupanije` na startu, `jls.json` tek nakon izlaska s razine države
  - `teme.js` – koji pokazatelji pripadaju kojoj temi (karta i info panel)
  - `indicator.js` – pretvara razinu, temu i mjeru u brojke po šifri za kartu
  - `format.js` – formatiranje brojeva prema `jedinica` i `decimale` iz `meta.json`
- `src/panels/` – lebdeći paneli: putanja, info panel, teme i prekidač ukupno / po stanovniku
  - `dev/DevOdabir.svelte` – birač područja samo u `npm run dev`, dok karta ne javlja klik na grad ili općinu
- `src/stories/` – priče (u izradi)
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

Karta čita `razina` i `podrucje` (kamera) te `indicator` iz `src/data/indicator.js` (boje), a ne temu i mjeru izravno. `indicator` je `{ kljuc, razina, title, unit, godina, izvor, poStanovniku, imaPoStanovniku, values: { [sifra]: broj | null } }` ili `null` (podaci se učitavaju ili tema nema pokazatelj na toj razini). `razina` je `'zupanija'` za državu, a `'jls'` za odabranu županiju i grad ili općinu u njoj, s vrijednostima za gradove i općine te županije. Ako tema za gradove nema pokazatelj (Imovina), odabrana županija dobiva vrijednosti županija. Karta na razini države boja sve županije, za odabranu županiju njezine gradove i općine, a za odabrani grad samo njega, u boji njegovog razreda. Koji pokazatelj pripada kojoj temi određuje `src/data/teme.js`.

U `.svelte` datotekama: `$view.tema`. U običnom JS-u: `view.subscribe((v) => …)`, koji vraća funkciju za odjavu.
