// Framework-agnostic entry point for the map. The UI (Svelte or anything else)
// only calls createMap() and talks to the returned MapLibre instance; it never
// reaches into map internals. Later phases add layers via functions in this folder.

import { MapLibreMap, NavigationControl, setWorkerUrl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import { BASEMAP_STYLE, CROATIA_BOUNDS, focusPadding, LABEL_LANGUAGE, MAX_BOUNDS } from './config.js';

// MapLibre 6 looks for its worker next to its own module file, which no longer
// exists once Vite bundles it. Ship the worker as a separate asset instead.
setWorkerUrl(workerUrl);

/**
 * @param {HTMLElement} container
 * @returns {import('maplibre-gl').MapLibreMap}
 */
export function createMap(container) {
  const map = new MapLibreMap({
    container,
    style: BASEMAP_STYLE,
    bounds: CROATIA_BOUNDS,
    fitBoundsOptions: { padding: focusPadding(container.clientWidth) },
    maxBounds: MAX_BOUNDS,
    attributionControl: { compact: true },
  });

  map.addControl(new NavigationControl({ visualizePitch: true }), 'top-right');
  map.on('style.load', () => useLocalLabels(map));

  return map;
}

// Positron prefers English names ("Croatia", "Zagreb County"); show the Croatian
// name where OSM has one and fall back to the local name everywhere else.
function useLocalLabels(map) {
  const label = ['coalesce', ['get', `name:${LABEL_LANGUAGE}`], ['get', 'name']];
  for (const layer of map.getStyle().layers) {
    if (layer.type === 'symbol' && layer.layout?.['text-field']) {
      map.setLayoutProperty(layer.id, 'text-field', label);
    }
  }
}
