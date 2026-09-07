import datetime
import logging
import os
import tempfile
from decimal import Decimal
from typing import List, Optional, Tuple

import requests
from django.conf import settings
from core.utils.http import logged_post, logged_get
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from core.nfse.base import NFSeProviderError
from core.nfse.paulistana.schemas.pedido_consulta_nfe_periodo_v02 import (
    PedidoConsultaNfePeriodo,
)
from core.nfse.paulistana.schemas.retorno_consulta_v02 import RetornoConsulta
from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpCpfcnpj
from core.nfse.paulistana.schemas_v1.pedido_envio_lote_rps_v01 import (
    PedidoEnvioLoteRps as PedidoEnvioLoteRpsV1,
)
from core.nfse.paulistana.schemas_v1.retorno_envio_lote_rps_v01 import (
    RetornoEnvioLoteRps as RetornoEnvioLoteRpsV1,
)
from core.nfse.paulistana.schemas_v1.tipos_nfe_v01 import (
    TpCpfcnpj as TpCpfcnpjV1,
    TpRps as TpRpsV1,
)
from .signer import assinar_xml, carregar_certificado_pfx

logger = logging.getLogger(__name__)

SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)


def extract_soap_fault(content: str | bytes) -> Optional[str]:
    """Extracts human-readable SOAP fault messages supporting SOAP 1.1, SOAP 1.2, and custom namespaces."""
    if not content:
        return None
    try:
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        root = etree.fromstring(content_bytes, parser=SAFE_PARSER)
        faults = root.xpath("//*[local-name()='Fault']")
        if faults:
            f = faults[0]
            # Try Text (SOAP 1.2)
            texts = f.xpath(".//*[local-name()='Text']/text()")
            if texts and texts[0].strip():
                return texts[0].strip()
            # Try faultstring (SOAP 1.1)
            fstrings = f.xpath(".//*[local-name()='faultstring']/text()")
            if fstrings and fstrings[0].strip():
                return fstrings[0].strip()
            # Try Reason
            reasons = f.xpath(".//*[local-name()='Reason']//text()")
            if reasons:
                joined_reason = " ".join(r.strip() for r in reasons if r.strip())
                if joined_reason:
                    return joined_reason
            # Try detail / Detail
            details = f.xpath(
                ".//*[local-name()='detail' or local-name()='Detail']//text()"
            )
            if details:
                joined_detail = " ".join(d.strip() for d in details if d.strip())
                if joined_detail:
                    return joined_detail
            return "Falha SOAP retornada pelo servidor da prefeitura."
    except Exception:
        pass
    return None


def extract_paulistana_xml_errors(xml_str: str) -> List[str]:
    """Fallback extractor for errors and alerts from Paulistana XML strings, independent of xsdata schemas."""
    erros: List[str] = []
    if not xml_str:
        return erros
    try:
        root = etree.fromstring(xml_str.encode("utf-8"), parser=SAFE_PARSER)
        error_nodes = root.xpath("//*[local-name()='Erro']")
        for err in error_nodes:
            cod = err.xpath(".//*[local-name()='Codigo']/text()")
            desc = err.xpath(".//*[local-name()='Descricao']/text()")
            c_val = cod[0].strip() if cod else ""
            d_val = desc[0].strip() if desc else ""
            if c_val and d_val:
                erros.append(f"{c_val} - {d_val}")
            elif d_val:
                erros.append(d_val)
            elif c_val:
                erros.append(f"Erro {c_val}")

        alert_nodes = root.xpath("//*[local-name()='Alerta']")
        for al in alert_nodes:
            cod = al.xpath(".//*[local-name()='Codigo']/text()")
            desc = al.xpath(".//*[local-name()='Descricao']/text()")
            c_val = cod[0].strip() if cod else ""
            d_val = desc[0].strip() if desc else ""
            if c_val and d_val:
                erros.append(f"Alerta {c_val} - {d_val}")
            elif d_val:
                erros.append(f"Alerta: {d_val}")
    except Exception:
        pass
    return erros


