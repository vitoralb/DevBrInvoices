import logging
import re
from decimal import Decimal
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

from .schemas.evt_cs.evt_cs import ESocial as EvtCS
from .schemas.evt_irrf.evt_irrf import ESocial as EvtIrrf
from .schemas.retorno_consulta.retorno_consulta_identificadores_eventos_v1_0_0 import (
    ESocial as RetornoConsultaIdentificadores,
)
from .schemas.retorno_download.retorno_solicitacao_download_eventos_v1_0_0 import (
    ESocial as RetornoDownloadEventos,
)

logger = logging.getLogger(__name__)


def build_totalizer_id(tipo_code: str, nr_recibo: str) -> str:
    """Constrói o ID de 36 caracteres do evento totalizador a partir do recibo do evento gerador
    (S-1299 para S-5011 e S-5012), conforme MOD v1.16 Seção 8.3.1 (p. 102):
    - Campo Fixo: 'ID' (2 posições)
    - Tipo do Evento: '011' (S-5011) ou '012' (S-5012) (3 posições)
    - Sequencial: 31 dígitos derivados do nrRecibo gerador (preenchido com zeros à esquerda)
    """
    if "." in (nr_recibo or ""):
        seq_digits = nr_recibo.split(".")[-1]
    else:
        clean_digits = re.sub(r"\D", "", nr_recibo or "")
        if clean_digits.startswith("11") and len(clean_digits) > 11:
            seq_digits = clean_digits[2:]
        else:
            seq_digits = clean_digits
    seq = seq_digits.zfill(31)
    tipo_3 = tipo_code.zfill(3)
    return f"ID{tipo_3}{seq}"


def normalize_event_id(event_id: str) -> str:
    r"""Normaliza identificador de evento para 36 posições conforme TS_Id (ID\d{34}).
    Algumas respostas da consulta de identificadores retornam totalizadores como ID11... ou ID12... (35 posições).
    """
    if not event_id:
        return ""
    if len(event_id) == 35:
        if event_id.startswith("ID11"):
            return "ID011" + event_id[4:]
        if event_id.startswith("ID12"):
            return "ID012" + event_id[4:]
        if event_id.startswith("ID13"):
            return "ID013" + event_id[4:]
    return event_id


def extract_event_version_key(
    xml_content: str = "",
    parsed_dict: dict | None = None,
    evt_id: str = "",
    recibo: str = "",
) -> int:
    """Extrai uma chave inteira estritamente crescente a partir do número de recibo
    (nrRecArqBase / nrRecibo) ou do identificador do evento (Id) para garantir que,
    havendo múltiplas retificações/fechamentos para uma mesma competência,
    apenas o evento mais recente e definitivo seja preservado.
    """
    rec_candidate = recibo
    if not rec_candidate and parsed_dict:
        rec_candidate = parsed_dict.get("nr_rec_arq_base") or parsed_dict.get("nr_rec") or parsed_dict.get("nr_recibo") or ""

    if not rec_candidate and xml_content:
        m = re.search(r"<(?:[a-zA-Z0-9_-]+:)?nrRecArqBase>([^<]+)</(?:[a-zA-Z0-9_-]+:)?nrRecArqBase>", xml_content)
        if not m:
            m = re.search(r"<(?:[a-zA-Z0-9_-]+:)?nrRecibo>([^<]+)</(?:[a-zA-Z0-9_-]+:)?nrRecibo>", xml_content)
        if m:
            rec_candidate = m.group(1).strip()

    if rec_candidate:
        if "." in rec_candidate:
            seq = rec_candidate.split(".")[-1]
        else:
            seq = rec_candidate
        digits = "".join(ch for ch in seq if ch.isdigit())
        if digits:
            try:
                return int(digits)
            except ValueError:
                pass

    id_candidate = evt_id
    if not id_candidate and parsed_dict:
        id_candidate = parsed_dict.get("id") or parsed_dict.get("evt_id") or ""
    if not id_candidate and xml_content:
        m = re.search(r'Id="([A-Za-z0-9_-]+)"', xml_content)
        if m:
            id_candidate = m.group(1).strip()

    if id_candidate:
        if id_candidate.startswith(("ID011", "ID012", "ID013")):
            seq = id_candidate[5:]
        elif id_candidate.startswith(("ID110", "ID120", "ID130")):
            seq = id_candidate[5:]
        elif id_candidate.startswith(("ID11", "ID12", "ID13")) and len(id_candidate) == 35:
            seq = id_candidate[4:]
        else:
            seq = id_candidate
        digits = "".join(ch for ch in seq if ch.isdigit())
        if digits:
            try:
                return int(digits)
            except ValueError:
                pass

    return 0


