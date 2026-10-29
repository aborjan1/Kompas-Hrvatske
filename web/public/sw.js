// Keeps MapTiler tiles, fonts and icons the visitor has already seen for 30 days, so a
// revisit draws Croatia from disk instead of MapTiler (their own cache headers are 4-8 h).
// Nothing is prefetched: only responses the map asked for anyway are stored.

const CACHE = 'maptiler-v1';
const MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;
const CACHED_AT = 'x-kh-cached-at';
// Style JSON is left out so a style change reaches visitors right away.
const CACHEABLE = /^https:\/\/api\.maptiler\.com\/(tiles|fonts|maps\/[^/]+\/sprite)/;

self.addEventListener('install', () => self.skipWaiting());
// Take over the open page at once, so the first visit already fills the cache.
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET' || !CACHEABLE.test(event.request.url)) return;
  event.respondWith(cacheFirst(event.request));
});

async function cacheFirst(request) {
  const cache = await caches.open(CACHE);
  const cached = await cache.match(request);
  if (cached && Date.now() - Number(cached.headers.get(CACHED_AT)) < MAX_AGE_MS) return cached;

  const response = await fetch(request);
  if (!response.ok) return response;
  // Our own timestamp, since a cross-origin response doesn't expose its Date header.
  const headers = new Headers(response.headers);
  headers.set(CACHED_AT, String(Date.now()));
  const body = await response.arrayBuffer();
  await cache.put(request, new Response(body, { status: response.status, headers }));
  return new Response(body, { status: response.status, headers: response.headers });
}
