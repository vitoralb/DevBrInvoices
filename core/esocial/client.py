import logging
import re
from lxml import etree

from core.nfse.cert import _temp_cert_file
from core.utils.http import logged_post
from .signer import assinar_xml_esocial
from .parser import (
    parse_retorno_consulta_identificadores,
    parse_retorno_solicitacao_download,
)

logger = logging.getLogger(__name__)


class EsocialClient:
    """Cliente SOAP para comunicação mTLS com os Web Services do eSocial (eSocial BX / Download Cirúrgico)."""

    URL_PROD_CONSULTA_ID = (
        "https://webservices.download.esocial.gov.br/servicos/empregador/dwlcirurgico/WsConsultarIdentificadoresEventos.svc"
    )
    URL_PROD_DOWNLOAD = (
        "https://webservices.download.esocial.gov.br/servicos/empregador/dwlcirurgico/WsSolicitarDownloadEventos.svc"
    )
    URL_PROD_CONSULTA_LOTE = (
        "https://webservices.consulta.esocial.gov.br/servicos/empregador/consultarloteeventos/WsConsultarLoteEventos.svc"
    )

    ACTION_CONSULTA_EMPREGADOR = (
        "http://www.esocial.gov.br/servicos/empregador/consulta/identificadores-eventos/v1_0_0/"
        "ServicoConsultarIdentificadoresEventos/ConsultarIdentificadoresEventosEmpregador"
    )
    ACTION_DOWNLOAD_ID = (
        "http://www.esocial.gov.br/servicos/empregador/download/solicitacao/v1_0_0/"
        "ServicoSolicitarDownloadEventos/SolicitarDownloadEventosPorId"
    )
    ACTION_DOWNLOAD_RECIBO = (
        "http://www.esocial.gov.br/servicos/empregador/download/solicitacao/v1_0_0/"
        "ServicoSolicitarDownloadEventos/SolicitarDownloadEventosPorNrRecibo"
    )

    def __init__(self, cert_pem: str, key_pem: str, debug_mode: bool = False):
        self.cert_pem = cert_pem.encode("utf-8") if isinstance(cert_pem, str) else cert_pem
        self.key_pem = key_pem.encode("utf-8") if isinstance(key_pem, str) else key_pem
        self.debug_mode = debug_mode

    @staticmethod
    def _extract_cnpj_base(cnpj: str) -> str:
        """Extrai os 8 primeiros caracteres do CNPJ (CNPJ raiz), conforme exigido pelos
        schemas de identificação do empregador no eSocial."""
        chars = re.sub(r"[^0-9a-zA-Z]", "", cnpj or "").upper()
        return chars[:8]

    def _post_soap(self, url: str, action: str, envelope_xml: str) -> str:
        """Envia uma requisição SOAP 1.1 com mTLS e registra a chamada em ApiLog."""
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": action,
        }
        with _temp_cert_file(self.cert_pem, self.key_pem) as cert_path:
            response = logged_post(
                url,
                data=envelope_xml.encode("utf-8"),
                headers=headers,
                cert=cert_path,
                timeout=60,
            )

        if response.status_code >= 400:
            logger.error(
                "eSocial SOAP request failed: HTTP %s - %s",
                response.status_code,
                response.text[:1000],
            )
            response.raise_for_status()

        return response.text

    def consultar_identificadores_eventos_empregador(
        self, cnpj: str, tp_evt: str, per_apur: str
    ) -> dict:
        """Consulta os identificadores dos eventos do empregador para uma determinada competência.
        Retorna dicionário com cd_resposta, desc_resposta e a lista de identificadores."""
        cnpj_base = self._extract_cnpj_base(cnpj)

        payload_xml = (
            f'<eSocial xmlns="http://www.esocial.gov.br/schema/consulta/identificadores-eventos/empregador/v1_0_0">'
            f"<consultaIdentificadoresEvts>"
            f"<ideEmpregador>"
            f"<tpInsc>1</tpInsc>"
            f"<nrInsc>{cnpj_base}</nrInsc>"
            f"</ideEmpregador>"
            f"<consultaEvtsEmpregador>"
            f"<tpEvt>{tp_evt}</tpEvt>"
            f"<perApur>{per_apur}</perApur>"
            f"</consultaEvtsEmpregador>"
            f"</consultaIdentificadoresEvts>"
            f"</eSocial>"
        )

        signed_xml = assinar_xml_esocial(payload_xml, self.key_pem, self.cert_pem)

        soap_envelope = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:v1="http://www.esocial.gov.br/servicos/empregador/consulta/identificadores-eventos/v1_0_0">\n'
            "  <soapenv:Header/>\n"
            "  <soapenv:Body>\n"
            "    <v1:ConsultarIdentificadoresEventosEmpregador>\n"
            "      <v1:consultaEventosEmpregador>\n"
            f"        {signed_xml}\n"
            "      </v1:consultaEventosEmpregador>\n"
            "    </v1:ConsultarIdentificadoresEventosEmpregador>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

        resp_xml = self._post_soap(
            self.URL_PROD_CONSULTA_ID,
            self.ACTION_CONSULTA_EMPREGADOR,
            soap_envelope,
        )

        # Extrai o resultado da tag de resposta SOAP
        root = etree.fromstring(resp_xml.encode("utf-8"))
        result_el = root.find(".//{*}ConsultarIdentificadoresEventosEmpregadorResult")
        if result_el is not None and len(result_el) > 0:
            inner_xml = etree.tostring(result_el[0], encoding="utf-8").decode("utf-8")
        elif result_el is not None:
            inner_xml = etree.tostring(result_el, encoding="utf-8").decode("utf-8")
        else:
            inner_xml = resp_xml

        return parse_retorno_consulta_identificadores(inner_xml)

    def solicitar_download_eventos_por_id(self, cnpj: str, event_ids: list[str]) -> dict:
        """Solicita o download de até 50 eventos pelo seu atributo Id.
        Retorna dicionário com cd_resposta, desc_resposta e a lista de arquivos retornados."""
        if not event_ids:
            return {"cd_resposta": 201, "desc_resposta": "Nenhum ID solicitado.", "arquivos": []}

        # O webservice aceita no máximo 50 IDs por requisição
        event_ids_slice = event_ids[:50]
        cnpj_base = self._extract_cnpj_base(cnpj)

        ids_xml = "".join(f"<id>{eid}</id>" for eid in event_ids_slice)
        payload_xml = (
            f'<eSocial xmlns="http://www.esocial.gov.br/schema/download/solicitacao/id/v1_0_0">'
            f"<download>"
            f"<ideEmpregador>"
            f"<tpInsc>1</tpInsc>"
            f"<nrInsc>{cnpj_base}</nrInsc>"
            f"</ideEmpregador>"
            f"<solicDownloadEvtsPorId>"
            f"{ids_xml}"
            f"</solicDownloadEvtsPorId>"
            f"</download>"
            f"</eSocial>"
        )

        signed_xml = assinar_xml_esocial(payload_xml, self.key_pem, self.cert_pem)

        soap_envelope = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:v1="http://www.esocial.gov.br/servicos/empregador/download/solicitacao/v1_0_0">\n'
            "  <soapenv:Header/>\n"
            "  <soapenv:Body>\n"
            "    <v1:SolicitarDownloadEventosPorId>\n"
            "      <v1:solicitacao>\n"
            f"        {signed_xml}\n"
            "      </v1:solicitacao>\n"
            "    </v1:SolicitarDownloadEventosPorId>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

        resp_xml = self._post_soap(
            self.URL_PROD_DOWNLOAD,
            self.ACTION_DOWNLOAD_ID,
            soap_envelope,
        )

        root = etree.fromstring(resp_xml.encode("utf-8"))
        result_el = root.find(".//{*}SolicitarDownloadEventosPorIdResult")
        if result_el is not None and len(result_el) > 0:
            inner_xml = etree.tostring(result_el[0], encoding="utf-8").decode("utf-8")
        elif result_el is not None:
            inner_xml = etree.tostring(result_el, encoding="utf-8").decode("utf-8")
        else:
            inner_xml = resp_xml

        return parse_retorno_solicitacao_download(inner_xml)

    def solicitar_download_eventos_por_nr_recibo(
        self, cnpj: str, nr_recibos: list[str]
    ) -> dict:
        """Solicita o download de até 50 eventos pelo seu número de recibo."""
        if not nr_recibos:
            return {"cd_resposta": 201, "desc_resposta": "Nenhum recibo solicitado.", "arquivos": []}

        recibos_slice = nr_recibos[:50]
        cnpj_base = self._extract_cnpj_base(cnpj)

        recs_xml = "".join(f"<nrRec>{rec}</nrRec>" for rec in recibos_slice)
        payload_xml = (
            f'<eSocial xmlns="http://www.esocial.gov.br/schema/download/solicitacao/nrRecibo/v1_0_0">'
            f"<download>"
            f"<ideEmpregador>"
            f"<tpInsc>1</tpInsc>"
            f"<nrInsc>{cnpj_base}</nrInsc>"
            f"</ideEmpregador>"
            f"<solicDownloadEventosPorNrRecibo>"
            f"{recs_xml}"
            f"</solicDownloadEventosPorNrRecibo>"
            f"</download>"
            f"</eSocial>"
        )

        signed_xml = assinar_xml_esocial(payload_xml, self.key_pem, self.cert_pem)

        soap_envelope = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:v1="http://www.esocial.gov.br/servicos/empregador/download/solicitacao/v1_0_0">\n'
            "  <soapenv:Header/>\n"
            "  <soapenv:Body>\n"
            "    <v1:SolicitarDownloadEventosPorNrRecibo>\n"
            "      <v1:solicitacao>\n"
            f"        {signed_xml}\n"
            "      </v1:solicitacao>\n"
            "    </v1:SolicitarDownloadEventosPorNrRecibo>\n"
            "  </soapenv:Body>\n"
            "</soapenv:Envelope>"
        )

        resp_xml = self._post_soap(
            self.URL_PROD_DOWNLOAD,
            self.ACTION_DOWNLOAD_RECIBO,
            soap_envelope,
        )

        root = etree.fromstring(resp_xml.encode("utf-8"))
        result_el = root.find(".//{*}SolicitarDownloadEventosPorNrReciboResult")
        if result_el is not None and len(result_el) > 0:
            inner_xml = etree.tostring(result_el[0], encoding="utf-8").decode("utf-8")
        elif result_el is not None:
            inner_xml = etree.tostring(result_el, encoding="utf-8").decode("utf-8")
        else:
            inner_xml = resp_xml

        return parse_retorno_solicitacao_download(inner_xml)

