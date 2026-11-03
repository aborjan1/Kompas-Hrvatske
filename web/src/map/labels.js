// Basemap label filtering, so names in neighbouring countries don't compete with the data.

// Mapbox Streets source layers with point names: cities, towns, villages, airports,
// and points of interest such as national parks. Sea names (natural_label) stay.
const PLACE_SOURCE_LAYERS = new Set(['place_label', 'airport_label', 'poi_label']);

/**
 * Hides place, airport and point-of-interest names outside `outline`. Country names stay so the
 * neighbours are still recognisable.
 * @param {import('mapbox-gl').Map} map
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
    // Outdoors writes these filters as expressions, so they combine with `within` as is.
    map.setFilter(layer.id, layer.filter ? ['all', layer.filter, inside] : inside);
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
