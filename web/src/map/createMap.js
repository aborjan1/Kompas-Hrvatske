// Framework-agnostic entry point for the map. The UI (Svelte or anything else)
// only calls createMap() and talks to the returned Mapbox GL instance; it never
// reaches into map internals. Later phases add layers via functions in this folder.

import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './controls.css';
import { BASEMAP_STYLE, INTRO_START, LABEL_LANGUAGE, MAPBOX_TOKEN, MAX_ZOOM } from './config.js';

mapboxgl.accessToken = MAPBOX_TOKEN;

/**
 * @param {HTMLElement} container
 * @returns {mapboxgl.Map}
 */
export function createMap(container) {
  const map = new mapboxgl.Map({
    container,
    // Outdoors has relief, the globe and its atmosphere built in.
    style: BASEMAP_STYLE,
    ...INTRO_START,
    maxZoom: MAX_ZOOM,
    // Flat, north-up map only: tilt and rotation add nothing to a choropleth.
    maxPitch: 0,
    dragRotate: false,
    pitchWithRotate: false,
    touchPitch: false,
    // Keep every tile seen this visit in memory, so zooming back out doesn't rebuild them.
    maxTileCacheSize: 2000,
    attributionControl: false,
  });

  map.touchZoomRotate.disableRotation();
  map.keyboard.disableRotation();
  map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right');
  setDataAttribution(map, '');
  map.on('style.load', () => useLocalLabels(map));

  return map;
}

/** @type {WeakMap<mapboxgl.Map, mapboxgl.AttributionControl>} */
const attributions = new WeakMap();

// The map's "i" button credits the basemap and, once meta.json has loaded, the
// boundaries (Državna geodetska uprava): source, download date and licence, as the
// Open Licence requires. `html` is trusted text built from meta.json.
/**
 * @param {mapboxgl.Map} map
 * @param {string} html
 */
export function setDataAttribution(map, html) {
  const old = attributions.get(map);
  if (old) map.removeControl(old);
  const control = new mapboxgl.AttributionControl({
    compact: true,
    ...(html ? { customAttribution: html } : {}),
  });
  map.addControl(control, 'bottom-right');
  attributions.set(map, control);
}

// Called once the camera has landed on an area (the whole country after the intro):
// the framed view becomes the furthest out the user can zoom and the edge they can
// pan to, so the area stays in focus while they look around it.
/** @param {mapboxgl.Map} map */
function lockToView(map) {
  // A little wider than the view: with bounds exactly the view, zooming out around a
  // cursor off-centre got stuck short of the minimum, so scrolling out never reached
  // the next level up (MapView.svelte).
  const view = map.getBounds();
  const padLng = (view.getEast() - view.getWest()) * 0.05;
  const padLat = (view.getNorth() - view.getSouth()) * 0.05;
  map.setMaxBounds([
    [view.getWest() - padLng, view.getSouth() - padLat],
    [view.getEast() + padLng, view.getNorth() + padLat],
  ]);
  // After the bounds: they can nudge the zoom in a hair, and the minimum must be
  // reachable for scrolling out to a higher level.
  map.setMinZoom(map.getZoom());
}

export const lockToCroatia = lockToView;
export const lockToArea = lockToView;

// Lifts the lock, so the camera can fly to another area.
/** @param {mapboxgl.Map} map */
export function unlockCamera(map) {
  map.setMaxBounds(null);
  map.setMinZoom(null);
}

// Turns the user's scroll, drag, keyboard and touch camera controls on or off. The
// zoom buttons stay; a click on them ends the flight and the lock applies right there.
/**
 * @param {mapboxgl.Map} map
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

// The style shows English names ("Croatia"); show the Croatian name where the tiles
// have one and the local name everywhere else. Only labels that are names, so road
// numbers on shields stay.
function useLocalLabels(map) {
  const label = ['coalesce', ['get', `name_${LABEL_LANGUAGE}`], ['get', 'name']];
  for (const layer of map.getStyle().layers) {
    const field = layer.type === 'symbol' && layer.layout?.['text-field'];
    if (field && JSON.stringify(field).includes('name')) {
      map.setLayoutProperty(layer.id, 'text-field', label);
    }
  }
}
