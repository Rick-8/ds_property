"""
Quote Requests Views
Handles quote request submissions, admin actions, notifications,
PDF invoice generation, payment, and responses.
"""

from decimal import Decimal
import json
from django.test import TestCase
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import (
    user_passes_test, login_required
)
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMultiAlternatives, mail_admins
from django.http import (
    HttpResponse, JsonResponse
)
from django.shortcuts import (
    render, get_object_or_404, redirect
)
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from .models import QuoteRequest, QuoteItem
from .forms import QuoteRequestForm
from .utils import render_quote_pdf_bytes
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY

# ===============================
# CUSTOMER QUOTE VIEWS
# ===============================


@login_required
def my_quotes(request):
    """
    Show logged-in user's quote requests, ensuring totals are accurate.
    """
    quotes = QuoteRequest.objects.filter(
        customer=request.user
    ).order_by('-submitted_at')

    for quote in quotes:
        quote.calculate_totals()
        quote.save()  # <-- This line is essential

    return render(
        request, 'quote_requests/my_quotes.html', {'quotes': quotes}
    )


def request_quote_view(request):
    """
    Allow users to submit a quote request. Prefill form for authenticated users.
    """
    if request.method == 'POST':
        form = QuoteRequestForm(
            request.POST, request.FILES, user=request.user
        )
        if form.is_valid():
            quote = form.save(commit=False)
            quote.status = 'PENDING'
            if request.user.is_authenticated:
                quote.customer = request.user
            quote.save()

            # Notify all superusers via email
            User = get_user_model()
            superusers = User.objects.filter(
                is_superuser=True
            ).values_list('email', flat=True)
            if superusers:
                subject = f"New Quote Request: {quote.name} - {quote.email}"
                admin_context = {'quote': quote}
                try:
                    admin_html = render_to_string(
                        'quote_requests/emails/quote_notification.html',
                        admin_context
                    )
                    admin_text = strip_tags(admin_html)
                    admin_email = EmailMultiAlternatives(
                        subject,
                        admin_text,
                        settings.DEFAULT_FROM_EMAIL,
                        list(superusers)
                    )
                    admin_email.attach_alternative(
                        admin_html, "text/html"
                    )
                    admin_email.send()
                except Exception as e:
                    print("Superuser email send error:", e)

            mail_admins(
                subject='New Quote Request Submitted',
                message=(
                    f'Quote Request #{quote.pk} from {quote.name} '
                    'has been submitted.'
                )
            )
            messages.success(
                request,
                "Your quote request has been submitted successfully!"
            )
            return redirect('home')
    else:
        if request.user.is_authenticated:
            initial_data = {
                'name': (
                    request.user.get_full_name()
                    or request.user.username
                ),
                'email': request.user.email,
                'phone': getattr(
                    request.user.profile, 'phone', ''
                ),
            }
            form = QuoteRequestForm(
                initial=initial_data, user=request.user
            )
        else:
            form = QuoteRequestForm(user=request.user)

    return render(
        request, 'quote_requests/request_quote.html', {'form': form}
    )

# ===============================
# ADMIN QUOTE VIEWS
# ===============================


@user_passes_test(lambda u: u.is_superuser)
def admin_quote_list(request):
    """
    Superuser view: List all quote requests.
    """
    quotes = QuoteRequest.objects.all().order_by('-submitted_at')
    return render(
        request, 'quote_requests/admin_quote_list.html', {'quotes': quotes}
    )


@user_passes_test(lambda u: u.is_superuser)
def quote_detail_view(request, pk):
    """
    Superuser view: See details for a quote request.
    """
    quote = get_object_or_404(QuoteRequest, pk=pk)
    return render(
        request, 'quote_requests/quote_detail.html', {'quote': quote}
    )


@user_passes_test(lambda u: u.is_superuser)
def decline_quote(request, pk):
    """
    Superuser: Decline a PENDING quote.
    """
    quote = get_object_or_404(QuoteRequest, pk=pk)
    if quote.status == 'PENDING':
        quote.status = 'DECLINED'
        quote.save()
        messages.info(request, "Quote declined.")
    return redirect(reverse('quote_detail', args=[quote.pk]))


