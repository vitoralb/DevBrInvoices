from dateutil.relativedelta import relativedelta
from core.utils.formatters import format_money_pt_br, format_cnpj

# Backward compatibility alias
_format_money_pt_br = format_money_pt_br


PT_BR_MONTHS = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def apply_invoice_macros(text, invoice, language="en", extra_context=None):
    if not text:
        return text

    last_day_prev_month = invoice.issue_date.replace(day=1) - relativedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)

    if language == "pt-br":
        invoice_date_str = invoice.issue_date.strftime("%d/%m/%Y")
        prev_month_start_str = first_day_prev_month.strftime("%d/%m/%Y")
        prev_month_end_str = last_day_prev_month.strftime("%d/%m/%Y")
        prev_month_name = PT_BR_MONTHS[last_day_prev_month.month]
    else:
        invoice_date_str = invoice.issue_date.strftime("%Y-%m-%d")
        prev_month_start_str = first_day_prev_month.strftime("%Y-%m-%d")
        prev_month_end_str = last_day_prev_month.strftime("%Y-%m-%d")
        prev_month_name = last_day_prev_month.strftime("%B")

    replacements = {
        "{{ invoice_date }}": invoice_date_str,
        "{{ prev_month_start }}": prev_month_start_str,
        "{{ prev_month_end }}": prev_month_end_str,
        "{{ prev_month_name }}": prev_month_name,
        "{{ prev_month_year }}": last_day_prev_month.strftime("%Y"),
        "{{ month_info }}": f"{prev_month_name} {last_day_prev_month.strftime('%Y')}",
        "{{ invoice_number }}": invoice.invoice_number,
        "{{ currency }}": invoice.currency,
        "{{ client_name }}": invoice.client.name,
    }

    from core.models import CompanySettings

    company = CompanySettings.load()
    if company and company.cnpj:
        replacements["{{ company_cnpj }}"] = format_cnpj(company.cnpj)

    try:
        val = invoice.total_foreign if invoice.total_foreign is not None else 0.0
        if language == "pt-br":
            replacements["{{ value_original }}"] = format_money_pt_br(val)
        else:
            replacements["{{ value_original }}"] = f"{val:,.2f}"
    except:
        replacements["{{ value_original }}"] = "0,00" if language == "pt-br" else "0.00"

    try:
        val = invoice.total_brl if invoice.total_brl is not None else 0.0
        if language == "pt-br":
            replacements["{{ value_brl }}"] = _format_money_pt_br(val)
        else:
            replacements["{{ value_brl }}"] = f"{val:,.2f}"
    except:
        replacements["{{ value_brl }}"] = "0,00" if language == "pt-br" else "0.00"

    if invoice.exchange_rate_to_brl is not None:
        if language == "pt-br":
            replacements["{{ exchange_rate }}"] = format_money_pt_br(
                invoice.exchange_rate_to_brl, decimals=4
            )
        else:
            replacements["{{ exchange_rate }}"] = f"{invoice.exchange_rate_to_brl:,.4f}"
    else:
        replacements["{{ exchange_rate }}"] = (
            "0,0000" if language == "pt-br" else "0.0000"
        )

    replacements["{{ effective_tax_rate }}"] = (
        "0,00" if language == "pt-br" else "0.00"
    )
    replacements["{{ nominal_tax_rate }}"] = (
        "0,00" if language == "pt-br" else "0.00"
    )

    if extra_context:
        from decimal import Decimal

        for k, v in extra_context.items():
            if isinstance(v, Decimal):
                replacements[k] = (
                    format_money_pt_br(v, decimals=2)
                    if language == "pt-br"
                    else f"{v:,.2f}"
                )
            else:
                replacements[k] = str(v)

    for k, v in replacements.items():
        text = text.replace(k, str(v))

    return text


def get_email_content(template_type, invoice, extra_context=None):
    from core.models import EmailTemplate

    template = EmailTemplate.objects.filter(template_type=template_type).first()

    language = "en"
    if template:
        subject = template.subject
        body = template.body
        language = template.language
    else:
        subject = ""
        body = ""

    if invoice:
        subject = apply_invoice_macros(subject, invoice, language)
        body = apply_invoice_macros(body, invoice, language)

    if extra_context:
        from decimal import Decimal

        for k, v in extra_context.items():
            if isinstance(v, Decimal):
                if language == "pt-br":
                    v = (
                        f"{v:,.2f}".replace(",", "_")
                        .replace(".", ",")
                        .replace("_", ".")
                    )
                else:
                    v = f"{v:,.2f}"
            subject = subject.replace(k, str(v))
            body = body.replace(k, str(v))

    return subject, body
