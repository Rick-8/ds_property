document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('scheduleForm');
  const saveBtn = document.getElementById('saveScheduleBtn');
  const overlay = document.getElementById('saving-overlay');

  if (!form || !saveBtn || !overlay) {
    console.error('Save overlay: Required elements missing.');
    return;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    overlay.classList.remove('d-none');
    overlay.classList.add('d-flex');
    saveBtn.disabled = true;

    try {
      const formData = new FormData(form);

      const response = await fetch(form.action, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();

      if (data.success) {
        overlay.classList.remove('d-flex');
        overlay.classList.add('d-none');
        saveBtn.disabled = false;

      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (error) {
      console.error('Save failed:', error);

      overlay.classList.remove('d-flex');
      overlay.classList.add('d-none');
      saveBtn.disabled = false;

      alert('Error saving schedule: ' + error.message);
    }
  });
});
