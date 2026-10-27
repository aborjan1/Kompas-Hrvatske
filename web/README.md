# Kompas Hrvatske – web

Vite + Svelte aplikacija s MapLibre kartom.

```powershell
cd web
npm install
npm run dev      # http://localhost:5173
npm run build    # izlaz u web/dist/
```

## Struktura

- `src/map/` – karta (MapLibre slojevi i kamera). Neovisno o frameworku: UI poziva samo `createMap(container)`.
  - `config.js` – podloga, granice Hrvatske, jezik oznaka
  - `createMap.js` – stvara kartu (OpenFreeMap Positron, oznake na hrvatskom)
  - `countyLayer.js` – choropleth županija: `createCountyLayer(map, geojson).setValues({ [sifra]: broj })`, 5 kvantilnih razreda
  - `legend.js` – legenda kao MapLibre kontrola
  - `dev/` – privremeni mock (granice iz geoBoundaries, ODbL; izmišljene vrijednosti) dok ne stignu pravi podaci
  - `MapView.svelte` – tanki Svelte omotač
- `src/panels/`, `src/stories/` – sučelje (u izradi)
- `public/data/` – gotove GeoJSON/JSON datoteke iz `pipeline/` (u izradi)
