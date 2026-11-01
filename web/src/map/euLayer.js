// EU project circles: one per city or municipality, area proportional to the EU money
// it received. In EU flag colours so they read as "EU" over any tema's ramp.

export const EU_SOURCE = 'eu-projekti';
export const EU_LAYER = 'eu-projekti-krugovi';

/** @type {GeoJSON.FeatureCollection} */
const EMPTY = { type: 'FeatureCollection', features: [] };
const MIN_RADIUS = 3;
// The largest amount (Zagreb) gets this radius; area, not radius, follows the amount.
const MAX_RADIUS = 30;

/** @param {import('maplibre-gl').MapLibreMap} map */
export function createEuLayer(map) {
  map.addSource(EU_SOURCE, { type: 'geojson', data: EMPTY, promoteId: 'sifra' });
  // Above the area fills and outlines, below roads' and places' labels.
  const beforeId = map.getStyle().layers.find((l) => l.type === 'symbol')?.id;
  map.addLayer(
    {
      id: EU_LAYER,
      type: 'circle',
      source: EU_SOURCE,
      paint: {
        'circle-color': '#ffcc00',
        'circle-opacity': 0.85,
        'circle-stroke-color': '#003399',
        'circle-stroke-width': ['case', ['boolean', ['feature-state', 'hover'], false], 2.5, 1.2],
        'circle-radius': MIN_RADIUS,
      },
    },
    beforeId,
  );

  return {
    /** @param {import('../data/euProjekti.js').EuJls[]} points */
    show(points) {
      const max = Math.max(1, ...points.map((p) => p.esif_eur));
      const radius = ['max', MIN_RADIUS, ['*', MAX_RADIUS, ['sqrt', ['/', ['get', 'esif_eur'], max]]]];
      // A bit larger up close, where there is room.
      map.setPaintProperty(EU_LAYER, 'circle-radius', [
        'interpolate', ['linear'], ['zoom'],
        6, radius,
        10, ['*', 1.6, radius],
      ]);
      map.getSource(EU_SOURCE).setData({
        type: 'FeatureCollection',
        features: points
          // Largest first, so small circles are drawn on top and stay clickable.
          .toSorted((a, b) => b.esif_eur - a.esif_eur)
          .map((p) => ({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: p.polozaj },
            properties: { sifra: p.sifra, mjesto: p.mjesto, broj: p.broj, esif_eur: p.esif_eur },
          })),
      });
    },

    hide() {
      map.getSource(EU_SOURCE).setData(EMPTY);
    },
  };
}
