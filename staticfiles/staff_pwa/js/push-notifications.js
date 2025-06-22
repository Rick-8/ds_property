// Helper: Convert base64 string to Uint8Array
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

if ('serviceWorker' in navigator && 'PushManager' in window) {
  navigator.serviceWorker.register('/serviceworker.js')
    .then(function (registration) {
      console.log('Service Worker registered with scope:', registration.scope);

      return registration.pushManager.getSubscription()
        .then(function (subscription) {
          if (subscription) {
            console.log('Already subscribed.');
            return subscription;
          }

          const vapidKey = window.vapidPublicKey;
          if (!vapidKey) {
            throw new Error("VAPID public key is missing.");
          }

          return registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(vapidKey)
          });
        });
    })
    .then(function (subscription) {
      if (subscription) {
        console.log('Subscription success:', subscription);
      }
    })
    .catch(function (error) {
      console.error('Push subscription failed:', error);
    });
} else {
  console.warn('Push messaging is not supported');
}
