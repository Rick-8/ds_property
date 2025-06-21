document.addEventListener('DOMContentLoaded', function () {
    const acceptForm = document.getElementById('acceptQuoteForm');
    if (acceptForm) {
        acceptForm.addEventListener('submit', function () {
            document.querySelector('.saving-text').innerHTML = "Sending Invoice&hellip;";
            showSavingOverlay(true);
        });
    }
});
