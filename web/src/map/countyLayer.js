// County (županija) choropleth. Boundaries are a GeoJSON FeatureCollection whose
// features carry `sifra` (two-digit county code, "01"–"21") and `naziv`.
// Values arrive separately as { [sifra]: number } so the map doesn't care which
// indicator is selected or where it came from; that's decided by app state.

const SOURCE = 'zupanije';
const FILL_LAYER = 'zupanije-fill';
const LINE_LAYER = 'zupanije-line';

// Sequential blue, light → dark, one hue so order reads without relying on hue.
export const CLASS_COLORS = ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'];
export const NO_DATA_COLOR = '#d6d5d1';

/**
 * @param {import('maplibre-gl').MapLibreMap} map
 * @param {GeoJSON.FeatureCollection} geojson
 */
export function createCountyLayer(map, geojson) {
  const codes = geojson.features.map((f) => f.properties.sifra);

  map.addSource(SOURCE, { type: 'geojson', data: geojson, promoteId: 'sifra' });

  // Below the basemap labels so place names stay readable on top of the fill.
  const beforeId = map.getStyle().layers.find((l) => l.type === 'symbol')?.id;
  map.addLayer(
    {
      id: FILL_LAYER,
      type: 'fill',
      source: SOURCE,
      paint: { 'fill-color': NO_DATA_COLOR, 'fill-opacity': 0.85 },
    },
    beforeId,
  );
  map.addLayer(
    {
      id: LINE_LAYER,
      type: 'line',
      source: SOURCE,
      paint: { 'line-color': '#ffffff', 'line-width': 1 },
    },
    beforeId,
  );

  return {
    /**
     * Colours counties by value in up to 5 quantile classes.
     * @param {Record<string, number | null>} values
     * @returns {{ classes: { color: string, min: number, max: number }[], hasMissing: boolean }}
     */
    setValues(values) {
      map.removeFeatureState({ source: SOURCE });
      for (const code of codes) {
        const value = values[code];
        if (Number.isFinite(value)) map.setFeatureState({ source: SOURCE, id: code }, { value });
      }

      const present = codes.map((c) => values[c]).filter(Number.isFinite);
      const classes = quantileClasses(present, CLASS_COLORS);
      map.setPaintProperty(FILL_LAYER, 'fill-color', colorExpression(classes));

      return { classes, hasMissing: present.length < codes.length };
    },
  };
}

// Splits sorted values into equal-count classes. Duplicate values never straddle
// a break, so fewer classes come back when data has many ties; colours are then
// spread across the full ramp so the darkest class still means "highest".
function quantileClasses(values, colors) {
  const sorted = [...values].sort((a, b) => a - b);
  if (sorted.length === 0) return [];

  const groups = [];
  let start = 0;
  for (let k = 1; k <= colors.length; k++) {
    let end = Math.round((k * sorted.length) / colors.length);
    while (end < sorted.length && end > 0 && sorted[end] === sorted[end - 1]) end++;
    if (end > start) groups.push(sorted.slice(start, end));
    start = Math.max(start, end);
  }

  const last = colors.length - 1;
  return groups.map((g, i) => ({
    color: colors[groups.length === 1 ? last : Math.round((i * last) / (groups.length - 1))],
    min: g[0],
    max: g[g.length - 1],
  }));
}

function colorExpression(classes) {
  const value = ['feature-state', 'value'];
  if (classes.length === 0) return NO_DATA_COLOR;

  const step = ['step', value, classes[0].color];
  for (const c of classes.slice(1)) step.push(c.min, c.color);
  return ['case', ['==', value, null], NO_DATA_COLOR, step];
}
