function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(
          cookie.substring(name.length + 1)
        );
        break;
      }
    }
  }
  return cookieValue;
}

function showToast(message) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '2000';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast shadow mb-2';
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');

  toast.innerHTML = `
    <div class="toast-body text-white d-flex justify-content-between align-items-center"
         style="background: rgba(0,0,0,0.4); border: 2px solid gold;">
      <span>${message}</span>
      <button type="button" class="btn-close btn-close-white ms-2"
              data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  container.appendChild(toast);

  const bootstrapToast = new bootstrap.Toast(toast);
  bootstrapToast.show();

  setTimeout(() => toast.remove(), 5000);
}

async function assignJobToRoute(jobId, routeId) {
  try {
    const response = await fetch(`/staff/assign_job_route/${jobId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ route_id: routeId }),
    });

    if (!response.ok)
      throw new Error(`Failed with status ${response.status}`);

    const data = await response.json();
    if (data.success) {
      console.log(`Job ${jobId} assigned to route ${routeId}`);
    } else {
      showToast('Error assigning route: ' + (data.error || 'Unknown error'));
    }
  } catch (error) {
    console.error('assignJobToRoute error:', error);
  }
}

async function assignStaffToJobs(assignments) {
  try {
    const response = await fetch('/staff/assign_job_staff/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(assignments),
    });

    if (!response.ok)
      throw new Error(`Failed with status ${response.status}`);

    const data = await response.json();
    if (data.success) {
      console.log('Staff assigned successfully');
    } else {
      showToast('Error assigning staff: ' + (data.error || 'Unknown error'));
    }
  } catch (error) {
    console.error('assignStaffToJobs error:', error);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.assign-route-btn').forEach(button => {
    button.addEventListener('click', () => {
      const jobId = button.dataset.jobId;
      const routeId = button.dataset.routeId;
      if (jobId && routeId) {
        assignJobToRoute(jobId, routeId);
      } else {
        console.error('Missing jobId or routeId on button dataset');
      }
    });
  });

  const assignStaffForm = document.getElementById('assign-staff-form');
  if (assignStaffForm) {
    assignStaffForm.addEventListener('submit', event => {
      event.preventDefault();

      const assignments = {};
      assignStaffForm.querySelectorAll('select[name^="job_"]').forEach(
        select => {
          const jobKey = select.name;
          const staffId = select.value ? Number(select.value) : null;
          assignments[jobKey] = staffId;
        }
      );

      assignStaffToJobs(assignments);
    });
  }

  document.querySelectorAll('select[name^="assignment_"]').forEach(select => {
    select.addEventListener('change', e => {
      const name = e.target.name;
      const newValue = e.target.value;

      document.querySelectorAll(`select[name="${name}"]`).forEach(s => {
        if (s !== e.target) {
          s.value = newValue;
        }
      });
    });
  });

  const form = document.getElementById('scheduleForm');
  const saveBtn = document.getElementById('saveScheduleBtn');
  const overlay = document.getElementById('saving-overlay');

  if (!form || !saveBtn || !overlay) return;

  form.addEventListener('submit', async event => {
    event.preventDefault();

    overlay.classList.remove('d-none');
    overlay.classList.add('d-flex');
    saveBtn.disabled = true;

    try {
      const formData = new FormData(form);

      for (let pair of formData.entries()) {
        console.log(`Sending: ${pair[0]} = ${pair[1]}`);
      }

      const response = await fetch(form.action, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
      });

      const result = await response.json();

      overlay.classList.remove('d-flex');
      overlay.classList.add('d-none');
      saveBtn.disabled = false;

      if (result.success) {
        showToast('✅ Schedule saved successfully.');
      } else {
        showToast('❌ Error: ' + (result.error || 'Unknown error.'));
      }
    } catch (err) {
      console.error('Schedule save failed:', err);
      overlay.classList.remove('d-flex');
      overlay.classList.add('d-none');
      saveBtn.disabled = false;
      showToast('❌ Save failed: ' + err.message);
    }
  });
});
