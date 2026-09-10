from decimal import Decimal
from dateutil.relativedelta import relativedelta
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
from ..models import Invoice, CompanySettings
from ..services import (
    consultar_nfe_na_prefeitura,
    enviar_nfe_para_prefeitura,
    fetch_exchange_rate,
)
from ..pdf_service import generate_pdf_bytes
from ..email_service import send_email_with_debug

logger = get_task_logger(__name__)


def _format_from_email(sender_name: str) -> str:
    """Returns DEFAULT_FROM_EMAIL formatted with display name."""
    addr = settings.DEFAULT_FROM_EMAIL
    if "<" not in addr:
        addr = f"{sender_name} <{addr}>"
    return addr


def _get_pdf_bytes_for_task(invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    company = CompanySettings.load()
    return generate_pdf_bytes(invoice, company)


@shared_task
def finalize_invoice_task(invoice_id, send_to_client=False, send_to_company=False):
    invoice = Invoice.objects.get(id=invoice_id)
    company = CompanySettings.load()

    invoice.status = "FINALIZED"
    invoice.task_id = ""
    invoice.save()

    if send_to_client or send_to_company:
        if company:
            email_invoice_task.delay(
                invoice.id,
                send_to_company=send_to_company,
                send_to_client=send_to_client,
                include_nfse=False,
            )

    return f"Invoice {invoice_id} finalized."


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=20,
    retry_backoff_max=3600,
    max_retries=10,
)
def cancel_invoice_task(self, invoice_id):
    from core.models import NfseLog
    from core.nfse.provider_factory import get_provider

    invoice = Invoice.objects.get(id=invoice_id)

    if hasattr(invoice, "nota_fiscal") and invoice.nota_fiscal:
        if not invoice.nota_fiscal.can_be_canceled:
            raise Exception(
                f"NFS-e {invoice.nota_fiscal.nf_number} foi autorizada há mais de 24 horas e não pode ser cancelada."
            )
        provider = get_provider(invoice)
        try:
            cancel_result = provider.cancelar_nfse(invoice)
            NfseLog.objects.create(
                invoice=invoice,
                origem="System / Celery Cancel",
                payload_enviado=cancel_result.xml_enviado,
                payload_retorno=cancel_result.xml_retorno,
                erro_mensagem=(
                    " | ".join(cancel_result.erros)
                    if not cancel_result.sucesso
                    else None
                ),
            )

            if not cancel_result.sucesso:
                raise Exception(
                    f"Falha ao cancelar NFS-e: {' | '.join(cancel_result.erros)}"
                )
        except Exception as e:
            logger.error(
                "Erro no cancelamento da NFS-e para invoice %s: %s",
                invoice.invoice_number,
                e,
            )

            if self.request.retries >= self.max_retries:
                invoice.task_retry_count = 0
                invoice.task_id = ""
                invoice.status = (
                    "FINALIZED"  # Revert to finalized so they can try again
                )
                invoice.save()

                # Send failure email
                company = CompanySettings.load()
                if company and company.email:
                    short_company_name = " ".join(company.company_name.split()[:3])
                    sender_name = f"{short_company_name} System"
                    from_email_addr = _format_from_email(sender_name)

                    from core.utils.macros import get_email_content

                    subject, body = get_email_content(
                        "COMPANY_CANCEL_FAILED",
                        invoice,
                        extra_context={"{{ error }}": str(e)},
                    )
                    try:
                        send_email_with_debug(
                            subject,
                            body,
                            [company.email],
                            [],
                            from_email_addr,
                            [],
                            company,
                        )
                    except Exception:
                        pass

                raise e
            else:
                invoice.task_retry_count = self.request.retries + 1
                invoice.save()
                raise e

    invoice.task_id = ""
    invoice.task_retry_count = 0
    invoice.status = "CANCELED"
    invoice.save()
    if hasattr(invoice, "nota_fiscal") and invoice.nota_fiscal:
        invoice.nota_fiscal.is_canceled = True
        invoice.nota_fiscal.save()
    return f"Invoice {invoice_id} canceled."


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_backoff_max=600,
    max_retries=3,
)
def email_invoice_task(
    self, invoice_id, send_to_company=False, send_to_client=False, include_nfse=False
):
    invoice = Invoice.objects.get(id=invoice_id)
    company = CompanySettings.load()

    if not company:
        return "Company settings not configured."

    pdf_bytes = _get_pdf_bytes_for_task(invoice.id)
    invoice_pdf_attachment = (
        f"{invoice.invoice_number}.pdf",
        pdf_bytes,
        "application/pdf",
    )
    company_attachments = [invoice_pdf_attachment]

    if include_nfse and hasattr(invoice, "nota_fiscal") and invoice.nota_fiscal:
        nf = invoice.nota_fiscal
        nfse_pdf = None
        if nf.danfse_pdf:
            try:
                if nf.danfse_pdf.storage.exists(nf.danfse_pdf.name):
                    nf.danfse_pdf.open("rb")
                    nfse_pdf = nf.danfse_pdf.read()
            except Exception as e:
                logger.warning("Error reading local danfse_pdf in email task: %s", e)
                nfse_pdf = None

        if not nfse_pdf:
            from core.nfse.provider_factory import get_provider
            from django.core.files.base import ContentFile

            try:
                from core.services.nfse_services import fetch_and_save_nfse_pdf

                provider = get_provider(invoice)
                nfse_pdf = fetch_and_save_nfse_pdf(invoice, provider)
            except Exception as e:
                logger.error(
                    "Error fetching NFS-e PDF from provider in email task: %s", e
                )
                nfse_pdf = None

        if nfse_pdf:
            company_attachments.append(
                (f"NFSe_{nf.nf_number}.pdf", nfse_pdf, "application/pdf")
            )

    # get first 3 words of company name for email display
    short_company_name = " ".join(company.company_name.split()[:3])
    sender_name = f"{short_company_name} Invoices"
    from_email_addr = _format_from_email(sender_name)

    # Client email: per AGENTS.md, NEVER attach NFS-e to client email
    if send_to_client and invoice.client.email:
        from core.utils.macros import get_email_content

        client_subject, client_body = get_email_content(
            "CLIENT_INVOICE_ISSUED", invoice
        )
        cc_list = (
            [cc.strip() for cc in invoice.client.email_cc.split(",") if cc.strip()]
            if invoice.client.email_cc
            else []
        )
        send_email_with_debug(
            client_subject,
            client_body,
            [invoice.client.email],
            cc_list,
            from_email_addr,
            [invoice_pdf_attachment],
            company,
        )

    # Company internal email
    if send_to_company and company.email:
        from core.utils.macros import get_email_content

        company_subject, company_body = get_email_content(
            "COMPANY_INVOICE_ISSUED", invoice
        )
        send_email_with_debug(
            company_subject,
            company_body,
            [company.email],
            [],
            from_email_addr,
            company_attachments,
            company,
        )

    invoice.task_id = ""
    invoice.status = "FINALIZED"
    invoice.save()
    return f"Emails sent for invoice {invoice_id}."


