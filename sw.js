// Keeps a copy of Helpercraft on this device, so the Home Screen app opens without internet.
// It only fetches Helpercraft's own files from its own address, and never sends anything anywhere.
const CACHE = 'helpercraft-v4';
const FILES = ['helpercraft.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable-512.png', 'icons/apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// Only Helpercraft's own files: the kept copy opens at once, and a newer copy, when there is internet, is saved for next time.
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin || !FILES.some(f => url.pathname.endsWith('/' + f))) return;
  const fresh = fetch(e.request).then(async r => {
    if (r.ok) await (await caches.open(CACHE)).put(e.request, r.clone());
    return r;
  });
  e.waitUntil(fresh.catch(() => {}));
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(hit => hit || fresh));
});
