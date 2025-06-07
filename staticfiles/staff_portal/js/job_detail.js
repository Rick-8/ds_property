document.addEventListener("DOMContentLoaded", function () {
  const feedbackInput = document.querySelector('textarea[name="feedback"]');
  const notCompletedBtn = document.getElementById("notCompletedBtn");
  const feedbackPrompt = document.getElementById("feedbackPrompt");
  const notCompletedForm = document.getElementById("notCompletedForm");

  if (feedbackInput && notCompletedBtn) {
    const checkFeedback = () => {
      const hasFeedback = feedbackInput.value.trim().length > 0;
      notCompletedBtn.disabled = !hasFeedback;

      // Hide the prompt if feedback is valid
      if (hasFeedback && feedbackPrompt) {
        feedbackPrompt.style.display = "none";
      } else if (!hasFeedback && feedbackPrompt) {
        feedbackPrompt.style.display = "block";
      }
    };

    feedbackInput.addEventListener("input", checkFeedback);

    // Confirm submission if enabled
    if (notCompletedForm) {
      notCompletedForm.addEventListener("submit", function (e) {
        const hasFeedback = feedbackInput.value.trim().length > 0;
        if (!hasFeedback) {
          e.preventDefault();
          if (feedbackPrompt) feedbackPrompt.style.display = "block";
          return;
        }

        const confirmSubmit = confirm("Are you sure you want to mark this job as not completed?");
        if (!confirmSubmit) {
          e.preventDefault();
        }
      });
    }

    checkFeedback(); // Run once on load
  }
});
