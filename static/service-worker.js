const CACHE = 'soracare-v3-shell';
const SHELL = ['/', '/static/style.css', '/static/app.js', '/manifest.json', '/static/icons/icon-192.png', '/static/icons/icon-512.png'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if(event.request.method !== 'GET') return;
  const url = new URL(event.request.url);

  // APIは常に最新を取りに行く。失敗時はブラウザ側のlocalStorage表示を維持する。
  if(url.pathname.startsWith('/api/')){
    event.respondWith(fetch(event.request));
    return;
  }

  // 画面・CSS・JSはキャッシュを即表示し、裏で最新版へ更新する。
  event.respondWith(
    caches.match(event.request).then(cached => {
      const network = fetch(event.request).then(response => {
        if(response && response.ok){
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put(event.request, copy));
        }
        return response;
      }).catch(() => cached);
      return cached || network;
    })
  );
});
