"""HTML to PDF rendering."""

from io import BytesIO

from django.template.loader import render_to_string


def render_html_to_pdf(template_name, context, request=None):
    html = render_to_string(template_name, context, request=request)
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return None, 'xhtml2pdf is not installed. Run: pip install xhtml2pdf'

    result = BytesIO()
    pdf = pisa.CreatePDF(html.encode('UTF-8'), dest=result, encoding='UTF-8')
    if pdf.err:
        return None, 'PDF generation failed.'
    return result.getvalue(), None
