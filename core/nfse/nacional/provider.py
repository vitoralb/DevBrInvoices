import base64
import datetime
import gzip
import logging
import os
import re
import tempfile
from decimal import Decimal
from typing import Optional, Tuple, List

import requests

from core.utils.http import logged_get as _logged_get, logged_post as _logged_post


from django.conf import settings
from django.db import transaction
from lxml import etree
from signxml import XMLSigner, methods, namespaces
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from core.models import CompanySettings, Invoice
from core.nfse.base import CancelResult, EmitResult, NFSeProvider, NFSeProviderError
from core.nfse.cert import carregar_certificado_pfx

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
)
from .schemas.v1_01.tipos_simples_v1_01 import TstipoIndTotTrib, TscodNaoNif

logger = logging.getLogger(__name__)

BACEN_CURRENCY_MAP = {
    "CAD": "165",
    "USD": "220",
    "EUR": "978",
    "GBP": "470",
    "BRL": "790",
}


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

    def _get_cert_pems(self) -> Tuple[bytes, bytes]:

        company = CompanySettings.objects.first()
        if not company or not company.pfx_cert_pem or not company.pfx_key_pem:
            raise Exception("Certificado digital não configurado. Por favor, faça o upload na página Sua Empresa.")
        return company.pfx_key_pem.encode('utf-8'), company.pfx_cert_pem.encode('utf-8')

    def _build_and_sign_dps(
        self,
        invoice: Invoice,
        company: CompanySettings,
        numero_dps: int,
        serie_dps: str,
    ) -> Tuple[Dps, str, str]:
        """Builds Dps dataclass and returns (dps_obj, signed_xml, id_dps)."""
        from core.services import _prepare_nf_data

        amount_brl, description, effective_rate_pct = _prepare_nf_data(invoice)
        service_desc = description.replace("\r", "").strip()[:2000]

        cnpj_prestador = re.sub(r"[^0-9a-zA-Z]", "", company.cnpj)
        cod_mun = company.address_city_ibge

        numero_dps_str = str(numero_dps)
        numero_dps_formatado = numero_dps_str.zfill(15)
        serie_formatada = str(serie_dps).zfill(5)

        # Regra do ID da DPS (45 posições): "DPS" + cMun(7) + tpInsc(1) + CNPJ(14) + serie(5) + nDPS(15)
        id_dps = f"DPS{cod_mun}2{cnpj_prestador}{serie_formatada}{numero_dps_formatado}"
        tp_amb = "2" if company.debug_mode else "1"

        client_obj = invoice.client
        country_code = (client_obj.address_country_code).upper()
        postal_code = (
            client_obj.address_postal_code
        )[:11]
        city_name = (
            client_obj.address_city
        )[:60]
        state_province = (
            client_obj.address_state_province
        )[:60]
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
            getattr(company, "default_codigo_tributacao_nacional", None) or "010101"
        ).strip()[:6]
        c_nbs = getattr(company, "default_codigo_nbs", None)
        if c_nbs:
            c_nbs = str(c_nbs).strip()[:9]

        if effective_rate_pct > Decimal("0.00"):
            tot_trib = TctribTotal(p_tot_trib_sn=f"{effective_rate_pct:.2f}")
        else:
            tot_trib = TctribTotal(ind_tot_trib=TstipoIndTotTrib.VALUE_0)

        # TODO: Support domestic client invoicing (endNac, cLocPrestacao, trib_issqn=1)
        # Foreign Client (Export of Services)
        toma = TcinfoPessoa(
            c_nao_nif=TscodNaoNif.VALUE_2,  # 2 = Não exigência do NIF
            x_nome=client_obj.name[:150],
            email=None,
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
                    im=None,  # IM is optional and rejected with E0120 when municipality has no CNC complementary records
                    x_nome=company.company_name[:150],
                    reg_trib=TcregTrib(
                        op_simp_nac="3",  # 3 = Optante - ME/EPP (Simples Nacional)
                        reg_ap_trib_sn="1",  # 1 = Apuração SN
                        reg_esp_trib="0",  # 0 = Nenhum
                    ),
                ),
                toma=toma,
                serv=Tcserv(
                    loc_prest=TclocPrest(c_pais_prestacao=country_code),
                    c_serv=Tccserv(
                        c_trib_nac=c_trib_nac,
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
            ),
        )

        # Serialize XML
        serializer = XmlSerializer(config=SerializerConfig(pretty_print=False))
        unsigned_xml = serializer.render(
            dps, ns_map={None: "http://www.sped.fazenda.gov.br/nfse"}
        )

        # Sign XML
        key_pem, cert_pem = self._get_cert_pems()
        root = etree.fromstring(unsigned_xml.encode("utf-8"))
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
                if "erros" in data and isinstance(data["erros"], list):
                    for err in data["erros"]:
                        if isinstance(err, dict):
                            cod = err.get("codigo", "")
                            desc = err.get("descricao", "")
                            comp = err.get("complemento", "")
                            msg = f"{cod} - {desc}" + (f" ({comp})" if comp else "")
                            erros.append(msg.strip(" -"))
                        else:
                            erros.append(str(err))
                # Format 2: ResponseErro: {"erro": {"codigo": "...", "descricao": "..."}}
                elif "erro" in data:
                    err = data["erro"]
                    if isinstance(err, dict):
                        cod = err.get("codigo", "")
                        desc = err.get("descricao", "")
                        comp = err.get("complemento", "")
                        msg = f"{cod} - {desc}" + (f" ({comp})" if comp else "")
                        erros.append(msg.strip(" -"))
                    else:
                        erros.append(str(err))
                # Format 3: ASP.NET Core ProblemDetails: {"title": "...", "errors": {"fieldName": ["err1", "err2"]}}
                if "errors" in data:
                    err_dict = data["errors"]
                    if isinstance(err_dict, dict):
                        for field_name, msgs in err_dict.items():
                            if isinstance(msgs, list):
                                for m in msgs:
                                    erros.append(f"{field_name}: {m}")
                            else:
                                erros.append(f"{field_name}: {msgs}")
                    elif isinstance(err_dict, list):
                        for m in err_dict:
                            erros.append(str(m))
                # Format 4: Standard API message fields
                for key in (
                    "message",
                    "Message",
                    "detail",
                    "title",
                    "error_description",
                    "error",
                ):
                    if (
                        key in data
                        and data[key]
                        and isinstance(data[key], str)
                        and data[key] not in erros
                    ):
                        erros.append(data[key])
            elif isinstance(data, list):
                for item in data:
                    erros.append(str(item))
        except Exception:
            text = resp.text.strip() if hasattr(resp, "text") and resp.text else ""
            if text:
                clean_text = re.sub(r"<[^>]+>", " ", text)[:300].strip()
                erros.append(f"HTTP {resp.status_code}: {clean_text}")

        if not erros:
            erros.append(
                f"Falha na comunicação com Sefin Nacional (HTTP {resp.status_code})"
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
                    if nfse_b64:
                        try:
                            decompressed_xml = gzip.decompress(
                                base64.b64decode(nfse_b64)
                            ).decode("utf-8")
                            match = re.search(r"<nNFSe>(\d+)</nNFSe>", decompressed_xml)
                            if match:
                                numero_nf = match.group(1)
                        except Exception as ex:
                            logger.warning(
                                "Error decompressing NFS-e XML on recovery: %s", ex
                            )
                if not numero_nf:
                    numero_nf = chave_acesso[-15:].lstrip("0")

                dh_proc = None
                match_dh = re.search(r"<dhProc>([^<]+)</dhProc>", decompressed_xml)
                if match_dh:
                    try:
                        dh_proc = datetime.datetime.fromisoformat(
                            match_dh.group(1).replace("Z", "+00:00")
                        )
                    except Exception:
                        pass

                c_trib_nac = re.search(
                    r"<cTribNac>([^<]+)</cTribNac>", decompressed_xml
                )
                c_nbs = re.search(r"<cNBS>([^<]+)</cNBS>", decompressed_xml)
                c_trib_mun = re.search(
                    r"<cTribMun>([^<]+)</cTribMun>", decompressed_xml
                )
                p_aliq = re.search(r"<pAliq>([^<]+)</pAliq>", decompressed_xml)
                if not p_aliq:
                    p_aliq = re.search(
                        r"<pAliqAplic>([^<]+)</pAliqAplic>", decompressed_xml
                    )
                v_iss = re.search(r"<vISSQN>([^<]+)</vISSQN>", decompressed_xml)

                return EmitResult(
                    sucesso=True,
                    chave_acesso_nacional=chave_acesso,
                    codigo_verificacao=chave_acesso,
                    numero_nf=numero_nf,
                    xml_retorno=decompressed_xml or nfse_resp.text,
                    data_hora_autorizacao=dh_proc,
                    codigo_tributacao_nacional=(
                        c_trib_nac.group(1) if c_trib_nac else ""
                    ),
                    codigo_nbs=c_nbs.group(1) if c_nbs else "",
                    codigo_servico_municipio=c_trib_mun.group(1) if c_trib_mun else "",
                    aliquota_iss=Decimal(p_aliq.group(1)) if p_aliq else None,
                    valor_iss=Decimal(v_iss.group(1)) if v_iss else None,
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

    def consultar_nfse(self, invoice: Invoice) -> Optional[EmitResult]:
        """Checks if the DPS for this invoice was already issued in Sefin Nacional."""
        if not invoice.document_number:
            return None
        company = CompanySettings.objects.first()
        if not company:
            return None

        cnpj_prestador = re.sub(r"[^0-9a-zA-Z]", "", company.cnpj)
        cod_mun = company.address_city_ibge
        serie_formatada = str(
            invoice.document_series or company.document_series or "1"
        ).zfill(5)
        numero_dps_formatado = str(invoice.document_number).zfill(15)
        id_dps = f"DPS{cod_mun}2{cnpj_prestador}{serie_formatada}{numero_dps_formatado}"

        base_url, _ = self._get_urls(company.debug_mode)
        key_pem, cert_pem = self._get_cert_pems()
        fd, temp_cert_path = tempfile.mkstemp(suffix=".pem")
        try:
            os.chmod(temp_cert_path, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(cert_pem + b"\n" + key_pem)
            return self._consultar_dps(id_dps, base_url, temp_cert_path)
        finally:
            if os.path.exists(temp_cert_path):
                try:
                    os.remove(temp_cert_path)
                except OSError:
                    pass

    def emitir_nfse(self, invoice: Invoice) -> EmitResult:
        company = CompanySettings.objects.first()
        if not company:
            raise ValueError("CompanySettings not found.")

        # Ensure document number is assigned
        if not invoice.document_number:
            with transaction.atomic():
                comp = CompanySettings.objects.select_for_update().first()
                if comp:
                    invoice.document_number = comp.next_document_number
                    invoice.document_series = comp.document_series or "1"
                    comp.next_document_number += 1
                    comp.save()
                    invoice.save()
                else:
                    raise ValueError("CompanySettings not found.")

        serie_dps = str(invoice.document_series or "1")
        numero_dps = invoice.document_number

        _, signed_xml, id_dps = self._build_and_sign_dps(
            invoice, company, numero_dps, serie_dps
        )

        base_url, _ = self._get_urls(company.debug_mode)
        endpoint = f"{base_url}/nfse"

        key_pem, cert_pem = self._get_cert_pems()
        fd, temp_cert_path = tempfile.mkstemp(suffix=".pem")
        try:
            os.chmod(temp_cert_path, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(cert_pem + b"\n" + key_pem)

            # Idempotency pre-check: Was this DPS already issued?
            try:
                already_issued = self._consultar_dps(id_dps, base_url, temp_cert_path)
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
                result.codigo_verificacao = result.chave_acesso_nacional

                nfse_b64 = data.get("nfseXmlGZipB64")
                if nfse_b64:
                    try:
                        decompressed_xml = gzip.decompress(
                            base64.b64decode(nfse_b64)
                        ).decode("utf-8")
                        result.xml_retorno = decompressed_xml

                        # Extract nNFSe
                        match = re.search(r"<nNFSe>(\d+)</nNFSe>", decompressed_xml)
                        if match:
                            result.numero_nf = match.group(1)

                        dh_proc = None
                        match_dh = re.search(
                            r"<dhProc>([^<]+)</dhProc>", decompressed_xml
                        )
                        if match_dh:
                            try:
                                dh_proc = datetime.datetime.fromisoformat(
                                    match_dh.group(1).replace("Z", "+00:00")
                                )
                            except Exception:
                                pass

                        c_trib_nac = re.search(
                            r"<cTribNac>([^<]+)</cTribNac>", decompressed_xml
                        )
                        c_nbs = re.search(r"<cNBS>([^<]+)</cNBS>", decompressed_xml)
                        c_trib_mun = re.search(
                            r"<cTribMun>([^<]+)</cTribMun>", decompressed_xml
                        )
                        p_aliq = re.search(r"<pAliq>([^<]+)</pAliq>", decompressed_xml)
                        if not p_aliq:
                            p_aliq = re.search(
                                r"<pAliqAplic>([^<]+)</pAliqAplic>", decompressed_xml
                            )
                        v_iss = re.search(r"<vISSQN>([^<]+)</vISSQN>", decompressed_xml)

                        result.data_hora_autorizacao = dh_proc
                        if c_trib_nac:
                            result.codigo_tributacao_nacional = c_trib_nac.group(1)
                        if c_nbs:
                            result.codigo_nbs = c_nbs.group(1)
                        if c_trib_mun:
                            result.codigo_servico_municipio = c_trib_mun.group(1)
                        if p_aliq:
                            result.aliquota_iss = Decimal(p_aliq.group(1))
                        if v_iss:
                            result.valor_iss = Decimal(v_iss.group(1))
                    except Exception as ex:
                        logger.warning("Error decompressing returned NFSe XML: %s", ex)

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
        finally:
            if os.path.exists(temp_cert_path):
                try:
                    os.remove(temp_cert_path)
                except OSError:
                    pass

    def baixar_pdf(self, invoice: Invoice) -> Optional[bytes]:
        company = CompanySettings.objects.first()
        if not company:
            return None

        nf = getattr(invoice, "nota_fiscal", None)
        chave_acesso = getattr(nf, "chave_acesso_nacional", None) or getattr(
            nf, "verification_code", None
        )
        if not chave_acesso:
            return None

        _, danfse_base_url = self._get_urls(company.debug_mode)
        url = f"{danfse_base_url}/{chave_acesso}"

        key_pem, cert_pem = self._get_cert_pems()
        fd, temp_cert_path = tempfile.mkstemp(suffix=".pem")
        try:
            os.chmod(temp_cert_path, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(cert_pem + b"\n" + key_pem)

            headers = {"Accept": "application/pdf"}
            resp = _logged_get(
                url,
                headers=headers,
                cert=temp_cert_path,
                timeout=30,
            )
            if resp.status_code == 200 and resp.content.startswith(b"%PDF"):
                return resp.content
            else:
                logger.warning(
                    "DANFSe PDF download returned status %s for chave %s",
                    resp.status_code,
                    chave_acesso,
                )
                return None
        except Exception as e:
            logger.warning("Error downloading DANFSe PDF: %s", e)
            return None
        finally:
            if os.path.exists(temp_cert_path):
                try:
                    os.remove(temp_cert_path)
                except OSError:
                    pass

    def cancelar_nfse(self, invoice: Invoice) -> CancelResult:
        company = CompanySettings.objects.first()
        if not company:
            return CancelResult(sucesso=False, erros=["CompanySettings not found."])

        nf = getattr(invoice, "nota_fiscal", None)
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

        cnpj_prestador = re.sub(r"[^0-9a-zA-Z]", "", company.cnpj)

        # Build PedRegEvento for cancelation (E101101)
        from core.nfse.nacional.schemas.v1_00.ped_reg_evento_v1_00 import PedRegEvento
        from core.nfse.nacional.schemas.v1_00.tipos_eventos_v1_00 import (
            TcinfPedReg,
            Te101101,
            Te101101XDesc,
        )
        from core.nfse.nacional.schemas.v1_00.tipos_simples_v1_00 import (
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
            versao="1.00",
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
                    x_motivo="Erro na Emissão",
                ),
            ),
        )

        serializer = XmlSerializer(config=SerializerConfig(pretty_print=False))
        unsigned_xml = serializer.render(
            ped_reg, ns_map={None: "http://www.sped.fazenda.gov.br/nfse"}
        )

        # Sign XML
        key_pem, cert_pem = self._get_cert_pems()
        root = etree.fromstring(unsigned_xml.encode("utf-8"))
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
        endpoint = f"{base_url}/nfse/eventos"

        fd, temp_cert_path = tempfile.mkstemp(suffix=".pem")
        try:
            os.chmod(temp_cert_path, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(cert_pem + b"\n" + key_pem)

            headers = {
                "Content-Type": "application/xml",
                "Accept": "application/json",
            }

            logger.info("Sending Cancel Event to Sefin Nacional: %s", endpoint)
            resp = _logged_post(
                endpoint,
                data=signed_xml.encode("utf-8"),
                headers=headers,
                cert=temp_cert_path,
                timeout=40,
            )

            cancelation_date = None
            if resp.status_code == 201:
                match = re.search(r"<dhEvento>([^<]+)</dhEvento>", resp.text)
                if match:
                    try:
                        cancelation_date = datetime.datetime.fromisoformat(
                            match.group(1).replace("Z", "+00:00")
                        )
                    except Exception:
                        pass

            result = CancelResult(
                sucesso=False,
                xml_enviado=signed_xml,
                xml_retorno=resp.text,
                cancelation_date=cancelation_date,
            )

            if resp.status_code == 201:
                result.sucesso = True
                return result
            else:
                result.erros = self._parse_error_response(resp)
                return result

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
        finally:
            if os.path.exists(temp_cert_path):
                try:
                    os.remove(temp_cert_path)
                except OSError:
                    pass

    def buscar_nfses_por_periodo(self, start_date, end_date) -> list:
        raise NotImplementedError(
            "Busca por período não suportada na API REST do Sefin Nacional."
        )

    def buscar_nfse_por_chave(self, chave_acesso: str) -> Optional[dict]:
        company = CompanySettings.objects.first()
        if not company:
            return None

        base_url, _ = self._get_urls(company.debug_mode)
        endpoint = f"{base_url}/nfse/{chave_acesso}"
        headers = {"Accept": "application/json"}

        key_pem, cert_pem = self._get_cert_pems()
        fd, temp_cert_path = tempfile.mkstemp(suffix=".pem")
        try:
            os.chmod(temp_cert_path, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(cert_pem + b"\n" + key_pem)

            resp = _logged_get(
                endpoint, headers=headers, cert=temp_cert_path, timeout=20
            )
            if resp.status_code == 200:
                data = resp.json()
                nfse_b64 = data.get("nfseXmlGZipB64")
                if nfse_b64:
                    try:
                        decompressed_xml = gzip.decompress(
                            base64.b64decode(nfse_b64)
                        ).decode("utf-8")
                        # Basic extraction
                        numero_nf = chave_acesso[-15:].lstrip("0")
                        match = re.search(r"<nNFSe>(\d+)</nNFSe>", decompressed_xml)
                        if match:
                            numero_nf = match.group(1)

                        dt_emi = datetime.date.today()
                        dt_match = re.search(
                            r"<dhProc>([^<]+)</dhProc>", decompressed_xml
                        )
                        if dt_match:
                            try:
                                dt_emi = datetime.datetime.fromisoformat(
                                    dt_match.group(1)
                                ).date()
                            except:
                                pass

                        # Fallback to dhEmi (DPS emission date) if dhProc is missing
                        if not dt_match:
                            dt_match_dhemi = re.search(
                                r"<dhEmi>([^<]+)</dhEmi>", decompressed_xml
                            )
                            if dt_match_dhemi:
                                try:
                                    dt_emi = datetime.datetime.fromisoformat(
                                        dt_match_dhemi.group(1)
                                    ).date()
                                except:
                                    pass

                        val = "0.00"
                        val_match = re.search(
                            r"<vServ>([^<]+)</vServ>", decompressed_xml
                        )
                        if val_match:
                            val = val_match.group(1)

                        desc = ""
                        desc_match = re.search(
                            r"<xDescServ>([^<]+)</xDescServ>", decompressed_xml
                        )
                        if desc_match:
                            desc = desc_match.group(1)

                        # In Sefin Nacional, cancellation is usually represented by an attached event
                        # like <e101101> or <xDesc>Cancelamento de NFS-e</xDesc>.
                        is_canceled = False
                        if (
                            re.search(
                                r"Cancelamento\s+de\s+NFS-e",
                                decompressed_xml,
                                re.IGNORECASE,
                            )
                            or "<e101101>" in decompressed_xml
                        ):
                            is_canceled = True

                        return {
                            "nf_number": numero_nf,
                            "verification_code": chave_acesso,
                            "chave_acesso_nacional": chave_acesso,
                            "amount_brl": val,
                            "description": desc,
                            "issue_date": dt_emi,
                            "provider": "NACIONAL",
                            "is_canceled": is_canceled,
                            "raw_xml": decompressed_xml,
                        }
                    except Exception as ex:
                        logger.warning(f"Error decompressing Nacional XML: {ex}")

            return None
        finally:
            if os.path.exists(temp_cert_path):
                try:
                    os.remove(temp_cert_path)
                except:
                    pass
