// Keeps Mapbox tiles, fonts and icons the visitor has already seen for 30 days, so a
// revisit draws Croatia from disk instead of Mapbox. Filled by normal use, or all at
// once by the warm-up for presentations (?zagrij, src/map/warmUp.js).

const CACHE = 'mapbox-v1';
const MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;
const CACHED_AT = 'x-kh-cached-at';
// Style JSON is left out so a style change reaches visitors right away. `styles/.../tiles/`
// is the satellite of the city view (src/map/cityLayers.js).
const CACHEABLE = /^https:\/\/api\.mapbox\.com\/(v4\/|fonts\/|styles\/v1\/[^?]+\/(sprite|tiles\/))/;

self.addEventListener('install', () => self.skipWaiting());
// Take over the open page at once, so the first visit already fills the cache.
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET' || !CACHEABLE.test(event.request.url)) return;
  event.respondWith(cacheFirst(event.request));
});

// Mapbox adds a per-map-load `sku` to every tile URL; without dropping it a tile
// stored on one visit would never match on the next.
function cacheKey(url) {
  const u = new URL(url);
  u.searchParams.delete('sku');
  return u.href;
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE);
  const key = cacheKey(request.url);
  const cached = await cache.match(key);
  if (cached && Date.now() - Number(cached.headers.get(CACHED_AT)) < MAX_AGE_MS) return cached;

  const response = await fetch(request);
  if (!response.ok) return response;
  // Our own timestamp, since a cross-origin response doesn't expose its Date header.
  const headers = new Headers(response.headers);
  headers.set(CACHED_AT, String(Date.now()));
  const body = await response.arrayBuffer();
  await cache.put(key, new Response(body, { status: response.status, headers }));
  return new Response(body, { status: response.status, headers: response.headers });
}
