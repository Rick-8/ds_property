const CACHE_NAME = 'ds-staff-pwa-v1';
const URLS_TO_CACHE = [
  '/',
  '/staff/my-jobs/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/pwa-install.js',
  '/static/js/push-notifications.js',
  '/static/media/dsproperty-logo.png',
  '/static/media/dsproperty-logo-pwa-512.png',
  '/static/media/favicon-32x32.png',
  '/static/media/favicon-16x16.png',
];

// Install event: cache assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(URLS_TO_CACHE);
    })
  );
});

// Activate event: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
});

// Fetch event: respond from cache or network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cached => {
      const fetchPromise = fetch(event.request)
        .then(networkResponse => {
          return caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, networkResponse.clone());
            return networkResponse;
          });
        })
        .catch(() => cached); // fallback if fetch fails

      return cached || fetchPromise;
    })
  );
});

// Push notifications support (if used)
self.addEventListener('push', function (event) {
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/static/media/dsproperty-logo.png',
    data: {
      url: data.url || '/',
    }
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});
