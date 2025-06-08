document.addEventListener("DOMContentLoaded", function () {
  const popup = document.getElementById("whatsapp-popup");
  const popupLink = popup.querySelector("a.whatsapp-button");
  const closeBtn = document.getElementById("close-whatsapp");

  let isDragging = false;
  let hasMoved = false;
  let offsetX = 0;
  let offsetY = 0;

  popup.addEventListener("mousedown", function (e) {
    if (e.target === closeBtn) return;
    if (e.button !== 0) return;

    const rect = popup.getBoundingClientRect();

    isDragging = true;
    hasMoved = false;

    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;

    popup.style.position = "fixed";
    popup.style.left = `${rect.left}px`;
    popup.style.top = `${rect.top}px`;
    popup.style.right = "auto";
    popup.style.bottom = "auto";

    e.preventDefault();

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  });

  function onMouseMove(e) {
    if (!isDragging) return;

    hasMoved = true;

    const x = e.clientX - offsetX;
    const y = e.clientY - offsetY;

    const maxX = window.innerWidth - popup.offsetWidth;
    const maxY = window.innerHeight - popup.offsetHeight;

    popup.style.left = `${Math.min(Math.max(0, x), maxX)}px`;
    popup.style.top = `${Math.min(Math.max(0, y), maxY)}px`;
  }

  function onMouseUp() {
    if (isDragging) {
      setTimeout(() => {
        isDragging = false;
      }, 0);
    }
    document.removeEventListener("mousemove", onMouseMove);
    document.removeEventListener("mouseup", onMouseUp);
  }

  popupLink.addEventListener("click", function (e) {
    if (hasMoved) {
      e.preventDefault();
      hasMoved = false;
    }
  });

  closeBtn.addEventListener("click", function () {
    popup.style.display = "none";
  });

  const toastElList = [].slice.call(document.querySelectorAll(".toast"));
  toastElList.forEach((toastEl) => {
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
  });
});