// script.js

document.addEventListener('DOMContentLoaded', function() {
    const cancelConfirmationModal = document.getElementById('cancelConfirmationModal');
    const confirmCancelButton = document.getElementById('confirmCancelButton');
    let currentAgreementId = null;

    // When modal is shown, populate it with data from the clicked button
    cancelConfirmationModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        currentAgreementId = button.getAttribute('data-agreement-id');
        const packageName = button.getAttribute('data-agreement-name');
        const propertyAddress = button.getAttribute('data-property-address');

        const modalPackageName = cancelConfirmationModal.querySelector('#modalPackageName');
        const modalPropertyAddress = cancelConfirmationModal.querySelector('#modalPropertyAddress');

        modalPackageName.textContent = packageName || '';
        modalPropertyAddress.textContent = propertyAddress || '';
    });

    // On confirm button click, send POST request to cancel the agreement
    confirmCancelButton.addEventListener('click', function() {
        if (!currentAgreementId) {
            alert('No agreement selected for cancellation.');
            return;
        }

        // Hide the modal immediately
        const modalInstance = bootstrap.Modal.getInstance(cancelConfirmationModal);
        modalInstance.hide();

        // Send POST request to cancel agreement
        fetch(`/memberships/cancel-agreement/${currentAgreementId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            credentials: 'same-origin',
            body: JSON.stringify({}) // empty body
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(errData.error || 'Failed to cancel subscription.');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert(data.message || 'Subscription cancelled successfully.');
                window.location.reload();
            } else {
                alert('Error: ' + (data.error || 'Unknown error occurred.'));
            }
        })
        .catch(error => {
            console.error('Cancellation error:', error);
            alert('An error occurred during cancellation: ' + error.message);
        });
    });

    // Helper function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
