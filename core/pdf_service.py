import weasyprint
from django.template.loader import render_to_string


def generate_pdf_bytes(invoice, company):
    """Generate PDF bytes for an invoice using WeasyPrint."""
    subtotal = sum(item.total_price_foreign for item in invoice.items.all())
    formatted_items = []
    for item in invoice.items.all():
        formatted_items.append(
            {
                "description": item.description,
                "quantity": f"{item.quantity:.2f}",
                "unit_price": f"{item.unit_price_foreign:,.2f}",
                "total_price": f"{item.total_price_foreign:,.2f}",
            }
        )
    html_string = render_to_string(
        "core/invoice_pdf.html",
        {
            "invoice": invoice,
            "company": company,
            "items": formatted_items,
            "subtotal": f"{subtotal:,.2f}",
        },
    )
    html = weasyprint.HTML(string=html_string)
    return html.write_pdf()
