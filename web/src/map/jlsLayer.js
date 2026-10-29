// City and municipality (JLS) choropleth for one county at a time, loaded from
// public/data/jls/<county code>.geojson when the user enters that county. Inside the
// county every JLS is filled by class, like the counties at country level; once one
// is selected the rest fade, so the surroundings stay readable around it.

import { JLS_BOUNDARIES_URL } from './config.js';
import { CLASS_COLORS, colorExpression, FILL_OPACITY, quantileClasses } from './countyLayer.js';
import { geometryBounds } from './geometry.js';

export const JLS_SOURCE = 'jls';
export const JLS_FILL_LAYER = 'jls-fill';
const LINE_LAYER = 'jls-line';
const HOVER_LAYER = 'jls-hover';
const SELECTED_HALO_LAYER = 'jls-selected-halo';
const SELECTED_LAYER = 'jls-selected';
const FADED_OPACITY = FILL_OPACITY / 2;

/** @type {GeoJSON.FeatureCollection} */
const EMPTY = { type: 'FeatureCollection', features: [] };
const isSelected = ['boolean', ['feature-state', 'selected'], false];
const isHovered = ['boolean', ['feature-state', 'hover'], false];

/** @param {import('maplibre-gl').MapLibreMap} map */
export function createJlsLayer(map) {
  map.addSource(JLS_SOURCE, { type: 'geojson', data: EMPTY, promoteId: 'sifra' });

  // Above the county layers, below roads and labels.
  const beforeId = map
    .getStyle()
    .layers.find((l) => l.type === 'symbol' || l['source-layer'] === 'transportation')?.id;
  const addLayer = (layer) => map.addLayer({ source: JLS_SOURCE, ...layer }, beforeId);
  // Transparent until values arrive; unfilled JLS still catch clicks.
  addLayer({
    id: JLS_FILL_LAYER,
    type: 'fill',
    paint: { 'fill-color': CLASS_COLORS[0], 'fill-opacity': 0 },
  });
  addLayer({
    id: LINE_LAYER,
    type: 'line',
    paint: { 'line-color': '#3a3a36', 'line-width': 0.6, 'line-opacity': 0.5 },
  });
  addLayer({
    id: HOVER_LAYER,
    type: 'line',
    paint: { 'line-color': '#1f1f1d', 'line-width': 1.5, 'line-opacity': ['case', isHovered, 1, 0] },
  });
  // A white halo under the dark outline keeps the selection visible on any class colour.
  addLayer({
    id: SELECTED_HALO_LAYER,
    type: 'line',
    layout: { 'line-join': 'round' },
    paint: { 'line-color': '#ffffff', 'line-width': 6, 'line-opacity': ['case', isSelected, 0.9, 0] },
  });
  addLayer({
    id: SELECTED_LAYER,
    type: 'line',
    layout: { 'line-join': 'round' },
    paint: { 'line-color': '#1f1f1d', 'line-width': 2.5, 'line-opacity': ['case', isSelected, 1, 0] },
  });

  let county = null;
  let loaded = Promise.resolve();
  /** @type {string[]} */
  let codes = [];
  /** @type {Map<string, import('maplibre-gl').LngLatBounds>} */
  let boundsByCode = new Map();
  let selected = null;
  /** @type {Record<string, number | null> | null} */
  let values = null;
  /** @type {{ color: string, min: number, max: number }[]} */
  let classes = [];

  // Values may arrive before the county's boundaries do, so they are kept and applied
  // again once the features are on the map.
  function applyValues() {
    for (const code of codes) {
      map.removeFeatureState({ source: JLS_SOURCE, id: code }, 'value');
      const value = values?.[code];
      if (Number.isFinite(value)) map.setFeatureState({ source: JLS_SOURCE, id: code }, { value });
    }
    map.setPaintProperty(JLS_FILL_LAYER, 'fill-color', colorExpression(classes));
    applyOpacity();
  }

  // Every JLS while browsing the county; once one is selected the others fade. No
  // values (the tema has nothing for cities): outlines only.
  function applyOpacity() {
    let opacity = 0;
    if (values) opacity = selected ? ['case', isSelected, FILL_OPACITY, FADED_OPACITY] : FILL_OPACITY;
    map.setPaintProperty(JLS_FILL_LAYER, 'fill-opacity', opacity);
  }

  function select(code) {
    if (selected) map.removeFeatureState({ source: JLS_SOURCE, id: selected }, 'selected');
    selected = code && boundsByCode.has(code) ? code : null;
    if (selected) map.setFeatureState({ source: JLS_SOURCE, id: selected }, { selected: true });
    applyOpacity();
  }

  return {
    /**
     * Shows the cities and municipalities of one county. Resolves once they are on
     * the map; asking again for the same county returns the same load.
     * @param {string} code County code ("01"–"21").
     */
    showCounty(code) {
      if (code === county) return loaded;
      county = code;
      select(null);
      loaded = fetch(JLS_BOUNDARIES_URL(code))
        .then((response) => {
          if (!response.ok) throw new Error(`jls/${code}.geojson: HTTP ${response.status}`);
          return response.json();
        })
        .then((geojson) => {
          // A newer county was asked for while this one loaded.
          if (code !== county) return;
          codes = geojson.features.map((f) => f.properties.sifra);
          boundsByCode = new Map(
            geojson.features.map((f) => [f.properties.sifra, geometryBounds(f.geometry)]),
          );
          map.getSource(JLS_SOURCE).setData(geojson);
          applyValues();
        });
      return loaded;
    },

    hide() {
      county = null;
      select(null);
      codes = [];
      boundsByCode = new Map();
      map.getSource(JLS_SOURCE).setData(EMPTY);
    },

    /**
     * Selects one city or municipality of the shown county (only it stays filled), or
     * none (every one is filled).
     * @param {string | null} code
     */
    select,

    /**
     * Colours the county's cities and municipalities by value in up to 5 quantile
     * classes.
     * @param {Record<string, number | null>} newValues Keyed by JLS code.
     * @param {string[]} [colors] Five colours, light → dark.
     * @returns {{ classes: { color: string, min: number, max: number }[], hasMissing: boolean }}
     */
    setValues(newValues, colors = CLASS_COLORS) {
      values = newValues;
      const all = Object.values(newValues);
      const present = all.filter(Number.isFinite);
      classes = quantileClasses(present, colors);
      applyValues();
      return { classes, hasMissing: present.length < all.length };
    },

    /** No values: the tema has nothing to show for cities and municipalities. */
    clearValues() {
      values = null;
      classes = [];
      applyValues();
      return { classes, hasMissing: false };
    },

    /**
     * @param {string} code
     * @returns {import('maplibre-gl').LngLatBounds | undefined}
     */
    bounds: (code) => boundsByCode.get(code),
  };
}
