document.addEventListener('DOMContentLoaded', function () {
    const cancelModal = document.getElementById('cancelConfirmationModal');
    const modalPackageName = document.getElementById('modalPackageName');
    const modalPropertyAddress = document.getElementById('modalPropertyAddress');
    const cancelForm = document.getElementById('cancelForm');

    if (!cancelModal || !cancelForm || !modalPackageName || !modalPropertyAddress) {
        console.error('Required modal elements not found.');
        return;
    }

    cancelModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        if (!button) {
            console.warn('No button triggered the modal.');
            return;
        }

        const agreementId = button.getAttribute('data-agreement-id');
        const packageName = button.getAttribute('data-agreement-name') || 'this';
        const propertyAddress = button.getAttribute('data-property-address') || '';

        if (!agreementId) {
            console.warn('No agreement ID found on the triggering button.');
            return;
        }

        modalPackageName.textContent = packageName;
        modalPropertyAddress.textContent = propertyAddress;

        cancelForm.action = `/memberships/cancel-agreement/${agreementId}/`;
    });

    cancelForm.addEventListener('submit', function (event) {
        event.preventDefault();

        if (!cancelForm.action || cancelForm.action.trim() === '') {
            console.error('Cancel form action is not set. Submission prevented.');
            alert('Something went wrong. Please try again.');
            return;
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
        const csrftoken = getCookie('csrftoken');

        fetch(cancelForm.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network error: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const modalInstance = bootstrap.Modal.getInstance(cancelModal);
                if (modalInstance) modalInstance.hide();

                window.location.href = data.redirect_url || '/memberships/all-subscriptions/';
            } else {
                alert('Cancellation failed: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error during cancellation:', error);
            alert('An error occurred while trying to cancel the agreement. Please try again later.');
        });
    });
});
