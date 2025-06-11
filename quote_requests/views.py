from django.shortcuts import render, redirect, get_object_or_404
from .models import QuoteRequest
from .forms import QuoteRequestForm, QuoteFeedbackForm
from django.core.mail import mail_admins
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.urls import reverse


def request_quote_view(request):
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST, request.FILES)
        if form.is_valid():
            quote = form.save()
            # Notify superusers
            mail_admins("New Quote Request", f"New quote from {quote.name}: {quote.description}")
            messages.success(request, "Your quote request has been submitted.")
            return redirect('quote_thanks')
    else:
        form = QuoteRequestForm()
    return render(request, 'quote_requests/request_quote.html', {'form': form})


@login_required
def quote_review_view(request):
    quotes = QuoteRequest.objects.filter(customer=request.user)
    return render(request, 'quote_requests/my_quotes.html', {'quotes': quotes})


@login_required
def quote_detail_view(request, pk):
    quote = get_object_or_404(QuoteRequest, pk=pk, customer=request.user)
    if request.method == 'POST':
        feedback_form = QuoteFeedbackForm(request.POST, instance=quote)
        if 'accept' in request.POST:
            quote.status = 'ACCEPTED'
            if feedback_form.is_valid():
                feedback_form.save()
            return redirect('start_stripe_payment', quote_id=quote.id)

        elif 'decline' in request.POST:
            quote.status = 'DECLINED'
            if feedback_form.is_valid():
                feedback_form.save()
            quote.status = 'LOCKED'
            quote.save()
            messages.info(request, "Quote declined. Thank you for your feedback.")
            return redirect('quote_review')
    else:
        feedback_form = QuoteFeedbackForm(instance=quote)

    return render(request, 'quote_requests/quote_detail.html', {
        'quote': quote,
        'feedback_form': feedback_form
    })
