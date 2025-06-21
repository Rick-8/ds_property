document.addEventListener('DOMContentLoaded', function () {
  const searchInput = document.getElementById('jobSearchInput');
  if (!searchInput) return;

  searchInput.addEventListener('keyup', function () {
    const query = this.value.trim().toLowerCase();

    // Select visible job entries each time
    // Desktop
    const desktopJobs = document.querySelectorAll('.d-md-block .job-entry');
    // Mobile
    const mobileJobs = document.querySelectorAll('.d-md-none .job-entry');

    [desktopJobs, mobileJobs].forEach(list => {
      list.forEach(entry => {
        const text = entry.textContent.toLowerCase();
        if (text.includes(query)) {
          entry.style.display = '';
        } else {
          entry.style.display = 'none';
        }
      });
    });
  });
});
