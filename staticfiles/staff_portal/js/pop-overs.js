(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]:not([data-popover-initialized])');
    popoverTriggerList.forEach(triggerEl => {
      new bootstrap.Popover(triggerEl, {
        sanitize: false, // Allow raw HTML in popover content (your form)
      });
      triggerEl.setAttribute('data-popover-initialized', 'true');
    });
  });

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
  let isSubmitting = false;

  document.addEventListener('submit', function (e) {
    if (e.target.matches('.assign-route-form')) {
      e.preventDefault();

      if (isSubmitting) return; // prevent duplicate submits
      isSubmitting = true;

      const form = e.target;
      const jobId = form.dataset.jobId;
      const routeId = form.route_id.value;
      const scheduledDate = form.scheduled_date.value;

      fetch(`/staff/jobs/${jobId}/assign_route/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ route_id: routeId, scheduled_date: scheduledDate }),
      })
      .then(res => {
        isSubmitting = false;
        if (!res.ok) {
          throw new Error('Network response was not OK');
        }
        return res.json();
      })
      .then(data => {
        if (data.success) {
          location.reload();
        } else {
          alert('Error: ' + data.error);
        }
      })
      .catch(error => {
        isSubmitting = false;
        console.error('Fetch error:', error);
        alert('An error occurred while assigning the route.');
      });
    }
  });
})();
