const CACHE_NAME = 'ds-staff-pwa-v3';
const STATIC_ASSETS = [
  '/',
  '/offline/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/staff_pwa/js/pwa-install.js',
  '/static/staff_pwa/js/push-notifications.js',
  '/static/media/dsproperty-logo.png',
  '/static/media/favicon-32x32.png',
  '/static/media/favicon-16x16.png',
];

const EXCLUDE_PATHS = [
  '/account/login',
  '/account/logout',
  '/account/signup',
  '/accounts/',
  '/admin/',
  '/api/',
];

// 🔍 Helper: check if request should be excluded
function isExcluded(url) {
  return EXCLUDE_PATHS.some(path => url.pathname.startsWith(path));
}

// 📦 Install: cache static assets
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

// 🧹 Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(key => {
        if (key !== CACHE_NAME) return caches.delete(key);
      }))
    )
  );
  self.clients.claim();
});

// 🌐 Fetch logic
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // 🔒 Skip excluded paths
  if (isExcluded(url)) return;

  // 📰 HTML pages: network-first (avoid stale login/logout views)
  if (req.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(req)
        .then(response => {
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(req, response.clone());
            return response;
          });
        })
        .catch(() => caches.match(req).then(res => res || caches.match('/offline/')))
    );
    return;
  }

  // 🧱 Static assets: cache-first
  if (STATIC_ASSETS.includes(url.pathname)) {
    event.respondWith(
      caches.match(req).then(cached =>
        cached || fetch(req).then(response => {
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(req, response.clone());
            return response;
          });
        }).catch(() => caches.match('/offline/'))
      )
    );
    return;
  }

  // 👷 Staff pages: network-first
  if (url.pathname.startsWith('/staff/')) {
    event.respondWith(
      fetch(req)
        .then(response => {
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(req, response.clone());
            return response;
          });
        })
        .catch(() => caches.match(req).then(res => res || caches.match('/offline/')))
    );
    return;
  }

  // 🛟 Fallback: try network, fallback to offline
  event.respondWith(fetch(req).catch(() => caches.match('/offline/')));
});

// 🔔 Push notifications
self.addEventListener('push', function (event) {
  const data = event.data?.json() || {};
  const options = {
    body: data.body || 'You have a new notification',
    icon: '/static/media/dsproperty-logo.png',
    data: {
      url: data.url || '/',
    },
  };
  event.waitUntil(
    self.registration.showNotification(data.title || 'New Message', options)
  );
});

// 🖱 Notification click
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});
