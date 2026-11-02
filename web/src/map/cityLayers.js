// City view for Zagreb and Rijeka: satellite imagery under the city's own layers, one
// group of layers per filter (src/data/gradskiPrikaz.js). Every layer exists from the
// start with empty data, so hover and click code can always name them; a filter's
// files load the first time it is switched on.

import { FILTRI } from '../data/gradskiPrikaz.js';
import { MAPBOX_TOKEN } from './config.js';
import { colorExpression, NO_DATA_COLOR, quantileClasses } from './countyLayer.js';

const BASE_URL = `${import.meta.env.BASE_URL}data/gradovi/`;
const SATELLITE = 'grad-satelit';
// The satellite blends in and out instead of popping; instant under reduced motion.
const FADE_MS = matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 800;
const EMPTY = { type: 'FeatureCollection', features: [] };

// Amber ramp for the districts, light → dark.
const DISTRICT_COLORS = ['#fef3c7', '#fcd34d', '#f59e0b', '#b45309', '#78350f'];
const ZONE_COLORS = [
  'match', ['get', 'vrsta'],
  'poslovna', '#7c3aed',
  'proizvodna', '#4338ca',
  'poslovna i proizvodna', '#6d28d9',
  'trgovačka', '#c026d3',
  'ugostiteljsko-turistička', '#db2777',
  '#8b5cf6',
];

/** Layers of each filter: source id → its file (per city when it differs), then the layers. */
const GROUPS = {
  ekonomska: {
    sources: { 'grad-cetvrti': { file: 'cetvrti.geojson' } },
    layers: [
      // Per-district (feature-state) from the start and switched without a transition:
      // Mapbox threw while blending a plain colour into the per-district one.
      {
        id: 'grad-cetvrti-fill', type: 'fill', source: 'grad-cetvrti',
        paint: {
          'fill-color': ['case', ['==', ['feature-state', 'value'], null], NO_DATA_COLOR, DISTRICT_COLORS[2]],
          'fill-color-transition': { duration: 0, delay: 0 },
          'fill-opacity': 0.55,
        },
      },
      { id: 'grad-cetvrti-line', type: 'line', source: 'grad-cetvrti', paint: { 'line-color': '#ffffff', 'line-width': 1.5 } },
    ],
  },
  zone: {
    sources: {
      'grad-zone': { file: 'gospodarske-zone.geojson' },
      'grad-brownfield': { file: 'brownfield.geojson' },
    },
    layers: [
      { id: 'grad-zone-fill', type: 'fill', source: 'grad-zone', paint: { 'fill-color': ZONE_COLORS, 'fill-opacity': 0.55 } },
      { id: 'grad-zone-line', type: 'line', source: 'grad-zone', filter: ['!=', ['get', 'izgradjenost'], 'neizgrađeno'], paint: { 'line-color': ZONE_COLORS, 'line-width': 1 } },
      // Unbuilt zones dashed: land ready for new investment.
      { id: 'grad-zone-nova', type: 'line', source: 'grad-zone', filter: ['==', ['get', 'izgradjenost'], 'neizgrađeno'], paint: { 'line-color': '#ffffff', 'line-width': 2, 'line-dasharray': [2, 1.5] } },
      { id: 'grad-brownfield-fill', type: 'fill', source: 'grad-brownfield', paint: { 'fill-color': '#92400e', 'fill-opacity': 0.6 } },
      { id: 'grad-brownfield-line', type: 'line', source: 'grad-brownfield', paint: { 'line-color': '#fde68a', 'line-width': 1.5 } },
    ],
  },
  ulaganja: {
    sources: { 'grad-ulaganja': { file: 'kapitalna-ulaganja.geojson' } },
    layers: [
      { id: 'grad-ulaganja', type: 'circle', source: 'grad-ulaganja', paint: dot(FILTRI.ulaganja.boja) },
    ],
  },
  imovina: {
    sources: {
      'grad-prostori': { file: { zagreb: 'prazni-prostori.geojson', rijeka: 'poslovni-prostori.geojson' } },
      'grad-trznice': { file: { zagreb: 'trznice.geojson' } },
      'grad-drustva': { file: { zagreb: 'gradska-drustva.geojson' } },
    },
    layers: [
      { id: 'grad-prostori', type: 'circle', source: 'grad-prostori', paint: dot(FILTRI.imovina.boja) },
      { id: 'grad-trznice', type: 'circle', source: 'grad-trznice', paint: dot('#16a34a') },
      { id: 'grad-drustva', type: 'circle', source: 'grad-drustva', paint: dot('#1d4ed8') },
    ],
  },
};

/** Layers a user can point at, for hover and click. */
export const CITY_POINT_LAYERS = ['grad-ulaganja', 'grad-prostori', 'grad-trznice', 'grad-drustva'];