@shared_task
def process_daily_invoices_task(force=False):
    company = CompanySettings.load()
    if not company:
        return "Company settings not configured."
    if not company.auto_finalize_invoices and not force:
        return "Auto finalization disabled."

    current_hour = timezone.localtime(timezone.now()).hour
    if current_hour != company.auto_invoice_hour and not force:
        return f"Not the configured hour. Current: {current_hour}, Configured: {company.auto_invoice_hour}"

    today = timezone.localdate()
    invoices = Invoice.objects.filter(issue_date=today, status="DRAFT")
    count = 0

    for invoice in invoices:
        invoice.status = "PROCESSING"
        invoice.save()

        # Determine exchange rate automatically
        exchange_rate = invoice.exchange_rate_to_brl
        exchange_rate_error = None
        if not exchange_rate:
            if invoice.currency == "BRL":
                exchange_rate = Decimal("1.00")
            else:
                try:
                    exchange_rate = fetch_exchange_rate(
                        invoice.issue_date, invoice.currency
                    )
                    if not exchange_rate:
                        exchange_rate_error = "Não foi possível obter a taxa de câmbio (API retornou vazio)."
                except Exception as e:
                    exchange_rate = None
                    exchange_rate_error = f"Erro ao obter taxa de câmbio: {str(e)}"

        # Finalize the invoice first and send client email right away
        finalize_invoice_task.delay(
            invoice.id,
            send_to_client=company.auto_send_emails,
            send_to_company=company.auto_send_emails,
        )

        # Check failsafes for NFS-e
        failsafe_triggered = False
        failsafe_reason = ""

        if exchange_rate_error:
            failsafe_triggered = True
            failsafe_reason = exchange_rate_error
        elif exchange_rate:
            total_foreign = sum(
                item.total_price_foreign for item in invoice.items.all()
            )
            amount_brl = total_foreign * Decimal(str(exchange_rate))
            if amount_brl > Decimal("100000.00"):
                failsafe_triggered = True
                failsafe_reason = f"Valor total em BRL ({amount_brl}) excede o limite de R$ 100.000,00."

        if failsafe_triggered:
            if company and company.email:
                short_company_name = " ".join(company.company_name.split()[:3])
                sender_name = f"{short_company_name} System"
                from_email_addr = _format_from_email(sender_name)

                from core.utils.macros import get_email_content

                subject, body = get_email_content(
                    "COMPANY_FAILSAFE_TRIGGERED",
                    invoice,
                    extra_context={"{{ failsafe_reason }}": failsafe_reason},
                )
                try:
                    send_email_with_debug(
                        subject, body, [company.email], [], from_email_addr, [], company
                    )
                except Exception:
                    pass
        elif company.auto_emit_nfse:
            from .nfse_tasks import issue_nfse_task

            issue_nfse_task.delay(
                invoice.id,
                str(exchange_rate),
                send_to_company=company.auto_send_emails,
                send_to_client=False,
            )

        count += 1

    return f"Processed {count} daily invoices."
