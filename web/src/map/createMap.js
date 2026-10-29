// Framework-agnostic entry point for the map. The UI (Svelte or anything else)
// only calls createMap() and talks to the returned MapLibre instance; it never
// reaches into map internals. Later phases add layers via functions in this folder.

import { LngLat, MapLibreMap, NavigationControl, setWorkerUrl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import {
  BASEMAP_STYLE,
  INTRO_START,
  LABEL_LANGUAGE,
  MAX_ZOOM,
  MIN_ZOOM,
  TERRAIN_ATTRIBUTION,
  TERRAIN_EXAGGERATION,
  TERRAIN_TILES,
} from './config.js';
import { clampToHull } from './geometry.js';

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
    ...INTRO_START,
    maxZoom: MAX_ZOOM,
    attributionControl: { compact: true },
  });

  map.addControl(new NavigationControl({ visualizePitch: true }), 'top-right');
  map.on('style.load', () => {
    useLocalLabels(map);
    addGlobeAndTerrain(map);
  });
  map.on('pitchend', () => terrainWhenTilted(map));

  return map;
}

// Called once the intro has landed (it starts from space, further out than MIN_ZOOM).
// The centre stays inside Croatia's convex hull so the map can't drift away (Bosnia,
// inside the hull, keeps panning from Zagreb to Split smooth), while zoom still reaches
// out to Europe. This replaces MapLibre's default constrain, so it clamps zoom itself.
/**
 * @param {import('maplibre-gl').MapLibreMap} map
 * @param {number[][]} hull From convexHull() in geometry.js.
 */
export function lockToCroatia(map, hull) {
  map.setMinZoom(MIN_ZOOM);
  map.setTransformConstrain((center, zoom) => ({
    center: LngLat.convert(/** @type {[number, number]} */ (clampToHull([center.lng, center.lat], hull))),
    zoom: clamp(zoom, MIN_ZOOM, MAX_ZOOM),
  }));
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

// Re-applied on every style load, so a basemap switch (orthophoto, phase 7) keeps them.
function addGlobeAndTerrain(map) {
  map.setProjection({ type: 'globe' });
  // Atmosphere glow around the globe, fading out as the camera nears the ground.
  map.setSky({ 'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 1, 5, 1, 7, 0] });
  map.addSource('teren', {
    type: 'raster-dem',
    tiles: [TERRAIN_TILES],
    encoding: 'terrarium',
    tileSize: 512,
    maxzoom: 12,
    attribution: TERRAIN_ATTRIBUTION,
  });
}

// Terrain is invisible from straight above and slow to load (every visible tile needs
// elevation too), so it is on only while the camera is tilted.
function terrainWhenTilted(map) {
  const tilted = map.getPitch() > 0;
  if (tilted === Boolean(map.getTerrain())) return;
  map.setTerrain(tilted ? { source: 'teren', exaggeration: TERRAIN_EXAGGERATION } : null);
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
