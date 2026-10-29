import base64
import datetime
import gzip
import logging
import os
import re
import ssl  # noqa: F401 - reserved for future in-memory SSL adapter
import tempfile
from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from core.utils.http import logged_get as _logged_get, logged_post as _logged_post
from django.conf import settings
from django.db import transaction
from lxml import etree
from signxml import XMLSigner, methods, namespaces
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from core.models import CompanySettings, Invoice, NotaFiscal
from core.nfse.base import (
    CancelResult,
    EmitResult,
    NFSeProvider,
    NFSeProviderError,
    extract_nota_fiscal,
)
from core.nfse.cert import _temp_cert_file

from .schemas.v1_01.dps_v1_01 import Dps
from .schemas.v1_01.tipos_complexos_v1_01 import (
    TccomExterior,
    Tccserv,
    TcenderExt,
    Tcendereco,
    TcinfDps,
    TcinfoPessoa,
    TcinfoPrestador,
    TcinfoTributacao,
    TcinfoValores,
    TclocPrest,
    TcregTrib,
    Tcserv,
    TctribMunicipal,
    TctribTotal,
    TcvservPrest,
    TcrtcinfoIbscbs,
    TcrtcinfoValoresIbscbs,
    TcrtcinfoTributosIbscbs,
    TcrtcinfoTributosSitClas,
)
from .schemas.v1_01.tipos_simples_v1_01 import (
    TstipoIndTotTrib,
    TscodNaoNif,
    TsrtcfinNfse,
    TsrtcindFinal,
    TsrtcindDest,
)

logger = logging.getLogger(__name__)

BACEN_CURRENCY_MAP = {
    "CAD": "165",
    "USD": "220",
    "EUR": "978",
    "GBP": "470",
    "BRL": "790",
}


def _decompress_gzip_b64(b64_str: str) -> Optional[str]:
    """Decompresses base64-encoded gzip content to string.
    Handles standard base64 gzip, double base64-encoded gzip, and plain base64 XML.
    """
    if not b64_str:
        return None
    try:
        raw_bytes = base64.b64decode(b64_str)
        # Check if output is double base64-encoded (e.g. begins with ASCII 'H4sI' or other base64 header)
        if raw_bytes.startswith(b"H4sI") or (not raw_bytes.startswith(b"\x1f\x8b") and b"<" not in raw_bytes[:10]):
            try:
                second_decode = base64.b64decode(raw_bytes)
                if second_decode.startswith(b"\x1f\x8b") or b"<" in second_decode[:10]:
                    raw_bytes = second_decode
            except Exception:
                pass

        if raw_bytes.startswith(b"\x1f\x8b"):
            return gzip.decompress(raw_bytes).decode("utf-8")
        elif b"<" in raw_bytes[:50]:
            return raw_bytes.decode("utf-8")
        else:
            return gzip.decompress(raw_bytes).decode("utf-8")
    except Exception as ex:
        logger.warning("Error decompressing base64 gzip XML: %s", ex)
        return None


def _parse_decompressed_nfse_xml(decompressed_xml: str) -> dict:
    """Extracts common fields from Sefin Nacional NFS-e XML."""
    data = {
        "numero_nf": "",
        "data_hora_autorizacao": None,
        "issue_date": None,
        "codigo_tributacao_nacional": "",
        "codigo_nbs": "",
        "codigo_servico_municipio": "",
        "aliquota_iss": None,
        "valor_iss": None,
        "amount_brl": "0.00",
        "description": "",
        "emit_cnpj": "",
        "dps_number": "",
        "dps_series": "",
        "cst_ibs_cbs": "",
        "c_class_trib_ibs_cbs": "",
        "c_ind_op_ibs_cbs": "",
    }
    if not decompressed_xml:
        return data

    match = re.search(r"<nNFSe>(\d+)</nNFSe>", decompressed_xml)
    if match:
        data["numero_nf"] = match.group(1)

    match_dh = re.search(r"<dhProc>([^<]+)</dhProc>", decompressed_xml)
    if not match_dh:
        match_dh = re.search(r"<dhEmi>([^<]+)</dhEmi>", decompressed_xml)
    if match_dh:
        try:
            data["data_hora_autorizacao"] = datetime.datetime.fromisoformat(
                match_dh.group(1).replace("Z", "+00:00")
            )
        except Exception:
            pass

    match_compet = re.search(r"<dCompet>([^<]+)</dCompet>", decompressed_xml)
    if match_compet:
        try:
            data["issue_date"] = datetime.date.fromisoformat(match_compet.group(1))
        except Exception:
            pass
    if not data["issue_date"] and data["data_hora_autorizacao"]:
        data["issue_date"] = data["data_hora_autorizacao"].date()

    c_trib_nac = re.search(r"<cTribNac>([^<]+)</cTribNac>", decompressed_xml)
    if c_trib_nac:
        data["codigo_tributacao_nacional"] = c_trib_nac.group(1)

    c_nbs = re.search(r"<cNBS>([^<]+)</cNBS>", decompressed_xml)
    if c_nbs:
        data["codigo_nbs"] = c_nbs.group(1)

    c_trib_mun = re.search(r"<cTribMun>([^<]+)</cTribMun>", decompressed_xml)
    if c_trib_mun:
        data["codigo_servico_municipio"] = c_trib_mun.group(1)

    p_aliq = re.search(r"<pAliq>([^<]+)</pAliq>", decompressed_xml)
    if not p_aliq:
        p_aliq = re.search(r"<pAliqAplic>([^<]+)</pAliqAplic>", decompressed_xml)
    if p_aliq:
        try:
            data["aliquota_iss"] = Decimal(p_aliq.group(1))
        except Exception:
            pass

    v_iss = re.search(r"<vISSQN>([^<]+)</vISSQN>", decompressed_xml)
    if v_iss:
        try:
            data["valor_iss"] = Decimal(v_iss.group(1))
        except Exception:
            pass

    v_liq = re.search(r"<vLiq>([^<]+)</vLiq>", decompressed_xml)
    if not v_liq:
        v_liq = re.search(r"<vServ>([^<]+)</vServ>", decompressed_xml)
    if v_liq:
        data["amount_brl"] = v_liq.group(1)

    desc_match = re.search(r"<xDescServ>([^<]+)</xDescServ>", decompressed_xml)
    if desc_match:
        data["description"] = desc_match.group(1)

    cnpj_match = re.search(r"<emit>.*?<CNPJ>([^<]+)</CNPJ>", decompressed_xml, re.DOTALL)
    if not cnpj_match:
        cnpj_match = re.search(r"<prest>.*?<CNPJ>([^<]+)</CNPJ>", decompressed_xml, re.DOTALL)
    if cnpj_match:
        data["emit_cnpj"] = cnpj_match.group(1)

    dps_num_match = re.search(r"<nDPS>([^<]+)</nDPS>", decompressed_xml)
    if dps_num_match:
        data["dps_number"] = dps_num_match.group(1)

    dps_ser_match = re.search(r"<serie>([^<]+)</serie>", decompressed_xml)
    if dps_ser_match:
        data["dps_series"] = dps_ser_match.group(1)

    ibscbs_match = re.search(r"<IBSCBS>(.*?)</IBSCBS>", decompressed_xml, re.DOTALL)
    if ibscbs_match:
        ibscbs_xml = ibscbs_match.group(1)
        c_ind_op = re.search(r"<cIndOp>([^<]+)</cIndOp>", ibscbs_xml)
        if c_ind_op:
            data["c_ind_op_ibs_cbs"] = c_ind_op.group(1).strip()

        cst_ibs = re.search(r"<CST>([^<]+)</CST>", ibscbs_xml)
        if cst_ibs:
            data["cst_ibs_cbs"] = cst_ibs.group(1).strip()

        c_class_trib = re.search(r"<cClassTrib>([^<]+)</cClassTrib>", ibscbs_xml)
        if c_class_trib:
            data["c_class_trib_ibs_cbs"] = c_class_trib.group(1).strip()

    return data