def _normalize_namespace(xml_str: str, target_event: str) -> str:
    """Normaliza namespaces de versões anteriores do eSocial (ex: v_S_01_01_00 ou v_S_01_02_00)
    para o layout S-1.3 (v_S_01_03_00) suportado pelas dataclasses geradas."""
    pattern = rf"http://www\.esocial\.gov\.br/schema/evt/{target_event}/v_S_01_\d{{2}}_\d{{2}}"
    replacement = f"http://www.esocial.gov.br/schema/evt/{target_event}/v_S_01_03_00"
    return re.sub(pattern, replacement, xml_str)


def parse_s5011_xml(xml_content: str) -> dict:
    """Processa o XML do evento S-5011 (evtCS) e retorna a base de cálculo total da folha
    (soma de vrBcCp00 em todas as lotações e categorias) e o INSS descontado (vrDescCP / vrCpSeg)."""
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8", errors="replace")

    normalized_xml = _normalize_namespace(xml_content, "evtCS")
    config = ParserConfig(fail_on_unknown_properties=False)
    parser = XmlParser(config=config)
    obj = parser.from_string(normalized_xml, EvtCS)

    evt = obj.evt_cs
    if not evt or not evt.info_cs:
        raise ValueError("Estrutura do evento S-5011 (evtCS/infoCS) não encontrada no XML.")

    per_apur = str(evt.ide_evento.per_apur) if evt.ide_evento and evt.ide_evento.per_apur else ""
    raw_ind = evt.info_cs.ind_exist_info
    ind_exist_info = int(getattr(raw_ind, "value", raw_ind)) if raw_ind is not None else 1
    nr_rec_arq_base = str(evt.info_cs.nr_rec_arq_base or "")

    # Se indExistInfo == 3: não há movimento no período
    if ind_exist_info == 3:
        return {
            "per_apur": per_apur,
            "total_payroll": Decimal("0.00"),
            "inss_tax": Decimal("0.00"),
            "ind_exist_info": ind_exist_info,
            "nr_rec_arq_base": nr_rec_arq_base,
        }

    total_payroll = Decimal("0.00")
    if evt.info_cs.ide_estab:
        for estab in evt.info_cs.ide_estab:
            if not estab.ide_lotacao:
                continue
            for lotacao in estab.ide_lotacao:
                if not lotacao.bases_remun:
                    continue
                for remun in lotacao.bases_remun:
                    if remun.bases_cp and remun.bases_cp.vr_bc_cp00 is not None:
                        total_payroll += Decimal(str(remun.bases_cp.vr_bc_cp00))

    inss_tax = None
    if evt.info_cs.info_cpseg:
        if evt.info_cs.info_cpseg.vr_desc_cp is not None:
            inss_tax = Decimal(str(evt.info_cs.info_cpseg.vr_desc_cp))
        elif evt.info_cs.info_cpseg.vr_cp_seg is not None:
            inss_tax = Decimal(str(evt.info_cs.info_cpseg.vr_cp_seg))

    return {
        "per_apur": per_apur,
        "total_payroll": total_payroll,
        "inss_tax": inss_tax,
        "ind_exist_info": ind_exist_info,
        "nr_rec_arq_base": nr_rec_arq_base,
    }


def parse_s5012_xml(xml_content: str) -> dict:
    """Processa o XML do evento S-5012 (evtIrrf) e retorna o total consolidado de IRRF
    apurado na competência (soma de vrCRMen)."""
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8", errors="replace")

    normalized_xml = _normalize_namespace(xml_content, "evtIrrf")
    config = ParserConfig(fail_on_unknown_properties=False)
    parser = XmlParser(config=config)
    obj = parser.from_string(normalized_xml, EvtIrrf)

    evt = obj.evt_irrf
    if not evt or not evt.info_irrf:
        raise ValueError("Estrutura do evento S-5012 (evtIrrf/infoIRRF) não encontrada no XML.")

    per_apur = str(evt.ide_evento.per_apur) if evt.ide_evento and evt.ide_evento.per_apur else ""
    raw_ind = evt.info_irrf.ind_exist_info
    ind_exist_info = int(getattr(raw_ind, "value", raw_ind)) if raw_ind is not None else 1
    nr_rec_arq_base = str(evt.info_irrf.nr_rec_arq_base or "")

    if ind_exist_info == 3 or not evt.info_irrf.info_crmen:
        return {
            "per_apur": per_apur,
            "total_irrf": Decimal("0.00"),
            "ind_exist_info": ind_exist_info,
            "nr_rec_arq_base": nr_rec_arq_base,
        }

    total_irrf = Decimal("0.00")
    for cr in evt.info_irrf.info_crmen:
        if cr.vr_crmen is not None:
            total_irrf += Decimal(str(cr.vr_crmen))

    return {
        "per_apur": per_apur,
        "total_irrf": total_irrf,
        "ind_exist_info": ind_exist_info,
        "nr_rec_arq_base": nr_rec_arq_base,
    }


