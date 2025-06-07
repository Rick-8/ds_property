  // Delete Modal
document.addEventListener("DOMContentLoaded", function () {
  const deleteModal = document.getElementById('confirmDeleteModal');
  const deleteMessage = document.getElementById('deleteMessage');

  deleteModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget;
    const actionUrl = button.getAttribute('data-action-url');
    const deleteAll = button.getAttribute('data-delete-all');
    const form = document.getElementById('deleteForm');

    form.action = actionUrl;

    if (deleteAll) {
      deleteMessage.textContent = "Are you sure you want to delete ALL jobs? This action is irreversible.";
    } else {
      deleteMessage.textContent = "Are you sure you want to delete this job?";
    }
  });

  // Filter table by Job ID or Property ID or Title
  const searchInput = document.getElementById("searchInput");
  searchInput.addEventListener("input", function () {
    const filter = this.value.toUpperCase();
    const table = document.getElementById("jobsTable");
    const rows = table.getElementsByTagName("tr");

    for (let i = 1; i < rows.length; i++) {
      const jobId = rows[i].getElementsByTagName("td")[0]?.textContent.toUpperCase() || "";
      const title = rows[i].getElementsByTagName("td")[1]?.textContent.toUpperCase() || "";

      if (jobId.includes(filter) || title.includes(filter)) {
        rows[i].style.display = "";
      } else {
        rows[i].style.display = "none";
      }
    }
  });
});
