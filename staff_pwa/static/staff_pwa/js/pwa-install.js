console.log("pwa-install.js loaded");

let deferredPrompt;

window.addEventListener('beforeinstallprompt', function (e) {
    console.log("beforeinstallprompt event fired!");
    e.preventDefault();
    deferredPrompt = e;

    // Check localStorage for dismissal every time event fires
    if (!localStorage.getItem('dsPwaBannerDismissed')) {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.classList.remove('d-none');
            banner.classList.add('fade-in-up');
        }
    }
});

// Called by Install button in banner
function installPWA() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(function (choiceResult) {
            const banner = document.getElementById('pwa-install-banner');
            if (banner) {
                banner.classList.add('d-none');
            }
            if (choiceResult.outcome === 'accepted') {
                localStorage.setItem('dsPwaBannerDismissed', '1');
            }
            deferredPrompt = null;
        });
    }
}

// Called by Dismiss button in banner
function dismissBanner() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.classList.add('d-none');
        localStorage.setItem('dsPwaBannerDismissed', '1');
    }
}

// Expose to global scope so template onclick can call
window.installPWA = installPWA;
window.dismissBanner = dismissBanner;