def parse_retorno_consulta_identificadores(xml_content: str) -> dict:
    """Processa a resposta do webservice WsConsultarIdentificadoresEventos
    (RetornoConsultaIdentificadoresEventos)."""
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8", errors="replace")

    config = ParserConfig(fail_on_unknown_properties=False)
    parser = XmlParser(config=config)
    obj = parser.from_string(xml_content, RetornoConsultaIdentificadores)

    consulta_evts = obj.retorno_consulta_identificadores_evts
    if not consulta_evts or not consulta_evts.status:
        raise ValueError("Estrutura status não encontrada no RetornoConsultaIdentificadores.")

    cd_resposta = int(consulta_evts.status.cd_resposta)
    desc_resposta = str(consulta_evts.status.desc_resposta or "")

    identificadores = []
    if (
        consulta_evts.retorno_identificadores_evts
        and consulta_evts.retorno_identificadores_evts.identificadores_evts
        and consulta_evts.retorno_identificadores_evts.identificadores_evts.identificador_evt
    ):
        for item in consulta_evts.retorno_identificadores_evts.identificadores_evts.identificador_evt:
            identificadores.append(
                {
                    "id": str(item.id or ""),
                    "nr_rec": str(item.nr_rec or ""),
                }
            )

    return {
        "cd_resposta": cd_resposta,
        "desc_resposta": desc_resposta,
        "identificadores": identificadores,
    }


def parse_retorno_solicitacao_download(xml_content: str) -> dict:
    """Processa a resposta do webservice WsSolicitarDownloadEventos
    (RetornoSolicitacaoDownloadEventos) e extrai os XMLs brutos de cada evento (<evt>)."""
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8", errors="replace")

    root = etree.fromstring(xml_content.encode("utf-8"))

    # Localiza status geral do download
    ns = {"es": "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0"}
    status_el = root.find(".//es:download/es:status", namespaces=ns)
    if status_el is None:
        status_el = root.find(".//{*}download/{*}status")

    cd_resposta = 0
    desc_resposta = ""
    if status_el is not None:
        cd_el = status_el.find("{*}cdResposta")
        desc_el = status_el.find("{*}descResposta")
        if cd_el is not None and cd_el.text:
            cd_resposta = int(cd_el.text)
        if desc_el is not None and desc_el.text:
            desc_resposta = desc_el.text

    arquivos = []
    for arq_el in root.iterfind(".//{*}arquivo"):
        arq_status_el = arq_el.find("{*}status")
        arq_cd = 0
        arq_desc = ""
        if arq_status_el is not None:
            cd_el = arq_status_el.find("{*}cdResposta")
            desc_el = arq_status_el.find("{*}descResposta")
            if cd_el is not None and cd_el.text:
                arq_cd = int(cd_el.text)
            if desc_el is not None and desc_el.text:
                arq_desc = desc_el.text

        evt_el = arq_el.find("{*}evt")
        evt_xml = ""
        evt_id = ""
        if evt_el is not None:
            evt_id = evt_el.get("Id", "")
            # O conteúdo de <evt> pode conter o XML completo do evento (<eSocial>) ou o nó raiz do evento
            inner_children = list(evt_el)
            if inner_children:
                evt_xml = etree.tostring(inner_children[0], encoding="utf-8").decode("utf-8")
            else:
                evt_xml = etree.tostring(evt_el, encoding="utf-8").decode("utf-8")

        rec_el = arq_el.find("{*}rec")
        rec_xml = ""
        rec_nr = ""
        if rec_el is not None:
            rec_nr = rec_el.get("nrRec", "")
            inner_children = list(rec_el)
            if inner_children:
                rec_xml = etree.tostring(inner_children[0], encoding="utf-8").decode("utf-8")
            else:
                rec_xml = etree.tostring(rec_el, encoding="utf-8").decode("utf-8")

        arquivos.append(
            {
                "cd_resposta": arq_cd,
                "desc_resposta": arq_desc,
                "evt_id": evt_id,
                "evt_xml": evt_xml,
                "rec_nr": rec_nr,
                "rec_xml": rec_xml,
            }
        )

    return {
        "cd_resposta": cd_resposta,
        "desc_resposta": desc_resposta,
        "arquivos": arquivos,
    }
