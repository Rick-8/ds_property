// --- Calculate totals and update review/accept button ---
function updateTotals() {
    const rows = document.querySelectorAll('.quote-item');
    let subtotal = 0;
    rows.forEach(row => {
        const qty = parseFloat(row.querySelector('input[name="quantity"]').value || 0);
        const price = parseFloat(row.querySelector('input[name="unit_price"]').value || 0);
        subtotal += qty * price;
    });

    const taxPercent = parseFloat(document.getElementById('taxPercent').value || 0);
    const tax = subtotal * (taxPercent / 100);
    const finalTotal = subtotal + tax;

    document.getElementById('subtotal').textContent = subtotal.toFixed(2);
    document.getElementById('taxAmount').textContent = tax.toFixed(2);
    document.getElementById('finalTotal').textContent = finalTotal.toFixed(2);

    setReviewAcceptBtnState();
}

// --- Update the Review/Accept button state based on status and total ---
window.setReviewAcceptBtnState = function () {
    const btn = document.getElementById('reviewAcceptBtn');
    const wrapper = document.getElementById('reviewAcceptBtnWrapper');
    const total = parseFloat(document.getElementById('finalTotal').textContent || "0");

    // Remove any previous tooltip instance
    if (wrapper) {
        let prevTip = bootstrap.Tooltip.getInstance(wrapper);
        if (prevTip) prevTip.dispose();
        wrapper.removeAttribute('data-bs-toggle');
        wrapper.removeAttribute('title');
    }

    if (!btn) return;

    if (window.quoteStatus === 'PENDING') {
        btn.classList.remove('btn-outline-green');
        btn.classList.add('btn-outline-gold');
        btn.textContent = "Review";
        btn.disabled = false; // Always enabled in PENDING!
    } else if (window.quoteStatus === 'REVIEWED') {
        btn.classList.remove('btn-outline-gold');
        btn.classList.add('btn-outline-green');
        btn.textContent = "Accept";
        if (total > 0) {
            btn.disabled = false;
        } else {
            btn.disabled = true;
            // Set tooltip on the span only when disabled in ACCEPT mode
            if (wrapper) {
                wrapper.setAttribute('data-bs-toggle', 'tooltip');
                wrapper.setAttribute('title', 'Build job quote first please');
                new bootstrap.Tooltip(wrapper);
            }
        }
    }
};

// Patch updateTotals so setReviewAcceptBtnState always runs after
updateTotals = (function (orig) {
    return function () {
        orig.apply(this, arguments);
        setReviewAcceptBtnState();
    }
})(updateTotals);

// --- DOM Ready ---
document.addEventListener('DOMContentLoaded', function () {
    // Add Item button
    document.getElementById('addItemBtn').addEventListener('click', function () {
        const container = document.getElementById('itemsContainer');
        const div = document.createElement('div');
        div.className = 'row mb-2 quote-item dark-opaque p-2 rounded gx-1 gy-2 align-items-center';
        div.innerHTML = `
            <div class="col-12 col-md-6 mb-2 mb-md-0">
                <input type="text" name="description" class="form-control" placeholder="Description" required>
            </div>
            <div class="col-6 col-md-2 mb-2 mb-md-0">
                <input type="number" name="quantity" class="form-control" value="1" min="1" required>
            </div>
            <div class="col-6 col-md-3 mb-2 mb-md-0">
                <input type="number" name="unit_price" class="form-control unit-price" step="0.01" placeholder="Unit Price" required>
            </div>
            <div class="col-12 col-md-1 d-flex align-items-center justify-content-end justify-content-md-center">
                <button type="button" class="btn btn-sm btn-danger remove-item" aria-label="Remove item">&times;</button>
            </div>`;
        container.appendChild(div);
        updateTotals();
    });

    // Input listeners (quantity, price, tax)
    document.addEventListener('input', function (e) {
        if (e.target.matches('.unit-price') || e.target.name === 'quantity' || e.target.id === 'taxPercent') {
            updateTotals();
        }
    });

    // Remove item handler
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-item')) {
            e.target.closest('.quote-item').remove();
            updateTotals();
        }
    });

    // View Quote PDF
    document.getElementById('viewQuoteBtn').addEventListener('click', function (e) {
        e.preventDefault();
        const form = document.getElementById('quoteForm');
        let input = form.querySelector('input[name="view_pdf_after"]');
        if (!input) {
            input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'view_pdf_after';
            form.appendChild(input);
        }
        input.value = '1';
        const formData = new FormData(form);
        fetch(form.action, {
            method: "POST",
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: formData
        }).then(response => {
            if (response.redirected) {
                window.open(response.url, '_blank');
            } else {
                window.open(window.quotePDFUrl, '_blank');
            }
        }).catch(() => {
            window.open(window.quotePDFUrl, '_blank');
        });
    });

    // Initialize totals and button state on page load
    updateTotals();

    // Review & Accept button click handler
    const reviewAcceptBtn = document.getElementById('reviewAcceptBtn');
    if (reviewAcceptBtn) {
        reviewAcceptBtn.addEventListener('click', function () {
            if (reviewAcceptBtn.disabled) return;
            if (window.quoteStatus === 'PENDING') {
                fetch(window.markReviewedUrl, {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(function () { window.location.reload(); })
                .catch(function () { alert("Failed to review quote. Please try again."); });
            } else if (window.quoteStatus === 'REVIEWED') {
                // ---- Save quote before showing modal ----
                const quoteForm = document.getElementById('quoteForm');
                const formData = new FormData(quoteForm);

                // Submit form via AJAX POST to save latest changes
                fetch(quoteForm.action, {
                    method: "POST",
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': quoteForm.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: formData
                })
                .then(function (resp) {
                    // Always show modal (whether or not anything changed)
                    var modal = new bootstrap.Modal(document.getElementById('confirmAcceptModal'));
                    modal.show();
                })
                .catch(function () {
                    alert("Could not save quote changes before sending invoice. Try again.");
                });
            }
        });
    }

    // --- Modal accept button handler to submit the form ---
    var confirmAcceptBtn = document.querySelector('#confirmAcceptModal .btn-outline-green');
    if (confirmAcceptBtn) {
        confirmAcceptBtn.addEventListener('click', function () {
            var acceptForm = document.querySelector('#confirmAcceptModal form');
            if (acceptForm) {
                // Disable button to prevent double submit
                confirmAcceptBtn.disabled = true;
                acceptForm.submit();
            }
        });
    }
});
