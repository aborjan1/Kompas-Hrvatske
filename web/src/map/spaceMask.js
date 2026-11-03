// Croatia alone in space: once the intro has landed, everything outside its land
// (neighbours, the sea, foreign names) fades into a starfield, with a soft glow along
// the coast and borders. The mask (public/data/svemir.geojson) is the region around
// Croatia with its mainland and islands cut out, precomputed as one valid polygon:
// a world-sized polygon with Croatia's rings as holes broke Mapbox's triangulation.

const SOURCE = 'svemir';
const MASK_LAYER = 'svemir-maska';
const GLOW_LAYER = 'svemir-sjaj';
const STARS = 'kh-zvijezde';
// Same as the space behind the globe (MapView.svelte), so the two read as one sky.
const SPACE_COLOR = '#0b1222';
const FADE_MS = matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 1500;

/**
 * @param {mapboxgl.Map} map
 * @param {GeoJSON.FeatureCollection<GeoJSON.MultiPolygon>} mask
 */
export function createSpaceMask(map, mask) {
  map.addImage(STARS, starfield(256), { pixelRatio: 2 });

  // The holes are Croatia; their edges get the glow.
  const croatiaRings = mask.features.flatMap((f) => f.geometry.coordinates.flatMap((polygon) => polygon.slice(1)));
  map.addSource(SOURCE, {
    type: 'geojson',
    data: {
      type: 'FeatureCollection',
      features: [
        { ...mask.features[0], properties: { uloga: 'maska' } },
        { type: 'Feature', properties: { uloga: 'obris' }, geometry: { type: 'MultiLineString', coordinates: croatiaRings } },
      ],
    },
  });

  // On top of the basemap and its labels, so nothing outside shows through; Croatia's
  // own layers and names are seen through the hole.
  const fade = { duration: FADE_MS, delay: 0 };
  map.addLayer({
    id: MASK_LAYER,
    type: 'fill',
    source: SOURCE,
    filter: ['==', ['get', 'uloga'], 'maska'],
    // No antialiased outline: its colour comes from fill-color, which a pattern fill
    // lacks, and Mapbox threw while fading it in. The glow draws the edge instead.
    paint: { 'fill-pattern': STARS, 'fill-antialias': false, 'fill-opacity': 0, 'fill-opacity-transition': fade },
  });
  map.addLayer({
    id: GLOW_LAYER,
    type: 'line',
    source: SOURCE,
    filter: ['==', ['get', 'uloga'], 'obris'],
    layout: { 'line-join': 'round' },
    paint: {
      'line-color': '#7cc4ff',
      'line-width': ['interpolate', ['linear'], ['zoom'], 6, 6, 10, 14],
      'line-blur': ['interpolate', ['linear'], ['zoom'], 6, 6, 10, 12],
      'line-opacity': 0,
      'line-opacity-transition': fade,
    },
  });

  return {
    /** Fades the rest of the world out. Called once the intro has landed. */
    show() {
      map.setPaintProperty(MASK_LAYER, 'fill-opacity', 1);
      map.setPaintProperty(GLOW_LAYER, 'line-opacity', 0.55);
    },
  };
}

/**
 * A square tile of night sky: dark blue with scattered stars of varying brightness,
 * the same every load (seeded), and seamless when repeated.
 * @param {number} size
 */
function starfield(size) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = /** @type {CanvasRenderingContext2D} */ (canvas.getContext('2d'));
  ctx.fillStyle = SPACE_COLOR;
  ctx.fillRect(0, 0, size, size);
  let seed = 7;
  const random = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < 70; i++) {
    const r = random() < 0.9 ? 0.6 : 1.2;
    ctx.fillStyle = `rgba(255, 255, 255, ${0.25 + random() * 0.7})`;
    ctx.beginPath();
    ctx.arc(random() * size, random() * size, r, 0, Math.PI * 2);
    ctx.fill();
  }
  return ctx.getImageData(0, 0, size, size);
}
