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
        comp.save(update_fields=["next_document_number", "updated_at"] if hasattr(comp, "updated_at") else ["next_document_number"])
        invoice.save(update_fields=["document_number", "document_series", "updated_at"])


def get_approx_tax_rate_pct(invoice_or_nf) -> Decimal:
    """Calcula a alíquota aproximada para o Simples Nacional (nominal da faixa,
    descontando ISS/PIS/COFINS em exportação)."""
    try:
        issue_date = getattr(invoice_or_nf, "issue_date", None)
        if not issue_date:
            return Decimal("0.00")

        rbt12, fator_r, _, _ = calculate_rbt12_and_fator_r(
            issue_date.replace(day=1),
            use_ideal_pro_labore=True,
        )
        annex = "ANNEX_III" if fator_r >= Decimal("28.00") else "ANNEX_V"

        if hasattr(invoice_or_nf, "is_export"):
            is_export = invoice_or_nf.is_export
        elif hasattr(invoice_or_nf, "nota_fiscal") and invoice_or_nf.nota_fiscal:
            is_export = invoice_or_nf.nota_fiscal.is_export
        else:
            client = getattr(invoice_or_nf, "client", None)
            if client and getattr(client, "address_country_code", None):
                is_export = client.address_country_code.upper() != "BR"
            else:
                is_export = True

        from core.services.tax_calculations import calculate_approx_tax_rate_pct

        return calculate_approx_tax_rate_pct(
            rbt12=rbt12,
            annex_type=annex,
            reference_date=issue_date,
            is_export=is_export,
        )
    except Exception as e:
        identifier = getattr(
            invoice_or_nf,
            "invoice_number",
            getattr(invoice_or_nf, "nf_number", None),
        )
        logger.warning(
            "Failed to calculate approx tax rate for invoice/NF %s: %s",
            identifier,
            e,
        )
        return Decimal("0.00")


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
            invoice.issue_date.replace(day=1),
            use_ideal_pro_labore=True,
        )
        annex = "ANNEX_III" if fator_r >= Decimal("28.00") else "ANNEX_V"

        is_export = True
        if hasattr(invoice, "nota_fiscal") and invoice.nota_fiscal:
            is_export = invoice.nota_fiscal.is_export
        elif invoice.client and invoice.client.address_country_code:
            is_export = invoice.client.address_country_code.upper() != "BR"

        rev_internal = Decimal("0.00") if is_export else amount_brl
        rev_export = amount_brl if is_export else Decimal("0.00")

        das_tax, _ = calculate_simples_tax(
            rev_internal, rev_export, rbt12, annex, invoice.issue_date
        )
        effective_rate_pct = (
            (das_tax / amount_brl * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if amount_brl > 0
            else Decimal("0.00")
        )

        from core.services.tax_calculations import calculate_approx_tax_rate_pct

        approx_rate_pct = calculate_approx_tax_rate_pct(
            rbt12=rbt12,
            annex_type=annex,
            reference_date=invoice.issue_date,
            is_export=is_export,
        )
    except Exception as e:
        logger.warning(
            "Failed to calculate effective/approx tax rate for invoice %s: %s",
            invoice.invoice_number,
            e,
        )
        effective_rate_pct = Decimal("0.00")
        approx_rate_pct = Decimal("0.00")

    from core.utils.macros import apply_invoice_macros
    from core.models import DEFAULT_NFSE_DESCRIPTION_TEMPLATE

    nfse_tmpl = getattr(invoice, "nfse_description", None)
    if not nfse_tmpl or nfse_tmpl == "Descrição dos Serviços":
        nfse_tmpl = DEFAULT_NFSE_DESCRIPTION_TEMPLATE
    description = apply_invoice_macros(
        nfse_tmpl,
        invoice,
        language="pt-br",
        extra_context={
            "{{ effective_tax_rate }}": effective_rate_pct,
            "{{ nominal_tax_rate }}": approx_rate_pct,
        },
    )
    return amount_brl, description, effective_rate_pct


def _create_nf_from_emit_result(invoice, result, provider) -> NotaFiscal:
    """Creates and persists a NotaFiscal from an EmitResult, saves the XML authorization,
    and attempts to download the NFS-e PDF. Idempotently updates if a NotaFiscal already exists."""
    from django.core.files.base import ContentFile

    amount_brl, description, _ = _prepare_nf_data(invoice)
    
    # Check if NotaFiscal already exists for this invoice or non-empty national key
    nf = None
    if getattr(invoice, "nota_fiscal", None):
        nf = invoice.nota_fiscal
    elif result.chave_acesso_nacional:
        nf = NotaFiscal.objects.filter(chave_acesso_nacional=result.chave_acesso_nacional).first()

    if nf:
        nf.invoice = invoice
        nf.nf_number = result.numero_nf
        nf.issue_date = invoice.issue_date
        nf.amount_brl = amount_brl
        nf.is_export = True
        nf.description = description.replace("\r", "").strip()
        nf.verification_code = result.codigo_verificacao
        nf.chave_acesso_nacional = result.chave_acesso_nacional
        nf.data_hora_autorizacao = result.data_hora_autorizacao
        nf.codigo_tributacao_nacional = (
            result.codigo_tributacao_nacional
            or getattr(invoice, "codigo_tributacao_nacional", "")
        )
        nf.codigo_nbs = result.codigo_nbs or getattr(invoice, "codigo_nbs", "")
        nf.aliquota_iss = result.aliquota_iss
        nf.valor_iss = result.valor_iss
        nf.codigo_servico_municipio = (
            result.codigo_servico_municipio
            or getattr(invoice, "codigo_servico_municipio", "")
        )
        nf.cst_ibs_cbs = getattr(result, "cst_ibs_cbs", "") or ""
        nf.c_class_trib_ibs_cbs = (
            getattr(result, "c_class_trib_ibs_cbs", "") or ""
        )
        nf.c_ind_op_ibs_cbs = getattr(result, "c_ind_op_ibs_cbs", "") or ""
        nf.save()
    else:
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
            codigo_tributacao_nacional=(
                result.codigo_tributacao_nacional
                or getattr(invoice, "codigo_tributacao_nacional", "")
            ),
            codigo_nbs=result.codigo_nbs or getattr(invoice, "codigo_nbs", ""),
            aliquota_iss=result.aliquota_iss,
            valor_iss=result.valor_iss,
            codigo_servico_municipio=(
                result.codigo_servico_municipio
                or getattr(invoice, "codigo_servico_municipio", "")
            ),
            cst_ibs_cbs=getattr(result, "cst_ibs_cbs", "") or "",
            c_class_trib_ibs_cbs=(
                getattr(result, "c_class_trib_ibs_cbs", "") or ""
            ),
            c_ind_op_ibs_cbs=getattr(result, "c_ind_op_ibs_cbs", "") or "",
        )

    xml_content = result.xml_retorno or result.xml_enviado
    if xml_content:
        file_bytes = (
            xml_content.encode("utf-8")
            if isinstance(xml_content, str)
            else xml_content
        )
        nf.xml_autorizacao.save(
            f"NFS-e_{nf.nf_number}.xml",
            ContentFile(file_bytes),
        )

    invoice.nota_fiscal = nf
    pdf_bytes = fetch_and_save_nfse_pdf(invoice, provider)
    if not pdf_bytes:
        try:
            from core.tasks.nfse_tasks import fetch_nfse_pdf_task

            fetch_nfse_pdf_task.delay(invoice_id=invoice.id)
        except Exception as task_ex:
            logger.warning("Could not dispatch fetch_nfse_pdf_task: %s", task_ex)

    return nf


