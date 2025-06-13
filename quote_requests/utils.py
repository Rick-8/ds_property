from weasyprint import HTML
from django.template.loader import render_to_string
import tempfile


def generate_invoice_pdf(quote):
    html_string = render_to_string("quote_requests/invoice_pdf.html", {'quote': quote})
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(string=html_string).write_pdf(target=pdf_file.name)
    return pdf_file
