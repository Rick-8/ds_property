// Check if staff for midnight logout
window.isStaff = window.isStaff || false;

// Splash screen handler
window.addEventListener('load', () => {
    const splash = document.getElementById('animated-splash');
    if (splash) {
        console.log("Splash screen displayed to user.");
        setTimeout(() => splash.remove(), 3000);
    }
});

// Modal + cancellation handling
document.addEventListener('DOMContentLoaded', function () {
    const cancelConfirmationModal = document.getElementById('cancelConfirmationModal');
    const confirmCancelButton = document.getElementById('confirmCancelButton');
    let currentAgreementId = null;

    if (cancelConfirmationModal) {
        cancelConfirmationModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            if (!button) return;

            currentAgreementId = button.getAttribute('data-agreement-id');
            const packageName = button.getAttribute('data-agreement-name');
            const propertyAddress = button.getAttribute('data-property-address');

            cancelConfirmationModal.querySelector('#modalPackageName').textContent = packageName || '';
            cancelConfirmationModal.querySelector('#modalPropertyAddress').textContent = propertyAddress || '';
        });
    }

    if (confirmCancelButton) {
        confirmCancelButton.addEventListener('click', function () {
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
            }
        });
    }

    // Set daily forced logout for staff
    if (window.location.pathname !== "/accounts/login/" && window.isStaff) {
        const sessionMarker = localStorage.getItem('staffSessionActive');
        if (!sessionMarker) {
            localStorage.setItem('staffSessionActive', new Date().toISOString());
        }
        forceLogoutAtMidnight();
    }
});

// Midnight forced logout
function forceLogoutAtMidnight() {
    const now = new Date();
    const nextMidnight = new Date();
    nextMidnight.setHours(24, 0, 0, 0);
    const msUntilMidnight = nextMidnight - now;

    setTimeout(() => {
        localStorage.removeItem('staffSessionActive');
        window.location.href = "/accounts/logout/";
    }, msUntilMidnight);
}

// CSRF helper
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
