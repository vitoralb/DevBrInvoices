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

from .invoices_tasks import _format_from_email, _get_pdf_bytes_for_task


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=20,
    retry_backoff_max=3600,
    max_retries=10,
)
def issue_nfse_task(
    self, invoice_id, exchange_rate, send_to_company=False, send_to_client=False
):
    invoice = Invoice.objects.get(id=invoice_id)
    company = CompanySettings.objects.first()

    # Save exchange rate
    invoice.exchange_rate_to_brl = Decimal(str(exchange_rate))
    invoice.save()

    try:
        # Check prefeitura first to avoid duplicate submissions
        try:
            found = consultar_nfe_na_prefeitura(invoice)
        except Exception as consult_err:
            logger.error(
                "Erro na consulta prévia da NFS-e para invoice %s: %s",
                invoice.invoice_number,
                consult_err,
            )
            from core.models import NfseLog

            NfseLog.objects.create(
                invoice=invoice,
                origem="System / Celery Pre-Check",
                erro_mensagem=f"Falha na consulta prévia da NFS-e: {consult_err}. Emissão abortada para evitar duplicidade.",
            )
            raise Exception(
                f"Falha na consulta prévia da NFS-e: {consult_err}. Emissão abortada para evitar duplicidade."
            )

        # Only submit new RPS if not found AND no batch protocol was already submitted
        if not found and not invoice.protocolo_envio:
            success = enviar_nfe_para_prefeitura(invoice)
            if not success:
                latest_log = invoice.nfse_logs.order_by("-created_at").first()
                err_detail = (
                    latest_log.erro_mensagem
                    if (latest_log and latest_log.erro_mensagem)
                    else "Erro retornado pelo provedor."
                )
                raise Exception(f"Falha na emissão da NFS-e: {err_detail}")

        # Re-fetch invoice to get the created nota_fiscal
        invoice.refresh_from_db()

        if not hasattr(invoice, "nota_fiscal") or not invoice.nota_fiscal:
            if invoice.protocolo_envio:
                raise Exception(
                    "NFS-e batch submitted but not processed yet. Waiting for prefeitura."
                )
            raise Exception("NFS-e not issued yet (nota fiscal not created).")

        nf = invoice.nota_fiscal

        invoice.task_id = ""
        invoice.task_retry_count = 0
        invoice.status = "FINALIZED"
        invoice.save()

        if send_to_company and company and company.email:
            pdf_bytes = None
            if nf.danfse_pdf:
                try:
                    pdf_bytes = nf.danfse_pdf.read()
                except Exception:
                    pdf_bytes = None

            if not pdf_bytes:
                from core.nfse.provider_factory import get_provider

                from core.services.nfse_services import fetch_and_save_nfse_pdf

                provider = get_provider(invoice)
                pdf_bytes = fetch_and_save_nfse_pdf(invoice, provider)
                if not pdf_bytes:
                    fetch_nfse_pdf_task.delay(invoice.id)

            if pdf_bytes:
                sender_name = (
                    f"{company.company_name} Invoices"
                    if company.company_name
                    else "Invoices"
                )
                from_email_addr = _format_from_email(sender_name)

                from core.utils.macros import get_email_content

                subject, body = get_email_content(
                    "COMPANY_NFSE_ISSUED",
                    invoice,
                    extra_context={
                        "{{ nf_number }}": nf.nf_number,
                        "{{ amount_brl }}": nf.amount_brl,
                        "{{ verification_code }}": nf.verification_code,
                    },
                )
                send_email_with_debug(
                    subject,
                    body,
                    [company.email],
                    [],
                    from_email_addr,
                    [
                        (
                            f"NFSe_{nf.nf_number}.pdf",
                            pdf_bytes,
                            "application/pdf",
                        )
                    ],
                    company,
                )

        return f"NFS-e {nf.nf_number} issued for invoice {invoice_id}."
    except Exception as e:
        if self.request.retries >= self.max_retries:
            invoice.task_retry_count = 0
            invoice.task_id = ""
            invoice.status = "FINALIZED"
            invoice.save()

            # Send failure email
            if company and company.email:
                sender_name = (
                    f"{company.company_name} System"
                    if company.company_name
                    else "System"
                )
                from_email_addr = _format_from_email(sender_name)

                from core.utils.macros import get_email_content

                subject, body = get_email_content(
                    "COMPANY_NFSE_FAILED",
                    invoice,
                    extra_context={"{{ error }}": str(e)},
                )
                try:
                    send_email_with_debug(
                        subject, body, [company.email], [], from_email_addr, [], company
                    )
                except Exception:
                    pass

            raise e
        else:
            invoice.task_retry_count = self.request.retries + 1
            invoice.save()
            raise e


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=600,
    max_retries=10,
)
def fetch_nfse_pdf_task(self, invoice_id=None, nf_id=None, force=False):
    """Asynchronously fetches and saves the NFS-e PDF (DANFSe) for an invoice or nota fiscal with retries."""
    from django.core.files.base import ContentFile
    from ..models import Invoice, NotaFiscal
    from core.nfse.provider_factory import get_provider

    invoice = None
    nf = None

    if invoice_id:
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            nf = getattr(invoice, "nota_fiscal", None)
            if not nf:
                return f"No NotaFiscal found for invoice {invoice_id}."
        except Invoice.DoesNotExist:
            return f"Invoice {invoice_id} not found."
    elif nf_id:
        try:
            nf = NotaFiscal.objects.get(id=nf_id)
        except NotaFiscal.DoesNotExist:
            return f"NotaFiscal {nf_id} not found."
    else:
        return "Must provide either invoice_id or nf_id."

    if not force and nf.danfse_pdf and nf.danfse_pdf.storage.exists(nf.danfse_pdf.name):
        return f"PDF already saved for NF {nf.nf_number}."

    class DummyInvoice:
        def __init__(self, nota_fiscal):
            self.nota_fiscal = nota_fiscal

    target = invoice if invoice else DummyInvoice(nf)

    from core.services.nfse_services import fetch_and_save_nfse_pdf

    provider = get_provider(target)
    pdf_bytes = fetch_and_save_nfse_pdf(target, provider, force=force)
    if pdf_bytes:
        logger.info("Successfully fetched and saved PDF for NF %s", nf.nf_number)
        return f"PDF successfully downloaded for NF {nf.nf_number}."
    else:
        logger.info(
            "PDF not ready yet for NF %s (retry %d/%d)",
            nf.nf_number,
            self.request.retries,
            self.max_retries,
        )
        raise Exception(f"PDF not ready yet for NF {nf.nf_number}.")


