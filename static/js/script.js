document.addEventListener('DOMContentLoaded', function() {
    // Try to get modal and button elements
    const cancelConfirmationModal = document.getElementById('cancelConfirmationModal');
    const confirmCancelButton = document.getElementById('confirmCancelButton');
    let currentAgreementId = null;

    if (cancelConfirmationModal) {
        cancelConfirmationModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;

            if (!button) {
                console.warn('Modal show event triggered without relatedTarget button');
                return;
            }

            currentAgreementId = button.getAttribute('data-agreement-id');
            const packageName = button.getAttribute('data-agreement-name');
            const propertyAddress = button.getAttribute('data-property-address');

            const modalPackageName = cancelConfirmationModal.querySelector('#modalPackageName');
            const modalPropertyAddress = cancelConfirmationModal.querySelector('#modalPropertyAddress');

            if (modalPackageName) modalPackageName.textContent = packageName || '';
            if (modalPropertyAddress) modalPropertyAddress.textContent = propertyAddress || '';
        });
    } else {
        console.warn('Cancel confirmation modal element not found.');
    }

    if (confirmCancelButton) {
        confirmCancelButton.addEventListener('click', function() {
            if (currentAgreementId) {
                const modalInstance = bootstrap.Modal.getInstance(cancelConfirmationModal);
                if (modalInstance) modalInstance.hide();

                fetch(`/memberships/cancel-agreement/${currentAgreementId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({})
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errorData => {
                            throw new Error(errorData.error || 'Failed to cancel subscription.');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        window.location.reload();
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred during cancellation: ' + error.message);
                });
            } else {
                console.warn('No agreement ID available to cancel.');
            }
        });
    } else {
        console.warn('Confirm cancel button element not found.');
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
