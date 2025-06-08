document.addEventListener('DOMContentLoaded', function () {
  const searchInput = document.getElementById('jobSearchInput');
  const jobEntries = document.querySelectorAll('.job-entry');

  searchInput.addEventListener('keyup', function () {
    const query = this.value.trim().toLowerCase();

    jobEntries.forEach(entry => {
      const text = entry.textContent.toLowerCase();
      if (text.includes(query)) {
        entry.style.display = '';
      } else {
        entry.style.display = 'none';
      }
    });
  });
});
