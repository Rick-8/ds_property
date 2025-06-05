document.addEventListener('DOMContentLoaded', function () {
    var cancelModal = document.getElementById('cancelConfirmationModal');
    if (!cancelModal) return;

    cancelModal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget;
        var agreementId = button.getAttribute('data-agreement-id');
        var agreementName = button.getAttribute('data-agreement-name');
        var propertyAddress = button.getAttribute('data-property-address');

        var modalPackageName = cancelModal.querySelector('#modalPackageName');
        var modalPropertyAddress = cancelModal.querySelector('#modalPropertyAddress');
        var confirmCancelButton = cancelModal.querySelector('#confirmCancelButton');

        modalPackageName.textContent = agreementName;
        modalPropertyAddress.textContent = propertyAddress;
        confirmCancelButton.onclick = function () {
            window.location.href = `/agreements/cancel/${agreementId}/`;
        };
    });
});
