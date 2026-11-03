// Zooming out below a county's or city's framed view goes up a level (city → county →
// country), like the breadcrumb. The camera lock (lockToArea in createMap.js) leaves
// ZALIHA_ZUMA below the framed view and no hard edges, so every way of zooming out is
// plain Mapbox zooming: pinch, trackpad, scroll wheel, the "−" button and key. Once the
// map has stopped (fingers off, wheel and inertia done), a view far enough out leaves,
// and one panned off the area eases back to it.

// How far below the framed view counts as leaving; less than ZALIHA_ZUMA (0.8), so it
// can be reached, and enough that a small pinch, with the inertia Mapbox adds after
// the fingers lift, or a stray scroll after landing, doesn't count.
const PRAG_IZLAZA = 0.5;

const ogranici = (x, min, max) => Math.min(Math.max(x, min), max);

import { t } from '../jezik.js';

/**
 * @param {mapboxgl.Map} map
 * @param {{ okvir: () => import('./createMap.js').Okvir | null, idiGore: () => void }} opcije
 *   `okvir` is where the camera landed, null during a flight.
 */
export function pratiOkvir(map, { okvir, idiGore }) {
  // For a touch gesture the zoom when the last finger lifted decides, not where Mapbox's
  // inertia carries it after: a quick small pinch can glide well past the threshold. It
  // holds for both moveends Mapbox fires (fingers off, then inertia done) and until the
  // next gesture of any kind starts.
  /** @type {number | null} */
  let zumPriPustanju = null;
  const okvirKarte = map.getContainer();
  for (const vrsta of ['touchstart', 'wheel', 'mousedown', 'keydown']) {
    okvirKarte.addEventListener(vrsta, () => (zumPriPustanju = null), { capture: true, passive: true });
  }
  okvirKarte.addEventListener('touchend', (e) => {
    if (e.touches.length === 0) zumPriPustanju = map.getZoom();
  }, true);

  map.on('moveend', () => {
    const zum = zumPriPustanju ?? map.getZoom();
    const o = okvir();
    if (!o) return;
    if (o.izlaz && zum < o.zum - PRAG_IZLAZA) {
      idiGore();
      return;
    }
    const c = map.getCenter();
    const lng = ogranici(c.lng, o.zapad, o.istok);
    const lat = ogranici(c.lat, o.jug, o.sjever);
    // Not `essential`: under prefers-reduced-motion it jumps back instead.
    if (lng !== c.lng || lat !== c.lat) map.easeTo({ center: [lng, lat], duration: 300 });
  });
}

/**
 * "+" and "−" in place of Mapbox's NavigationControl: the same look (its classes, so its
 * icons, controls.css and the dark phone look in raspored.css apply) with Croatian names
 * for screen readers. Each is disabled at the zoom limit; "−" at a county or city takes
 * the map out to the level up through pratiOkvir().
 */
export class ZoomKontrola {
  /** @param {mapboxgl.Map} map */
  onAdd(map) {
    this.map = map;
    this.container = document.createElement('div');
    this.container.className = 'mapboxgl-ctrl mapboxgl-ctrl-group';
    this.plus = gumb('mapboxgl-ctrl-zoom-in', t('Približi', 'Zoom in'), (e) => map.zoomIn({}, { originalEvent: e }));
    this.minus = gumb('mapboxgl-ctrl-zoom-out', t('Udalji', 'Zoom out'), (e) => map.zoomOut({}, { originalEvent: e }));
    this.container.append(this.plus, this.minus);

    // After the move: the camera lock sets the new limits on the same moveend.
    this.osvjezi = () => setTimeout(() => this.azuriraj());
    map.on('zoom', this.osvjezi);
    map.on('moveend', this.osvjezi);
    this.azuriraj();
    return this.container;
  }

  onRemove() {
    this.map.off('zoom', this.osvjezi);
    this.map.off('moveend', this.osvjezi);
    this.container.remove();
  }

  /** Button names in the current language (MapView calls this on a switch). */
  prevedi() {
    for (const [b, naziv] of [[this.plus, t('Približi', 'Zoom in')], [this.minus, t('Udalji', 'Zoom out')]]) {
      b.title = naziv;
      b.setAttribute('aria-label', naziv);
    }
  }

  azuriraj() {
    const map = this.map;
    this.plus.disabled = map.getZoom() >= map.getMaxZoom() - 0.01;
    this.minus.disabled = map.getZoom() <= map.getMinZoom() + 0.01;
  }
}

function gumb(klasa, naziv, onclick) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = klasa;
  b.title = naziv;
  b.setAttribute('aria-label', naziv);
  const ikona = document.createElement('span');
  ikona.className = 'mapboxgl-ctrl-icon';
  ikona.setAttribute('aria-hidden', 'true');
  b.append(ikona);
  b.addEventListener('click', onclick);
  return b;
}
