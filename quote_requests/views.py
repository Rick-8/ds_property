from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from django.contrib import messages
from django.urls import reverse
from django.core.mail import mail_admins
from .utils import generate_invoice_pdf
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from .models import QuoteRequest, QuoteItem
from .forms import QuoteRequestForm
from accounts.models import Property
from staff_portal.models import Job
from decimal import Decimal
import stripe
import tempfile
from django.contrib.auth.decorators import login_required
from datetime import date
from memberships.models import ServiceAgreement
from xhtml2pdf import pisa
from django.template.loader import get_template


@login_required
def my_quotes(request):
    quotes = QuoteRequest.objects.filter(customer=request.user).order_by('-submitted_at')
    return render(request, 'quote_requests/my_quotes.html', {'quotes': quotes})


# Public view for customers to submit a quote request
def request_quote_view(request):
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.status = 'PENDING'
            if request.user.is_authenticated:
                quote.customer = request.user
            quote.save()

            mail_admins(
                subject='New Quote Request Submitted',
                message = f'Quote Request #{quote.pk} from {quote.name} has been submitted.'
            )

            messages.success(request, "Your quote request has been submitted successfully!")
            return redirect('home')
    else:
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'phone': getattr(request.user.profile, 'phone', ''),
            }
            form = QuoteRequestForm(initial=initial_data, user=request.user)
        else:
            form = QuoteRequestForm(user=request.user)

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
    from quote_requests.utils import generate_invoice_pdf  # make sure this function exists
    from django.core.mail import EmailMessage
    from django.utils.html import strip_tags
    from django.template.loader import render_to_string

    quote = get_object_or_404(QuoteRequest, pk=pk)

    if quote.status == 'PENDING':
        # Update status
        quote.status = 'AWAITING_PAYMENT'
        quote.payment_status = 'UNPAID'
        quote.calculate_totals()
        quote.save()

        # Generate PDF invoice
        pdf_file = generate_invoice_pdf(quote)

        # Create Stripe Checkout session
        YOUR_DOMAIN = 'https://ds-property-group-04ec2ca20d25.herokuapp.com'
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Quote #{quote.pk} Payment',
                    },
                    'unit_amount': int(quote.total_price * 100),  # Stripe uses cents
                },
                'quantity': 1,
            }],
            metadata={
                'quote_id': str(quote.pk),
                'user_id': str(quote.customer.id if quote.customer else ''),
            },
            mode='payment',
            customer_email=quote.email,
            success_url=YOUR_DOMAIN + '/quotes/thank-you/',
            cancel_url=YOUR_DOMAIN + '/quotes/cancel/',
        )

        # Email customer with invoice and link
        subject = f"Your Quote #{quote.pk} – Ready for Payment"
        html_message = render_to_string('emails/send_invoice.html', {
            'quote': quote,
            'checkout_url': session.url,
        })
        plain_message = strip_tags(html_message)

        email = EmailMessage(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [quote.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.attach(f"Quote-{quote.pk}.pdf", pdf_file.read(), 'application/pdf')
        email.send()

        messages.success(request, "Invoice sent to customer. Waiting for payment before job is created.")
    return redirect(reverse('quote_detail', args=[quote.pk]))



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
            if desc.strip():
                QuoteItem.objects.create(
                    quote=quote,
                    description=desc.strip(),
                    quantity=int(qty),
                    unit_price=Decimal(price)
                )

        # Update tax percent and totals
        quote.tax_percent = Decimal(tax_percent)
        quote.calculate_totals()

        # If the user clicked "Save and View PDF", redirect to PDF
        if request.POST.get('view_pdf_after'):
            return redirect(reverse('view_quote_pdf', args=[quote.pk]))

    return redirect('quote_detail', pk=pk)

def mark_quote_reviewed(request, pk):
    quote = get_object_or_404(QuoteRequest, pk=pk)
    quote.status = 'REVIEWED'
    quote.save()
    return redirect('quote_detail', pk=pk)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        quote_id = session.get('metadata', {}).get('quote_id')

        try:
            quote = QuoteRequest.objects.get(pk=quote_id)
        except QuoteRequest.DoesNotExist:
            return HttpResponse(status=404)

        if quote.payment_status != 'PAID':
            # Mark quote as paid
            quote.payment_status = 'PAID'
            quote.status = 'PAID'
            quote.save()

            # Create the Job
            job = Job.objects.create(
                title=f"One-off job for {quote.name}",
                description=quote.description,
                property=quote.property,
                scheduled_date=quote.preferred_date or quote.submitted_at.date(),
                quote_request=quote,
                status='PENDING'
            )
            job.title = f"C{job.id} - {job.title}"
            job.save()

            # Email receipt
            send_mail(
                subject=f"Payment Confirmation – Quote #{quote.pk}",
                message=f"Hi {quote.name},\n\nYour payment has been received. Your job is now scheduled. Thank you!",
                from_email=None,
                recipient_list=[quote.email],
            )

    return HttpResponse(status=200)


def payment_thank_you(request):
    return render(request, 'quote_requests/thanks.html')


def payment_cancelled(request):
    return render(request, 'quote_requests/payment_cancelled.html')


def view_quote_pdf(request, quote_id):
    quote = get_object_or_404(QuoteRequest, pk=quote_id)
    template_path = 'quote_requests/invoice_pdf.html'

    context = {
        'quote': quote,
        'request': request,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Quote-{quote.id}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)
    return response


@require_POST
@user_passes_test(lambda u: u.is_superuser)
def update_quote_description(request, quote_id):
    quote = get_object_or_404(QuoteRequest, pk=quote_id)
    quote.description = request.POST.get("description", "")
    quote.save()
    messages.success(request, "Description updated.")
    return redirect('quote_detail', pk=quote.pk)