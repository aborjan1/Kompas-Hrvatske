// Framework-agnostic entry point for the map. The UI (Svelte or anything else)
// only calls createMap() and talks to the returned MapLibre instance; it never
// reaches into map internals. Later phases add layers via functions in this folder.

import { LngLat, LngLatBounds, MapLibreMap, NavigationControl, setWorkerUrl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import './controls.css';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import {
  BASEMAP_STYLE,
  INTRO_START,
  LABEL_LANGUAGE,
  CROATIA_BOUNDS,
  FOCUS_PADDING,
  MAX_ZOOM,
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
    // Flat, north-up map only: tilt and rotation add nothing to a choropleth.
    maxPitch: 0,
    dragRotate: false,
    pitchWithRotate: false,
    touchPitch: false,
    // Keep every tile seen this visit in memory, so zooming back out doesn't rebuild
    // tiles (costs memory, not MapTiler requests).
    maxTileCacheSize: 2000,
    attributionControl: { compact: true },
  });

  map.touchZoomRotate.disableRotation();
  map.keyboard.disableRotation();
  map.addControl(new NavigationControl({ showCompass: false }), 'top-right');
  // Added first, so later bottom-left controls (the legend) stack above it.
  map.addControl(new MapTilerLogo(), 'bottom-left');
  map.on('style.load', () => {
    useLocalLabels(map);
    addCountryBorders(map);
    addGlobe(map);
  });

  return map;
}

// Called once the intro has landed (it starts from space). The whole-country view is
// the furthest out the user can zoom, whatever the screen size.
// The centre stays inside Croatia's convex hull so the map can't drift away (Bosnia,
// inside the hull, keeps panning from Zagreb to Split smooth). This replaces
// MapLibre's default constrain, so it clamps zoom itself.
/**
 * @param {import('maplibre-gl').MapLibreMap} map
 * @param {number[][]} hull From convexHull() in geometry.js.
 */
export function lockToCroatia(map, hull) {
  const minZoom = map.cameraForBounds(CROATIA_BOUNDS, { padding: FOCUS_PADDING })?.zoom ?? map.getZoom();
  map.setMinZoom(minZoom);
  map.setTransformConstrain((center, zoom) => ({
    center: LngLat.convert(/** @type {[number, number]} */ (clampToHull([center.lng, center.lat], hull))),
    zoom: clamp(zoom, minZoom, MAX_ZOOM),
  }));
}

// Keeps the camera on a selected county or city: the centre stays inside the area's
// bounding box and the user can't zoom out past the framed view, so the area stays
// in focus while they look around it.
/**
 * @param {import('maplibre-gl').MapLibreMap} map
 * @param {import('maplibre-gl').LngLatBoundsLike} bounds
 */
export function lockToArea(map, bounds) {
  const box = LngLatBounds.convert(bounds);
  const framed = map.cameraForBounds(box, { padding: FOCUS_PADDING, pitch: map.getPitch() });
  const minZoom = Math.min(framed?.zoom ?? map.getZoom(), MAX_ZOOM);
  map.setMinZoom(minZoom);
  map.setTransformConstrain((center, zoom) => ({
    center: new LngLat(
      clamp(center.lng, box.getWest(), box.getEast()),
      clamp(center.lat, box.getSouth(), box.getNorth()),
    ),
    zoom: clamp(zoom, minZoom, MAX_ZOOM),
  }));
}

// Lifts lockToCroatia() / lockToArea(), so the camera can fly to another area.
/** @param {import('maplibre-gl').MapLibreMap} map */
export function unlockCamera(map) {
  map.setMinZoom(null);
  map.setTransformConstrain(null);
}

// Turns the user's scroll, drag, keyboard and touch camera controls on or off. The
// zoom buttons stay; a click on them ends the flight and the lock applies right there.
/**
 * @param {import('maplibre-gl').MapLibreMap} map
 * @param {boolean} enabled
 */
export function setUserInput(map, enabled) {
  const handlers = [
    map.scrollZoom,
    map.boxZoom,
    map.dragPan,
    map.keyboard,
    map.doubleClickZoom,
    // Rotation stays off (createMap()), enable() keeps it that way.
    map.touchZoomRotate,
  ];
  for (const handler of handlers) {
    if (enabled) handler.enable();
    else handler.disable();
  }
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

// Re-applied on every style load, so a basemap switch (orthophoto, phase 7) keeps it.
// Relief is the style's own hillshade; 3D terrain popped in on tilt and cost a second DEM.
function addGlobe(map) {
  map.setProjection({ type: 'globe' });
  // Atmosphere glow around the globe, fading out as the camera nears the ground.
  map.setSky({ 'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 1, 5, 1, 7, 0] });
}

// The style shows English or Latin names ("Croatia"); show the Croatian name where
// OSM has one and fall back to the local name everywhere else. Only labels that are
// names, so road numbers on shields stay.
function useLocalLabels(map) {
  const label = ['coalesce', ['get', `name:${LABEL_LANGUAGE}`], ['get', 'name']];
  for (const layer of map.getStyle().layers) {
    const field = layer.type === 'symbol' && layer.layout?.['text-field'];
    if (field && JSON.stringify(field).includes('name')) {
      map.setLayoutProperty(layer.id, 'text-field', label);
    }
  }
}

// Landscape draws no national borders; draw them from the tiles' OpenMapTiles `boundary`
// data, sea borders included.
const CROATIA_CODES = ['HR', 'HRV', 'Croatia', 'Hrvatska'];

function addCountryBorders(map) {
  const layers = map.getStyle().layers;
  const source = 'maptiler_planet';
  if (!map.getSource(source)) return;
  map.addLayer(
    {
      id: 'kh-granice-drzava',
      type: 'line',
      source,
      'source-layer': 'boundary',
      // Land borders everywhere, sea borders only Croatia's (adm0_l/adm0_r name the
      // countries on each side; matched loosely since the tiles' naming isn't documented).
      filter: [
        'all',
        ['==', ['get', 'admin_level'], 2],
        [
          'any',
          ['!=', ['get', 'maritime'], 1],
          ['in', ['get', 'adm0_l'], ['literal', CROATIA_CODES]],
          ['in', ['get', 'adm0_r'], ['literal', CROATIA_CODES]],
        ],
      ],
      layout: { 'line-join': 'round' },
      paint: {
        'line-color': '#000000',
        // Sea borders dashed, as on most maps.
        'line-dasharray': ['case', ['==', ['get', 'maritime'], 1], ['literal', [3, 2]], ['literal', [1, 0]]],
        'line-width': ['interpolate', ['linear'], ['zoom'], 3, 0.8, 7, 1.6, 10, 2.4],
      },
    },
    layers.find((l) => l.type === 'symbol')?.id,
  );
}

// The free MapTiler plan requires its logo on the map.
class MapTilerLogo {
  onAdd() {
    const link = document.createElement('a');
    link.className = 'maplibregl-ctrl kh-maptiler-logo';
    link.href = 'https://www.maptiler.com/';
    link.target = '_blank';
    link.rel = 'noopener';
    const logo = document.createElement('img');
    logo.src = 'https://api.maptiler.com/resources/logo.svg';
    logo.alt = 'MapTiler';
    logo.height = 24;
    link.append(logo);
    return link;
  }

  onRemove() {}
}
