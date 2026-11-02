// Presentation warm-up: with ?zagrij in the address, downloads every basemap tile
// over Croatia (zoom 0-10, about 500 tiles / 40 MB) into the service worker's cache
// (public/sw.js), so the demo never waits for the network. Only for the presenter's
// own laptop; visitors never trigger it. Needs the production build, where the
// service worker runs.

import { CROATIA_BOUNDS, MAPBOX_TOKEN, MAX_ZOOM } from './config.js';

const PARALLEL = 6;

export const shouldWarmUp = () => new URLSearchParams(location.search).has('zagrij');

/** @param {mapboxgl.Map} map */
export async function warmUp(map) {
  const status = new WarmUpStatus();
  map.addControl(status, 'top-left');
  if (import.meta.env.DEV || !('serviceWorker' in navigator)) {
    status.show('Zagrijavanje radi samo u objavljenoj verziji (npm run build + preview).');
    return;
  }
  // On a first visit the service worker is still starting; tiles fetched before it
  // controls the page would bypass its cache.
  status.show('Pripremam kartu…');
  await navigator.serviceWorker.ready;
  if (!navigator.serviceWorker.controller) {
    await new Promise((resolve) => navigator.serviceWorker.addEventListener('controllerchange', resolve, { once: true }));
  }

  // Same URL Mapbox GL requests, minus its per-load `sku`, which the service worker
  // drops from its cache keys too.
  const tileset = /** @type {{ url: string }} */ (map.getStyle().sources.composite).url.replace('mapbox://', '');
  const urls = tilesOver(CROATIA_BOUNDS, Math.floor(MAX_ZOOM)).map(
    ([z, x, y]) => `https://api.mapbox.com/v4/${tileset}/${z}/${x}/${y}.vector.pbf?access_token=${MAPBOX_TOKEN}`,
  );

  let done = 0;
  let failed = 0;
  const next = urls.values();
  async function worker() {
    for (const url of next) {
      const ok = await fetch(url).then((r) => r.ok, () => false);
      done++;
      if (!ok) failed++;
      status.show(`Pripremam kartu: ${done} / ${urls.length}`);
    }
  }
  await Promise.all(Array.from({ length: PARALLEL }, worker));
  status.show(
    failed ? `Karta pripremljena, ${failed} dijelova nije uspjelo. Osvježi s ?zagrij za ponovni pokušaj.`
    : 'Karta pripremljena za prezentaciju ✓',
  );
}

/**
 * Every tile (512 px, so tile zoom = map zoom) covering the bounds, zoom 0 to maxZoom.
 * @param {number[][]} bounds [[west, south], [east, north]]
 * @param {number} maxZoom
 */
function tilesOver([[west, south], [east, north]], maxZoom) {
  const x = (lng, z) => Math.floor(((lng + 180) / 360) * 2 ** z);
  const y = (lat, z) => {
    const r = (lat * Math.PI) / 180;
    return Math.floor(((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2) * 2 ** z);
  };
  const tiles = [];
  for (let z = 0; z <= maxZoom; z++) {
    for (let tx = x(west, z); tx <= x(east, z); tx++) {
      for (let ty = y(north, z); ty <= y(south, z); ty++) tiles.push([z, tx, ty]);
    }
  }
  return tiles;
}

class WarmUpStatus {
  onAdd() {
    this.container = document.createElement('div');
    this.container.className = 'mapboxgl-ctrl kh-panel kh-zagrijavanje';
    return this.container;
  }

  onRemove() {
    this.container.remove();
  }

  /** @param {string} text */
  show(text) {
    this.container.textContent = text;
  }
}
