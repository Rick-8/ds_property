document.addEventListener("DOMContentLoaded", function () {
  // --- Existing Feedback / Missed logic ---
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

  // --- Overlay Lock/Unlock Logic ---
  if (window.JOB_DETAIL_CONTEXT && window.JOB_DETAIL_CONTEXT.isLocked) {
    // Disable all controls except overlay and its Back button
    document.querySelectorAll('input, textarea, select, button').forEach(function(el) {
      if (!el.closest('#lockOverlay')) el.disabled = true;
    });
    document.querySelectorAll('a').forEach(function(link) {
      if (!link.closest('#lockOverlay')) {
        link.style.pointerEvents = "none";
        link.style.opacity = "0.5";
      }
    });

    // Unlock overlay logic (AJAX)
    var unlockForm = document.getElementById('unlockForm');
    if (unlockForm) {
      unlockForm.addEventListener('submit', function(e){
        e.preventDefault();
        var pw = document.getElementById('superuserPassword').value;
        var errorMsg = document.getElementById('unlockError');
        errorMsg.style.display = 'none';

        fetch(window.JOB_DETAIL_CONTEXT.unlockUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.JOB_DETAIL_CONTEXT.csrfToken,
          },
          body: JSON.stringify({ password: pw }),
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            document.getElementById('lockOverlay').style.display = 'none';
            // Re-enable controls if unlocked
            document.querySelectorAll('input, textarea, select, button').forEach(function(el) {
              el.disabled = false;
            });
            document.querySelectorAll('a').forEach(function(link) {
              link.style.pointerEvents = "";
              link.style.opacity = "";
            });
          } else {
            errorMsg.style.display = 'block';
          }
        });
      });
    }
  }
});
