import logging
import os
import datetime
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Union

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction

from core.models import CompanySettings, Invoice, NotaFiscal
from core.nfse.base import CancelResult, EmitResult, NFSeProvider, NFSeProviderError
from .client import NFeClient, extract_paulistana_xml_errors
import core.nfse.paulistana.schemas_v1.tipos_nfe_v01 as v1
from xsdata.models.datatype import XmlDate
from core.services import _prepare_nf_data
from .rps_signer import assinar_rps_v1
from .utils import to_xml

logger = logging.getLogger(__name__)


class PaulistanaProvider(NFSeProvider):
    def _get_client(self, company: CompanySettings):

        if not company.pfx_cert_pem or not company.pfx_key_pem:
            raise Exception(
                "Certificado digital não configurado. Por favor, faça o upload na página Sua Empresa."
            )
        cnpj = company.cnpj.replace(".", "").replace("/", "").replace("-", "")
        im = company.inscricao_municipal
        return NFeClient(company.pfx_cert_pem, company.pfx_key_pem, cnpj, im), im

    def emitir_nfse(self, invoice: Invoice) -> EmitResult:
        from core.models import paulistana_emission_blocked

        if paulistana_emission_blocked():
            return EmitResult(
                sucesso=False,
                erros=[
                    "A emissão de NFS-e pela Paulistana está encerrada desde 01/11/2026 para ME/EPP do Simples Nacional. Utilize o Emissor Nacional."
                ],
            )

        company = CompanySettings.load()
        client, im = self._get_client(company)
        client_obj = invoice.client

        # Assign document number if it doesn't have one
        if not invoice.document_number:
            from core.services.nfse_services import assign_next_document_number

            assign_next_document_number(invoice)

        rps_series = invoice.document_series
        numero_rps = str(invoice.document_number)

        amount_brl, description, effective_rate_pct = _prepare_nf_data(invoice)
        nf_description = description.replace("\r", "").strip()

        # for export we can use only logradoro field for the address, lets assemble it  here as street + num + complemento
        logradoro = client_obj.address_line1 or ""
        if client_obj.address_number:
            logradoro += f" {client_obj.address_number}"
        if client_obj.address_line2:
            logradoro += f", {client_obj.address_line2}"
        if client_obj.address_postal_code:
            logradoro += f", {client_obj.address_postal_code}"

        cod_servico = str(
            getattr(invoice, "codigo_servico_municipio", "") or ""
        ).strip()
        if not cod_servico:
            return EmitResult(
                sucesso=False,
                erros=[
                    "Código de Serviço do Município é obrigatório para emissão de RPS na Paulistana."
                ],
            )

        rps = v1.TpRps(
            assinatura="",
            chave_rps=v1.TpChaveRps(
                inscricao_prestador=im,
                serie_rps=rps_series,
                numero_rps=numero_rps,
            ),
            tipo_rps=v1.TpTipoRps.RPS,
            data_emissao=XmlDate.from_date(invoice.issue_date),
            status_rps=v1.TpStatusNfe.N,
            tributacao_rps="P",
            valor_servicos=f"{amount_brl:.2f}",
            valor_deducoes="0.00",
            codigo_servico=cod_servico,
            aliquota_servicos="0.00",
            issretido=False,
            razao_social_tomador=client_obj.name,
            endereco_tomador=v1.TpEndereco(
                tipo_logradouro=None,
                logradouro=logradoro or None,
                numero_endereco=None,
                complemento_endereco=None,
                bairro=None,
                cidade=None,
                uf=None,
                cep=None,
            ),
            discriminacao=nf_description,
        )

        try:
            rps.assinatura = assinar_rps_v1(rps, client.key_pem)
            payload_xml = to_xml(rps)
        except Exception as sign_ex:
            logger.exception("Error signing RPS: %s", sign_ex)
            return EmitResult(
                sucesso=False,
                erros=[f"Erro ao assinar RPS: {sign_ex}"],
            )

        result = EmitResult(sucesso=False, xml_enviado=payload_xml)

        if company and company.debug_mode:
            try:
                resultado, signed_xml_str, retorno_xml_str = (
                    client.testar_envio_lote_rps([rps])
                )
            except NFSeProviderError as pe:
                logger.error("Provider error in Paulistana debug test: %s", pe)
                result.xml_enviado = pe.raw_request or payload_xml
                result.xml_retorno = pe.raw_response or ""
                result.erros = [pe.message]
                return result
            except Exception as e:
                logger.exception("Unexpected error in Paulistana debug test: %s", e)
                result.xml_enviado = payload_xml
                result.erros = [
                    f"Erro inesperado no envio de teste à prefeitura: {str(e)}"
                ]
                return result

            result.xml_enviado = signed_xml_str
            result.xml_retorno = retorno_xml_str

            if (
                resultado
                and getattr(resultado, "cabecalho", None)
                and getattr(resultado.cabecalho, "sucesso", False)
            ):
                result.sucesso = True
                result.numero_nf = f"DEBUG-{numero_rps}"
                result.codigo_verificacao = "DEBUG-FAKE-CODE"
                from core.nfse.paulistana.mock import build_mock_paulistana_nfse_xml
                from django.utils import timezone

                result.xml_retorno = build_mock_paulistana_nfse_xml(
                    invoice=invoice,
                    company=company,
                    numero_nfe=numero_rps,
                    codigo_verificacao=result.codigo_verificacao,
                )
                result.data_hora_autorizacao = timezone.now()
                is_export = (
                    (getattr(client_obj, "address_country_code", "") or "").upper()
                    != "BR"
                    if client_obj
                    else True
                )
                if is_export:
                    result.aliquota_iss = Decimal("0.00")
                    result.valor_iss = Decimal("0.00")
                else:
                    amount_brl, _, effective_rate_pct = _prepare_nf_data(invoice)
                    result.aliquota_iss = effective_rate_pct
                    result.valor_iss = (
                        (amount_brl * (effective_rate_pct / Decimal("100.0"))).quantize(
                            Decimal("0.01")
                        )
                        if effective_rate_pct
                        else Decimal("0.00")
                    )
                return result
            else:
                erros = getattr(resultado, "erro", []) if resultado else []
                for e in erros:
                    result.erros.append(f"{e.codigo} - {e.descricao}")
                if getattr(resultado, "alerta", []):
                    for a in resultado.alerta:
                        result.erros.append(f"Alerta {a.codigo} - {a.descricao}")
                if not result.erros and retorno_xml_str:
                    result.erros.extend(extract_paulistana_xml_errors(retorno_xml_str))
                if not result.erros:
                    result.erros.append("Falha desconhecida no modo homologação/teste")
            return result

        # Production mode
        try:
            resultado, signed_xml_str, retorno_xml_str = client.enviar_lote_rps([rps])
        except NFSeProviderError as pe:
            logger.error("Provider error transmitting RPS to Paulistana: %s", pe)
            result.xml_enviado = pe.raw_request or payload_xml
            result.xml_retorno = pe.raw_response or ""
            result.erros = [pe.message]
            return result
        except Exception as e:
            logger.exception("Unexpected error transmitting RPS to Paulistana: %s", e)
            result.xml_enviado = payload_xml
            result.erros = [f"Erro inesperado no envio à prefeitura: {str(e)}"]
            return result

        result.xml_enviado = signed_xml_str
        result.xml_retorno = retorno_xml_str

        if (
            resultado
            and getattr(resultado, "cabecalho", None)
            and getattr(resultado.cabecalho, "sucesso", False)
        ):
            chave_list = getattr(resultado, "chave_nfe_rps", None)
            chave = (
                chave_list[0]
                if isinstance(chave_list, list) and chave_list
                else chave_list
            )
            if chave and getattr(chave, "chave_nfe", None):
                result.sucesso = True
                result.numero_nf = str(chave.chave_nfe.numero_nfe)
                result.codigo_verificacao = str(chave.chave_nfe.codigo_verificacao)
                chave_nac = getattr(chave.chave_nfe, "chave_nota_nacional", None)
                if chave_nac:
                    result.chave_acesso_nacional = str(chave_nac)

                # NOVO: Fetch the emitted NFe to populate data_hora_autorizacao, etc.
                try:
                    numero_lote = None
                    if getattr(resultado, "cabecalho", None) and getattr(
                        resultado.cabecalho, "informacoes_lote", None
                    ):
                        numero_lote = getattr(
                            resultado.cabecalho.informacoes_lote, "numero_lote", None
                        )

                    if numero_lote:
                        notas, retorno_lote_xml = client.consultar_lote(
                            str(numero_lote)
                        )
                        if notas:
                            for nota in notas:
                                result.xml_retorno = to_xml(nota)

                                data_hora = getattr(nota, "data_emissao_nfe", None)
                                if data_hora:
                                    from django.utils import timezone

                                    data_hora = timezone.make_aware(
                                        datetime.datetime(
                                            data_hora.year,
                                            data_hora.month,
                                            data_hora.day,
                                            data_hora.hour,
                                            data_hora.minute,
                                            data_hora.second,
                                        )
                                    )
                                    result.data_hora_autorizacao = data_hora

                                aliquota_iss_val = getattr(
                                    nota, "aliquota_servicos", None
                                )
                                if aliquota_iss_val is not None:
                                    result.aliquota_iss = Decimal(str(aliquota_iss_val))
                                valor_iss_val = getattr(nota, "valor_iss", None)
                                if valor_iss_val is not None:
                                    result.valor_iss = Decimal(str(valor_iss_val))

                                result.codigo_servico_municipio = getattr(
                                    nota, "codigo_servico", ""
                                )
                                break
                    else:
                        # Fallback se por algum motivo não der para consultar o lote
                        consulta_result = self.consultar_nfse(invoice)
                        if consulta_result:
                            result.xml_retorno = consulta_result.xml_retorno
                            result.data_hora_autorizacao = (
                                consulta_result.data_hora_autorizacao
                            )
                            result.aliquota_iss = consulta_result.aliquota_iss
                            result.valor_iss = consulta_result.valor_iss
                            result.codigo_servico_municipio = (
                                consulta_result.codigo_servico_municipio
                            )
                            result.codigo_tributacao_nacional = (
                                consulta_result.codigo_tributacao_nacional
                            )
                            result.codigo_nbs = consulta_result.codigo_nbs
                except Exception as ex:
                    logger.warning(
                        "Failed to fetch full NFe details after emission: %s", ex
                    )

                return result
            else:
                result.sucesso = False
                result.erros.append(
                    "Sucesso retornado, mas chave NFe ausente na resposta"
                )
        else:
            if resultado:
                erros = getattr(resultado, "erro", []) or []
                for e in erros:
                    result.erros.append(f"{e.codigo} - {e.descricao}")
                if getattr(resultado, "alerta", []):
                    for a in resultado.alerta:
                        result.erros.append(f"Alerta {a.codigo} - {a.descricao}")
            if not result.erros and retorno_xml_str:
                result.erros.extend(extract_paulistana_xml_errors(retorno_xml_str))
            if not result.erros:
                result.erros.append(
                    "Falha na comunicação com a prefeitura ou retorno inválido."
                )

        return result

    def consultar_nfse(self, invoice: Invoice) -> Optional[EmitResult]:
        """Checks if the RPS for this invoice was already converted into an NFe in São Paulo."""
        if not invoice.document_number:
            return None
        company = CompanySettings.load()
        if not company:
            return None

        client, im = self._get_client(company)
        # Note: Do NOT catch and swallow exceptions here!
        # If an exception occurs, let it propagate so that caller (consultar_nfe_na_prefeitura / issue_nfse_task)
        # knows consultation could not be verified and aborts emission to prevent duplicates.
        dt_fim = min(invoice.issue_date + timedelta(days=5), date.today())
        dt_inicio = dt_fim - timedelta(days=30)
        notas = client.consultar_nfe_emitidas(dt_inicio=dt_inicio, dt_fim=dt_fim)
        if not notas:
            return None

        numero_rps_target = str(invoice.document_number)
        for nota in notas:
            if (
                hasattr(nota, "chave_rps")
                and nota.chave_rps
                and str(nota.chave_rps.numero_rps) == numero_rps_target
            ):
                ret_xml = to_xml(nota)
                chave_nac = getattr(nota.chave_nfe, "chave_nota_nacional", "")

                # Extrair atributos adicionais
                data_hora = getattr(nota, "data_emissao_nfe", None)
                if data_hora:
                    from django.utils import timezone

                    data_hora = timezone.make_aware(
                        datetime.datetime(
                            data_hora.year,
                            data_hora.month,
                            data_hora.day,
                            data_hora.hour,
                            data_hora.minute,
                            data_hora.second,
                        )
                    )

                aliquota_iss_val = getattr(nota, "aliquota_servicos", None)
                valor_iss_val = getattr(nota, "valor_iss", None)

                def _safe_dec(v):
                    if v is None:
                        return None
                    s = str(v).strip().replace(",", ".")
                    if not s:
                        return None
                    try:
                        return Decimal(s)
                    except Exception:
                        return None

                return EmitResult(
                    sucesso=True,
                    numero_nf=str(nota.chave_nfe.numero_nfe),
                    codigo_verificacao=str(nota.chave_nfe.codigo_verificacao),
                    chave_acesso_nacional=str(chave_nac) if chave_nac else "",
                    xml_retorno=ret_xml,
                    data_hora_autorizacao=data_hora,
                    codigo_servico_municipio=getattr(nota, "codigo_servico", ""),
                    aliquota_iss=_safe_dec(aliquota_iss_val),
                    valor_iss=_safe_dec(valor_iss_val),
                )
        return None

    def cancelar_nfse(self, invoice_or_nf: Union[Invoice, NotaFiscal]) -> CancelResult:
        company = CompanySettings.load()
        if not company:
            return CancelResult(sucesso=False, erros=["CompanySettings not found."])

        from core.nfse.base import extract_nota_fiscal

        nf = extract_nota_fiscal(invoice_or_nf)
        if not nf or not nf.nf_number or not nf.verification_code:
            return CancelResult(
                sucesso=False, erros=["NFS-e não encontrada para cancelamento."]
            )

        client, im = self._get_client(company)

        # Test mode mock since test environment often fails cancellations
        if company.debug_mode:
            from core.nfse.paulistana.mock import update_paulistana_xml_cancelled
            from django.utils import timezone

            cancel_dt = timezone.now()
            updated_xml = ""
            if nf and nf.xml_autorizacao:
                try:
                    if nf.xml_autorizacao.storage.exists(nf.xml_autorizacao.name):
                        with nf.xml_autorizacao.open("rb") as f:
                            existing_xml = f.read().decode("utf-8", errors="replace")
                        updated_xml = update_paulistana_xml_cancelled(
                            existing_xml, cancel_dt
                        )
                except Exception as ex:
                    logger.warning(
                        "Could not update Paulistana XML for cancellation: %s", ex
                    )

            return CancelResult(
                sucesso=True,
                xml_enviado="<MockCancelRequest></MockCancelRequest>",
                xml_retorno=updated_xml or "<MockCancelResponse></MockCancelResponse>",
                cancelation_date=cancel_dt,
            )

        try:
            sucesso, xml_enviado, xml_retorno, erros = client.cancelar_nfe(
                nf.nf_number, nf.verification_code
            )

            cancelation_date = None
            if sucesso and xml_retorno:
                import re
                from django.utils import timezone

                match = re.search(
                    r"<DataCancelamento>([^<]+)</DataCancelamento>", xml_retorno
                )
                if match:
                    try:
                        dt_str = match.group(1).strip()
                        if (
                            "Z" not in dt_str
                            and "+" not in dt_str
                            and "-" not in dt_str[11:]
                        ):
                            cancelation_date = timezone.make_aware(
                                datetime.datetime.fromisoformat(dt_str)
                            )
                        else:
                            cancelation_date = datetime.datetime.fromisoformat(
                                dt_str.replace("Z", "+00:00")
                            )
                    except Exception:
                        pass

                if not cancelation_date:
                    try:
                        consulta = self.consultar_nfse(invoice)
                        if consulta and consulta.xml_retorno:
                            match2 = re.search(
                                r"<DataCancelamento>([^<]+)</DataCancelamento>",
                                consulta.xml_retorno,
                            )
                            if match2:
                                dt_str2 = match2.group(1).strip()
                                if (
                                    "Z" not in dt_str2
                                    and "+" not in dt_str2
                                    and "-" not in dt_str2[11:]
                                ):
                                    cancelation_date = timezone.make_aware(
                                        datetime.datetime.fromisoformat(dt_str2)
                                    )
                                else:
                                    cancelation_date = datetime.datetime.fromisoformat(
                                        dt_str2.replace("Z", "+00:00")
                                    )
                    except Exception:
                        pass

            if not sucesso:
                # Idempotency check: what if the note was already canceled externally?
                err_text = " ".join(erros or []).lower()
                if "já cancelada" in err_text or "ja cancelada" in err_text or "1206" in err_text:
                    try:
                        nfe_data = self.buscar_nfse_por_numero(nf.nf_number)
                        if nfe_data and nfe_data.get("is_canceled"):
                            from django.utils import timezone

                            return CancelResult(
                                sucesso=True,
                                xml_enviado=xml_enviado,
                                xml_retorno=nfe_data.get("raw_xml") or xml_retorno,
                                cancelation_date=nfe_data.get("cancelation_date") or timezone.now(),
                            )
                    except Exception:
                        pass

            return CancelResult(
                sucesso=sucesso,
                xml_enviado=xml_enviado,
                xml_retorno=xml_retorno,
                erros=erros,
                cancelation_date=cancelation_date,
            )
        except Exception as e:
            logger.exception("Unexpected error canceling NFSe in Paulistana: %s", e)
            return CancelResult(
                sucesso=False, erros=[f"Erro inesperado no cancelamento: {e}"]
            )

    def baixar_pdf(
        self, invoice_or_nf: Union[Invoice, NotaFiscal]
    ) -> Optional[bytes]:
        from core.nfse.paulistana.client import download_nfse_pdf
        from core.nfse.base import extract_nota_fiscal

        company = CompanySettings.load()
        if not company:
            return None

        nf = extract_nota_fiscal(invoice_or_nf)
        if not nf or not nf.nf_number:
            return None

        im = company.inscricao_municipal
        ver_code = str(getattr(nf, "verification_code", "") or "").strip()

        # Try to read local authorization XML if present
        xml_str = None
        if nf.xml_autorizacao:
            try:
                if nf.xml_autorizacao.storage.exists(nf.xml_autorizacao.name):
                    with nf.xml_autorizacao.open("rb") as f:
                        xml_str = f.read().decode("utf-8", errors="replace")
            except Exception as ex:
                logger.warning(
                    "Could not read xml_autorizacao in baixar_pdf: %s", ex
                )

        from core.nfse.paulistana.mock import is_paulistana_xml_mocked

        is_mock = is_paulistana_xml_mocked(xml_str, ver_code)

        # In debug mode (or when dealing with a mocked nota):
        # Only use the mock PDF if the XML itself is also mocked.
        # If the nota was imported from the provider with a valid XML and valid verification code,
        # the real PDF from the tax authority must be used.
        if is_mock:
            if not xml_str:
                from core.nfse.paulistana.mock import (
                    build_mock_paulistana_nfse_xml,
                    update_paulistana_xml_cancelled,
                )

                invoice = getattr(nf, "invoice", None) or (
                    invoice_or_nf if isinstance(invoice_or_nf, Invoice) else None
                )
                if invoice:
                    xml_str = build_mock_paulistana_nfse_xml(
                        invoice, company, nf.nf_number, nf.verification_code
                    )
                    if getattr(nf, "is_canceled", False):
                        xml_str = update_paulistana_xml_cancelled(
                            xml_str, getattr(nf, "cancelation_date", None)
                        )

            if xml_str:
                from core.nfse.paulistana.mock import render_paulistana_debug_pdf

                try:
                    return render_paulistana_debug_pdf(xml_str)
                except Exception as ex:
                    logger.exception(
                        "Failed to render Paulistana debug PDF: %s", ex
                    )
                    return None

        if not im or not ver_code:
            return None

        return download_nfse_pdf(im, nf.nf_number, ver_code)

    def _parse_nfe_to_dict(self, nota) -> dict:
        """Converts a Paulistana TpNfe object to a standardized dictionary."""
        chave_nac = (
            getattr(nota.chave_nfe, "chave_nota_nacional", "")
            if hasattr(nota, "chave_nfe")
            else ""
        )
        nf_num = str(nota.chave_nfe.numero_nfe) if hasattr(nota, "chave_nfe") else ""
        cod_ver = (
            str(nota.chave_nfe.codigo_verificacao) if hasattr(nota, "chave_nfe") else ""
        )

        val = "0.00"
        if hasattr(nota, "valor_servicos"):
            val = str(nota.valor_servicos or "0.00")
        elif hasattr(nota, "valor_nfe"):
            val = str(nota.valor_nfe or "0.00")

        desc = nota.discriminacao if hasattr(nota, "discriminacao") else ""

        dt_emi = date.today()
        if hasattr(nota, "data_emissao_nfe") and nota.data_emissao_nfe:
            try:
                dt_emi = date(
                    nota.data_emissao_nfe.year,
                    nota.data_emissao_nfe.month,
                    nota.data_emissao_nfe.day,
                )
            except Exception:
                pass
        elif hasattr(nota, "data_emissao") and nota.data_emissao:
            try:
                dt_emi = date(
                    nota.data_emissao.year,
                    nota.data_emissao.month,
                    nota.data_emissao.day,
                )
            except Exception:
                pass

        is_canceled = False
        if hasattr(nota, "status_nfe"):
            status_val = getattr(nota.status_nfe, "value", str(nota.status_nfe))
            if status_val == "C":
                is_canceled = True

        cancelation_date = None
        data_cancel = getattr(nota, "data_cancelamento", None)
        if data_cancel:
            from django.utils import timezone

            cancelation_date = timezone.make_aware(
                datetime.datetime(
                    data_cancel.year,
                    data_cancel.month,
                    data_cancel.day,
                    getattr(data_cancel, "hour", 0),
                    getattr(data_cancel, "minute", 0),
                    getattr(data_cancel, "second", 0),
                )
            )

        data_hora = getattr(nota, "data_emissao_nfe", None)
        if data_hora:
            from django.utils import timezone

            data_hora = timezone.make_aware(
                datetime.datetime(
                    data_hora.year,
                    data_hora.month,
                    data_hora.day,
                    getattr(data_hora, "hour", 0),
                    getattr(data_hora, "minute", 0),
                    getattr(data_hora, "second", 0),
                )
            )

        aliquota_iss_val = getattr(nota, "aliquota_servicos", None)
        valor_iss_val = getattr(nota, "valor_iss", None)

        def _safe_dec(v):
            if v is None:
                return None
            s = str(v).strip().replace(",", ".")
            if not s:
                return None
            try:
                return Decimal(s)
            except Exception:
                return None

        return {
            "nf_number": nf_num,
            "verification_code": cod_ver,
            "chave_acesso_nacional": chave_nac,
            "amount_brl": val,
            "description": desc,
            "issue_date": dt_emi,
            "provider": "PAULISTANA",
            "is_canceled": is_canceled,
            "cancelation_date": cancelation_date,
            "raw_xml": to_xml(nota),
            "data_hora_autorizacao": data_hora,
            "codigo_servico_municipio": getattr(nota, "codigo_servico", ""),
            "aliquota_iss": _safe_dec(aliquota_iss_val),
            "valor_iss": _safe_dec(valor_iss_val),
        }

    def buscar_nfse_por_numero(self, numero: str | int) -> Optional[dict]:
        """Fetches a specific NFS-e by number using ConsultaNFe."""
        company = CompanySettings.load()
        if not company:
            return None

        client, _ = self._get_client(company)
        notas, raw_xml = client.consultar_nfe(numero)
        if not notas:
            return None

        return self._parse_nfe_to_dict(notas[0])

    def buscar_nfse_por_chave(self, chave_acesso: str) -> Optional[dict]:
        raise NotImplementedError(
            "Busca por chave não implementada para Paulistana. Use a busca por número."
        )