class NFeClient:
    def __init__(self, cert_pem: str, key_pem: str, cnpj: str, inscricao_municipal: str):
        self.cnpj = cnpj
        self.inscricao_municipal = inscricao_municipal
        self.cert_pem = cert_pem.encode('utf-8') if isinstance(cert_pem, str) else cert_pem
        self.key_pem = key_pem.encode('utf-8') if isinstance(key_pem, str) else key_pem
        self.url = getattr(
            settings, "NFE_SP_URL", "https://nfews.prefeitura.sp.gov.br/lotenfe.asmx"
        )

        self.serializer_config = SerializerConfig(pretty_print=True)
        self.serializer = XmlSerializer(config=self.serializer_config)
        self.parser_config = ParserConfig(
            fail_on_unknown_properties=False,
            fail_on_converter_warnings=False,
        )
        self.parser = XmlParser(config=self.parser_config)

    def _enviar_soap(
        self, xml_assinado_str: str, request_name: str, versao_schema: str = "2"
    ) -> str:
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <{request_name} xmlns="http://www.prefeitura.sp.gov.br/nfe">
      <VersaoSchema>{versao_schema}</VersaoSchema>
      <MensagemXML><![CDATA[{xml_assinado_str}]]></MensagemXML>
    </{request_name}>
  </soap12:Body>
