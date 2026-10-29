// Offline support: network first so a new deploy shows up straight away, the cache when there is no network.
const CACHE = 'drums-v1';   // bump to drop old files
const CORE = ['./', 'index.html', 'manifest.webmanifest', 'img/scene.webp', 'img/icon-192.png', 'img/icon-512.png', 'img/apple-touch-icon.png'];

addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => skipWaiting())));
addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => clients.claim())));
addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  e.respondWith(fetch(e.request).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
    return res;
  }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(hit => hit || caches.match('index.html'))));
});
