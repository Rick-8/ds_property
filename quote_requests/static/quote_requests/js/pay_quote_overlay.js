document.addEventListener('DOMContentLoaded', function () {
    let paymentAnimation = null;

    function initPaymentOverlay() {
        const container = document.getElementById('paymentLottie');
        if (!container) return;
        paymentAnimation = lottie.loadAnimation({
            container: container,
            renderer: 'svg',
            loop: true,
            autoplay: false,
            path: '/static/animations/payment_loader.json'
        });
    }

    window.showPaymentOverlay = function(show = true, message = null) {
        const overlay = document.getElementById('paymentOverlay');
        const msgElem = document.getElementById('paymentOverlayMsg');
        if (!overlay) return;

        if (show) {
            overlay.classList.add('visible');
            if (msgElem && message) msgElem.innerText = message;
            if (paymentAnimation) paymentAnimation.goToAndPlay(0, true);
        } else {
            overlay.classList.remove('visible');
            if (paymentAnimation) paymentAnimation.stop();
        }
    };

    initPaymentOverlay();
});