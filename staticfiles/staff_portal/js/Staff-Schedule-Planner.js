document.addEventListener("DOMContentLoaded", () => {
  // Utility: Get CSRF token from cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Elements
  const form = document.getElementById("scheduleForm");
  const msg = document.getElementById("scheduleSuccessMsg");

  if (!form) {
    console.error('Schedule form with id "scheduleForm" not found.');
    return; // stop if no form
  }
  if (!msg) {
    console.warn('Success message element with id "scheduleSuccessMsg" not found.');
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    // No validation for empty fields — allow empty selects to submit

    try {
      const formData = new FormData(form);

      const response = await fetch(saveScheduleUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Network response was not OK (status: ${response.status})`);
      }

      const data = await response.json();

      if (data.success) {
        if (msg) {
          msg.classList.remove("d-none");
          setTimeout(() => msg.classList.add("d-none"), 3000);
        } else {
          alert("Schedule saved successfully.");
        }
      } else {
        alert("Error saving schedule: " + (data.error || "Unknown error"));
        console.error("Server error response:", data);
      }
    } catch (error) {
      console.error("Fetch or JSON parsing error:", error);
      alert("An unexpected error occurred. Please try again later.");
    }
  });
});
