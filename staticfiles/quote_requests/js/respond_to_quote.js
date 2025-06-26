document.addEventListener("DOMContentLoaded", function () {
  if (typeof showPaymentOverlay === "function") {
    showPaymentOverlay(false);
  }

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
  }

  const paymentForm = document.getElementById("payment-form");

  if (paymentForm && document.getElementById("card-element")) {
    const quoteId = paymentForm.getAttribute("data-quote-id");
    const stripeKey = paymentForm.getAttribute("data-stripe-key");
    const stripe = Stripe(stripeKey);
    const elements = stripe.elements();

    const card = elements.create("card", {
      style: {
        base: { color: "#F8F9FA", fontSize: "16px" },
        invalid: { color: "#dc3545" },
      },
    });

    card.mount("#card-element");

    card.on("change", (event) => {
      document.getElementById("card-errors").textContent =
        event.error ? event.error.message : "";
    });

    paymentForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const payBtn = document.getElementById("submit-button");
      const cancelPaymentBtn = document.getElementById("cancelPaymentBtn");
      const payBtnText = document.getElementById("payBtnText");

      payBtn.disabled = true;
      payBtnText.style.display = "none";
      cancelPaymentBtn.style.display = "none";

      if (payBtnLottie && payBtnLottieInstance) {
        payBtnLottie.style.display = "block";
        payBtnLottie.style.width = "100%";
        payBtnLottie.style.height = "200px";
        payBtnLottieInstance.goToAndPlay(0, true);
      }

      showPaymentOverlay(true, "Processing your payment...");
      document.getElementById("payment-message").textContent = "";

      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

      let resp = await fetch(`/quotes/${quoteId}/create-payment-intent/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({}),
      });

      if (!resp.ok) {
        payBtn.disabled = false;
        payBtnText.style.display = "inline-block";
        cancelPaymentBtn.style.display = "inline-block";
        payBtnLottie.style.display = "none";
        payBtnLottieInstance.stop();
        showPaymentOverlay(false);
        document.getElementById("payment-message").textContent = `Server error: ${resp.status}`;
        return;
      }

      let data = await resp.json();

      if (data.error) {
        payBtn.disabled = false;
        payBtnText.style.display = "inline-block";
        cancelPaymentBtn.style.display = "inline-block";
        payBtnLottie.style.display = "none";
        payBtnLottieInstance.stop();
        showPaymentOverlay(false);
        document.getElementById("payment-message").textContent = data.error;
        return;
      }

      const { error, paymentIntent } = await stripe.confirmCardPayment(
        data.clientSecret,
        { payment_method: { card: card } }
      );

      if (error) {
        payBtn.disabled = false;
        payBtnText.style.display = "inline-block";
        cancelPaymentBtn.style.display = "inline-block";
        payBtnLottie.style.display = "none";
        payBtnLottieInstance.stop();
        showPaymentOverlay(false);
        document.getElementById("payment-message").textContent = error.message;
      } else if (paymentIntent && paymentIntent.status === "succeeded") {
        setTimeout(() => {
          window.location.href = "/quotes/payment-success/";
        }, 900);
      } else {
        payBtn.disabled = false;
        payBtnText.style.display = "inline-block";
        cancelPaymentBtn.style.display = "inline-block";
        payBtnLottie.style.display = "none";
        payBtnLottieInstance.stop();
        showPaymentOverlay(false);
        document.getElementById("payment-message").textContent =
          "Unexpected error occurred. Please try again.";
      }
    });
  }

  const acceptBtn = document.getElementById("acceptBtn");
  if (acceptBtn) {
    acceptBtn.addEventListener("click", function () {
      document.getElementById("action-btns").style.display = "none";
      const paymentAccordion = new bootstrap.Collapse(
        document.getElementById("paymentAccordion"),
        { toggle: true }
      );
    });
  }

  const cancelPaymentBtn = document.getElementById("cancelPaymentBtn");
  if (cancelPaymentBtn) {
    cancelPaymentBtn.addEventListener("click", function () {
      if (typeof showPaymentOverlay === "function") {
        showPaymentOverlay(false);
      }
      window.location.reload();
    });
  }
});