def enviar_nfe_para_prefeitura(invoice):
    from core.nfse.provider_factory import get_provider

    company = CompanySettings.load()
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

    log_entry.payload_enviado = result.xml_enviado or ""
    log_entry.payload_retorno = result.xml_retorno or ""
    log_entry.save()

    if result.sucesso:
        try:
            nf = _create_nf_from_emit_result(invoice, result, provider)
            log_entry.nota_fiscal = nf
            log_entry.save()
            return True
        except Exception as save_err:
            logger.exception("Error saving NotaFiscal record: %s", save_err)
            log_entry.erro_mensagem = f"NFS-e autorizada, mas falhou ao salvar localmente: {save_err}"
            log_entry.save()
            raise save_err
    else:
        err_list = [e.strip() for e in (result.erros or []) if e and e.strip()]
        log_entry.erro_mensagem = (
            "\n".join(err_list)
            if err_list
            else (result.xml_retorno or "Falha desconhecida na emissão")
        )
        log_entry.save()
        return False


def consultar_nfe_na_prefeitura(invoice):
    """Checks with the configured NFS-e provider if the invoice was already emitted."""
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
        _create_nf_from_emit_result(invoice, result, provider)
        return True

    return False


def _save_nf_events(nf, events_list):
    """Saves or updates NotaFiscalEvent records for a NotaFiscal.
    Returns (is_canceled, cancelation_date) if any event is a cancellation event.
    """
    from core.models import NotaFiscalEvent
    from django.utils import timezone

    is_canceled = False
    cancelation_date = None

    if not nf or not events_list:
        return is_canceled, cancelation_date

    for ev in events_list:
        if not isinstance(ev, dict):
            continue

        id_ev = ev.get("id_evento", "")
        code_ev = ev.get("codigo_evento", "")
        seq_ev = ev.get("n_seq_evento", 1)
        nsu_ev = ev.get("nsu")
        tipo_ev = ev.get("tipo_evento", "")

        # Guard: discard empty phantom events that have no identifying data
        if not id_ev and not code_ev and not nsu_ev and not tipo_ev and not ev.get("raw_xml"):
            continue

        event_obj = None
        if id_ev:
            event_obj = NotaFiscalEvent.objects.filter(
                nota_fiscal=nf, id_evento=id_ev
            ).first()
        if not event_obj and nsu_ev:
            event_obj = NotaFiscalEvent.objects.filter(
                nota_fiscal=nf, nsu=nsu_ev
            ).first()
        if not event_obj and code_ev:
            event_obj = NotaFiscalEvent.objects.filter(
                nota_fiscal=nf, codigo_evento=code_ev, n_seq_evento=seq_ev
            ).first()
        if not event_obj and tipo_ev:
            event_obj = NotaFiscalEvent.objects.filter(
                nota_fiscal=nf, tipo_evento=tipo_ev, n_seq_evento=seq_ev
            ).first()

        if event_obj:
            updated_fields = []
            if nsu_ev and not event_obj.nsu:
                event_obj.nsu = nsu_ev
                updated_fields.append("nsu")
            if id_ev and not event_obj.id_evento:
                event_obj.id_evento = id_ev
                updated_fields.append("id_evento")
            if code_ev and not event_obj.codigo_evento:
                event_obj.codigo_evento = code_ev
                updated_fields.append("codigo_evento")
            if tipo_ev and not event_obj.tipo_evento:
                event_obj.tipo_evento = tipo_ev
                updated_fields.append("tipo_evento")
            if ev.get("dh_evento") and not event_obj.dh_evento:
                event_obj.dh_evento = ev.get("dh_evento")
                updated_fields.append("dh_evento")
            if ev.get("descricao") and not event_obj.descricao:
                event_obj.descricao = ev.get("descricao")
                updated_fields.append("descricao")
            if ev.get("codigo_motivo") and not event_obj.codigo_motivo:
                event_obj.codigo_motivo = ev.get("codigo_motivo")
                updated_fields.append("codigo_motivo")
            if ev.get("motivo") and not event_obj.motivo:
                event_obj.motivo = ev.get("motivo")
                updated_fields.append("motivo")
            if ev.get("raw_xml") and not event_obj.raw_xml:
                event_obj.raw_xml = ev.get("raw_xml")
                updated_fields.append("raw_xml")
            if updated_fields:
                event_obj.save(update_fields=updated_fields)
        else:
            event_obj = NotaFiscalEvent.objects.create(
                nota_fiscal=nf,
                nsu=nsu_ev,
                id_evento=id_ev,
                tipo_evento=tipo_ev,
                codigo_evento=code_ev,
                n_seq_evento=seq_ev,
                dh_evento=ev.get("dh_evento"),
                descricao=ev.get("descricao", ""),
                codigo_motivo=ev.get("codigo_motivo", ""),
                motivo=ev.get("motivo", ""),
                raw_xml=ev.get("raw_xml", ""),
            )

        if ev.get("is_cancellation"):
            is_canceled = True
            if not cancelation_date and ev.get("dh_evento"):
                cancelation_date = ev.get("dh_evento")

    return is_canceled, cancelation_date


