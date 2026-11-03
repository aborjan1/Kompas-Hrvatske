// Zooming out past an area's framed view goes up a level (city → county → country), as
// the scroll wheel does in MapView.svelte, now also for a pinch, the "−" button and the
// "−" key. The camera lock (createMap.js) sets the framed view as the minimum zoom, so
// Mapbox stops a pinch there and greys out its own "−": neither could leave an area.

/**
 * Whether the camera is as far out as the lock allows.
 * @param {mapboxgl.Map} map
 */
export const naNajmanjem = (map) => map.getZoom() <= map.getMinZoom() + 0.01;

// How far the fingers must close, from their distance when the pinch reached the minimum
// zoom, before it counts: a deliberate pinch, not a wobble right after landing.
const PRAG_PINCHA = 0.7;

/**
 * Goes up a level when two fingers pinch in at the minimum zoom; once per pinch.
 * @param {mapboxgl.Map} map
 * @param {() => void} idiGore
 */
export function pratiPinch(map, idiGore) {
  let pocetak = null; // finger distance when the pinch was at the minimum zoom
  let iskoristeno = false;
  const razmak = (t) => Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);

  map.on('touchmove', ({ originalEvent: e }) => {
    if (e.touches.length !== 2 || iskoristeno || !map.touchZoomRotate.isEnabled()) return;
    // Spreading the fingers zooms in as usual; the count starts again at the minimum.
    if (!naNajmanjem(map)) {
      pocetak = null;
      return;
    }
    const sada = razmak(e.touches);
    if (pocetak === null) pocetak = sada;
    else if (sada < pocetak * PRAG_PINCHA) {
      iskoristeno = true;
      idiGore();
    }
  });
  const kraj = ({ originalEvent: e }) => {
    if (e.touches.length >= 2) return;
    pocetak = null;
    iskoristeno = false;
  };
  map.on('touchend', kraj);
  map.on('touchcancel', kraj);
}

/**
 * The "−" key at the minimum zoom goes up a level, like the button.
 * @param {mapboxgl.Map} map
 * @param {() => void} idiGore
 */
export function pratiTipkovnicu(map, idiGore) {
  map.getCanvasContainer().addEventListener('keydown', (e) => {
    if (e.key !== '-' || e.ctrlKey || e.metaKey || e.altKey) return;
    if (map.keyboard.isEnabled() && naNajmanjem(map)) idiGore();
  });
}

/**
 * "+" and "−" in place of Mapbox's NavigationControl, with its classes so it looks the
 * same (Mapbox's icons, controls.css, the dark phone look in raspored.css). "−" at the
 * minimum zoom goes up a level and is disabled only where there is none (the country).
 */
export class ZoomKontrola {
  /** @param {{ idiGore: () => void, imaGore: () => boolean }} opcije */
  constructor({ idiGore, imaGore }) {
    this.idiGore = idiGore;
    this.imaGore = imaGore;
  }

  /** @param {mapboxgl.Map} map */
  onAdd(map) {
    this.map = map;
    this.container = document.createElement('div');
    this.container.className = 'mapboxgl-ctrl mapboxgl-ctrl-group';
    this.plus = gumb('mapboxgl-ctrl-zoom-in', 'Približi', (e) => map.zoomIn({}, { originalEvent: e }));
    this.minus = gumb('mapboxgl-ctrl-zoom-out', 'Udalji', (e) => {
      if (naNajmanjem(map) && this.imaGore()) {
        this.idiGore();
        // At once, not only after the flight: in Croatia "−" has nowhere left to go.
        this.osvjezi();
      } else map.zoomOut({}, { originalEvent: e });
    });
    this.container.append(this.plus, this.minus);

    // After the move: the camera lock sets the new minimum zoom on the same moveend.
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

  azuriraj() {
    const map = this.map;
    this.plus.disabled = map.getZoom() >= map.getMaxZoom() - 0.01;
    this.minus.disabled = naNajmanjem(map) && !this.imaGore();
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
