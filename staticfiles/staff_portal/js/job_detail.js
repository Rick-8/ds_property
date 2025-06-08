document.addEventListener("DOMContentLoaded", function () {
  const feedbackInput = document.querySelector('#feedbackInput') || document.querySelector('textarea[name="feedback"]');
  const notCompletedBtn = document.getElementById("notCompletedBtn");
  const feedbackPrompt = document.getElementById("feedbackPrompt");
  const notCompletedForm = document.getElementById("notCompletedForm");
  const confirmMissedBtn = document.getElementById("confirmMissedBtn");

  // Hide the prompt on load
  if (feedbackPrompt) {
    feedbackPrompt.style.display = "none";
  }

  // Check if job is already completed
  const isCompleted = notCompletedBtn?.dataset.isCompleted === "true";
  if (isCompleted && notCompletedBtn) {
    notCompletedBtn.disabled = true;
    notCompletedBtn.title = "Job already completed";
    return;  // Exit script early to skip further logic
  }

  // Enable or disable the 'Not Completed' button based on feedback presence
  function checkFeedback() {
    const hasFeedback = feedbackInput && feedbackInput.value.trim().length > 0;

    if (notCompletedBtn) {
      notCompletedBtn.disabled = !hasFeedback;
    }

    if (feedbackPrompt && !hasFeedback) {
      feedbackPrompt.style.display = "block";
    } else if (feedbackPrompt && hasFeedback) {
      feedbackPrompt.style.display = "none";
    }
  }

  // Monitor input in feedback box
  if (feedbackInput) {
    feedbackInput.addEventListener("input", checkFeedback);
  }

  // Prevent modal opening if button is disabled
  if (notCompletedBtn) {
    notCompletedBtn.addEventListener("click", function (e) {
      if (notCompletedBtn.disabled && feedbackPrompt) {
        e.preventDefault();
        feedbackPrompt.style.display = "block";
      }
    });
  }

  // Handle modal confirmation button
  if (confirmMissedBtn) {
    confirmMissedBtn.addEventListener("click", function () {
      const hasFeedback = feedbackInput && feedbackInput.value.trim().length > 0;

      if (!hasFeedback) {
        if (feedbackPrompt) feedbackPrompt.style.display = "block";
        return;
      }

      if (notCompletedForm) {
        notCompletedForm.submit();
      }
    });
  }

  // Run the check on page load
  checkFeedback();
});