def import_nfses(
    provider_type: str | None = None,
):
    import re
    from core.nfse.paulistana.provider import PaulistanaProvider
    from core.nfse.nacional.provider import (
        NacionalProvider,
        _decompress_gzip_b64,
        _parse_decompressed_nfse_xml,
        _parse_decompressed_evento_xml,
    )
    from core.models import Invoice, NotaFiscal, CompanySettings
    from django.core.files.base import ContentFile
    from django.db import transaction
    from django.utils import timezone
    from decimal import Decimal
    from core.utils.rate_limiter import RateLimiter

    company = CompanySettings.load()
    if not provider_type:
        provider_type = company.nfse_provider if company else "PAULISTANA"

    if provider_type == "NACIONAL":
        from django.core.cache import cache
        from datetime import datetime

        cooldown_until = cache.get("adn_dfe_cooldown_until")
        if cooldown_until:
            if isinstance(cooldown_until, datetime) and cooldown_until <= timezone.now():
                cache.delete("adn_dfe_cooldown_until")
                cooldown_until = None
        if cooldown_until:
            if isinstance(cooldown_until, datetime):
                time_str = (
                    timezone.localtime(cooldown_until).strftime("%H:%M")
                    if not timezone.is_naive(cooldown_until)
                    else cooldown_until.strftime("%H:%M")
                )
            else:
                time_str = str(cooldown_until)
            return (
                0,
                f"Consulta ao ADN em espera obrigatória até {time_str} (limite de 1h da Receita quando não há documentos novos).",
            )

        provider = NacionalProvider()
        if not company:
            return 0, "CompanySettings not found."

        start_nsu = int(company.last_adn_nsu or 0)
        raw_items, max_nsu = provider.consultar_dfe_por_nsu(start_nsu)
        if not raw_items:
            return (
                0,
                "Nenhuma nova NFS-e ou evento encontrado no ADN. A base já está atualizada.",
            )

        # Sort in ascending NSU order to process emissions before cancellations
        raw_items = sorted(raw_items, key=lambda x: x.get("NSU") or 0)

        my_cnpj = re.sub(r"\D", "", company.cnpj)
        imported_nfs_count = 0
        updated_events_count = 0
        imported_dates = []

        for item in raw_items:
            nsu = item.get("NSU")
            chave = item.get("ChaveAcesso") or ""
            tipo_doc = item.get("TipoDocumento")
            tipo_ev = item.get("TipoEvento")
            xml_b64 = item.get("ArquivoXml")
            xml_str = _decompress_gzip_b64(xml_b64) or ""

            # Filter: only process documents where company is Prestador
            # In 50-digit chave: chave[9:23] is prestador CNPJ
            cnpj_prestador = chave[9:23] if len(chave) == 50 else ""
            if not cnpj_prestador and xml_str:
                cnpj_match = re.search(
                    r"<emit>.*?<CNPJ>([^<]+)</CNPJ>", xml_str, re.DOTALL
                )
                if not cnpj_match:
                    cnpj_match = re.search(
                        r"<prest>.*?<CNPJ>([^<]+)</CNPJ>", xml_str, re.DOTALL
                    )
                if cnpj_match:
                    cnpj_prestador = cnpj_match.group(1)

            if cnpj_prestador != my_cnpj:
                # Tomador document (service purchased by company from third-party) - skip importing as our NFSe
                continue

            # Only import Nacional documents (ambGer == '2' or existing in NotaFiscal)
            amb_ger = chave[7] if len(chave) == 50 else ""
            if (
                amb_ger != "2"
                and not NotaFiscal.objects.filter(chave_acesso_nacional=chave).exists()
            ):
                continue

            if tipo_doc == "NFSE":
                parsed_nfse = _parse_decompressed_nfse_xml(xml_str)
                nf_num = parsed_nfse["numero_nf"] or chave[-15:].lstrip("0")

                with transaction.atomic():
                    nf = NotaFiscal.objects.filter(
                        chave_acesso_nacional=chave
                    ).first()
                    created = False
                    if not nf:
                        nf = NotaFiscal(
                            nf_number=nf_num,
                            chave_acesso_nacional=chave,
                            amount_brl=Decimal(
                                str(parsed_nfse["amount_brl"] or "0.00")
                            ),
                            description=parsed_nfse["description"] or "",
                            issue_date=parsed_nfse["issue_date"]
                            or timezone.localdate(),
                            is_export=True,
                            data_hora_autorizacao=parsed_nfse[
                                "data_hora_autorizacao"
                            ],
                            codigo_tributacao_nacional=parsed_nfse[
                                "codigo_tributacao_nacional"
                            ],
                            codigo_nbs=parsed_nfse["codigo_nbs"],
                            codigo_servico_municipio=parsed_nfse[
                                "codigo_servico_municipio"
                            ],
                            aliquota_iss=parsed_nfse["aliquota_iss"],
                            valor_iss=parsed_nfse["valor_iss"],
                            cst_ibs_cbs=parsed_nfse.get("cst_ibs_cbs", ""),
                            c_class_trib_ibs_cbs=parsed_nfse.get("c_class_trib_ibs_cbs", ""),
                            c_ind_op_ibs_cbs=parsed_nfse.get("c_ind_op_ibs_cbs", ""),
                        )
                        created = True
                    else:
                        if not nf.cst_ibs_cbs and parsed_nfse.get("cst_ibs_cbs"):
                            nf.cst_ibs_cbs = parsed_nfse["cst_ibs_cbs"]
                        if not nf.c_class_trib_ibs_cbs and parsed_nfse.get("c_class_trib_ibs_cbs"):
                            nf.c_class_trib_ibs_cbs = parsed_nfse["c_class_trib_ibs_cbs"]
                        if not nf.c_ind_op_ibs_cbs and parsed_nfse.get("c_ind_op_ibs_cbs"):
                            nf.c_ind_op_ibs_cbs = parsed_nfse["c_ind_op_ibs_cbs"]

                    # Auto-link to unlinked invoice if DPS matches
                    dps_ser = parsed_nfse.get("dps_series")
                    dps_num = parsed_nfse.get("dps_number")
                    if not nf.invoice and dps_num:
                        try:
                            doc_num_int = int(dps_num)
                            inv_match = Invoice.objects.filter(
                                nota_fiscal__isnull=True,
                                document_number=doc_num_int,
                            )
                            if dps_ser:
                                inv_match = inv_match.filter(
                                    document_series=str(int(dps_ser))
                                )
                            inv_found = inv_match.first()
                            if inv_found:
                                nf.invoice = inv_found
                        except Exception:
                            pass

                    if xml_str:
                        nf.xml_autorizacao.save(
                            f"NFS-e_{nf_num}.xml",
                            ContentFile(xml_str.encode("utf-8")),
                            save=False,
                        )
                    nf.save()
                    imported_dates.append(nf.issue_date)

                    # Advance next_document_number if serie matches company.document_series
                    if dps_num and dps_ser:
                        try:
                            s1 = str(dps_ser).strip().lstrip("0")
                            s2 = str(company.document_series).strip().lstrip("0")
                            if s1 == s2 or str(dps_ser).strip() == str(company.document_series).strip():
                                dps_num_int = int(str(dps_num).strip())
                                if dps_num_int >= company.next_document_number:
                                    company.next_document_number = (
                                        dps_num_int + 1
                                    )
                                    company.save(
                                        update_fields=["next_document_number"]
                                    )
                        except Exception:
                            pass

                    if created:
                        imported_nfs_count += 1
                        # Check if note already has events (e.g. cancellation) registered at Sefin
                        # even if ADN distribution queue hasn't assigned an NSU yet
                        try:
                            evs = provider.consultar_eventos_nfse(chave)
                            if evs:
                                is_canc, canc_dt = _save_nf_events(nf, evs)
                                if is_canc and not nf.is_canceled:
                                    nf.is_canceled = True
                                    nf.cancelation_date = canc_dt or timezone.now()
                                    nf.save(
                                        update_fields=[
                                            "is_canceled",
                                            "cancelation_date",
                                            "updated_at",
                                        ]
                                    )
                                    if nf.invoice and nf.invoice.status != "CANCELED":
                                        nf.invoice.status = "CANCELED"
                                        nf.invoice.save(
                                            update_fields=["status", "updated_at"]
                                        )
                        except Exception as ev_ex:
                            logger.debug(
                                "Could not query initial events on import for NF %s: %s",
                                nf_num,
                                ev_ex,
                            )

                        try:
                            fetch_and_save_nfse_pdf(nf, provider)
                        except Exception as pdf_ex:
                            logger.warning(
                                "Could not generate PDF on import for NF %s: %s",
                                nf_num,
                                pdf_ex,
                            )

            elif tipo_doc == "EVENTO":
                ev_data = _parse_decompressed_evento_xml(
                    xml_str, nsu=nsu, tipo_evento_adn=tipo_ev
                )
                nf = NotaFiscal.objects.filter(
                    chave_acesso_nacional=chave
                ).first()
                if not nf:
                    r_nfse = provider.buscar_nfse_por_chave(chave)
                    if r_nfse:
                        nf = NotaFiscal.objects.create(
                            nf_number=r_nfse["nf_number"],
                            chave_acesso_nacional=chave,
                            amount_brl=Decimal(
                                str(r_nfse["amount_brl"] or "0.00")
                            ),
                            description=r_nfse["description"] or "",
                            issue_date=r_nfse["issue_date"],
                            is_export=True,
                            data_hora_autorizacao=r_nfse[
                                "data_hora_autorizacao"
                            ],
                            codigo_tributacao_nacional=r_nfse[
                                "codigo_tributacao_nacional"
                            ],
                            codigo_nbs=r_nfse["codigo_nbs"],
                            codigo_servico_municipio=r_nfse[
                                "codigo_servico_municipio"
                            ],
                            aliquota_iss=r_nfse["aliquota_iss"],
                            valor_iss=r_nfse["valor_iss"],
                            cst_ibs_cbs=r_nfse.get("cst_ibs_cbs", ""),
                            c_class_trib_ibs_cbs=r_nfse.get("c_class_trib_ibs_cbs", ""),
                            c_ind_op_ibs_cbs=r_nfse.get("c_ind_op_ibs_cbs", ""),
                        )
                        if r_nfse.get("raw_xml"):
                            nf.xml_autorizacao.save(
                                f"NFS-e_{nf.nf_number}.xml",
                                ContentFile(r_nfse["raw_xml"].encode("utf-8")),
                                save=False,
                            )
                            nf.save()
                        imported_nfs_count += 1

                if nf:
                    imported_dates.append(nf.issue_date)
                    is_canc, canc_dt = _save_nf_events(nf, [ev_data])
                    updated_events_count += 1
                    if is_canc and not nf.is_canceled:
                        nf.is_canceled = True
                        nf.cancelation_date = canc_dt or timezone.now()
                        nf.save(
                            update_fields=[
                                "is_canceled",
                                "cancelation_date",
                                "updated_at",
                            ]
                        )
                        if nf.invoice and nf.invoice.status != "CANCELED":
                            nf.invoice.status = "CANCELED"
                            nf.invoice.save(
                                update_fields=["status", "updated_at"]
                            )
                        try:
                            fetch_and_save_nfse_pdf(nf, provider, force=True)
                        except Exception as pdf_ex:
                            logger.warning(
                                "Could not regenerate PDF on event import for NF %s: %s",
                                nf.nf_number,
                                pdf_ex,
                            )

        # Update last_adn_nsu cursor
        if max_nsu > company.last_adn_nsu:
            company.last_adn_nsu = max_nsu
            company.save(update_fields=["last_adn_nsu"])

        if imported_nfs_count > 0 or updated_events_count > 0:
            try:
                from core.services.consolidation import (
                    populate_consolidations_for_imported_notes,
                )

                populate_consolidations_for_imported_notes(imported_dates)
            except Exception as cons_ex:
                logger.warning(
                    "Falha ao povoar consolidações após importação Nacional: %s",
                    cons_ex,
                )

        msg = f"Importação concluída: {imported_nfs_count} nova(s) NFS-e(s) e {updated_events_count} evento(s) sincronizado(s) até o NSU {max_nsu}."
        return imported_nfs_count + updated_events_count, msg

    elif provider_type != "PAULISTANA":
        return 0, f"Provedor {provider_type} não suportado."

    provider = PaulistanaProvider()
    limiter = RateLimiter(max_per_second=4.0)

    # Identificar notas já existentes no banco de dados local para Paulistana
    existing_numbers = set()
    paulistana_nfs = NotaFiscal.objects.exclude(verification_code="")
    for nf_str in paulistana_nfs.values_list("nf_number", flat=True):
        if nf_str and nf_str.strip().isdigit():
            existing_numbers.add(int(nf_str.strip()))

    count = 0
    imported_dates = []

    def _salvar_nota(r: dict) -> bool:
        nonlocal count
        if not r:
            return False

        nf_num = r.get("nf_number")
        chave = r.get("chave_acesso_nacional")
        cod_ver = r.get("verification_code")

        with transaction.atomic():
            exists = False
            if chave:
                exists = NotaFiscal.objects.filter(chave_acesso_nacional=chave).exists()
            if not exists and nf_num:
                q = NotaFiscal.objects.filter(nf_number=nf_num)
                if cod_ver:
                    q = q.filter(verification_code=cod_ver)
                exists = q.exists()

            if not exists:
                nf = NotaFiscal(
                    nf_number=nf_num,
                    verification_code=cod_ver,
                    chave_acesso_nacional=chave or None,
                    amount_brl=Decimal(str(r["amount_brl"])),
                    description=r.get("description", ""),
                    issue_date=r["issue_date"],
                    is_canceled=r.get("is_canceled", False),
                    cancelation_date=r.get("cancelation_date"),
                    is_export=True,
                    data_hora_autorizacao=r.get("data_hora_autorizacao"),
                    codigo_tributacao_nacional=r.get("codigo_tributacao_nacional", ""),
                    codigo_nbs=r.get("codigo_nbs", ""),
                    aliquota_iss=r.get("aliquota_iss"),
                    valor_iss=r.get("valor_iss"),
                    codigo_servico_municipio=r.get("codigo_servico_municipio", ""),
                )
                if r.get("raw_xml"):
                    nf.xml_autorizacao.save(
                        f"NFS-e_{nf_num}.xml",
                        ContentFile(r["raw_xml"].encode("utf-8")),
                        save=False,
                    )
                nf.save()
                imported_dates.append(r["issue_date"])
                count += 1
                return True
            else:
                # Sincroniza cancelamento se foi cancelada na prefeitura
                if r.get("is_canceled") and nf_num:
                    nf_obj = NotaFiscal.objects.filter(nf_number=nf_num).first()
                    if nf_obj and not nf_obj.is_canceled:
                        nf_obj.is_canceled = True
                        nf_obj.cancelation_date = r.get("cancelation_date")
                        nf_obj.save(update_fields=["is_canceled", "cancelation_date"])
                        imported_dates.append(nf_obj.issue_date)
                return False

    # 1. Caso haja buracos nas notas já cadastradas (1 até max_num)
    if existing_numbers:
        max_num = max(existing_numbers)
        holes = [i for i in range(1, max_num) if i not in existing_numbers]
        for h in holes:
            limiter.wait()
            try:
                res = provider.buscar_nfse_por_numero(h)
                if res:
                    _salvar_nota(res)
            except Exception as ex:
                logger.error(f"Erro ao buscar nota fiscal {h} na prefeitura: {ex}")

        start_newer = max_num + 1
    else:
        # Caso não existam notas cadastradas, procurar todas a partir da 1
        start_newer = 1

    # 2. Procurar notas mais novas a partir de start_newer até encontrar nota inexistente (retorno 0 notas)
    curr_nfe = start_newer
    while True:
        limiter.wait()
        try:
            res = provider.buscar_nfse_por_numero(curr_nfe)
        except Exception as ex:
            logger.error(f"Erro ao buscar nota fiscal {curr_nfe} na prefeitura: {ex}")
            break

        if res:
            _salvar_nota(res)
            curr_nfe += 1
        else:
            # Nota inexistente (0 notas retornadas para X). Encerra busca.
            break

    if count > 0:
        try:
            from core.services.consolidation import (
                populate_consolidations_for_imported_notes,
            )

            populate_consolidations_for_imported_notes(imported_dates)
        except Exception as cons_ex:
            logger.warning(
                "Falha ao povoar consolidações após importação Paulistana: %s",
                cons_ex,
            )

    if count == 0:
        return (
            0,
            "Nenhuma nova NFS-e encontrada para importação. A base já está atualizada.",
        )
    return count, f"Foram importadas {count} NFS-e(s) com sucesso."


