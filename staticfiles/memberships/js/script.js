 document.addEventListener('DOMContentLoaded', function() {
        const cancelConfirmationModal = document.getElementById('cancelConfirmationModal');
        const confirmCancelButton = document.getElementById('confirmCancelButton');
        let currentAgreementId = null;

        cancelConfirmationModal.addEventListener('show.bs.modal', function (event) {
            // Button that triggered the modal
            const button = event.relatedTarget;
            // Extract info from data-bs-* attributes
            currentAgreementId = button.getAttribute('data-agreement-id');
            const packageName = button.getAttribute('data-agreement-name');
            const propertyAddress = button.getAttribute('data-property-address');

            // Update the modal's content.
            const modalPackageName = cancelConfirmationModal.querySelector('#modalPackageName');
            const modalPropertyAddress = cancelConfirmationModal.querySelector('#modalPropertyAddress');

            modalPackageName.textContent = packageName;
            modalPropertyAddress.textContent = propertyAddress; // This line should now work correctly
        });

        confirmCancelButton.addEventListener('click', function() {
            if (currentAgreementId) {
                // Hide the modal immediately
                const modal = bootstrap.Modal.getInstance(cancelConfirmationModal);
                modal.hide();

                // Make an AJAX request to cancel the agreement
                fetch(`/memberships/cancel-agreement/${currentAgreementId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken') // Function to get CSRF token
                    },
                    body: JSON.stringify({}) // Empty body for POST request
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
                        // Reload the page or update the table row
                        window.location.reload();
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred during cancellation: ' + error.message);
                });
            }
        });

        // Helper function to get CSRF token
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    });