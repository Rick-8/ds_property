let deferredPrompt;

// Check if banner was dismissed previously
const hasDismissed = localStorage.getItem('dsPwaBannerDismissed');

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the default mini-infobar
    e.preventDefault();
    deferredPrompt = e;

    // Only show banner if not previously dismissed
    if (!hasDismissed) {
        const installBanner = document.getElementById('pwa-install-banner');
        if (installBanner) {
            installBanner.classList.remove('d-none');
            installBanner.classList.add('fade-in-up');
        }
    }
});

function installPWA() {
    if (deferredPrompt) {
        deferredPrompt.prompt();

        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('✅ User accepted the PWA install prompt');
            } else {
                console.log('❌ User dismissed the PWA install prompt');
            }

            deferredPrompt = null;

            const installBanner = document.getElementById('pwa-install-banner');
            if (installBanner) {
                installBanner.style.display = 'none';
            }
        });
    }
}

function dismissBanner() {
    const installBanner = document.getElementById('pwa-install-banner');
    if (installBanner) {
        installBanner.style.display = 'none';
        localStorage.setItem('dsPwaBannerDismissed', 'true');
    }
}