def cancel_nota_fiscal(invoice_or_nf, origem="System"):
    """Cancels a NotaFiscal with the tax authority and synchronizes local records and logs."""
    from django.core.files.base import ContentFile
    from django.utils import timezone
    from core.models import Invoice, NotaFiscal, NfseLog
    from core.nfse.base import extract_nota_fiscal
    from core.nfse.provider_factory import get_provider

    invoice = None
    nf = None
    if isinstance(invoice_or_nf, Invoice):
        invoice = invoice_or_nf
        nf = getattr(invoice, "nota_fiscal", None)
    elif isinstance(invoice_or_nf, NotaFiscal):
        nf = invoice_or_nf
        invoice = getattr(nf, "invoice", None)
    else:
        nf = extract_nota_fiscal(invoice_or_nf)
        invoice = getattr(invoice_or_nf, "invoice", None) if hasattr(invoice_or_nf, "invoice") else None

    if nf and not nf.can_be_canceled:
        raise Exception(
            f"NFS-e {nf.nf_number} foi autorizada há mais de 24 horas e não pode ser cancelada."
        )

    provider = get_provider(invoice or nf)
    result = provider.cancelar_nfse(invoice or nf)

    # Always log cancellation attempt
    NfseLog.objects.create(
        invoice=invoice,
        nota_fiscal=nf,
        origem=origem,
        payload_enviado=result.xml_enviado or "",
        payload_retorno=result.xml_retorno or "",
        erro_mensagem=" | ".join(result.erros) if not result.sucesso else "",
    )

    if result.sucesso:
        if nf and result.xml_retorno and ("<evento" in result.xml_retorno or "<pedRegEvento" in result.xml_retorno):
            try:
                from core.nfse.nacional.provider import _parse_decompressed_evento_xml
                parsed_ev = _parse_decompressed_evento_xml(result.xml_retorno)
                if parsed_ev:
                    _save_nf_events(nf, [parsed_ev])
            except Exception as ev_err:
                logger.warning("Falha ao salvar evento retornado no cancelamento: %s", ev_err)

        if invoice:
            invoice.status = "CANCELED"
            invoice.save(update_fields=["status"])

        if nf:
            nf.is_canceled = True
            nf.cancelation_date = result.cancelation_date or timezone.now()

            xml_to_save = result.xml_retorno
            if not xml_to_save:
                try:
                    consult_res = provider.consultar_nfse(invoice or nf)
                    if consult_res and consult_res.xml_retorno:
                        xml_to_save = consult_res.xml_retorno
                except Exception as e:
                    logger.warning(
                        "Failed to fetch updated XML for canceled NFS-e: %s", e
                    )

            if xml_to_save and ("<NFSe" in xml_to_save or "<tpNFe" in xml_to_save):
                if nf.xml_autorizacao:
                    nf.xml_autorizacao.delete(save=False)

                file_content = (
                    xml_to_save.encode("utf-8")
                    if isinstance(xml_to_save, str)
                    else xml_to_save
                )
                nf.xml_autorizacao.save(
                    f"NFS-e_{nf.nf_number}.xml",
                    ContentFile(file_content),
                    save=False,
                )

            nf.save()

            from core.tasks.nfse_tasks import fetch_nfse_pdf_task

            fetch_nfse_pdf_task.delay(
                invoice_id=invoice.id if invoice else None,
                nf_id=nf.id if nf else None,
                force=True,
            )

    return result


