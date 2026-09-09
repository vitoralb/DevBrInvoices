import logging
import csv
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.db import transaction
from django.db.models.functions import Coalesce
from django.db.models import Sum
from ..models import CompanySettings, NotaFiscal, NfseLog
import requests

logger = logging.getLogger(__name__)

from .tax_calculations import calculate_rbt12_and_fator_r, calculate_simples_tax
from .consolidation import consolidate_month


def fetch_exchange_rate(target_date, currency="CAD"):
    if currency.upper() == "BRL":
        return Decimal("1.0000")

    # Try BCB first
    currency_map = {"CAD": "48", "USD": "61", "EUR": "222", "GBP": "115"}
    moeda = currency_map.get(currency.upper(), "48")

    bcb_end_date = target_date - timedelta(days=1)
    bcb_start_date = target_date - timedelta(days=7)
    bcb_date_format = "%d/%m/%Y"

    bcb_url = (
        f"https://ptax.bcb.gov.br/ptax_internet/consultaBoletim.do?"
        f"method=gerarCSVFechamentoMoedaNoPeriodo&ChkMoeda={moeda}"
        f"&DATAINI={bcb_start_date.strftime(bcb_date_format)}&DATAFIM={bcb_end_date.strftime(bcb_date_format)}"
    )

    try:
        response = requests.get(
            bcb_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10
        )
        response.raise_for_status()
        csv_data = response.content.decode("iso-8859-1")

        rows = list(csv.reader(csv_data.strip().split("\n"), delimiter=";"))
        if rows:
            latest_row = rows[-1]
            venda_rate_str = latest_row[4].replace(",", ".")
            return Decimal(venda_rate_str).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
    except Exception as e:
        logger.warning(f"Error fetching exchange rate from BCB: {e}")

    return None


def assign_next_document_number(invoice):
    """Assigns the next document number and series to the invoice atomically.
    Uses a SELECT FOR UPDATE lock on CompanySettings to prevent concurrent
    providers from assigning the same number.
    """
    with transaction.atomic():
        comp = CompanySettings.objects.select_for_update().first()
        if not comp:
            raise ValueError("CompanySettings not found.")
        invoice.document_number = comp.next_document_number
        invoice.document_series = comp.document_series or "1"
        comp.next_document_number += 1
        comp.save()
        invoice.save()


@transaction.atomic
def _prepare_nf_data(invoice):
    total_foreign = sum(
        (item.total_price_foreign for item in invoice.items.all()),
        Decimal("0.00"),
    )
    if not invoice.exchange_rate_to_brl:
        raise ValueError(
            f"Exchange rate not set for invoice {invoice.invoice_number}. "
            "Cannot prepare NF data without a valid exchange rate."
        )
    amount_brl = (total_foreign * invoice.exchange_rate_to_brl).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    try:
        rbt12, fator_r, _, _ = calculate_rbt12_and_fator_r(
            invoice.issue_date.replace(day=1)
        )
        annex = "ANNEX_III" if fator_r >= Decimal("28.00") else "ANNEX_V"
        das_tax, _ = calculate_simples_tax(
            amount_brl, Decimal("0.00"), rbt12, annex, invoice.issue_date
        )
        effective_rate_pct = (
            (das_tax / amount_brl * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if amount_brl > 0
            else Decimal("0.00")
        )
    except Exception as e:
        logger.warning(
            "Failed to calculate effective tax rate for invoice %s: %s",
            invoice.invoice_number,
            e,
        )
        effective_rate_pct = Decimal("0.00")

    end_date = invoice.issue_date.replace(day=1) - timedelta(days=1)
    start_date = end_date.replace(day=1)

    def fmt_br(val, decimals=2):
        s = f"{val:,.{decimals}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")

    raw_client_desc = "Serviços de desenvolvimento de software. Referente ao período de {start_date} a {end_date}."
    client_desc = raw_client_desc.replace(
        "{start_date}", start_date.strftime("%d/%m/%Y")
    ).replace("{end_date}", end_date.strftime("%d/%m/%Y"))

    description = (
        f"{client_desc}\n"
        f"Serviço prestado exclusivamente para o exterior, não será usado no Brasil.\n\n"
        f"Valor em moeda estrangeira: {invoice.currency} {fmt_br(total_foreign)}\n"
        f"Taxa de conversão: {fmt_br(invoice.exchange_rate_to_brl, 4)}\n"
        f"Valor em Reais: R$ {fmt_br(amount_brl)}\n\n"
        f"Invoice n° {invoice.invoice_number} - emitida em {invoice.issue_date.strftime('%d/%m/%Y')}.\n\n"
        f"Valor líquido da Nota Fiscal = R$ {fmt_br(amount_brl)}.\n\n"
        f" - Conforme Lei 12.741/2012, o percentual total de impostos incidentes neste serviço prestado é de aproximadamente {fmt_br(effective_rate_pct)}%"
    )
    return amount_brl, description, effective_rate_pct


