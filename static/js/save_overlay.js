let savingAnimation = null;

function initSavingOverlay() {
    const container = document.getElementById('savingLottie');
    if (!container) return;

    savingAnimation = lottie.loadAnimation({
        container: container,
        renderer: 'svg',
        loop: true,
        autoplay: false,
        path: '/static/animations/tree-cutting.json',  // Make sure your static files are served here
    });
}

function showSavingOverlay(show = true) {
    const overlay = document.getElementById('savingOverlay');
    if (!overlay || !savingAnimation) return;

    overlay.style.display = show ? 'flex' : 'none';
    if (show) {
        savingAnimation.goToAndPlay(0, true);
    } else {
        savingAnimation.stop();
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initSavingOverlay();
});
