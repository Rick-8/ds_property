document.addEventListener("DOMContentLoaded", function () {
  // Defensive: Hide overlay on every load
  if (typeof showPaymentOverlay === "function") {
    showPaymentOverlay(false);
  }

  // Setup the Pay Button Lottie Loader
  let payBtnLottie = document.getElementById("payBtnLottie");
  let payBtnLottieInstance = null;
  if (payBtnLottie && window.lottie) {
    payBtnLottieInstance = lottie.loadAnimation({
      container: payBtnLottie,
      renderer: "svg",
      loop: true,
      autoplay: false,
      path: "/static/animations/payment_loader.json",
    });
    payBtnLottie.style.width = "32px";
    payBtnLottie.style.height = "32px";
    payBtnLottie.style.verticalAlign = "middle";
  }

  // Stripe Elements Setup
  var paymentForm = document.getElementById("payment-form");
  if (paymentForm && document.getElementById("card-element")) {
    var quoteId = paymentForm.getAttribute("data-quote-id");
    var stripeKey =
      paymentForm.getAttribute("data-stripe-key") || "pk_test_12345";
    var stripe = Stripe(stripeKey);
    var elements = stripe.elements();
    var card = elements.create("card", {
      style: {
        base: {
          color: "#F8F9FA",
          fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
          fontSmoothing: "antialiased",
          fontSize: "16px",
          "::placeholder": { color: "#6c757d" },
        },
        invalid: { color: "#dc3545", iconColor: "#dc3545" },
      },
    });
    card.mount("#card-element");
    card.on("change", function (event) {
      document.getElementById("card-errors").textContent = event.error
        ? event.error.message
        : "";
    });

    paymentForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const payBtn = document.getElementById("submit-button");
      const payBtnText = document.getElementById("payBtnText");

      payBtn.disabled = true;
      if (payBtnText) payBtnText.style.display = "none";
      if (payBtnLottie && payBtnLottieInstance) {
        payBtnLottie.style.display = "inline-block";
        payBtnLottieInstance.goToAndPlay(0, true);
      }

      showPaymentOverlay(true, "Processing your payment...");
      document.getElementById("payment-message").textContent = "";

      // Request a PaymentIntent from backend
      let resp = await fetch(`/quotes/${quoteId}/create-payment-intent/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      let data = await resp.json();
      if (data.error) {
        showPaymentOverlay(false);
        payBtn.disabled = false;
        if (payBtnText) payBtnText.style.display = "";
        if (payBtnLottie && payBtnLottieInstance) {
          payBtnLottie.style.display = "none";
          payBtnLottieInstance.stop();
        }
        document.getElementById("payment-message").textContent = data.error;
        return;
      }

      // Confirm card payment with Stripe.js
      const clientSecret = data.clientSecret;
      const { error, paymentIntent } = await stripe.confirmCardPayment(
        clientSecret,
        { payment_method: { card: card } }
      );

      if (error) {
        showPaymentOverlay(false);
        payBtn.disabled = false;
        if (payBtnText) payBtnText.style.display = "";
        if (payBtnLottie && payBtnLottieInstance) {
          payBtnLottie.style.display = "none";
          payBtnLottieInstance.stop();
        }
        document.getElementById("payment-message").textContent = error.message;
      } else if (paymentIntent && paymentIntent.status === "succeeded") {
        setTimeout(() => {
          window.location.href = "/quotes/payment-success/";
        }, 900);
      } else {
        showPaymentOverlay(false);
        payBtn.disabled = false;
        if (payBtnText) payBtnText.style.display = "";
        if (payBtnLottie && payBtnLottieInstance) {
          payBtnLottie.style.display = "none";
          payBtnLottieInstance.stop();
        }
        document.getElementById("payment-message").textContent =
          "Unexpected error occurred. Please try again.";
      }
    });
  }

  // Cancel Payment Button (reloads the page)
  var cancelPaymentBtn = document.getElementById("cancelPaymentBtn");
  if (cancelPaymentBtn) {
    cancelPaymentBtn.addEventListener("click", function () {
      if (typeof showPaymentOverlay === "function") {
        showPaymentOverlay(false);
      }
      window.location.reload();
    });
  }
  // Accessibility: return focus to Decline button after modal closes
  var declineBtn = document.getElementById("declineBtn");
  var confirmModal = document.getElementById("confirmModal");
  if (confirmModal) {
    confirmModal.addEventListener("hidden.bs.modal", function () {
      if (declineBtn) declineBtn.focus();
    });
  }
});