def enviar_nfe_para_prefeitura(invoice):
    from django.core.files.base import ContentFile
    from core.nfse.provider_factory import get_provider

    company = CompanySettings.objects.first()
    provider = get_provider(invoice)

    amount_brl, description, _ = _prepare_nf_data(invoice)

    log_entry = NfseLog.objects.create(invoice=invoice, origem="System / Celery")

    try:
        result = provider.emitir_nfse(invoice)
    except Exception as e:
        logger.exception(
            "Unexpected exception in emitir_nfse for invoice %s: %s",
            invoice.invoice_number,
            e,
        )
        if hasattr(e, "raw_request") and e.raw_request:
            log_entry.payload_enviado = e.raw_request
        if hasattr(e, "raw_response") and e.raw_response:
            log_entry.payload_retorno = e.raw_response
        elif (
            hasattr(e, "response")
            and e.response is not None
            and hasattr(e.response, "text")
        ):
            log_entry.payload_retorno = e.response.text

        log_entry.erro_mensagem = str(e)
        log_entry.save()
        raise e

    log_entry.payload_enviado = result.xml_enviado
    log_entry.payload_retorno = result.xml_retorno

    if result.sucesso:
        # Save NF
        nf = NotaFiscal.objects.create(
            invoice=invoice,
            nf_number=result.numero_nf,
            issue_date=invoice.issue_date,
            amount_brl=amount_brl,
            is_export=True,
            description=description.replace("\r", "").strip(),
            verification_code=result.codigo_verificacao,
            chave_acesso_nacional=result.chave_acesso_nacional,
            data_hora_autorizacao=result.data_hora_autorizacao,
            codigo_tributacao_nacional=result.codigo_tributacao_nacional,
            codigo_nbs=result.codigo_nbs,
            aliquota_iss=result.aliquota_iss,
            valor_iss=result.valor_iss,
            codigo_servico_municipio=result.codigo_servico_municipio,
        )

        # Save XML return
        if result.xml_retorno:
            nf.xml_autorizacao.save(
                f"NFSe_{nf.nf_number}.xml",
                ContentFile(result.xml_retorno.encode("utf-8")),
            )
        elif result.xml_enviado:
            nf.xml_autorizacao.save(
                f"NFSe_{nf.nf_number}.xml",
                ContentFile(result.xml_enviado.encode("utf-8")),
            )

        # Try to download PDF
        invoice.nota_fiscal = nf  # For the provider to access it
        pdf_bytes = fetch_and_save_nfse_pdf(invoice, provider)
        if not pdf_bytes:
            try:
                from core.tasks import fetch_nfse_pdf_task

                fetch_nfse_pdf_task.delay(invoice.id)
            except Exception as task_ex:
                logger.warning("Could not dispatch fetch_nfse_pdf_task: %s", task_ex)

        log_entry.save()
        return True
    else:
        log_entry.erro_mensagem = (
            "\n".join(result.erros)
            if result.erros
            else (result.xml_retorno or "Falha desconhecida na emissão")
        )
        log_entry.save()
        return False