def _parse_decompressed_evento_xml(
    decompressed_xml: str, nsu: Optional[int] = None, tipo_evento_adn: Optional[str] = None
) -> dict:
    """Extracts common fields from Sefin Nacional / ADN Event XML."""
    data = {
        "nsu": nsu,
        "id_evento": "",
        "tipo_evento": tipo_evento_adn or "",
        "codigo_evento": "",
        "n_seq_evento": 1,
        "dh_evento": None,
        "descricao": "",
        "codigo_motivo": "",
        "motivo": "",
        "is_cancellation": False,
        "raw_xml": decompressed_xml,
    }
    if not decompressed_xml or not decompressed_xml.strip():
        return {}

    match_id = re.search(r'Id="([^"]+)"', decompressed_xml)
    if match_id:
        data["id_evento"] = match_id.group(1)

    match_code = re.search(r"<e(\d{6})[ >]", decompressed_xml)
    if match_code:
        data["codigo_evento"] = match_code.group(1)
    elif tipo_evento_adn and "CANCELAMENTO" in tipo_evento_adn:
        data["codigo_evento"] = "101101"

    match_seq = re.search(r"<nSeqEvento>(\d+)</nSeqEvento>", decompressed_xml)
    if match_seq:
        try:
            data["n_seq_evento"] = int(match_seq.group(1))
        except Exception:
            pass

    match_dh = re.search(r"<dhProc>([^<]+)</dhProc>", decompressed_xml)
    if not match_dh:
        match_dh = re.search(r"<dhEvento>([^<]+)</dhEvento>", decompressed_xml)
    if match_dh:
        try:
            data["dh_evento"] = datetime.datetime.fromisoformat(
                match_dh.group(1).replace("Z", "+00:00")
            )
        except Exception:
            pass

    match_desc = re.search(r"<xDesc>([^<]+)</xDesc>", decompressed_xml)
    if match_desc:
        data["descricao"] = match_desc.group(1).strip()

    match_cmotivo = re.search(r"<cMotivo>([^<]+)</cMotivo>", decompressed_xml)
    if match_cmotivo:
        data["codigo_motivo"] = match_cmotivo.group(1).strip()

    match_xmotivo = re.search(r"<xMotivo>([^<]+)</xMotivo>", decompressed_xml)
    if not match_xmotivo:
        match_xmotivo = re.search(r"<xProcAdm>([^<]+)</xProcAdm>", decompressed_xml)
    if match_xmotivo:
        data["motivo"] = match_xmotivo.group(1).strip()

    canc_codes = {"101101", "101103", "105102", "105104", "305101"}
    canc_types = {
        "CANCELAMENTO",
        "CANCELAMENTO_POR_SUBSTITUICAO",
        "CANCELAMENTO_DEFERIDO_ANALISE_FISCAL",
        "CANCELAMENTO_POR_OFICIO",
    }
    if (
        data["codigo_evento"] in canc_codes
        or (tipo_evento_adn and tipo_evento_adn.upper() in canc_types)
        or re.search(r"Cancelamento\s+de\s+NFS-e", decompressed_xml, re.IGNORECASE)
    ):
        data["is_cancellation"] = True

    return data


