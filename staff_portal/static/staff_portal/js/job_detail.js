document.addEventListener("DOMContentLoaded", function () {
  const feedbackInput = document.querySelector('textarea[name="feedback"]');
  const notCompletedBtn = document.getElementById("notCompletedBtn");
  const feedbackPrompt = document.getElementById("feedbackPrompt");
  const notCompletedForm = document.getElementById("notCompletedForm");

  if (feedbackPrompt) {
    feedbackPrompt.style.display = "none";
  }

  if (feedbackInput && notCompletedBtn) {
    feedbackInput.addEventListener("input", function () {
      const hasFeedback = feedbackInput.value.trim().length > 0;
      notCompletedBtn.disabled = !hasFeedback;

      if (hasFeedback && feedbackPrompt.style.display !== "none") {
        feedbackPrompt.style.display = "none";
      }
    });
  }

  if (notCompletedBtn && feedbackPrompt) {
    notCompletedBtn.parentElement.addEventListener("click", function (e) {
      const hasFeedback = feedbackInput?.value.trim().length > 0;

      if (notCompletedBtn.disabled && !hasFeedback) {
        e.preventDefault();
        feedbackPrompt.style.display = "block";
      }
    });
  }

  if (notCompletedForm && feedbackInput) {
    notCompletedForm.addEventListener("submit", function (e) {
      const hasFeedback = feedbackInput.value.trim().length > 0;

      if (!hasFeedback) {
        e.preventDefault();
        if (feedbackPrompt) feedbackPrompt.style.display = "block";
        return;
      }

      const confirmed = confirm("Are you sure you want to mark this job as not completed?");
      if (!confirmed) {
        e.preventDefault();
      }
    });
  }
});