def consultar_nfe_na_prefeitura(invoice):
    """Checks with the configured NFS-e provider if the invoice was already emitted."""
    from django.core.files.base import ContentFile
    from core.nfse.provider_factory import get_provider

    if hasattr(invoice, "nota_fiscal") and invoice.nota_fiscal:
        return True
    if not invoice.document_number:
        return False

    provider = get_provider(invoice)
    # Note: Do NOT swallow exceptions here!
    # If an exception occurs during consultation, propagate it to caller so
    # emission is aborted to avoid duplicate emissions.
    result = provider.consultar_nfse(invoice)
    if result and result.sucesso:
        amount_brl, description, _ = _prepare_nf_data(invoice)
        nf = NotaFiscal.objects.create(
            invoice=invoice,
            nf_number=result.numero_nf,
            issue_date=invoice.issue_date,
            amount_brl=amount_brl,
            is_export=True,
            description=description.replace("\r", "").strip(),
            verification_code=result.codigo_verificacao,
            chave_acesso_nacional=result.chave_acesso_nacional,
            data_hora_autorizacao=result.data_hora_autorizacao,
            codigo_tributacao_nacional=result.codigo_tributacao_nacional,
            codigo_nbs=result.codigo_nbs,
            aliquota_iss=result.aliquota_iss,
            valor_iss=result.valor_iss,
            codigo_servico_municipio=result.codigo_servico_municipio,
        )
        if result.xml_retorno:
            nf.xml_autorizacao.save(
                f"NFSe_{nf.nf_number}.xml",
                ContentFile(result.xml_retorno.encode("utf-8")),
            )
        elif result.xml_enviado:
            nf.xml_autorizacao.save(
                f"NFSe_{nf.nf_number}.xml",
                ContentFile(result.xml_enviado.encode("utf-8")),
            )

        # Try to download PDF
        invoice.nota_fiscal = nf
        fetch_and_save_nfse_pdf(invoice, provider)
        return True

    return False


def import_nfses(provider_type, start_date=None, end_date=None, chave_acesso=None):
    from core.nfse.paulistana.provider import PaulistanaProvider
    from core.nfse.nacional.provider import NacionalProvider
    from core.models import NotaFiscal
    from django.core.files.base import ContentFile
    import datetime
    from decimal import Decimal

    if provider_type == "PAULISTANA":
        provider = PaulistanaProvider()
        if not start_date or not end_date:
            return 0, "Datas de início e fim são obrigatórias para Paulistana."

        # start_date and end_date are strings, convert to date
        if isinstance(start_date, str):
            start_date = datetime.date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.date.fromisoformat(end_date)

        resultados = provider.buscar_nfses_por_periodo(start_date, end_date)
    elif provider_type == "NACIONAL":
        provider = NacionalProvider()
        if not chave_acesso:
            return 0, "Chave de acesso é obrigatória para Sefin Nacional."

        res = provider.buscar_nfse_por_chave(chave_acesso)
        resultados = [res] if res else []
    else:
        return 0, "Provedor inválido."

    count = 0
    for r in resultados:
        if not r:
            continue

        nf_num = r["nf_number"]
        chave = r["chave_acesso_nacional"]

        # Check if already exists
        exists = False
        if chave:
            exists = NotaFiscal.objects.filter(chave_acesso_nacional=chave).exists()
        if not exists and nf_num:
            # Also check by nf_number + verification_code to be safe
            cod_ver = r.get("verification_code")
            q = NotaFiscal.objects.filter(nf_number=nf_num)
            if cod_ver:
                q = q.filter(verification_code=cod_ver)
            exists = q.exists()

        if not exists:
            with transaction.atomic():
                # Re-check inside the transaction to avoid race condition
                if chave:
                    exists = NotaFiscal.objects.filter(
                        chave_acesso_nacional=chave
                    ).exists()
                if not exists and nf_num:
                    cod_ver = r.get("verification_code")
                    q = NotaFiscal.objects.filter(nf_number=nf_num)
                    if cod_ver:
                        q = q.filter(verification_code=cod_ver)
                    exists = q.exists()

                if not exists:
                    nf = NotaFiscal(
                        nf_number=nf_num,
                        verification_code=r.get("verification_code"),
                        chave_acesso_nacional=chave,
                        amount_brl=Decimal(r["amount_brl"]),
                        description=r["description"],
                        issue_date=r["issue_date"],
                        is_canceled=r.get("is_canceled", False),
                        cancelation_date=r.get("cancelation_date"),
                        is_export=True,
                        data_hora_autorizacao=r.get("data_hora_autorizacao"),
                        codigo_tributacao_nacional=r.get(
                            "codigo_tributacao_nacional", ""
                        ),
                        codigo_nbs=r.get("codigo_nbs", ""),
                        aliquota_iss=r.get("aliquota_iss"),
                        valor_iss=r.get("valor_iss"),
                        codigo_servico_municipio=r.get("codigo_servico_municipio", ""),
                    )
                    if r.get("raw_xml"):
                        nf.xml_autorizacao.save(
                            f"NFSe_{nf_num}.xml",
                            ContentFile(r["raw_xml"].encode("utf-8")),
                            save=False,
                        )
                    nf.save()
                    count += 1

    return count, f"Foram importadas {count} NFS-es com sucesso."


