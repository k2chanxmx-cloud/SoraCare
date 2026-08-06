const CACHE='soracare-v1';
const ASSETS=['/','/static/style.css','/static/app.js','/static/icons/icon-192.png','/static/icons/icon-512.png'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS))));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',event=>{if(event.request.method==='GET')event.respondWith(fetch(event.request).catch(()=>caches.match(event.request)));});
