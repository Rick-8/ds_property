from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from django.contrib import messages
from django.urls import reverse
from django.core.mail import mail_admins
from .utils import generate_invoice_pdf

from .models import QuoteRequest, QuoteItem
from .forms import QuoteRequestForm
from accounts.models import Property
from staff_portal.models import Job
from decimal import Decimal
import stripe
import tempfile


# Public view for customers to submit a quote request
def request_quote_view(request):
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST, request.FILES)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.status = 'PENDING'

            # If the user is logged in, attach them to the quote
            if request.user.is_authenticated:
                quote.customer = request.user

            quote.save()

            # Notify superusers/admins via email
            mail_admins(
                subject='New Quote Request Submitted',
                message=f'Quote Request #{quote.pk} from {quote.full_name} has been submitted.'
            )

            messages.success(request, "Your quote request has been submitted successfully!")
            return redirect('home')
    else:
        form = QuoteRequestForm()

    return render(request, 'quote_requests/request_quote.html', {'form': form})


# Superuser-only: list all quote requests
@user_passes_test(lambda u: u.is_superuser)
def admin_quote_list(request):
    quotes = QuoteRequest.objects.all().order_by('-submitted_at')
    return render(request, 'quote_requests/admin_quote_list.html', {'quotes': quotes})


# Superuser-only: detail view of a specific quote
@user_passes_test(lambda u: u.is_superuser)
def quote_detail_view(request, pk):
    quote = get_object_or_404(QuoteRequest, pk=pk)
    return render(request, 'quote_requests/quote_detail.html', {'quote': quote})


# Superuser-only: accept a quote and create a Job
stripe.api_key = settings.STRIPE_SECRET_KEY

@require_POST
@user_passes_test(lambda u: u.is_superuser)
def accept_quote(request, pk):
    quote = get_object_or_404(QuoteRequest, pk=pk)

    if quote.status == 'PENDING':
        # Make sure totals are fresh
        quote.calculate_totals()

        # Create Stripe Checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(quote.total * 100),  # Stripe uses cents
                    'product_data': {
                        'name': f"Invoice for Quote #{quote.pk}"
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('quote_payment_success', args=[quote.pk])),
            cancel_url=request.build_absolute_uri(reverse('quote_detail', args=[quote.pk])),
            metadata={'quote_id': quote.pk}
        )

        # Update quote status and store session ID
        quote.status = 'AWAITING_PAYMENT'
        quote.payment_status = 'UNPAID'
        quote.stripe_session_id = session.id
        quote.save()

        # Generate invoice PDF
        pdf_file = generate_invoice_pdf(quote)

        # Send email with payment link and invoice
        email = EmailMessage(
            subject=f"Invoice for Quote #{quote.pk}",
            body=(
                f"Dear {quote.name},\n\n"
                f"Please find your invoice attached.\n\n"
                f"To securely pay online, click the link below:\n\n"
                f"{session.url}\n\n"
                f"Once payment is confirmed, we'll schedule your job.\n\n"
                f"Thank you,\nDS Property Group"
            ),
            to=[quote.email],
        )
        email.attach_file(pdf_file.name)
        email.send()

        messages.success(request, "Invoice sent to customer with payment link.")

    return redirect('quote_detail', pk=pk)


# Superuser-only: decline a quote
@user_passes_test(lambda u: u.is_superuser)
def decline_quote(request, pk):
    quote = get_object_or_404(QuoteRequest, pk=pk)
    if quote.status == 'PENDING':
        quote.status = 'DECLINED'
        quote.save()
        messages.info(request, "Quote declined.")
    return redirect(reverse('quote_detail', args=[quote.pk]))


@staff_member_required
def update_quote_notes(request, pk):
    quote = get_object_or_404(QuoteRequest, pk=pk)
    if request.method == 'POST':
        quote.admin_notes = request.POST.get('admin_notes', '')
        quote.save()
    return redirect('quote_detail', pk=pk)


def update_quote_items(request, pk):
    quote = get_object_or_404(QuoteRequest, pk=pk)

    if request.method == 'POST':
        # Clear old items
        quote.items.all().delete()

        # Get all item fields from POST
        descriptions = request.POST.getlist('description')
        quantities = request.POST.getlist('quantity')
        unit_prices = request.POST.getlist('unit_price')
        tax_percent = request.POST.get('tax_percent', 0)

        # Save each new item
        for desc, qty, price in zip(descriptions, quantities, unit_prices):
            if desc.strip():  # ignore blank lines
                QuoteItem.objects.create(
                    quote=quote,
                    description=desc.strip(),
                    quantity=int(qty),
                    unit_price=Decimal(price)
                )

        # Update tax percent and totals
        quote.tax_percent = Decimal(tax_percent)
        quote.calculate_totals()

    return redirect('quote_detail', pk=pk)


def mark_quote_reviewed(request, pk):
    quote = get_object_or_404(QuoteRequest, pk=pk)
    quote.status = 'REVIEWED'
    quote.save()
    return redirect('quote_detail', pk=pk)
