
let savingAnimation = null;

/**
 * Initializes the Lottie animation for the saving overlay.
 * IMPORTANT: The 'path' for the animation needs a global variable or be dynamic
 * if the {% static %} tag cannot be used directly in an external JS file.
 * For now, we'll assume it will be correctly handled by Django's staticfiles,
 * but often you'd pass this via data attributes or a global JS var.
 */
function initSavingOverlay() {
    const container = document.getElementById('savingLottie');
    if (!container) {
        console.warn("Lottie container #savingLottie not found.");
        return;
    }

    // The path here should be relative to your staticfiles serving, or
    // you might need to make it available via a global variable set in the template.
    // Assuming /static/ is the root for static files.
    savingAnimation = lottie.loadAnimation({
        container: container,
        renderer: 'svg',
        loop: true,
        autoplay: false, // Start paused
        path: '/static/animations/tree-cutting.json', // Direct path, needs /static/ to work
    });
}

/**
 * Shows or hides the saving overlay and controls the animation.
 * @param {boolean} show - True to show, false to hide.
 */
function showSavingOverlay(show = true) {
    const overlay = document.getElementById('savingOverlay');
    if (!overlay || !savingAnimation) {
        console.warn("Saving overlay or animation not initialized.");
        return;
    }

    overlay.style.display = show ? 'flex' : 'none'; // Use flex for centering with CSS
    if (show) {
        savingAnimation.goToAndPlay(0, true); // Play from the start
    } else {
        savingAnimation.stop(); // Stop the animation
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initSavingOverlay(); // Initialize the Lottie animation when the DOM is ready

    const cancelConfirmationModal = document.getElementById('cancelConfirmationModal');
    const cancelForm = document.getElementById('cancelForm'); // The form within the modal
    const confirmCancelButton = document.getElementById('confirmCancelButton'); // The submit button within the form

    // Event listener for when the Bootstrap modal is about to be shown
    if (cancelConfirmationModal) {
        cancelConfirmationModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget; // The "Cancel" button that triggered the modal
            if (!button) {
                console.warn('Modal show event triggered without relatedTarget button.');
                return; // Exit if no button triggered it (unexpected)
            }

            // Extract data from the triggering button's data attributes
            const agreementId = button.getAttribute('data-agreement-id');
            const packageName = button.getAttribute('data-agreement-name');
            const propertyAddress = button.getAttribute('data-property-address');

            // Populate the modal's body content
            const modalBody = cancelConfirmationModal.querySelector('.modal-body');
            if (modalBody) {
                modalBody.innerHTML = `Are you sure you want to cancel the <strong>${packageName}</strong> subscription for <strong>${propertyAddress}</strong>? This action cannot be undone.`;
            }

            // Set the action URL for the form to the specific agreement's cancellation endpoint
            if (cancelForm && agreementId) {
                cancelForm.action = `/memberships/cancel-agreement/${agreementId}/`;
            } else {
                console.warn('Cancel form or agreement ID not found when showing modal.');
            }

            // Reset the confirm button's state in case it was disabled from a previous attempt
            if (confirmCancelButton) {
                confirmCancelButton.disabled = false;
                confirmCancelButton.innerHTML = '<strong>Cancel Subscription</strong>'; // Restore original text
            }
        });
    } else {
        console.warn('Cancel confirmation modal element not found.');
    }

    // Event listener for the form submission
    // This is where we show the overlay and disable the button to prevent multiple submissions
    if (cancelForm) {
        cancelForm.addEventListener('submit', function(event) {
            // IMPORTANT: Do NOT call event.preventDefault() here.
            // We want the form to submit normally, allowing Django to redirect.

            // Hide the modal immediately
            const modalInstance = bootstrap.Modal.getInstance(cancelConfirmationModal);
            if (modalInstance) modalInstance.hide();

            // Show the loading overlay
            showSavingOverlay(true);

            // Disable the submit button to prevent accidental multiple clicks
            if (confirmCancelButton) {
                confirmCancelButton.disabled = true;
                // Change button text to indicate loading, assumes Bootstrap spinner styles
                confirmCancelButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Cancelling...';
            }
        });
    } else {
        console.warn('Cancel form element not found.');
    }
});