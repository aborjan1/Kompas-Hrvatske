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
  // The zoom buttons are added by MapView.svelte (ZoomKontrola in odzumiravanje.js): its
  // "−" also goes up a level, which Mapbox's own control can't.
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

// How far the centre may wander from where it landed, as a share of the framed view each
// way, before the camera eases back towards the area (pratiOkvir in odzumiravanje.js).
const PROSTOR = 0.35;
// How far below the framed view a county or city can be zoomed out. Zooming out into it
// is how the user leaves for the level up (odzumiravanje.js); the country has no level
// up, so it gets none.
export const ZALIHA_ZUMA = 0.8;

/**
 * @typedef {object} Okvir Where the camera landed and how far it may go from there.
 * @property {number} zum The framed view's zoom.
 * @property {boolean} izlaz Whether zooming out below it leaves for the level up.
 * @property {number} zapad Bounds for the centre (lng / lat).
 * @property {number} istok
 * @property {number} jug
 * @property {number} sjever
 */

// Called once the camera has landed on an area (the whole country after the intro). The
// area stays in focus without hard edges: Mapbox enforces maxBounds by zooming the map
// back *in*, which fought every zoom out (the map jerked and stuck instead of zooming
// out). So only the minimum zoom is set here, and a camera that wandered off is eased
// back once it stops (pratiOkvir).
/**
 * @param {mapboxgl.Map} map
 * @param {number} zaliha Zoom allowed below the framed view.
 * @returns {Okvir}
 */
function lockToView(map, zaliha) {
  map.setMaxBounds(null);
  const zum = map.getZoom();
  map.setMinZoom(zum - zaliha);
  const pogled = map.getBounds();
  const sredina = map.getCenter();
  const dLng = (pogled.getEast() - pogled.getWest()) * PROSTOR;
  const dLat = (pogled.getNorth() - pogled.getSouth()) * PROSTOR;
  return {
    zum,
    izlaz: zaliha > 0,
    zapad: sredina.lng - dLng,
    istok: sredina.lng + dLng,
    jug: sredina.lat - dLat,
    sjever: sredina.lat + dLat,
  };
}

/** @param {mapboxgl.Map} map */
export const lockToCroatia = (map) => lockToView(map, 0);
/** @param {mapboxgl.Map} map */
export const lockToArea = (map) => lockToView(map, ZALIHA_ZUMA);

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
