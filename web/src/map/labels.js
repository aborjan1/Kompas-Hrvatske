// Basemap label filtering, so names in neighbouring countries don't compete with the data.

import { convertFilter } from '@maplibre/maplibre-gl-style-spec';

// OpenMapTiles source layers with point names: cities, towns, villages, airports.
const PLACE_SOURCE_LAYERS = new Set(['place', 'aerodrome_label']);

/**
 * Hides place and airport names outside `outline`. Country names stay so the
 * neighbours are still recognisable.
 * @param {import('maplibre-gl').MapLibreMap} map
 * @param {GeoJSON.MultiPolygon} outline From simplifiedOutline() in geometry.js.
 */
export function hidePlacesOutside(map, outline) {
  const inside = [
    'any',
    ['==', ['get', 'class'], 'country'],
    // The bounding box is a cheap first check that rejects most of Europe.
    ['all', ['within', boundingBox(outline)], ['within', outline]],
  ];
  for (const layer of map.getStyle().layers) {
    if (layer.type !== 'symbol' || !PLACE_SOURCE_LAYERS.has(layer['source-layer'])) continue;
    map.setFilter(layer.id, layer.filter ? ['all', toExpression(layer.filter), inside] : inside);
  }
}

// MapTiler styles still use the legacy filter syntax in places, which can't be mixed
// with expressions like `within` in one filter.
function toExpression(filter) {
  return isExpressionFilter(filter) ? filter : convertFilter(filter);
}

// Same test MapLibre uses internally (not exported by the style spec package).
function isExpressionFilter(filter) {
  if (filter === true || filter === false) return true;
  if (!Array.isArray(filter) || filter.length === 0) return false;
  switch (filter[0]) {
    case 'has':
      return filter.length >= 2 && filter[1] !== '$id' && filter[1] !== '$type';
    case 'in':
      return filter.length >= 3 && (typeof filter[1] !== 'string' || Array.isArray(filter[2]));
    case '!in':
    case '!has':
    case 'none':
      return false;
    case '==':
    case '!=':
    case '>':
    case '>=':
    case '<':
    case '<=':
      return filter.length !== 3 || Array.isArray(filter[1]) || Array.isArray(filter[2]);
    case 'any':
    case 'all':
      return filter.slice(1).every((f) => typeof f === 'boolean' || isExpressionFilter(f));
    default:
      return true;
  }
}

/** @param {GeoJSON.MultiPolygon} outline @returns {GeoJSON.Polygon} */
function boundingBox(outline) {
  const points = outline.coordinates.flat(2);
  const lngs = points.map((p) => p[0]);
  const lats = points.map((p) => p[1]);
  const [w, e, s, n] = [Math.min(...lngs), Math.max(...lngs), Math.min(...lats), Math.max(...lats)];
  return { type: 'Polygon', coordinates: [[[w, s], [e, s], [e, n], [w, n], [w, s]]] };
}
