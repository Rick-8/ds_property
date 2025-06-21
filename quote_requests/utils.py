from weasyprint import HTML
from django.template.loader import render_to_string
import tempfile
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO


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