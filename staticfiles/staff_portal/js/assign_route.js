document.addEventListener('DOMContentLoaded', function () {
  console.log('assign_route.js loaded');

});

document.addEventListener('DOMContentLoaded', function () {
  var popoverTriggerList = [].slice.call(document.querySelectorAll('.assign-route-btn'));
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  document.body.addEventListener('submit', function (e) {
    if (e.target.classList.contains('assign-route-form')) {
      e.preventDefault();
      const form = e.target;
      const jobId = form.getAttribute('data-job-id');
      const routeId = form.querySelector('select[name="route_id"]').value;

      fetch(`/staff/assign-job/${jobId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ route_id: routeId }),
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          const btn = document.querySelector(`button[data-job-id="${jobId}"]`);
          bootstrap.Popover.getInstance(btn).hide();

          form.closest('li').remove();
        } else {
          alert('Failed to assign route: ' + (data.error || 'Unknown error'));
        }
      })
      .catch(() => alert('Error assigning route.'));
    }
  });

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
