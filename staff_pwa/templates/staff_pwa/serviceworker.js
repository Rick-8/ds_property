const CACHE_NAME = 'ds-staff-pwa-v2';
const STATIC_ASSETS = [
  '/',
  '/offline/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/staff_pwa/js/pwa-install.js',
  '/static/staff_pwa/js/push-notifications.js',
  '/static/staff_pwa/media/dsproperty-logo.png',
  '/static/staff_pwa/media/dsproperty-logo-pwa-512.png',
  '/static/staff_pwa/media/favicon-32x32.png',
  '/static/staff_pwa/media/favicon-16x16.png',
];

// Install event: cache essential static assets
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
});

// Activate event: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    )
  );
  self.clients.claim();
});

// Fetch event: network-first for staff views, cache-first for static assets
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  if (url.pathname.startsWith('/staff/')) {
    // Always try network first for dynamic staff pages
    event.respondWith(
      fetch(event.request)
        .then(response => {
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, response.clone());
            return response;
          });
        })
        .catch(() => caches.match(event.request).then(res => res || caches.match('/offline/')))
    );
  } else {
    // Static content: prefer cache
    event.respondWith(
      caches.match(event.request).then(cached => {
        return cached ||
          fetch(event.request)
            .then(response => {
              return caches.open(CACHE_NAME).then(cache => {
                cache.put(event.request, response.clone());
                return response;
              });
            })
            .catch(() => caches.match('/offline/'));
      })
    );
  }
});

// Push notifications
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

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});
