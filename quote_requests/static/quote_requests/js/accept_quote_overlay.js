document.addEventListener('DOMContentLoaded', function () {
    const acceptForm = document.getElementById('acceptQuoteForm');
    const savingOverlay = document.getElementById('savingOverlay');
    const savingText = document.querySelector('.saving-text');
    const confirmAcceptModal = document.getElementById('confirmAcceptModal');

    if (acceptForm && savingOverlay && savingText && confirmAcceptModal) {
        acceptForm.addEventListener('submit', function (e) {
            e.preventDefault();

            // Hide the modal using Bootstrap 5
            if (typeof bootstrap !== 'undefined') {
                let modalInstance = bootstrap.Modal.getInstance(confirmAcceptModal);
                if (!modalInstance) {
                    modalInstance = new bootstrap.Modal(confirmAcceptModal);
                }
                modalInstance.hide();
            } else {
                // fallback: hide manually
                confirmAcceptModal.style.display = 'none';
            }

            // Show overlay
            savingText.innerHTML = "Sending Invoice&hellip;";
            savingOverlay.style.display = 'flex';
            savingOverlay.classList.add('visible');

            // Submit the form after a short delay
            setTimeout(() => {
                acceptForm.submit();
            }, 700);
        });
    }
});