@shared_task(bind=True)
def import_nfses_task(
    self, provider_type, start_date=None, end_date=None, chave_acesso=None
):
    from core.services import import_nfses

    try:
        count, msg = import_nfses(provider_type, start_date, end_date, chave_acesso)
        return {"count": count, "message": msg}
    except Exception as e:
        logger.exception("Error in import_nfses_task: %s", e)
        return {"count": 0, "message": f"Erro durante a importação: {str(e)}"}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=600,
    max_retries=10,
)
def cancel_nfse_standalone_task(self, nf_id):
    from core.models import NotaFiscal, NfseLog
    from core.nfse.provider_factory import get_provider

    nf = NotaFiscal.objects.get(id=nf_id)
    if nf.is_canceled:
        return f"NFSe {nf_id} already canceled."

    class DummyInvoice:
        # provider.cancelar_nfse expects an invoice with a nota_fiscal
        def __init__(self, nota_fiscal):
            self.nota_fiscal = nota_fiscal

    dummy = DummyInvoice(nf)
    provider = get_provider(dummy)

    cancel_result = provider.cancelar_nfse(dummy)

    # We don't have a real invoice for NfseLog, but we can bypass or just not log it
    # NfseLog requires invoice. Since there's no invoice, we might skip NfseLog for standalone
    # Or change NfseLog to allow null invoice.
    # But wait, NfseLog invoice is a ForeignKey(Invoice, null=False).
    # For standalone NFS-es, we don't have an Invoice. We'll skip it for now.

    if not cancel_result.sucesso:
        raise Exception(f"Falha ao cancelar NFS-e: {' | '.join(cancel_result.erros)}")

    nf.is_canceled = True
    nf.save()
    return f"NFSe {nf_id} canceled successfully."
