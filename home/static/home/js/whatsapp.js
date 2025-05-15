document.addEventListener("DOMContentLoaded", function () {
  const closeBtn = document.getElementById("close-whatsapp");
  const popup = document.getElementById("whatsapp-popup");
  const whatsappBtn = document.querySelector(".whatsapp-button");

  if (closeBtn && popup) {
    closeBtn.addEventListener("click", function () {
      popup.style.display = "none";
    });
  }

  if (whatsappBtn) {
    whatsappBtn.addEventListener("click", function () {
      // Replace with your WhatsApp number (country code + number, no + or spaces)
      const whatsappNumber = "447700900123";  
      const url = `https://wa.me/${whatsappNumber}`;
      window.open(url, "_blank");
    });
  }
});
