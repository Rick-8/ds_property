from weasyprint import HTML
import logging
from django.template.loader import render_to_string
import tempfile
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.conf import settings
from django.utils.html import strip_tags
from django.core.mail import EmailMessage
from django.utils import timezone
from staff_portal.models import Job

logger = logging.getLogger(__name__)

def generate_invoice_pdf(quote):
    html_string = render_to_string("quote_requests/invoice_pdf.html", {'quote': quote})
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(string=html_string).write_pdf(target=pdf_file.name)
    return pdf_file

def render_quote_pdf_bytes(quote, request):
    template_path = 'quote_requests/invoice_pdf.html'
    context = {'quote': quote, 'request': request}
    template = get_template(template_path)
    html = template.render(context)
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)
    if pisa_status.err:
        return None
    pdf_file.seek(0)
    return pdf_file.read()

def create_one_off_job_from_quote(quote):
    """
    Idempotently creates a one-off Job from a paid QuoteRequest.
    Sends a confirmation email to the customer (once only).
    """
    try:
        # Make sure we have a property
        prop = quote.related_property
        if not prop:
            logger.error(f"❌ Cannot create job: Quote {quote.pk} has no related_property!")
            return None

        # --- Prevent duplicate jobs/emails ---
        existing_job = Job.objects.filter(quote_request=quote).first()
        if existing_job:
            logger.info(f"⚠️ Job already exists for quote {quote.pk} (Job #{existing_job.pk}). Skipping email.")
            return existing_job

        job = Job.objects.create(
            title=f"C - One-off job for {quote.name}",
            description=quote.description,
            property=prop,
            quote_request=quote,
            status='PENDING',
            scheduled_date=timezone.now().date(),
        )
        job.title = f"C{job.id} - {job.title}"
        job.save()

        # Confirmation email (if template exists)
        subject = f"✅ Payment Received for Quote #{quote.pk}"
        html = render_to_string(
            "quote_requests/emails/quote_paid_confirmation.html",
            {'quote': quote, 'job': job},
        )
        plain = strip_tags(html)
        email = EmailMessage(
            subject,
            plain,
            settings.DEFAULT_FROM_EMAIL,
            [quote.email],
        )
        email.attach_alternative(html, "text/html")
        email.send(fail_silently=True)

        logger.info(f"✅ One-off Job created and confirmation sent for paid quote #{quote.pk}.")
        return job


    except Exception as e:
        logger.error(f"❌ Failed to create one-off job from quote {quote.pk}: {e}", exc_info=True)
        return None