@require_POST
@user_passes_test(lambda u: u.is_superuser)
def accept_quote(request, pk):
    """
    Superuser: Accept quote, generate PDF, and email customer & superusers.
    """
    quote = get_object_or_404(QuoteRequest, pk=pk)
    if quote.status == 'REVIEWED':
        try:
            quote.status = 'ACCEPTED'
            quote.calculate_totals()
            quote.save()

            from django.contrib.auth import get_user_model
            User = get_user_model()
            superusers = User.objects.filter(
                is_superuser=True
            ).values_list('email', flat=True)
            if superusers:
                subject = f"Quote Accepted: {quote.name} - {quote.email}"
                admin_context = {'quote': quote}
                try:
                    admin_html = render_to_string(
                        'quote_requests/emails/quote_notification.html',
                        admin_context
                    )
                    admin_text = strip_tags(admin_html)
                    admin_email = EmailMultiAlternatives(
                        subject,
                        admin_text,
                        settings.DEFAULT_FROM_EMAIL,
                        list(superusers)
                    )
                    admin_email.attach_alternative(
                        admin_html, "text/html"
                    )
                    admin_email.send()
                except Exception as e:
                    print("Superuser email send error:", e)

            pdf_bytes = render_quote_pdf_bytes(quote, request)
            if not pdf_bytes:
                raise Exception("Failed to generate PDF for email.")

            from django.conf import settings
            domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
            scheme = 'https' if not settings.DEBUG else 'http'
            response_url = f"{scheme}://{domain}{reverse('respond_to_quote', args=[quote.response_token])}"

            subject = f"Your Quote #{quote.pk} – Please Review and Respond"
            html_message = render_to_string(
                'quote_requests/emails/send_invoice_for_response.html',
                {'quote': quote, 'response_url': response_url}
            )
            plain_message = strip_tags(html_message)
            email = EmailMultiAlternatives(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [quote.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.attach(
                f"Quote-{quote.pk}.pdf", pdf_bytes, 'application/pdf'
            )
            email.send()
        except Exception as e:
            print("EMAIL ERROR:", e)
            messages.error(request, f"Failed to send email: {e}")
        else:
            messages.success(
                request,
                "Quote marked as ACCEPTED and sent to customer."
            )
    else:
        messages.error(
            request,
            f"Quote cannot be accepted while in '{quote.status}' status. "
            "Please click 'Pending Review' first to review and approve the quote."
        )
    return redirect(reverse('quote_detail', args=[quote.pk]))


@staff_member_required
def update_quote_notes(request, pk):
    """
    Staff: Update admin notes on a quote.
    """
    quote = get_object_or_404(QuoteRequest, pk=pk)
    if request.method == 'POST':
        quote.admin_notes = request.POST.get('admin_notes', '')
        quote.save()
    return redirect('quote_detail', pk=pk)


def update_quote_items(request, pk):
    """
    Admin: Update the items (rows) for a quote.
    """
    quote = get_object_or_404(QuoteRequest, pk=pk)

    if request.method == 'POST':
        quote.items.all().delete()
        descriptions = request.POST.getlist('description')
        quantities = request.POST.getlist('quantity')
        unit_prices = request.POST.getlist('unit_price')
        tax_percent = request.POST.get('tax_percent', 0)
        for desc, qty, price in zip(descriptions, quantities, unit_prices):
            if desc.strip():
                QuoteItem.objects.create(
                    quote=quote,
                    description=desc.strip(),
                    quantity=int(qty),
                    unit_price=Decimal(price)
                )
        quote.tax_percent = Decimal(tax_percent)
        quote.calculate_totals()
        if request.POST.get('view_pdf_after'):
            return redirect(reverse('view_quote_pdf', args=[quote.pk]))

    return redirect('quote_detail', pk=pk)


def mark_quote_reviewed(request, pk):
    """
    Admin: Mark quote as reviewed so it can be accepted.
    """
    quote = get_object_or_404(QuoteRequest, pk=pk)
    quote.status = 'REVIEWED'
    quote.save()
    return redirect('quote_detail', pk=pk)


@require_POST
@user_passes_test(lambda u: u.is_superuser)
def update_quote_description(request, quote_id):
    """
    Admin: Update the quote's overall description text.
    """
    quote = get_object_or_404(QuoteRequest, pk=quote_id)
    quote.description = request.POST.get("description", "")
    quote.save()
    messages.success(request, "Description updated.")
    return redirect('quote_detail', pk=quote.pk)


def view_quote_pdf(request, quote_id):
    """
    Generate the quote PDF (identical to the email attachment).
    """
    quote = get_object_or_404(QuoteRequest, pk=quote_id)
    pdf_bytes = render_quote_pdf_bytes(quote, request)
    if not pdf_bytes:
        return HttpResponse('PDF generation failed', status=500)
    response = HttpResponse(
        pdf_bytes, content_type='application/pdf'
    )
    response['Content-Disposition'] = (
        f'filename="Quote-{quote.id}.pdf"'
    )
    return response

# ===============================
# PAYMENT VIEWS
# ===============================


@csrf_exempt
def create_payment_intent(request, quote_id):
    """
    Create Stripe PaymentIntent for the quote. Used by frontend JS.
    """
    if request.method != "POST":
        return JsonResponse({'error': 'POST required'}, status=400)

    try:
        quote = QuoteRequest.objects.get(pk=quote_id)
    except QuoteRequest.DoesNotExist:
        return JsonResponse({'error': 'Quote not found'}, status=404)

    try:
        body = request.body.decode('utf-8')
        data = json.loads(body) if body else {}
        # (data not used here)
        amount = int(Decimal(quote.total) * 100)  # cents
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={'quote_id': str(quote.id)},
            description=f"Payment for Quote #{quote.id}",
        )
        return JsonResponse({'clientSecret': payment_intent.client_secret})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def respond_to_quote(request, token):
    """
    Show quote to customer, display Stripe payment form if appropriate.
    """
    quote = get_object_or_404(QuoteRequest, response_token=token)
    return render(request, 'quote_requests/respond_to_quote.html', {
        'quote': quote,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@require_POST
def respond_decline_quote(request, token):
    """
    Customer declines the quote from their email link.
    """
    quote = get_object_or_404(QuoteRequest, response_token=token)
    if quote.status in ['REVIEWED', 'UNPAID']:
        quote.status = 'DECLINED'
        quote.save()
    return render(
        request, "quote_requests/respond_to_quote.html", {"quote": quote}
    )


def payment_success(request):
    """
    Render the payment success page after Stripe payment.
    """
    return render(request, 'quote_requests/payment_success.html')


def payment_thank_you(request):
    """
    Show the post-payment thank you page.
    """
    return render(request, 'quote_requests/thanks.html')


def payment_cancelled(request):
    """
    Render payment cancelled/failure page.
    """
    return render(request, 'quote_requests/payment_cancelled.html')