def cancel_nota_fiscal(invoice):
    from core.nfse.provider_factory import get_provider
    from django.core.files.base import ContentFile

    provider = get_provider(invoice)
    result = provider.cancelar_nfse(invoice)

    if result.sucesso:
        invoice.status = "CANCELED"
        invoice.save()

        nf = invoice.nota_fiscal
        if nf:
            nf.is_canceled = True
            if result.cancelation_date:
                nf.cancelation_date = result.cancelation_date

            xml_to_save = result.xml_retorno
            if not xml_to_save:
                try:
                    consult_res = provider.consultar_nfse(invoice)
                    if consult_res and consult_res.xml_retorno:
                        xml_to_save = consult_res.xml_retorno
                except Exception as e:
                    import logging

                    logging.getLogger(__name__).warning(
                        "Failed to fetch updated XML for canceled NFS-e: %s", e
                    )

            if xml_to_save:
                if nf.xml_autorizacao:
                    nf.xml_autorizacao.delete(save=False)

                file_content = (
                    xml_to_save.encode("utf-8")
                    if isinstance(xml_to_save, str)
                    else xml_to_save
                )

                nf.xml_autorizacao.save(
                    f"NFSe_{nf.nf_number}.xml",
                    ContentFile(file_content),
                    save=False,
                )

            nf.save()

            from core.tasks.nfse_tasks import fetch_nfse_pdf_task

            fetch_nfse_pdf_task.delay(invoice_id=invoice.id, force=True)

    return result


def fetch_and_save_nfse_pdf(invoice_or_nf, provider, force=False):
    """Fetches the NFS-e PDF from the provider and saves it to the NotaFiscal record.
    Returns the pdf bytes if successful, None if not yet ready.
    """
    from django.core.files.base import ContentFile

    if hasattr(invoice_or_nf, "nota_fiscal"):
        nf = invoice_or_nf.nota_fiscal
        target = invoice_or_nf
    else:
        nf = invoice_or_nf
        target = invoice_or_nf

    if not nf:
        return None

    pdf_bytes = provider.baixar_pdf(target)
    if pdf_bytes:
        if force and nf.danfse_pdf:
            nf.danfse_pdf.delete(save=False)
        nf.danfse_pdf.save(f"NFS-e_{nf.nf_number}.pdf", ContentFile(pdf_bytes))
    return pdf_bytes
