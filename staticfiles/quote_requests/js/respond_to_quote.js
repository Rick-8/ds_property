document.addEventListener('DOMContentLoaded', function() {
    var confirmModal = document.getElementById('confirmModal');
    var confirmForm = document.getElementById('confirmForm');
    var modalLabel = document.getElementById('confirmModalLabel');
    var modalBody = document.getElementById('confirmModalBody');
    var submitBtn = document.getElementById('confirmModalSubmit');

    confirmModal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget;
        var action = button.getAttribute('data-action');
        var formAction = button.getAttribute('data-form-action');

        // Set form action URL
        confirmForm.action = formAction;

        // Customise modal text/title/button depending on action
        if (action === 'accept') {
            modalLabel.textContent = 'Accept Quote & Pay';
            modalBody.textContent = 'Are you sure you want to accept this quote and proceed to payment?';
            submitBtn.textContent = 'Accept & Pay';
            submitBtn.className = 'btn btn-gold';
        } else if (action === 'decline') {
            modalLabel.textContent = 'Decline Quote';
            modalBody.textContent = 'Are you sure you want to decline this quote? This cannot be undone.';
            submitBtn.textContent = 'Decline Quote';
            submitBtn.className = 'btn btn-outline-gold';
        }
    });
});