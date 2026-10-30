/* The Golden Hour — service worker v3 */
const PREFIX = "golden-hour-";
const CACHE = "golden-hour-v3";
const BASE = new URL('./', self.location.href).pathname;
const CORE = ['', 'index.html', 'manifest.json', 'manifest-dark.json',
  'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png',
  'assets/gh-theme.css', 'assets/gh-theme.js', 'assets/gh-halloween.css', 'assets/gh-halloween.js']
  .map(path => BASE + path);
function noStore(response) {
  return /(?:^|,)\s*no-store\b/i.test(response.headers.get("Cache-Control") || "");
}

async function remember(request, response) {
  try {
    const cache = await caches.open(CACHE);
    if (noStore(response) || response.status === 404 || response.status === 410) {
      await cache.delete(request);
    } else if (response.ok) {
      await cache.put(request, response.clone());
    }
  } catch (_) { /* Storage failure must not discard a network response. */ }
  return response;
}

self.addEventListener("install", (e) => {
  e.waitUntil(Promise.all(CORE.map(async (url) => {
    const response = await fetch(url, { cache: "reload" });
    if (!response.ok) throw new Error("Precache failed: " + url);
    await remember(url, response);
  })).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith(PREFIX) && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.status >= 500 && !noStore(response)) {
      const hit = await caches.match(request, { cacheName: CACHE });
      if (hit) return hit;
    }
    return await remember(request, response);
  } catch (_) {
    return (await caches.match(request, { cacheName: CACHE })) || Response.error();
  }
}

async function cacheFirst(request) {
  let hit;
  try { hit = await caches.match(request, { cacheName: CACHE }); } catch (_) {}
  return hit || remember(request, await fetch(request));
}

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.origin !== self.location.origin || !url.pathname.startsWith(BASE)) return;
  if (url.pathname === BASE + "sw.js") return;
  if (e.request.cache === "no-store" || noStore(e.request)) {
    e.respondWith(fetch(e.request));
    return;
  }
  const staticAsset = /\.(?:css|js|png|jpe?g|webp|gif|svg|ico|woff2?|ttf|otf)$/i.test(url.pathname);
  e.respondWith(e.request.mode === "navigate" || !staticAsset
    ? networkFirst(e.request)
    : cacheFirst(e.request));
});
