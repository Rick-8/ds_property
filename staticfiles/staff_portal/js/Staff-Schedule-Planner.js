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

    if (!response.ok) throw new Error(`Failed with status ${response.status}`);

    const data = await response.json();
    if (data.success) {
      console.log(`Job ${jobId} assigned to route ${routeId}`);
    } else {
      alert('Error assigning route: ' + (data.error || 'Unknown error'));
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

    if (!response.ok) throw new Error(`Failed with status ${response.status}`);

    const data = await response.json();
    if (data.success) {
      console.log('Staff assigned successfully');
    } else {
      alert('Error assigning staff: ' + (data.error || 'Unknown error'));
    }
  } catch (error) {
    console.error('assignStaffToJobs error:', error);
  }
}

async function saveSchedule(formElement) {
  try {
    const formData = new FormData(formElement);
    const response = await fetch('/staff/save_schedule/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: formData,
    });

    if (!response.ok) throw new Error(`Failed with status ${response.status}`);

    const data = await response.json();
    if (data.success) {
      console.log('Schedule saved successfully');
      alert('Schedule saved!');
    } else {
      alert('Error saving schedule: ' + (data.error || 'Unknown error'));
    }
  } catch (error) {
    console.error('saveSchedule error:', error);
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
      assignStaffForm.querySelectorAll('select[name^="job_"]').forEach(select => {
        const jobKey = select.name;
        const staffId = select.value ? Number(select.value) : null;
        assignments[jobKey] = staffId;
      });

      assignStaffToJobs(assignments);
    });
  }

  const scheduleForm = document.getElementById('schedule-form');
  if (scheduleForm) {
    scheduleForm.addEventListener('submit', event => {
      event.preventDefault();
      saveSchedule(scheduleForm);
    });
  }
});