def fetch_and_save_nfse_pdf(invoice_or_nf, provider, force=False):
    """Fetches the NFS-e PDF from the provider and saves it to the NotaFiscal record.
    Returns the pdf bytes if successful, None if not yet ready.
    """
    from django.core.files.base import ContentFile
    from core.nfse.base import extract_nota_fiscal

    nf = extract_nota_fiscal(invoice_or_nf)
    if not nf:
        return None

    pdf_bytes = provider.baixar_pdf(invoice_or_nf)
    if pdf_bytes:
        if force and nf.danfse_pdf:
            nf.danfse_pdf.delete(save=False)
        nf.danfse_pdf.save(f"NFS-e_{nf.nf_number}.pdf", ContentFile(pdf_bytes), save=False)
        nf.save(update_fields=["danfse_pdf", "updated_at"])
    return pdf_bytes



def sync_nota_fiscal(nf) -> tuple[bool, str]:
    """
    Sincroniza os dados de uma NFS-e local com o provedor/prefeitura.
    Atualiza status (inclusive cancelamento externo), metadados fiscais,
    XML de autorização e, se cancelada, atualiza o status da Invoice associada.
    """
    from core.nfse.provider_factory import get_provider
    from django.core.files.base import ContentFile
    from django.utils import timezone
    from decimal import Decimal

    provider = get_provider(nf)

    # 1. Consulta dados atualizados na prefeitura
    try:
        r = None
        if nf.provider_type == "PAULISTANA":
            if nf.nf_number:
                r = provider.buscar_nfse_por_numero(nf.nf_number)
        elif nf.provider_type == "NACIONAL":
            if nf.chave_acesso_nacional:
                r = provider.buscar_nfse_por_chave(nf.chave_acesso_nacional)
            elif nf.nf_number:
                r = provider.buscar_nfse_por_numero(nf.nf_number)
        else:
            if nf.nf_number:
                r = provider.buscar_nfse_por_numero(nf.nf_number)
            elif nf.chave_acesso_nacional:
                r = provider.buscar_nfse_por_chave(nf.chave_acesso_nacional)
    except Exception as ex:
        logger.exception("Erro ao consultar NFS-e %s junto ao provedor: %s", nf.nf_number, ex)
        return False, f"Erro ao consultar o provedor: {ex}"

    if not r:
        return False, f"NFS-e {nf.nf_number} não encontrada junto ao provedor."

    # 2. Atualizar campos cadastrais e fiscais
    was_canceled_before = nf.is_canceled
    now_canceled = r.get("is_canceled", False)

    # Salva eventos retornados pela consulta (se houver)
    events = r.get("events", [])
    if events:
        ev_canceled, ev_date = _save_nf_events(nf, events)
        if ev_canceled:
            now_canceled = True
            if not r.get("cancelation_date") and ev_date:
                r["cancelation_date"] = ev_date

    if r.get("verification_code"):
        nf.verification_code = r["verification_code"]
    if r.get("chave_acesso_nacional"):
        nf.chave_acesso_nacional = r["chave_acesso_nacional"]
    if r.get("amount_brl"):
        try:
            nf.amount_brl = Decimal(str(r["amount_brl"]))
        except Exception:
            pass
    if r.get("description"):
        nf.description = r["description"]
    if r.get("issue_date"):
        nf.issue_date = r["issue_date"]
    if r.get("data_hora_autorizacao"):
        nf.data_hora_autorizacao = r["data_hora_autorizacao"]
    if r.get("codigo_servico_municipio"):
        nf.codigo_servico_municipio = r["codigo_servico_municipio"]
    if r.get("codigo_tributacao_nacional"):
        nf.codigo_tributacao_nacional = r["codigo_tributacao_nacional"]
    if r.get("codigo_nbs"):
        nf.codigo_nbs = r["codigo_nbs"]
    if r.get("aliquota_iss") is not None:
        nf.aliquota_iss = r["aliquota_iss"]
    if r.get("valor_iss") is not None:
        nf.valor_iss = r["valor_iss"]

    # 3. Tratamento de cancelamento
    cancellation_detected = False
    if now_canceled:
        nf.is_canceled = True
        nf.cancelation_date = r.get("cancelation_date") or nf.cancelation_date or timezone.now()
        if not was_canceled_before:
            cancellation_detected = True

        # Se houver Invoice vinculada, sincronizar seu status para CANCELED
        if nf.invoice and nf.invoice.status != "CANCELED":
            nf.invoice.status = "CANCELED"
            nf.invoice.save(update_fields=["status", "updated_at"])

    # 4. Atualizar XML se presente
    if r.get("raw_xml"):
        nf.xml_autorizacao.save(
            f"NFS-e_{nf.nf_number}.xml",
            ContentFile(r["raw_xml"].encode("utf-8")),
            save=False,
        )

    # 5. Salvar NotaFiscal
    nf.save()

    # 6. Se cancelamento acabou de ser detectado, tentar atualizar PDF
    if cancellation_detected:
        try:
            fetch_and_save_nfse_pdf(nf, provider, force=True)
        except Exception as ex:
            logger.warning("Falha ao atualizar PDF da NFS-e cancelada: %s", ex)

        return True, f"NFS-e {nf.nf_number} sincronizada com sucesso: identificada como CANCELADA na prefeitura."

    return True, f"NFS-e {nf.nf_number} sincronizada com sucesso com o provedor."