</soap12:Envelope>"""

        # Write certs to temporary file with restrictive permissions (0600)
        fd, temp_cert_path = tempfile.mkstemp(suffix=".pem")
        
        response_text = ""
        error_msg = ""
        try:
            os.chmod(temp_cert_path, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(self.cert_pem + b"\n" + self.key_pem)

            headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
            response = logged_post(
                self.url,
                data=soap_body.encode("utf-8"),
                headers=headers,
                cert=temp_cert_path,
                timeout=35,
            )
            response_text = response.text

            # Inspect for SOAP Fault or RetornoXML before generic raise_for_status
            if response.status_code != 200:
                try:
                    root = etree.fromstring(response.content, parser=SAFE_PARSER)
                    ns = {"n": "http://www.prefeitura.sp.gov.br/nfe"}
                    retorno = root.xpath(
                        f".//n:{request_name.replace('Request', 'Response')}/n:RetornoXML",
                        namespaces=ns,
                    )
                    if retorno and retorno[0].text:
                        return retorno[0].text
                except Exception:
                    pass

                fault_msg = extract_soap_fault(response.content)
                if fault_msg:
                    error_msg = f"SOAP Fault: {fault_msg}"
                    raise NFSeProviderError(
                        error_msg,
                        raw_response=response.text,
                        status_code=response.status_code,
                        raw_request=xml_assinado_str,
                    )

                snippet = response.text.strip()[:300]
                error_msg = f"HTTP {response.status_code}: {snippet or 'Erro na comunicação com a prefeitura'}"
                raise NFSeProviderError(
                    error_msg,
                    raw_response=response.text,
                    status_code=response.status_code,
                    raw_request=xml_assinado_str,
                )

            try:
                root = etree.fromstring(response.content, parser=SAFE_PARSER)
            except Exception:
                error_msg = f"Resposta SOAP inválida (XML malformado): {response.text[:300]}"
                raise NFSeProviderError(
                    error_msg,
                    raw_response=response.text,
                    status_code=200,
                    raw_request=xml_assinado_str,
                )

            ns = {"n": "http://www.prefeitura.sp.gov.br/nfe"}
            retorno_node = root.xpath(
                f".//n:{request_name.replace('Request', 'Response')}/n:RetornoXML",
                namespaces=ns,
            )

            if not retorno_node or not retorno_node[0].text:
                fault_msg = extract_soap_fault(response.content)
                if fault_msg:
                    error_msg = f"SOAP Fault: {fault_msg}"
                    raise NFSeProviderError(
                        error_msg,
                        raw_response=response.text,
                        status_code=200,
                        raw_request=xml_assinado_str,
                    )
                error_msg = f"Nó RetornoXML não encontrado na resposta SOAP: {response.text[:300]}"
                raise NFSeProviderError(
                    error_msg,
                    raw_response=response.text,
                    status_code=200,
                    raw_request=xml_assinado_str,
                )

            return retorno_node[0].text
        except Exception as e:
            if not error_msg:
                error_msg = str(e)
            raise e
        finally:
            pass

            if os.path.exists(temp_cert_path):
                try:
                    os.remove(temp_cert_path)
                except OSError:
                    pass

    def consultar_nfe_emitidas(
        self, dt_inicio: datetime.date, dt_fim: datetime.date, pagina: int = 1
    ):
        pedido = PedidoConsultaNfePeriodo(
            cabecalho=PedidoConsultaNfePeriodo.Cabecalho(
                versao="2",
                cpfcnpjremetente=TpCpfcnpj(cnpj=self.cnpj),
                cpfcnpj=TpCpfcnpj(cnpj=self.cnpj),
                inscricao=self.inscricao_municipal,
                dt_inicio=dt_inicio.strftime("%Y-%m-%d"),
                dt_fim=dt_fim.strftime("%Y-%m-%d"),
                numero_pagina=str(pagina),
            ),
            signature=None,
        )

        xml_str = self.serializer.render(pedido)
        root = etree.fromstring(xml_str.encode("utf-8"), parser=SAFE_PARSER)
        signed_xml = assinar_xml(root, self.key_pem, self.cert_pem)
        signed_xml_str = etree.tostring(signed_xml, encoding="utf-8").decode("utf-8")

        retorno_xml_str = self._enviar_soap(
            signed_xml_str, "ConsultaNFeEmitidasRequest", versao_schema="2"
        )
        retorno: RetornoConsulta = self.parser.from_string(
            retorno_xml_str, RetornoConsulta
        )

        if not retorno.cabecalho.sucesso:
            erros = (
                " | ".join(e.descricao for e in retorno.erro)
                if retorno.erro
                else "Erro desconhecido na consulta."
            )
            raise NFSeProviderError(
                f"Erro na consulta de NFS-e: {erros}", raw_response=retorno_xml_str
            )

        return retorno.nfe

    def consultar_lote(self, numero_lote: str):
        from core.nfse.paulistana.schemas.pedido_consulta_lote_v02 import (
            PedidoConsultaLote,
        )
        from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpCpfcnpj

        pedido = PedidoConsultaLote(
            cabecalho=PedidoConsultaLote.Cabecalho(
                versao="2",
                cpfcnpjremetente=TpCpfcnpj(cnpj=self.cnpj),
                numero_lote=numero_lote,
            ),
            signature=None,
        )

        xml_str = self.serializer.render(pedido)
        root = etree.fromstring(xml_str.encode("utf-8"), parser=SAFE_PARSER)
        signed_xml = assinar_xml(root, self.key_pem, self.cert_pem)
        signed_xml_str = etree.tostring(signed_xml, encoding="utf-8").decode("utf-8")

        retorno_xml_str = self._enviar_soap(
            signed_xml_str, "ConsultaLoteRequest", versao_schema="2"
        )
        retorno: RetornoConsulta = self.parser.from_string(
            retorno_xml_str, RetornoConsulta
        )

        if not retorno.cabecalho.sucesso:
            erros = (
                " | ".join(e.descricao for e in retorno.erro)
                if retorno.erro
                else "Erro desconhecido na consulta do lote."
            )
            raise NFSeProviderError(
                f"Erro na consulta de lote: {erros}", raw_response=retorno_xml_str
            )

        return retorno.nfe, retorno_xml_str

    def cancelar_nfe(
        self, nf_number: str, verification_code: str
    ) -> Tuple[bool, str, str, List[str]]:
        from core.nfse.paulistana.schemas.pedido_cancelamento_nfe_v02 import (
            PedidoCancelamentoNfe,
        )
        from core.nfse.paulistana.schemas.retorno_cancelamento_nfe_v02 import (
            RetornoCancelamentoNfe,
        )
        from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpChaveNfe
        from .rps_signer import assinar_cancelamento

        # 1. Sign the interior AssinaturaCancelamento
        assinatura_cancelamento = assinar_cancelamento(
            self.inscricao_municipal, nf_number, self.key_pem
        )

        pedido = PedidoCancelamentoNfe(
            cabecalho=PedidoCancelamentoNfe.Cabecalho(
                versao="2",
                cpfcnpjremetente=TpCpfcnpj(cnpj=self.cnpj),
                transacao=True,
            ),
            detalhe=[
                PedidoCancelamentoNfe.Detalhe(
                    chave_nfe=TpChaveNfe(
                        inscricao_prestador=self.inscricao_municipal,
                        numero_nfe=int(nf_number),
                        codigo_verificacao=verification_code,
                    ),
                    assinatura_cancelamento=assinatura_cancelamento,
                )
            ],
            signature=None,
        )

        xml_str = self.serializer.render(pedido)
        root = etree.fromstring(xml_str.encode("utf-8"), parser=SAFE_PARSER)
        signed_xml = assinar_xml(root, self.key_pem, self.cert_pem)
        signed_xml_str = etree.tostring(signed_xml, encoding="utf-8").decode("utf-8")

        try:
            retorno_xml_str = self._enviar_soap(
                signed_xml_str, "CancelamentoNFeRequest", versao_schema="2"
            )
        except NFSeProviderError as pe:
            return False, signed_xml_str, pe.raw_response or "", [pe.message]

        try:
            retorno: RetornoCancelamentoNfe = self.parser.from_string(
                retorno_xml_str, RetornoCancelamentoNfe
            )
        except Exception as ex:
            return (
                False,
                signed_xml_str,
                retorno_xml_str,
                [f"Falha ao processar retorno: {ex}"],
            )

        erros = []
        sucesso = False
        if retorno.cabecalho and retorno.cabecalho.sucesso:
            sucesso = True
        else:
            if retorno.erro:
                for e in retorno.erro:
                    erros.append(f"{e.codigo} - {e.descricao}")
            if not erros:
                erros.extend(extract_paulistana_xml_errors(retorno_xml_str))
                if not erros:
                    erros.append("Falha desconhecida no cancelamento.")

        return sucesso, signed_xml_str, retorno_xml_str, erros

    def _enviar_lote_rps_internal(
        self, lote_rps: List[TpRpsV1], request_name: str
    ) -> Tuple[Optional[RetornoEnvioLoteRpsV1], str, str]:
        if not lote_rps:
            raise ValueError("O lote de RPS não pode estar vazio.")
        if len(lote_rps) > 50:
            raise ValueError(
                "O lote de RPS excede o limite máximo permitido de 50 documentos."
            )

        valor_servicos = sum(
            Decimal(str(r.valor_servicos or "0.00")) for r in lote_rps
        ).quantize(Decimal("0.01"))
        valor_deducoes = sum(
            Decimal(str(r.valor_deducoes or "0.00")) for r in lote_rps
        ).quantize(Decimal("0.01"))

        pedido = PedidoEnvioLoteRpsV1(
            cabecalho=PedidoEnvioLoteRpsV1.Cabecalho(
                cpfcnpjremetente=TpCpfcnpjV1(cnpj=self.cnpj),
                transacao=True,
                dt_inicio=min(r.data_emissao for r in lote_rps),
                dt_fim=max(r.data_emissao for r in lote_rps),
                qtd_rps=len(lote_rps),
                valor_total_servicos=f"{valor_servicos:.2f}",
                valor_total_deducoes=f"{valor_deducoes:.2f}",
            ),
            rps=lote_rps,
            signature=None,
        )

        xml_str = self.serializer.render(pedido)
        root = etree.fromstring(xml_str.encode("utf-8"), parser=SAFE_PARSER)
        signed_xml = assinar_xml(root, self.key_pem, self.cert_pem)
        signed_xml_str = etree.tostring(signed_xml, encoding="utf-8").decode("utf-8")

        retorno_xml_str = self._enviar_soap(
            signed_xml_str, request_name, versao_schema="1"
        )
        retorno = None
        try:
            retorno = self.parser.from_string(retorno_xml_str, RetornoEnvioLoteRpsV1)
        except Exception as parse_ex:
            logger.warning(
                "xsdata parsing failed for RetornoEnvioLoteRps: %s. Raw XML retained.",
                parse_ex,
            )
            retorno = None

        return retorno, signed_xml_str, retorno_xml_str

    def testar_envio_lote_rps(
        self, lote_rps: List[TpRpsV1], numero_lote: int = 1
    ) -> Tuple[Optional[RetornoEnvioLoteRpsV1], str, str]:
        return self._enviar_lote_rps_internal(lote_rps, "TesteEnvioLoteRPSRequest")

    def enviar_lote_rps(
        self, lote_rps: List[TpRpsV1], numero_lote: int = 1
    ) -> Tuple[Optional[RetornoEnvioLoteRpsV1], str, str]:
        return self._enviar_lote_rps_internal(lote_rps, "EnvioLoteRPSRequest")


def download_nfse_pdf(im: str, nf_number: str, verification_code: str):
    """Download NFS-e PDF from São Paulo prefeitura or generate a fake one in debug mode."""
    if verification_code == "DEBUG-FAKE-CODE":
        import weasyprint

        html_string = (
            f"<html><body><h1>FAKE NFS-e PDF</h1>"
            f"<p>NFS-e Number: {nf_number}</p>"
            f"<p>This is a test PDF generated in Debug Mode.</p></body></html>"
        )
        return weasyprint.HTML(string=html_string).write_pdf()

    url = f"https://nfe.prefeitura.sp.gov.br/contribuinte/notaprintpdf.aspx?inscricao={im}&nf={nf_number}&verificacao={verification_code}"
    try:
        response = logged_get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Error downloading NFS-e PDF: {e}")
        return None
