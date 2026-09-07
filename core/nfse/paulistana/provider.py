import logging
import os
import datetime
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import transaction

from core.models import CompanySettings, Invoice, NotaFiscal
from core.nfse.base import CancelResult, EmitResult, NFSeProvider, NFSeProviderError
from .client import NFeClient, extract_paulistana_xml_errors
import core.nfse.paulistana.schemas_v1.tipos_nfe_v01 as v1
from xsdata.models.datatype import XmlDate
from core.services import _prepare_nf_data
from .models import assinar_rps_v1
from .utils import to_xml

logger = logging.getLogger(__name__)


class PaulistanaProvider(NFSeProvider):
    def _get_client(self, company: CompanySettings):

        if not company.pfx_cert_pem or not company.pfx_key_pem:
            raise Exception("Certificado digital não configurado. Por favor, faça o upload na página Sua Empresa.")
        cnpj = company.cnpj.replace(".", "").replace("/", "").replace("-", "")
        im = company.inscricao_municipal
        return NFeClient(company.pfx_cert_pem, company.pfx_key_pem, cnpj, im), im

    def emitir_nfse(self, invoice: Invoice) -> EmitResult:
        company = CompanySettings.objects.first()
        client, im = self._get_client(company)
        client_obj = invoice.client

        # Assign document number if it doesn't have one
        if not invoice.document_number:
            with transaction.atomic():
                comp = CompanySettings.objects.select_for_update().first()
                if comp:
                    invoice.document_number = comp.next_document_number
                    invoice.document_series = comp.document_series
                    if not comp.debug_mode:
                        comp.next_document_number += 1
                    comp.save()
                    invoice.save()
                else:
                    raise Exception(
                        "CompanySettings not found, cannot assign document number."
                    )

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
            codigo_servico="2668",
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
        company = CompanySettings.objects.first()
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

    def cancelar_nfse(self, invoice: Invoice) -> CancelResult:
        company = CompanySettings.objects.first()
        if not company:
            return CancelResult(sucesso=False, erros=["CompanySettings not found."])

        nf = getattr(invoice, "nota_fiscal", None)
        if not nf or not nf.nf_number or not nf.verification_code:
            return CancelResult(
                sucesso=False, erros=["NFS-e não encontrada para esta invoice."]
            )

        client, im = self._get_client(company)

        # Test mode mock since test environment often fails cancellations
        if company.debug_mode:
            return CancelResult(
                sucesso=True,
                xml_enviado="<MockCancelRequest></MockCancelRequest>",
                xml_retorno="<MockCancelResponse></MockCancelResponse>",
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

    def baixar_pdf(self, invoice: Invoice) -> bytes:
        from core.nfse.paulistana.client import download_nfse_pdf

        company = CompanySettings.objects.first()
        im = company.inscricao_municipal

        nf = getattr(invoice, "nota_fiscal", None)
        if not nf or not nf.nf_number or not nf.verification_code:
            return None

        if company and company.debug_mode:
            # We return dummy bytes since we can't fetch real PDFs in Paulistana debug mode sometimes
            # or we rely on the implementation inside download_nfse_pdf
            pass

        return download_nfse_pdf(im, nf.nf_number, nf.verification_code)

    def buscar_nfses_por_periodo(self, start_date, end_date) -> list:
        """Fetch NFS-es dividing period in chunks of max 31 days if needed."""
        company = CompanySettings.objects.first()
        if not company:
            return []

        client, _ = self._get_client(company)
        resultados = []

        current_start = start_date
        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=30), end_date)
            try:
                # The Paulistana API returns parsed objects
                notas = client.consultar_nfe_emitidas(
                    dt_inicio=current_start, dt_fim=current_end
                )
                if notas:
                    for nota in notas:
                        # Extract basic info into dict
                        chave_nac = (
                            getattr(nota.chave_nfe, "chave_nota_nacional", "")
                            if hasattr(nota, "chave_nfe")
                            else ""
                        )
                        nf_num = (
                            str(nota.chave_nfe.numero_nfe)
                            if hasattr(nota, "chave_nfe")
                            else ""
                        )
                        cod_ver = (
                            str(nota.chave_nfe.codigo_verificacao)
                            if hasattr(nota, "chave_nfe")
                            else ""
                        )

                        val = "0.00"
                        if hasattr(nota, "valor_servicos"):
                            val = nota.valor_servicos
                        elif hasattr(nota, "valor_nfe"):
                            val = nota.valor_nfe

                        desc = (
                            nota.discriminacao if hasattr(nota, "discriminacao") else ""
                        )

                        # Date
                        if hasattr(nota, "data_emissao_nfe") and nota.data_emissao_nfe:
                            try:
                                dt_emi = date(
                                    nota.data_emissao_nfe.year,
                                    nota.data_emissao_nfe.month,
                                    nota.data_emissao_nfe.day,
                                )
                            except:
                                dt_emi = current_start
                        elif hasattr(nota, "data_emissao") and nota.data_emissao:
                            try:
                                dt_emi = date(
                                    nota.data_emissao.year,
                                    nota.data_emissao.month,
                                    nota.data_emissao.day,
                                )
                            except:
                                dt_emi = current_start
                        else:
                            dt_emi = current_start

                        is_canceled = False
                        if hasattr(nota, "status_nfe"):
                            status_val = getattr(
                                nota.status_nfe, "value", str(nota.status_nfe)
                            )
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
                                    data_cancel.hour,
                                    data_cancel.minute,
                                    data_cancel.second,
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

                        resultados.append(
                            {
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
                                "codigo_servico_municipio": getattr(
                                    nota, "codigo_servico", ""
                                ),
                                "aliquota_iss": _safe_dec(aliquota_iss_val),
                                "valor_iss": _safe_dec(valor_iss_val),
                            }
                        )
            except Exception as e:
                logger.error(
                    f"Error fetching paulistana NFS-es from {current_start} to {current_end}: {e}"
                )

            current_start = current_end + timedelta(days=1)

        return resultados

    def buscar_nfse_por_chave(self, chave_acesso: str) -> Optional[dict]:
        raise NotImplementedError(
            "Busca por chave não implementada para Paulistana. Use a busca por período."
        )