// Every location the same small dot: where something is, not how big; the amount is in
// the tooltip.
function dot(color) {
  return {
    'circle-color': color,
    'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 2.5, 10, 4, 13, 5.5],
    'circle-stroke-color': '#ffffff',
    'circle-stroke-width': 1,
  };
}
export const CITY_AREA_LAYERS = ['grad-brownfield-fill', 'grad-zone-fill', 'grad-cetvrti-fill'];

/** @param {mapboxgl.Map} map */
export function createCityLayers(map) {
  // Above the area fills and EU circles (they would only cover the photo), below labels.
  const beforeId = map.getStyle().layers.find((l) => l.type === 'symbol')?.id;
  // Static Tiles API: the raster tiles behind mapbox://mapbox.satellite answer 429 on
  // our plan, while the same imagery through the satellite style's tiles works.
  map.addSource(SATELLITE, {
    type: 'raster',
    tiles: [`https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/512/{z}/{x}/{y}?access_token=${MAPBOX_TOKEN}`],
    tileSize: 512,
    attribution: '© Mapbox © Maxar',
  });
  map.addLayer(
    {
      id: SATELLITE,
      type: 'raster',
      source: SATELLITE,
      layout: { visibility: 'none' },
      paint: { 'raster-opacity': 0, 'raster-opacity-transition': { duration: FADE_MS, delay: 0 } },
    },
    beforeId,
  );
  let hideSatellite = 0;

  for (const group of Object.values(GROUPS)) {
    for (const id of Object.keys(group.sources)) {
      map.addSource(id, {
        type: 'geojson',
        data: EMPTY,
        ...(id === 'grad-cetvrti' ? { promoteId: 'sifra' } : { generateId: true }),
      });
    }
    for (const layer of group.layers) {
      map.addLayer({ ...layer, layout: { ...layer.layout, visibility: 'none' } }, beforeId);
    }
  }

  /** @type {Map<string, Promise<void>>} key "<city>/<source>" → load */
  const loads = new Map();
  let shownCity = null;

  /** Fills a filter's sources with the city's files, once per city. */
  function load(city, filter) {
    return Promise.all(
      Object.entries(GROUPS[filter].sources).map(([id, { file }]) => {
        const name = typeof file === 'string' ? file : file[city];
        if (!name) return null;
        const key = `${city}/${id}`;
        if (!loads.has(key)) {
          loads.set(key, fetchJson(`${BASE_URL}${city}/${name}`).then((geojson) => {
            if (city !== shownCity) return;
            map.getSource(id).setData(geojson);
            if (id === 'grad-cetvrti') return colourDistricts(city);
          }));
        }
        return loads.get(key);
      }),
    ).catch((error) => {
      // A failed file can be tried again next time the filter is switched on.
      for (const id of Object.keys(GROUPS[filter].sources)) loads.delete(`${city}/${id}`);
      console.error(error);
    });
  }

  async function colourDistricts(city) {
    const { podrucja } = await fetchJson(`${BASE_URL}${city}/cetvrti.json`);
    const values = Object.values(podrucja).map((d) => [d.sifra, d.pokazatelji.udio_gospodarske_povrsine]);
    for (const [sifra, value] of values) {
      if (Number.isFinite(value)) map.setFeatureState({ source: 'grad-cetvrti', id: sifra }, { value });
    }
    const classes = quantileClasses(values.map(([, v]) => v).filter(Number.isFinite), DISTRICT_COLORS);
    map.setPaintProperty('grad-cetvrti-fill', 'fill-color', colorExpression(classes));
  }

  return {
    /**
     * Shows a city's view with the given filters, or hides it (city null).
     * @param {string | null} city Folder name in gradovi/ ("zagreb", "rijeka").
     * @param {string[]} filters The switched-on filters this city has.
     */
    show(city, filters) {
      if (city !== shownCity) {
        // Another city's data must not show under this one.
        for (const group of Object.values(GROUPS)) {
          for (const id of Object.keys(group.sources)) map.getSource(id).setData(EMPTY);
        }
        loads.clear();
        shownCity = city;
      }
      // Fade, then hide once faded out: a hidden layer stops loading satellite tiles.
      clearTimeout(hideSatellite);
      if (city) map.setLayoutProperty(SATELLITE, 'visibility', 'visible');
      else hideSatellite = setTimeout(() => map.setLayoutProperty(SATELLITE, 'visibility', 'none'), FADE_MS);
      map.setPaintProperty(SATELLITE, 'raster-opacity', city ? 1 : 0);
      for (const [filter, group] of Object.entries(GROUPS)) {
        const on = Boolean(city) && filters.includes(filter);
        if (on) load(city, filter);
        for (const layer of group.layers) map.setLayoutProperty(layer.id, 'visibility', on ? 'visible' : 'none');
      }
    },
  };
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return response.json();
}