class NacionalProvider(NFSeProvider):
    def _get_urls(self, debug_mode: bool) -> Tuple[str, str]:
        if debug_mode:
            base_url = getattr(
                settings,
                "NFSE_NACIONAL_DEBUG_URL",
                "https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional",
            )
            danfse_url = getattr(
                settings,
                "NFSE_NACIONAL_DANFSE_DEBUG_URL",
                "https://adn.producaorestrita.nfse.gov.br/danfse",
            )
        else:
            base_url = getattr(
                settings,
                "NFSE_NACIONAL_PROD_URL",
                "https://sefin.nfse.gov.br/SefinNacional",
            )
            danfse_url = getattr(
                settings,
                "NFSE_NACIONAL_DANFSE_PROD_URL",
                "https://adn.nfse.gov.br/danfse",
            )
        return base_url.rstrip("/"), danfse_url.rstrip("/")

    def _get_adn_contribuintes_url(self, debug_mode: bool) -> str:
        if debug_mode:
            return getattr(
                settings,
                "NFSE_NACIONAL_ADN_DEBUG_URL",
                "https://adn.producaorestrita.nfse.gov.br/contribuintes",
            ).rstrip("/")
        return getattr(
            settings,
            "NFSE_NACIONAL_ADN_PROD_URL",
            "https://adn.nfse.gov.br/contribuintes",
        ).rstrip("/")

    def _get_cnc_url(self, debug_mode: bool) -> str:
        if debug_mode:
            return getattr(
                settings,
                "NFSE_NACIONAL_CNC_DEBUG_URL",
                "https://adn.producaorestrita.nfse.gov.br/cnc",
            ).rstrip("/")
        return getattr(
            settings,
            "NFSE_NACIONAL_CNC_PROD_URL",
            "https://adn.nfse.gov.br/cnc",
        ).rstrip("/")

    def _consultar_cnc(
        self, company: CompanySettings, temp_cert_path: str
    ) -> Dict[str, Any]:
        """Consulta o Cadastro Nacional de Contribuintes (CNC) no ADN para verificar
        se o CNPJ possui cadastro no município emissor e se está habilitado para emissão de NFS-e,
        além de obter a Inscrição Municipal a ser informada na DPS.

        Regras:
        - Se o CNC retornar documentos localizados para o CNPJ:
          - Checa se SituacaoEmissaoNFSe == "HABILITADO" (case-insensitive).
          - Se NÃO estiver HABILITADO: falha a emissão (habilitado=False).
          - Se estiver HABILITADO: habilitado=True, IM obtida do CNC (ou da empresa).
        - Se o CNC retornar 404 / NENHUM_DOCUMENTO_LOCALIZADO:
          - Município não possui registros complementares no CNC para este CNPJ (ou não conveniado no CNC).
          - habilitado=True, im=None (para evitar a rejeição E0120).
        """
        cnc_base_url = self._get_cnc_url(company.debug_mode)
        endpoint = f"{cnc_base_url}/consulta/cad"
        cnpj_prestador = company.cnpj_clean
        cod_mun = company.address_city_ibge

        params = {
            "codMunicipio": cod_mun,
            "inscricaoFederal": cnpj_prestador,
        }
        headers = {"Accept": "application/json"}

        try:
            logger.info(
                "Consultando CNC no ADN (%s) para CNPJ %s e município %s",
                endpoint,
                cnpj_prestador,
                cod_mun,
            )
            resp = _logged_get(
                endpoint,
                params=params,
                headers=headers,
                cert=temp_cert_path,
                timeout=20,
            )
        except Exception as e:
            logger.warning(
                "Falha na requisição ao CNC no ADN para CNPJ %s (município %s): %s",
                cnpj_prestador,
                cod_mun,
                e,
            )
            # Em caso de falha de conexão/timeout com o CNC, adota fallback seguro
            fallback_im = (
                None
                if company.debug_mode
                else (
                    str(company.inscricao_municipal).strip()[:15]
                    if company.inscricao_municipal
                    else None
                )
            )
            return {
                "habilitado": True,
                "im": fallback_im,
                "motivo_inabilitado": None,
                "raw_response": None,
            }

        # Status 404 indica que nenhum registro complementar foi localizado no CNC
        if resp.status_code == 404:
            logger.info(
                "Nenhum registro complementar localizado no CNC para CNPJ %s no município %s. Campo IM será omitido da DPS (evita erro E0120).",
                cnpj_prestador,
                cod_mun,
            )
            return {
                "habilitado": True,
                "im": None,
                "motivo_inabilitado": None,
                "raw_response": getattr(resp, "json", lambda: None)(),
            }

        if resp.status_code == 200:
            try:
                data = resp.json()
            except Exception:
                data = {}

            cadastro_list = data.get("ListaCadastroMunicipal") or []
            if not cadastro_list:
                logger.info(
                    "CNC retornou ListaCadastroMunicipal vazia para CNPJ %s. Campo IM será omitido.",
                    cnpj_prestador,
                )
                return {
                    "habilitado": True,
                    "im": None,
                    "motivo_inabilitado": None,
                    "raw_response": data,
                }

            # Localiza o registro correspondente ao município e CNPJ
            matching_cad = None
            for cad in cadastro_list:
                inf_cad = cad.get("InfCad") or {}
                insc = re.sub(r"\D", "", str(inf_cad.get("Inscricao") or ""))
                cad_mun = str(cad.get("CodigoMunicipio") or "").strip()
                if (not insc or insc == cnpj_prestador) and (
                    not cad_mun or cad_mun == str(cod_mun)
                ):
                    matching_cad = cad
                    break
            if not matching_cad:
                matching_cad = cadastro_list[0]

            inf_cad = matching_cad.get("InfCad") or {}
            situacao_emissao = str(inf_cad.get("SituacaoEmissaoNFSe") or "").strip()

            # Se retornado o cadastro para o CNPJ e SituacaoEmissaoNFSe não estiver Habilitado, falhar a emissão
            if situacao_emissao.upper() != "HABILITADO":
                motivo = (
                    f"Emissão de NFS-e rejeitada: o CNPJ {company.cnpj} não está habilitado para emissão "
                    f"no CNC do município {cod_mun} (Situação no CNC: '{situacao_emissao or 'NÃO INFORMADA'}')."
                )
                logger.error(motivo)
                return {
                    "habilitado": False,
                    "im": None,
                    "motivo_inabilitado": motivo,
                    "raw_response": data,
                }

            # Contribuinte habilitado: incluir IM na DPS (conforme informações complementares do CNC)
            im_cad = str(inf_cad.get("InscricaoMunicipal") or "").strip()
            if not im_cad and company.inscricao_municipal:
                im_cad = str(company.inscricao_municipal).strip()

            im_val = im_cad[:15] if im_cad else None
            logger.info(
                "Contribuinte habilitado no CNC para CNPJ %s no município %s. IM a ser informada na DPS: %s",
                cnpj_prestador,
                cod_mun,
                im_val,
            )
            return {
                "habilitado": True,
                "im": im_val,
                "motivo_inabilitado": None,
                "raw_response": data,
            }

        # Demais status HTTP (ex: 400 ou 500)
        logger.warning(
            "Resposta inesperada do CNC (HTTP %s): %s",
            resp.status_code,
            getattr(resp, "text", "")[:300],
        )
        fallback_im = (
            None
            if company.debug_mode
            else (
                str(company.inscricao_municipal).strip()[:15]
                if company.inscricao_municipal
                else None
            )
        )
        return {
            "habilitado": True,
            "im": fallback_im,
            "motivo_inabilitado": None,
            "raw_response": None,
        }

    def _get_cert_pems(self) -> Tuple[bytes, bytes]:

        company = CompanySettings.load()
        if not company or not company.pfx_cert_pem or not company.pfx_key_pem:
            raise Exception(
                "Certificado digital não configurado. Por favor, faça o upload na página Sua Empresa."
            )
        return company.pfx_key_pem.encode("utf-8"), company.pfx_cert_pem.encode("utf-8")

    def _build_and_sign_dps(
        self,
        invoice: Invoice,
        company: CompanySettings,
        numero_dps: int,
        serie_dps: str,
        im_prestador: Optional[str] = None,
    ) -> Tuple[Dps, str, str]:
        """Builds Dps dataclass and returns (dps_obj, signed_xml, id_dps)."""
        from core.services import _prepare_nf_data

        amount_brl, description, effective_rate_pct = _prepare_nf_data(invoice)
        service_desc = description.replace("\r", "").strip()[:2000]

        cnpj_prestador = company.cnpj_clean
        cod_mun = company.address_city_ibge

        numero_dps_str = str(numero_dps)
        numero_dps_formatado = numero_dps_str.zfill(15)
        serie_formatada = str(serie_dps).zfill(5)

        # Regra do ID da DPS (45 posições): "DPS" + cMun(7) + tpInsc(1) + CNPJ(14) + serie(5) + nDPS(15)
        id_dps = f"DPS{cod_mun}2{cnpj_prestador}{serie_formatada}{numero_dps_formatado}"
        tp_amb = "2" if company.debug_mode else "1"

        client_obj = invoice.client
        country_code = ((client_obj.address_country_code or "US").strip()).upper()
        postal_code = ((client_obj.address_postal_code or "").strip())[:11] or "N/A"
        city_name = ((client_obj.address_city or "").strip())[:60] or "N/A"
        state_province = ((client_obj.address_state_province or "").strip())[:60] or "N/A"
        bairro = (client_obj.address_neighborhood or "Centro")[:60]
        logradouro = (client_obj.address_line1 or "")[:255]
        numero = (client_obj.address_number or "1")[:60]
        complemento = client_obj.address_line2 or None
        if complemento:
            complemento = complemento[:156]

        total_foreign = invoice.total_foreign
        currency = invoice.currency.upper()
        tp_moeda = BACEN_CURRENCY_MAP.get(currency, "165")

        issue_tz = datetime.timezone(datetime.timedelta(hours=-3))
        now_dt = datetime.datetime.now(issue_tz)
        dh_emi = now_dt.strftime("%Y-%m-%dT%H:%M:%S-03:00")
        d_compet = invoice.issue_date.strftime("%Y-%m-%d")

        c_trib_nac = str(
            getattr(invoice, "codigo_tributacao_nacional", "") or ""
        ).strip()[:6]
        if not c_trib_nac:
            raise ValueError(
                "Código de Tributação Nacional é obrigatório para emissão da DPS Nacional."
            )

        c_nbs = getattr(invoice, "codigo_nbs", None)
        if c_nbs:
            c_nbs = str(c_nbs).strip()[:9]
        if not c_nbs:
            raise ValueError(
                "Código NBS é obrigatório para emissão da DPS Nacional."
            )

        c_trib_mun = str(
            getattr(invoice, "codigo_servico_municipio", "") or ""
        ).strip()
        if c_trib_mun:
            if len(c_trib_mun) > 3 or not c_trib_mun.isdigit():
                raise ValueError(
                    f"Código de Serviço do Município ('{c_trib_mun}') possui mais de 3 dígitos. "
                    "Para emissão via DPS Nacional, o cTribMun deve ter no máximo 3 dígitos."
                )
            c_trib_mun_val = c_trib_mun.zfill(3)
        else:
            c_trib_mun_val = None

        from core.services import get_approx_tax_rate_pct

        approx_rate_pct = get_approx_tax_rate_pct(invoice)
        if approx_rate_pct > Decimal("0.00"):
            tot_trib = TctribTotal(p_tot_trib_sn=f"{approx_rate_pct:.2f}")
        else:
            tot_trib = TctribTotal(ind_tot_trib=TstipoIndTotTrib.VALUE_0)

        # TODO: Support domestic client invoicing (endNac, cLocPrestacao, trib_issqn=1)
        # Foreign Client (Export of Services)
        toma_email = (
            client_obj.email.strip()[:80]
            if client_obj.email and client_obj.email.strip()
            else None
        )
        client_nif = (
            client_obj.nif.strip()[:40]
            if getattr(client_obj, "nif", None) and client_obj.nif.strip()
            else None
        )
        toma = TcinfoPessoa(
            nif=client_nif,
            c_nao_nif=None if client_nif else TscodNaoNif.VALUE_2,  # 2 = Não exigência do NIF
            x_nome=client_obj.name[:150],
            email=toma_email,
            end=Tcendereco(
                end_ext=TcenderExt(
                    c_pais=country_code,
                    c_end_post=postal_code,
                    x_cidade=city_name,
                    x_est_prov_reg=state_province,
                ),
                x_lgr=logradouro,
                nro=numero,
                x_cpl=complemento,
                x_bairro=bairro,
            ),
        )

        prest_email = (
            company.email.strip()[:80]
            if company.email and company.email.strip()
            else None
        )
        prest_phone = None
        if company.phone_number:
            phone_digits = re.sub(r"\D", "", company.phone_number)
            if phone_digits.startswith("55") and len(phone_digits) in (12, 13):
                phone_digits = phone_digits[2:]
            if 6 <= len(phone_digits) <= 20:
                prest_phone = phone_digits

        ibscbs = None
        if getattr(company, "enable_cbs_ibs", False):
            cst = (str(getattr(invoice, "cst_ibs_cbs", "") or "").strip() or "410")[:3]
            c_class_trib = (str(getattr(invoice, "c_class_trib_ibs_cbs", "") or "").strip() or "410004")[:6]
            c_ind_op = (str(getattr(invoice, "c_ind_op_ibs_cbs", "") or "").strip() or "100301")[:6]

            ibscbs = TcrtcinfoIbscbs(
                fin_nfse=TsrtcfinNfse.VALUE_0,  # 0 = Regular
                ind_final=TsrtcindFinal.VALUE_0,  # 0 = Não
                c_ind_op=c_ind_op,
                ind_dest=TsrtcindDest.VALUE_0,  # 0 = Próprio tomador
                valores=TcrtcinfoValoresIbscbs(
                    trib=TcrtcinfoTributosIbscbs(
                        g_ibscbs=TcrtcinfoTributosSitClas(
                            cst=cst,
                            c_class_trib=c_class_trib,
                        )
                    )
                ),
            )

        dps = Dps(
            versao="1.01",
            inf_dps=TcinfDps(
                id=id_dps,
                tp_amb=tp_amb,
                dh_emi=dh_emi,
                ver_aplic="1.0.0",
                serie=str(serie_dps),
                n_dps=numero_dps_str,
                d_compet=d_compet,
                tp_emit="1",  # 1 = Prestador emitindo
                c_loc_emi=cod_mun,
                prest=TcinfoPrestador(
                    cnpj=cnpj_prestador,
                    email=prest_email,
                    fone=prest_phone,
                    im=im_prestador,  # IM is populated when complementary records exist in CNC; omitted when absent to prevent E0120
                    x_nome=None,  # E0121: O nome ou razão social do prestador não deve ser informado quando tpEmit=1 (o próprio prestador)
                    reg_trib=TcregTrib(
                        op_simp_nac="3",  # 3 = Optante - ME/EPP (Simples Nacional)
                        reg_ap_trib_sn="1",  # 1 = Apuração SN
                        reg_esp_trib="0",  # 0 = Nenhum
                    ),
                ),
                toma=toma,
                serv=Tcserv(
                    loc_prest=TclocPrest(c_loc_prestacao=cod_mun),
                    c_serv=Tccserv(
                        c_trib_nac=c_trib_nac,
                        c_trib_mun=c_trib_mun_val,
                        c_nbs=c_nbs,
                        x_desc_serv=service_desc,
                    ),
                    com_ext=TccomExterior(
                        md_prestacao="1",  # 1 = Transfronteiriço
                        vinc_prest="0",  # 0 = Sem Vínculo societário
                        tp_moeda=tp_moeda,
                        v_serv_moeda=f"{total_foreign:.2f}",
                        mec_afcomex_p="01",  # 01 = Nenhum
                        mec_afcomex_t="01",  # 01 = Nenhum
                        mov_temp_bens="1",  # 1 = Não vinculado a movimentação física
                        mdic="0",  # 0 = Não compartilhar com MDIC
                    ),
                ),
                valores=TcinfoValores(
                    v_serv_prest=TcvservPrest(v_serv=f"{amount_brl:.2f}"),
                    trib=TcinfoTributacao(
                        trib_mun=TctribMunicipal(
                            trib_issqn="3",  # 3 = Exportação de serviço
                            c_pais_result=country_code,
                            tp_ret_issqn="1",  # 1 = Não Retido
                        ),
                        tot_trib=tot_trib,
                    ),
                ),
                ibscbs=ibscbs,
            ),
        )

        # Serialize XML
        serializer = XmlSerializer(config=SerializerConfig(pretty_print=False))
        unsigned_xml = serializer.render(
            dps, ns_map={None: "http://www.sped.fazenda.gov.br/nfse"}
        )

        # Sign XML
        key_pem, cert_pem = self._get_cert_pems()
        _safe_parser = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(unsigned_xml.encode("utf-8"), parser=_safe_parser)
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        )
        signer.namespaces = {None: namespaces.ds}
        signed_root = signer.sign(
            root,
            key=key_pem,
            cert=cert_pem,
            reference_uri=f"#{id_dps}",
        )
        signed_bytes = etree.tostring(signed_root, encoding="utf-8")
        signed_xml = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n{signed_bytes.decode("utf-8")}'
        )

        return dps, signed_xml, id_dps

    def _parse_error_response(self, resp) -> List[str]:
        """Parses error responses supporting both NFSePostResponseErro, ResponseErro, and ASP.NET structures."""
        erros: List[str] = []
        if resp is None:
            return ["Resposta vazia do servidor."]
        try:
            data = resp.json()
            if isinstance(data, dict):
                # Format 1: NFSePostResponseErro: {"erros": [{"codigo": "...", "descricao": "...", "complemento": "..."}]}
                raw_erros = data.get("erros") or data.get("Erros")
                if raw_erros and isinstance(raw_erros, list):
                    for err in raw_erros:
                        if isinstance(err, dict):
                            cod = err.get("codigo") or err.get("Codigo") or ""
                            desc = err.get("descricao") or err.get("Descricao") or ""
                            comp = err.get("complemento") or err.get("Complemento") or ""
                            msg = f"{cod} - {desc}".strip(" -")
                            if comp:
                                msg = f"{msg} ({comp})" if msg else str(comp)
                            if msg.strip():
                                erros.append(msg.strip())
                        elif err:
                            erros.append(str(err).strip())
                # Format 2: ResponseErro: {"erro": {"codigo": "...", "descricao": "..."}}
                elif "erro" in data or "Erro" in data:
                    err = data.get("erro") or data.get("Erro")
                    if isinstance(err, dict):
                        cod = err.get("codigo") or err.get("Codigo") or ""
                        desc = err.get("descricao") or err.get("Descricao") or ""
                        comp = err.get("complemento") or err.get("Complemento") or ""
                        msg = f"{cod} - {desc}".strip(" -")
                        if comp:
                            msg = f"{msg} ({comp})" if msg else str(comp)
                        if msg.strip():
                            erros.append(msg.strip())
                    elif err:
                        erros.append(str(err).strip())
                # Format 3: ASP.NET Core ProblemDetails: {"title": "...", "errors": {"fieldName": ["err1", "err2"]}}
                if "errors" in data or "Errors" in data:
                    err_dict = data.get("errors") or data.get("Errors")
                    if isinstance(err_dict, dict):
                        for field_name, msgs in err_dict.items():
                            if isinstance(msgs, list):
                                for m in msgs:
                                    if m:
                                        erros.append(f"{field_name}: {m}")
                            elif msgs:
                                erros.append(f"{field_name}: {msgs}")
                    elif isinstance(err_dict, list):
                        for m in err_dict:
                            if m:
                                erros.append(str(m))
                # Format 4: Standard API message fields
                for key in (
                    "message",
                    "Message",
                    "detail",
                    "Detail",
                    "title",
                    "Title",
                    "error_description",
                    "error",
                ):
                    val = data.get(key)
                    if val and isinstance(val, str) and val.strip() and val not in erros:
                        erros.append(val.strip())
            elif isinstance(data, list):
                for item in data:
                    if item:
                        erros.append(str(item).strip())
        except Exception:
            text = resp.text.strip() if hasattr(resp, "text") and resp.text else ""
            if text:
                clean_text = re.sub(r"<[^>]+>", " ", text)[:300].strip()
                erros.append(f"HTTP {resp.status_code}: {clean_text}")

        erros = [e.strip() for e in erros if e and e.strip()]

        if not erros:
            status = getattr(resp, "status_code", "Unknown")
            erros.append(
                f"Falha na comunicação com Sefin Nacional (HTTP {status})"
            )
        return erros

    def _consultar_dps(
        self, id_dps: str, base_url: str, temp_cert_path: str
    ) -> Optional[EmitResult]:
        """Queries Sefin Nacional to check if the DPS was already issued (idempotency)."""
        endpoint = f"{base_url}/dps/{id_dps}"
        headers = {"Accept": "application/json"}
        logger.info("Checking if DPS %s is already issued: %s", id_dps, endpoint)
        resp = _logged_get(endpoint, headers=headers, cert=temp_cert_path, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            chave_acesso = data.get("chaveAcesso")
            if chave_acesso:
                logger.info(
                    "DPS %s was already issued with chave %s. Retrieving NFS-e...",
                    id_dps,
                    chave_acesso,
                )
                nfse_resp = _logged_get(
                    f"{base_url}/nfse/{chave_acesso}",
                    headers=headers,
                    cert=temp_cert_path,
                    timeout=20,
                )
                decompressed_xml = ""
                numero_nf = ""
                if nfse_resp.status_code == 200:
                    nfse_data = nfse_resp.json()
                    nfse_b64 = nfse_data.get("nfseXmlGZipB64")
                    decompressed_xml = _decompress_gzip_b64(nfse_b64) or ""
                    parsed = _parse_decompressed_nfse_xml(decompressed_xml)
                    numero_nf = parsed["numero_nf"]
                if not numero_nf:
                    numero_nf = chave_acesso[-15:].lstrip("0")

                return EmitResult(
                    sucesso=True,
                    chave_acesso_nacional=chave_acesso,
                    codigo_verificacao="",
                    numero_nf=numero_nf,
                    xml_retorno=decompressed_xml or nfse_resp.text,
                    data_hora_autorizacao=parsed["data_hora_autorizacao"],
                    codigo_tributacao_nacional=parsed["codigo_tributacao_nacional"],
                    codigo_nbs=parsed["codigo_nbs"],
                    codigo_servico_municipio=parsed["codigo_servico_municipio"],
                    aliquota_iss=parsed["aliquota_iss"],
                    valor_iss=parsed["valor_iss"],
                    cst_ibs_cbs=parsed.get("cst_ibs_cbs", ""),
                    c_class_trib_ibs_cbs=parsed.get("c_class_trib_ibs_cbs", ""),
                    c_ind_op_ibs_cbs=parsed.get("c_ind_op_ibs_cbs", ""),
                )
        elif resp.status_code == 404:
            # 404 means the DPS was NOT issued yet (expected on first emission)
            return None
        else:
            err_msgs = self._parse_error_response(resp)
            raise NFSeProviderError(
                f"Erro na consulta de DPS em Sefin Nacional (HTTP {resp.status_code}): {' | '.join(err_msgs)}",
                raw_response=resp.text,
                status_code=resp.status_code,
            )

    def consultar_nfse(
        self, invoice_or_nf: Union[Invoice, NotaFiscal]
    ) -> Optional[EmitResult]:
        """Checks if the DPS for this invoice or nota fiscal was already issued in Sefin Nacional."""
        from core.nfse.base import extract_nota_fiscal

        if isinstance(invoice_or_nf, Invoice):
            if not invoice_or_nf.document_number:
                return None
            doc_number = invoice_or_nf.document_number
            doc_series = invoice_or_nf.document_series
        else:
            nf = extract_nota_fiscal(invoice_or_nf)
            if not nf or not nf.nf_number:
                return None
            doc_number = (
                int(nf.nf_number) if str(nf.nf_number).isdigit() else nf.nf_number
            )
            doc_series = getattr(nf, "document_series", "1")

        company = CompanySettings.load()
        if not company:
            return None

        cnpj_prestador = company.cnpj_clean
        cod_mun = company.address_city_ibge
        serie_formatada = str(
            doc_series or company.document_series or "1"
        ).zfill(5)
        numero_dps_formatado = str(doc_number).zfill(15)
        id_dps = f"DPS{cod_mun}2{cnpj_prestador}{serie_formatada}{numero_dps_formatado}"

        base_url, _ = self._get_urls(company.debug_mode)
        key_pem, cert_pem = self._get_cert_pems()
        with _temp_cert_file(cert_pem, key_pem) as temp_cert_path:
            return self._consultar_dps(id_dps, base_url, temp_cert_path)

    def emitir_nfse(self, invoice: Invoice) -> EmitResult:
        company = CompanySettings.load()
        if not company:
            raise ValueError("CompanySettings not found.")

        # Ensure document number is assigned
        if not invoice.document_number:
            from core.services.nfse_services import assign_next_document_number

            assign_next_document_number(invoice)

        serie_dps = str(invoice.document_series or "1")
        numero_dps = invoice.document_number

        # Validate fiscal code constraints early
        c_trib_mun = str(
            getattr(invoice, "codigo_servico_municipio", "") or ""
        ).strip()
        if c_trib_mun and (len(c_trib_mun) > 3 or not c_trib_mun.isdigit()):
            return EmitResult(
                sucesso=False,
                erros=[
                    f"Código de Serviço do Município ('{c_trib_mun}') possui mais de 3 dígitos. "
                    "Para emissão via DPS Nacional, o cTribMun deve ter no máximo 3 dígitos."
                ],
            )

        base_url, _ = self._get_urls(company.debug_mode)
        endpoint = f"{base_url}/nfse"

        key_pem, cert_pem = self._get_cert_pems()
        with _temp_cert_file(cert_pem, key_pem) as temp_cert_path:
            # 1. Consultar CNC para checar habilitação do CNPJ e necessidade de inclusão da IM
            cnc_info = self._consultar_cnc(company, temp_cert_path)
            if not cnc_info.get("habilitado", True):
                motivo = (
                    cnc_info.get("motivo_inabilitado")
                    or "CNPJ não habilitado para emissão de NFS-e no CNC."
                )
                logger.error(
                    "Emissão abortada para invoice %s: %s",
                    invoice.invoice_number,
                    motivo,
                )
                return EmitResult(
                    sucesso=False,
                    erros=[motivo],
                )

            im_prestador = cnc_info.get("im")

            try:
                _, signed_xml, id_dps = self._build_and_sign_dps(
                    invoice, company, numero_dps, serie_dps, im_prestador=im_prestador
                )
            except Exception as e:
                logger.error(
                    "Erro ao preparar/assinar DPS Nacional para invoice %s: %s",
                    invoice.invoice_number,
                    e,
                )
                return EmitResult(
                    sucesso=False,
                    erros=[str(e)],
                )

            try:

                # Idempotency pre-check: Was this DPS already issued?
                try:
                    already_issued = self._consultar_dps(
                        id_dps, base_url, temp_cert_path
                    )
                    if already_issued:
                        already_issued.xml_enviado = signed_xml
                        return already_issued
                except Exception as check_ex:
                    logger.error(
                        "DPS idempotency pre-check failed for %s: %s. Aborting emission to prevent duplicates.",
                        id_dps,
                        check_ex,
                    )
                    raw_resp = getattr(check_ex, "raw_response", "") or ""
                    return EmitResult(
                        sucesso=False,
                        xml_enviado=signed_xml,
                        xml_retorno=raw_resp,
                        erros=[
                            f"Falha na consulta prévia da DPS (idempotência): {check_ex}. Emissão abortada para evitar duplicidade."
                        ],
                    )

                # Compress to GZip base64
                compressed_dps = gzip.compress(signed_xml.encode("utf-8"))
                dps_b64 = base64.b64encode(compressed_dps).decode("utf-8")

                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                body = {"dpsXmlGZipB64": dps_b64}

                logger.info("Sending DPS %s to Sefin Nacional: %s", id_dps, endpoint)
                resp = _logged_post(
                    endpoint,
                    json=body,
                    headers=headers,
                    cert=temp_cert_path,
                    timeout=40,
                )

                result = EmitResult(
                    sucesso=False,
                    xml_enviado=signed_xml,
                    xml_retorno=resp.text,
                )

                if resp.status_code == 201:
                    data = resp.json()
                    result.sucesso = True
                    result.chave_acesso_nacional = data.get("chaveAcesso", "")
                    result.codigo_verificacao = ""

                    nfse_b64 = data.get("nfseXmlGZipB64")
                    decompressed_xml = _decompress_gzip_b64(nfse_b64)
                    if decompressed_xml:
                        result.xml_retorno = decompressed_xml
                        parsed = _parse_decompressed_nfse_xml(decompressed_xml)
                        result.numero_nf = parsed["numero_nf"]
                        result.data_hora_autorizacao = parsed["data_hora_autorizacao"]
                        result.codigo_tributacao_nacional = parsed["codigo_tributacao_nacional"]
                        result.codigo_nbs = parsed["codigo_nbs"]
                        result.codigo_servico_municipio = parsed["codigo_servico_municipio"]
                        result.aliquota_iss = parsed["aliquota_iss"]
                        result.cst_ibs_cbs = parsed.get("cst_ibs_cbs", "")
                        result.c_class_trib_ibs_cbs = parsed.get("c_class_trib_ibs_cbs", "")
                        result.c_ind_op_ibs_cbs = parsed.get("c_ind_op_ibs_cbs", "")

                    if company.enable_cbs_ibs:
                        if not result.cst_ibs_cbs:
                            result.cst_ibs_cbs = (str(getattr(invoice, "cst_ibs_cbs", "") or "").strip() or "410")[:3]
                        if not result.c_class_trib_ibs_cbs:
                            result.c_class_trib_ibs_cbs = (str(getattr(invoice, "c_class_trib_ibs_cbs", "") or "").strip() or "410004")[:6]
                        if not result.c_ind_op_ibs_cbs:
                            result.c_ind_op_ibs_cbs = (str(getattr(invoice, "c_ind_op_ibs_cbs", "") or "").strip() or "100301")[:6]

                    if not result.numero_nf:
                        # Fallback to document number or part of chave de acesso
                        result.numero_nf = result.chave_acesso_nacional[-15:].lstrip(
                            "0"
                        ) or str(numero_dps)

                    return result

                else:
                    result.erros = self._parse_error_response(resp)
                    return result

            except Exception as e:
                logger.exception("Error transmitting DPS to Nacional: %s", e)
                raw_retorno = ""
                err_list = []
                if hasattr(e, "response") and e.response is not None:
                    raw_retorno = e.response.text
                    err_list = self._parse_error_response(e.response)
                elif hasattr(e, "raw_response") and e.raw_response:
                    raw_retorno = e.raw_response

                if not err_list:
                    err_list = [str(e)]

                return EmitResult(
                    sucesso=False,
                    xml_enviado=signed_xml if "signed_xml" in locals() else "",
                    xml_retorno=raw_retorno,
                    erros=err_list,
                )

    def baixar_pdf(
        self, invoice_or_nf: Union[Invoice, NotaFiscal]
    ) -> Optional[bytes]:
        company = CompanySettings.load()
        if not company:
            return None

        nf = extract_nota_fiscal(invoice_or_nf)
        if not nf:
            return None

        xml_content = None
        if nf.xml_autorizacao:
            try:
                if nf.xml_autorizacao.storage.exists(nf.xml_autorizacao.name):
                    with nf.xml_autorizacao.open("rb") as f:
                        xml_content = f.read().decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning("Could not read existing xml_autorizacao: %s", e)

        chave_acesso = getattr(nf, "chave_acesso_nacional", None) or getattr(
            nf, "verification_code", None
        )

        if not xml_content and chave_acesso:
            try:
                data = self.buscar_nfse_por_chave(chave_acesso)
                if data and data.get("raw_xml"):
                    xml_content = data["raw_xml"]
                    from django.core.files.base import ContentFile

                    nf.xml_autorizacao.save(
                        f"NFS-e_{nf.nf_number}.xml",
                        ContentFile(xml_content.encode("utf-8")),
                        save=True,
                    )
            except Exception as e:
                logger.warning(
                    "Failed to retrieve XML from Nacional API for chave %s: %s",
                    chave_acesso,
                    e,
                )

        if not xml_content:
            logger.warning(
                "Cannot generate DANFSe PDF: XML not available for NFS-e %s",
                getattr(nf, "nf_number", None),
            )
            return None

        try:
            from brazilfiscalreport.danfse import Danfse, DanfseConfig

            config = DanfseConfig(
                watermark_cancelled=bool(getattr(nf, "is_canceled", False)),
                display_canhoto=False,
            )
            danfse = Danfse(xml=xml_content, config=config)
            pdf_output = danfse.output()
            return bytes(pdf_output) if pdf_output else None
        except Exception as e:
            logger.exception(
                "Error generating DANFSe PDF via BrazilFiscalReport: %s", e
            )
            return None

    def cancelar_nfse(
        self, invoice_or_nf: Union[Invoice, NotaFiscal]
    ) -> CancelResult:
        company = CompanySettings.load()
        if not company:
            return CancelResult(sucesso=False, erros=["CompanySettings not found."])

        nf = extract_nota_fiscal(invoice_or_nf)
        chave_acesso = getattr(nf, "chave_acesso_nacional", None) or getattr(
            nf, "verification_code", None
        )
        if not chave_acesso:
            return CancelResult(
                sucesso=False,
                erros=[
                    "NFS-e não encontrada para esta invoice ou chave nacional ausente."
                ],
            )

        cnpj_prestador = company.cnpj_clean

        # Build PedRegEvento for cancelation (E101101)
        from core.nfse.nacional.schemas.v1_01.ped_reg_evento_v1_01 import PedRegEvento
        from core.nfse.nacional.schemas.v1_01.tipos_eventos_v1_01 import (
            TcinfPedReg,
            Te101101,
            Te101101XDesc,
        )
        from core.nfse.nacional.schemas.v1_01.tipos_simples_v1_01 import (
            TstipoAmbiente,
            TscodJustCanc,
        )

        tp_amb = (
            TstipoAmbiente.VALUE_2 if company.debug_mode else TstipoAmbiente.VALUE_1
        )
        issue_tz = datetime.timezone(datetime.timedelta(hours=-3))
        dh_evento = datetime.datetime.now(issue_tz).strftime("%Y-%m-%dT%H:%M:%S-03:00")

        # Id: PRE + 50 digitos da chave + 6 digitos do tipo evento
        id_evento = f"PRE{chave_acesso}101101"

        ped_reg = PedRegEvento(
            versao="1.01",
            inf_ped_reg=TcinfPedReg(
                id=id_evento,
                tp_amb=tp_amb,
                ver_aplic="1.0.0",
                dh_evento=dh_evento,
                cnpjautor=cnpj_prestador,
                ch_nfse=chave_acesso,
                e101101=Te101101(
                    x_desc=Te101101XDesc.CANCELAMENTO_DE_NFS_E,
                    c_motivo=TscodJustCanc.VALUE_1,  # 1 - Erro na Emissão
                    x_motivo="Cancelamento solicitado pelo prestador por erro na emissao",
                ),
            ),
        )

        serializer = XmlSerializer(config=SerializerConfig(pretty_print=False))
        unsigned_xml = serializer.render(
            ped_reg, ns_map={None: "http://www.sped.fazenda.gov.br/nfse"}
        )

        # Sign XML
        key_pem, cert_pem = self._get_cert_pems()
        _safe_parser = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(unsigned_xml.encode("utf-8"), parser=_safe_parser)
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        )
        signer.namespaces = {None: namespaces.ds}
        signed_root = signer.sign(
            root,
            key=key_pem,
            cert=cert_pem,
            reference_uri=f"#{id_evento}",
        )
        signed_bytes = etree.tostring(signed_root, encoding="utf-8")
        signed_xml = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n{signed_bytes.decode("utf-8")}'
        )

        base_url, _ = self._get_urls(company.debug_mode)
        endpoint = f"{base_url}/nfse/{chave_acesso}/eventos"

        compressed_ped = gzip.compress(signed_xml.encode("utf-8"))
        ped_b64 = base64.b64encode(compressed_ped).decode("utf-8")

        with _temp_cert_file(cert_pem, key_pem) as temp_cert_path:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                body = {"pedidoRegistroEventoXmlGZipB64": ped_b64}

                logger.info("Sending Cancel Event to Sefin Nacional: %s", endpoint)
                resp = _logged_post(
                    endpoint,
                    json=body,
                    headers=headers,
                    cert=temp_cert_path,
                    timeout=40,
                )

                if resp.status_code == 201:
                    data = resp.json()
                    ev_b64 = data.get("eventoXmlGZipB64")
                    decompressed_ev = _decompress_gzip_b64(ev_b64) or resp.text
                    parsed_ev = _parse_decompressed_evento_xml(
                        decompressed_ev, tipo_evento_adn="CANCELAMENTO"
                    )
                    from django.utils import timezone

                    return CancelResult(
                        sucesso=True,
                        xml_enviado=signed_xml,
                        xml_retorno=decompressed_ev,
                        cancelation_date=parsed_ev.get("dh_evento") or timezone.now(),
                    )
                else:
                    # Idempotency check: was it already canceled?
                    try:
                        events = self.consultar_eventos_nfse(chave_acesso)
                        canc_ev = next(
                            (ev for ev in events if ev.get("is_cancellation")), None
                        )
                        if canc_ev:
                            from django.utils import timezone

                            return CancelResult(
                                sucesso=True,
                                xml_enviado=signed_xml,
                                xml_retorno=canc_ev.get("raw_xml") or resp.text,
                                cancelation_date=canc_ev.get("dh_evento")
                                or timezone.now(),
                            )
                    except Exception:
                        pass

                    return CancelResult(
                        sucesso=False,
                        xml_enviado=signed_xml,
                        xml_retorno=resp.text,
                        erros=self._parse_error_response(resp),
                    )

            except Exception as e:
                logger.exception("Error transmitting Cancel Event to Nacional: %s", e)
                raw_retorno = ""
                err_list = []
                if hasattr(e, "response") and e.response is not None:
                    raw_retorno = e.response.text
                    err_list = self._parse_error_response(e.response)
                elif hasattr(e, "raw_response") and e.raw_response:
                    raw_retorno = e.raw_response

                if not err_list:
                    err_list = [str(e)]

                return CancelResult(
                    sucesso=False,
                    xml_enviado=signed_xml if "signed_xml" in locals() else "",
                    xml_retorno=raw_retorno,
                    erros=err_list,
                )

    def consultar_eventos_nfse(self, chave_acesso: str) -> List[dict]:
        """Queries all events associated with a national access key.
        Checks ADN /NFSe/{chaveAcesso}/Eventos first, then falls back to Sefin
        /nfse/{chaveAcesso}/eventos/101101/1 if ADN has not yet indexed a cancellation.
        """
        company = CompanySettings.load()
        if not company or not chave_acesso:
            return []

        adn_url = self._get_adn_contribuintes_url(company.debug_mode)
        base_url, _ = self._get_urls(company.debug_mode)
        endpoint_adn = f"{adn_url}/NFSe/{chave_acesso}/Eventos"
        headers = {"Accept": "application/json"}

        key_pem, cert_pem = self._get_cert_pems()
        events: List[dict] = []
        with _temp_cert_file(cert_pem, key_pem) as temp_cert_path:
            # 1. Query ADN
            try:
                resp_adn = _logged_get(
                    endpoint_adn, headers=headers, cert=temp_cert_path, timeout=20
                )
                if resp_adn.status_code == 200:
                    data = resp_adn.json()
                    lote = data.get("LoteDFe") or []
                    for item in lote:
                        if item.get("TipoDocumento") == "EVENTO":
                            xml_b64 = item.get("ArquivoXml")
                            decompressed = _decompress_gzip_b64(xml_b64) or ""
                            ev = _parse_decompressed_evento_xml(
                                decompressed,
                                nsu=item.get("NSU"),
                                tipo_evento_adn=item.get("TipoEvento"),
                            )
                            if ev:
                                events.append(ev)
            except Exception as adn_ex:
                logger.warning(
                    "Error querying ADN events for chave %s: %s", chave_acesso, adn_ex
                )

            # 2. Fallback to Sefin if no cancellation event was found
            has_cancellation = any(ev.get("is_cancellation") for ev in events)
            if not has_cancellation:
                try:
                    endpoint_sefin = (
                        f"{base_url}/nfse/{chave_acesso}/eventos/101101/1"
                    )
                    resp_sefin = _logged_get(
                        endpoint_sefin,
                        headers=headers,
                        cert=temp_cert_path,
                        timeout=15,
                    )
                    if resp_sefin.status_code == 200:
                        data_sefin = resp_sefin.json()
                        ev_list = data_sefin.get("eventos") or []
                        if ev_list:
                            for sev in ev_list:
                                ev_xml_b64 = sev.get("arquivoXml")
                                decompressed_sev = (
                                    _decompress_gzip_b64(ev_xml_b64) or ""
                                )
                                ev = _parse_decompressed_evento_xml(
                                    decompressed_sev, tipo_evento_adn="CANCELAMENTO"
                                )
                                if ev:
                                    events.append(ev)
                        elif data_sefin.get("eventoXmlGZipB64"):
                            decompressed_sev = (
                                _decompress_gzip_b64(
                                    data_sefin.get("eventoXmlGZipB64")
                                )
                                or ""
                            )
                            ev = _parse_decompressed_evento_xml(
                                decompressed_sev, tipo_evento_adn="CANCELAMENTO"
                            )
                            if ev:
                                events.append(ev)
                except Exception as sefin_ex:
                    logger.debug(
                        "Fallback check for Sefin event 101101 returned: %s", sefin_ex
                    )

        return events

    def buscar_nfse_por_numero(self, numero: str | int) -> Optional[dict]:
        """Stub: busca de NFS-e por número não implementada no momento para Nacional."""
        return None

    def buscar_nfse_por_chave(self, chave_acesso: str) -> Optional[dict]:
        company = CompanySettings.load()
        if not company:
            return None

        base_url, _ = self._get_urls(company.debug_mode)
        endpoint = f"{base_url}/nfse/{chave_acesso}"
        headers = {"Accept": "application/json"}

        key_pem, cert_pem = self._get_cert_pems()
        with _temp_cert_file(cert_pem, key_pem) as temp_cert_path:

            resp = _logged_get(
                endpoint, headers=headers, cert=temp_cert_path, timeout=20
            )
            if resp.status_code == 200:
                data = resp.json()
                nfse_b64 = data.get("nfseXmlGZipB64")
                decompressed_xml = _decompress_gzip_b64(nfse_b64)
                if decompressed_xml:
                    parsed = _parse_decompressed_nfse_xml(decompressed_xml)
                    numero_nf = parsed["numero_nf"] or chave_acesso[-15:].lstrip("0")

                    events = self.consultar_eventos_nfse(chave_acesso)
                    is_canceled = any(ev.get("is_cancellation") for ev in events)
                    cancelation_date = next(
                        (
                            ev.get("dh_evento")
                            for ev in events
                            if ev.get("is_cancellation")
                        ),
                        None,
                    )

                    return {
                        "nf_number": numero_nf,
                        "verification_code": "",
                        "chave_acesso_nacional": chave_acesso,
                        "amount_brl": parsed["amount_brl"],
                        "description": parsed["description"],
                        "issue_date": parsed["issue_date"] or datetime.date.today(),
                        "data_hora_autorizacao": parsed["data_hora_autorizacao"],
                        "codigo_tributacao_nacional": parsed[
                            "codigo_tributacao_nacional"
                        ],
                        "codigo_servico_municipio": parsed["codigo_servico_municipio"],
                        "codigo_nbs": parsed["codigo_nbs"],
                        "aliquota_iss": parsed["aliquota_iss"],
                        "valor_iss": parsed["valor_iss"],
                        "cst_ibs_cbs": parsed.get("cst_ibs_cbs", ""),
                        "c_class_trib_ibs_cbs": parsed.get("c_class_trib_ibs_cbs", ""),
                        "c_ind_op_ibs_cbs": parsed.get("c_ind_op_ibs_cbs", ""),
                        "provider": "NACIONAL",
                        "is_canceled": is_canceled,
                        "cancelation_date": cancelation_date,
                        "events": events,
                        "raw_xml": decompressed_xml,
                        "dps_series": parsed["dps_series"],
                        "dps_number": parsed["dps_number"],
                        "emit_cnpj": parsed["emit_cnpj"],
                    }

            return None

    def consultar_dfe_por_nsu(
        self, ultimo_nsu: int = 0
    ) -> Tuple[List[dict], int]:
        """Queries the ADN Distribution API for all DF-e records newer than ultimo_nsu.
        Paginates through /DFe/{current_nsu} until no further documents are available.
        Returns (documents_list, highest_nsu_reached).
        """
        company = CompanySettings.load()
        if not company:
            return [], ultimo_nsu

        from django.core.cache import cache
        from django.utils import timezone
        from datetime import timedelta

        cooldown_key = "adn_dfe_cooldown_until"
        cooldown_val = cache.get(cooldown_key)
        if cooldown_val:
            from datetime import datetime

            if isinstance(cooldown_val, datetime) and cooldown_val <= timezone.now():
                cache.delete(cooldown_key)
                cooldown_val = None
            else:
                logger.info("ADN DFe query skipped: cooldown is active.")
                return [], ultimo_nsu

        adn_url = self._get_adn_contribuintes_url(company.debug_mode)
        headers = {"Accept": "application/json"}
        key_pem, cert_pem = self._get_cert_pems()

        current_nsu = int(ultimo_nsu or 0)
        all_items: List[dict] = []

        with _temp_cert_file(cert_pem, key_pem) as temp_cert_path:
            while True:
                endpoint = f"{adn_url}/DFe/{current_nsu}"
                logger.info("Querying ADN DFe distribution at %s", endpoint)
                try:
                    resp = _logged_get(
                        endpoint, headers=headers, cert=temp_cert_path, timeout=30
                    )
                except Exception as ex:
                    logger.error(
                        "Error communicating with ADN DFe at %s: %s", endpoint, ex
                    )
                    break

                if resp.status_code == 200:
                    data = resp.json()
                    lote = data.get("LoteDFe") or []
                    if not lote:
                        cache.set(
                            cooldown_key,
                            timezone.now() + timedelta(hours=1),
                            timeout=3600,
                        )
                        break

                    for item in lote:
                        nsu = item.get("NSU")
                        if nsu is not None and nsu > current_nsu:
                            current_nsu = nsu
                        all_items.append(item)

                    if len(lote) < 50:
                        cache.set(
                            cooldown_key,
                            timezone.now() + timedelta(hours=1),
                            timeout=3600,
                        )
                        break
                elif resp.status_code == 404:
                    logger.debug(
                        "ADN DFe reached end of backlog at NSU %s", current_nsu
                    )
                    cache.set(
                        cooldown_key,
                        timezone.now() + timedelta(hours=1),
                        timeout=3600,
                    )
                    break
                else:
                    logger.warning(
                        "ADN DFe query at NSU %s returned HTTP %s: %s",
                        current_nsu,
                        resp.status_code,
                        resp.text[:300],
                    )
                    break

        return all_items, current_nsu
