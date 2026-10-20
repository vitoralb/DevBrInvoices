import datetime
import logging
import re
from decimal import Decimal
from typing import Optional, Union
import xml.etree.ElementTree as ET

from django.template.loader import render_to_string
from django.utils import timezone
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.models.datatype import XmlDate, XmlDateTime

from core.models import CompanySettings, Invoice, NotaFiscal
from core.nfse.paulistana.schemas.tipos_nfe_v02 import (
    TpNfe,
    TpChaveNfe,
    TpChaveRps,
    TpCpfcnpj,
    TpEndereco,
    TpStatusNfe,
    TpOpcaoSimples,
    TpTipoRps,
    TpNaoSim,
)
from core.nfse.paulistana.utils import to_xml

logger = logging.getLogger(__name__)


def is_paulistana_xml_mocked(
    xml_str: Optional[str], verification_code: Optional[str]
) -> bool:
    """Checks if a Paulistana NFS-e or XML is a synthetic/debug mock.
    Returns False ONLY when the note has a valid verification code AND a valid,
    authentic XML imported from the provider (i.e. not synthetic/mocked).
    """
    cod = str(verification_code or "").strip().upper()
    if not cod or cod.startswith("DEBUG") or cod.startswith("DBG"):
        return True

    if not xml_str or not xml_str.strip():
        return True

    upper_xml = xml_str.upper()
    if "DEBUG-" in upper_xml or "<CODIGOVERIFICACAO>DBG" in upper_xml:
        return True

    try:
        root = ET.fromstring(xml_str.encode("utf-8"))
        if root is None:
            return True
        tag = root.tag.lower()
        has_nfe = (
            "nfe" in tag
            or root.find(".//{*}ChaveNFe") is not None
            or root.find(".//ChaveNFe") is not None
            or "retorno" in tag
        )
        if not has_nfe:
            return True
    except Exception:
        return True

    return False


def build_mock_paulistana_nfse_xml(
    invoice: Invoice,
    company: CompanySettings,
    numero_nfe: Union[int, str],
    codigo_verificacao: Optional[str] = None,
) -> str:
    """Constructs a fully populated, authentic São Paulo tpNFe XML for debug/test mode."""
    from core.services import _prepare_nf_data

    amount_brl, description, effective_rate_pct = _prepare_nf_data(invoice)
    clean_desc = description.replace("\r", "").strip()

    # Numeric RPS and NF-e number
    num_str = str(numero_nfe)
    if num_str.startswith("DEBUG-"):
        num_str = num_str[6:]
    num_val = int(num_str) if num_str.isdigit() else (invoice.document_number or 1)

    # Inscrição Municipal
    im_clean = re.sub(r"[^0-9]", "", company.inscricao_municipal or "0")
    im_val = int(im_clean) if im_clean.isdigit() else 12345678

    # Código de Verificação
    cod_ver = (
        codigo_verificacao
        if codigo_verificacao and not codigo_verificacao.startswith("DEBUG-")
        else f"DBG{num_val:04d}X"
    )

    # Chave Nacional (50 digits)
    cnpj_prestador = re.sub(r"[^0-9a-zA-Z]", "", company.cnpj or "00000000000000")[:14].zfill(14).upper()
    chave_nac = f"35503082{cnpj_prestador}0000100000000000{str(num_val).zfill(5)}1234567"

    now_dt = datetime.datetime.now()
    issue_date = invoice.issue_date or now_dt.date()

    # Check if export of services (foreign client)
    is_export = (
        (getattr(invoice.client, "address_country_code", "") or "").upper() != "BR"
        if getattr(invoice, "client", None)
        else True
    )

    if is_export:
        tributacao_nfe = "P"
        valor_iss = Decimal("0.00")
        aliq_serv = Decimal("0.0000")
    else:
        tributacao_nfe = "T"
        valor_iss = (
            (amount_brl * (effective_rate_pct / Decimal("100.0"))).quantize(Decimal("0.01"))
            if effective_rate_pct
            else Decimal("0.00")
        )
        aliq_serv = (
            (effective_rate_pct / Decimal("100.0")).quantize(Decimal("0.0001"))
            if effective_rate_pct
            else Decimal("0.0000")
        )

    # CEP Prestador
    cep_prest_clean = re.sub(
        r"[^0-9]", "", getattr(company, "address_cep", "") or "01001000"
    )
    cep_prest_val = int(cep_prest_clean) if cep_prest_clean.isdigit() else 1001000

    # Client address
    client_obj = invoice.client
    client_cep_clean = re.sub(
        r"[^0-9]", "", getattr(client_obj, "address_postal_code", "") or ""
    )
    client_cep_val = int(client_cep_clean) if client_cep_clean.isdigit() else None

    # Endereço Prestador
    cidade_ibge = getattr(company, "address_city_ibge", "") or "3550308"
    cidade_ibge_val = int(cidade_ibge) if str(cidade_ibge).isdigit() else 3550308

    end_prest = TpEndereco(
        tipo_logradouro=(
            getattr(company, "address_tipo_logradouro", "") or "Rua"
        )[:10],
        logradouro=(
            getattr(company, "address_line1", "") or "Avenida Paulista"
        )[:50],
        numero_endereco=(getattr(company, "address_number", "") or "1000")[:10],
        complemento_endereco=(
            getattr(company, "address_line2", "") or ""
        )[:30]
        or None,
        bairro=(
            getattr(company, "address_neighborhood", "") or "Bela Vista"
        )[:30],
        cidade=cidade_ibge_val,
        uf=(getattr(company, "address_uf", "") or "SP")[:2],
        cep=cep_prest_val,
    )

    # Endereço Tomador
    end_toma = TpEndereco(
        logradouro=(client_obj.address_line1 or "Foreign Street")[:50],
        numero_endereco=(client_obj.address_number or "1")[:10],
        complemento_endereco=(client_obj.address_line2 or "")[:30] or None,
        bairro=(client_obj.address_neighborhood or "Downtown")[:30],
        cidade=None,
        uf=None,
        cep=client_cep_val,
    )

    nota = TpNfe(
        assinatura=f"DEBUG-MOCK-SIGNATURE-{num_val}".encode("ascii"),
        chave_nfe=TpChaveNfe(
            inscricao_prestador=im_val,
            numero_nfe=num_val,
            codigo_verificacao=cod_ver,
            chave_nota_nacional=chave_nac,
        ),
        data_emissao_nfe=XmlDateTime.from_datetime(now_dt),
        numero_lote=1,
        chave_rps=TpChaveRps(
            inscricao_prestador=im_val,
            serie_rps=str(invoice.document_series or "1")[:5],
            numero_rps=invoice.document_number or num_val,
        ),
        tipo_rps=TpTipoRps.RPS,
        data_emissao_rps=XmlDate.from_date(issue_date),
        data_fato_gerador_nfe=XmlDateTime.from_datetime(
            datetime.datetime.combine(issue_date, datetime.time.min)
        ),
        cpfcnpjprestador=TpCpfcnpj(cnpj=cnpj_prestador),
        razao_social_prestador=(
            getattr(company, "company_name", "") or "Empresa Prestadora"
        )[:75],
        endereco_prestador=end_prest,
        email_prestador=(getattr(company, "email", "") or "")[:75] or None,
        status_nfe=TpStatusNfe.N,
        tributacao_nfe=tributacao_nfe,
        opcao_simples=TpOpcaoSimples.VALUE_4,
        valor_servicos=f"{amount_brl:.2f}",
        valor_deducoes="0.00",
        valor_pis="0.00",
        valor_cofins="0.00",
        valor_inss="0.00",
        valor_ir="0.00",
        valor_csll="0.00",
        codigo_servico=getattr(invoice, "codigo_servico_municipio", "") or "02668",
        aliquota_servicos=f"{aliq_serv:.4f}",
        valor_iss=f"{valor_iss:.2f}",
        valor_credito="0.00",
        issretido=False,
        razao_social_tomador=(client_obj.name or "Foreign Client Inc")[:75],
        endereco_tomador=end_toma,
        email_tomador=(client_obj.email or "")[:75] or None,
        discriminacao=clean_desc,
        fonte_carga_tributaria="IBPT",
        exigibilidade_suspensa=TpNaoSim.VALUE_0,
    )

    return to_xml(nota)


def update_paulistana_xml_cancelled(
    xml_content: str, cancel_dt: Optional[datetime.datetime] = None
) -> str:
    """Updates a São Paulo tpNFe XML marking it as CANCELLED (StatusNFe='C')."""
    if not cancel_dt:
        cancel_dt = timezone.now()

    # Primary path: xsdata typed serialization
    try:
        parser = XmlParser()
        nota = parser.from_string(xml_content, TpNfe)
        nota.status_nfe = TpStatusNfe.C
        nota.data_cancelamento = XmlDateTime.from_datetime(cancel_dt)
        return to_xml(nota)
    except Exception as e:
        logger.warning(
            "xsdata failed to parse tpNFe for cancellation (%s). Falling back to ElementTree.",
            e,
        )

    # Fallback path: ElementTree DOM manipulation
    try:
        root = ET.fromstring(xml_content)
        status_elem = root.find("StatusNFe")
        if status_elem is not None:
            status_elem.text = "C"
        else:
            status_elem = ET.SubElement(root, "StatusNFe")
            status_elem.text = "C"

        canc_elem = root.find("DataCancelamento")
        dt_str = cancel_dt.strftime("%Y-%m-%dT%H:%M:%S")
        if canc_elem is not None:
            canc_elem.text = dt_str
        else:
            canc_elem = ET.SubElement(root, "DataCancelamento")
            canc_elem.text = dt_str

        return ET.tostring(root, encoding="utf-8").decode("utf-8")
    except Exception as ex2:
        logger.error("ElementTree fallback failed for tpNFe cancellation: %s", ex2)
        return xml_content


def _format_currency(val) -> str:
    try:
        d = Decimal(str(val or "0.00"))
        # Format as 1.234,56
        s = f"{d:,.2f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def _format_cnpj(cnpj_raw: str) -> str:
    c = re.sub(r"[^0-9a-zA-Z]", "", str(cnpj_raw or "")).upper()
    if len(c) == 14:
        return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"
    elif len(c) == 11:
        return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"
    return cnpj_raw or "Não Informado"


def _format_im(im_raw: str) -> str:
    c = re.sub(r"[^0-9]", "", str(im_raw or ""))
    if len(c) >= 8:
        return f"{c[:1]}.{c[1:4]}.{c[4:7]}-{c[7:]}"
    return im_raw or "Não Informado"


def parse_paulistana_nfse_xml_for_pdf(xml_content: str) -> dict:
    """Parses a Paulistana tpNFe XML into a template context dictionary for PDF rendering."""
    root = ET.fromstring(xml_content)

    def find_text(path, default=""):
        elem = root.find(path)
        return (elem.text or "").strip() if elem is not None and elem.text else default

    # Identification
    nfe_num = find_text("ChaveNFe/NumeroNFe") or find_text("ChaveRPS/NumeroRPS") or "1"
    cod_verif = find_text("ChaveNFe/CodigoVerificacao", "DEBUG-FAKE-CODE")
    chave_nac = find_text("ChaveNFe/ChaveNotaNacional", "")

    dt_emi_raw = find_text("DataEmissaoNFe") or find_text("DataEmissaoRPS")
    data_emissao_fmt = ""
    if dt_emi_raw:
        try:
            # Handle ISO datetime e.g. 2026-10-16T14:30:00
            clean_dt = dt_emi_raw.replace("Z", "").split("+")[0]
            dt_obj = datetime.datetime.fromisoformat(clean_dt)
            data_emissao_fmt = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            data_emissao_fmt = dt_emi_raw

    status_nfe = find_text("StatusNFe", "N")
    is_canceled = (status_nfe == "C")
    trib_nfe = find_text("TributacaoNFe", "P")
    is_export = (trib_nfe == "P")
    dt_canc_raw = find_text("DataCancelamento")
    data_canc_fmt = ""
    if dt_canc_raw:
        try:
            clean_dt = dt_canc_raw.replace("Z", "").split("+")[0]
            dt_obj = datetime.datetime.fromisoformat(clean_dt)
            data_canc_fmt = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            data_canc_fmt = dt_canc_raw

    # Prestador
    cnpj_prest = _format_cnpj(find_text("CPFCNPJPrestador/CNPJ") or find_text("CPFCNPJPrestador/CPF"))
    im_prest = _format_im(find_text("ChaveNFe/InscricaoPrestador") or find_text("ChaveRPS/InscricaoPrestador"))
    nome_prest = find_text("RazaoSocialPrestador")
    email_prest = find_text("EmailPrestador")
    
    end_p_tipo = find_text("EnderecoPrestador/TipoLogradouro")
    end_p_logr = find_text("EnderecoPrestador/Logradouro")
    end_p_num = find_text("EnderecoPrestador/NumeroEndereco")
    end_p_cpl = find_text("EnderecoPrestador/ComplementoEndereco")
    end_p_bairro = find_text("EnderecoPrestador/Bairro")
    end_p_uf = find_text("EnderecoPrestador/UF", "SP")
    end_p_cep = find_text("EnderecoPrestador/CEP")
    if end_p_cep and len(end_p_cep) == 8:
        end_p_cep = f"{end_p_cep[:5]}-{end_p_cep[5:]}"
    endereco_prest_str = f"{end_p_tipo} {end_p_logr}, {end_p_num}".strip()
    if end_p_cpl:
        endereco_prest_str += f" - {end_p_cpl}"
    if end_p_bairro:
        endereco_prest_str += f" - {end_p_bairro}"

    # Tomador
    nome_toma = find_text("RazaoSocialTomador", "CLIENTE TOMADOR")
    cnpj_toma = find_text("CPFCNPJTomador/CNPJ") or find_text("CPFCNPJTomador/CPF")
    cnpj_toma_str = _format_cnpj(cnpj_toma) if cnpj_toma else "Não Informado / Exterior"
    im_toma = find_text("InscricaoMunicipalTomador", "Não Informado")
    email_toma = find_text("EmailTomador")

    end_t_logr = find_text("EnderecoTomador/Logradouro")
    end_t_num = find_text("EnderecoTomador/NumeroEndereco")
    end_t_cpl = find_text("EnderecoTomador/ComplementoEndereco")
    end_t_bairro = find_text("EnderecoTomador/Bairro")
    endereco_toma_str = f"{end_t_logr} {end_t_num}".strip()
    if end_t_cpl:
        endereco_toma_str += f" - {end_t_cpl}"
    if end_t_bairro:
        endereco_toma_str += f" - {end_t_bairro}"

    # Discriminação
    discriminacao = find_text("Discriminacao")

    # Values
    v_serv = find_text("ValorServicos", "0.00")
    v_dedu = find_text("ValorDeducoes", "0.00")
    v_pis = find_text("ValorPIS", "0.00")
    v_cofins = find_text("ValorCOFINS", "0.00")
    v_inss = find_text("ValorINSS", "0.00")
    v_ir = find_text("ValorIR", "0.00")
    v_csll = find_text("ValorCSLL", "0.00")
    cod_serv = find_text("CodigoServico", "02668")
    aliq_serv = find_text("AliquotaServicos", "0.00")
    v_iss = find_text("ValorISS", "0.00")
    v_cred = find_text("ValorCredito", "0.00")
    iss_retido = find_text("ISSRetido", "false").lower() in ("true", "1")

    # Format percentage
    try:
        aliq_dec = Decimal(aliq_serv)
        if aliq_dec < Decimal("1.00") and aliq_dec > Decimal("0.00"):
            aliq_dec = aliq_dec * Decimal("100.0")
        aliq_fmt = f"{aliq_dec:.2f}%".replace(".", ",")
    except Exception:
        aliq_fmt = "0,00%"

    # Base de cálculo = ValorServicos - ValorDeducoes
    try:
        bc_dec = Decimal(v_serv) - Decimal(v_dedu)
    except Exception:
        bc_dec = Decimal(v_serv)

    # Service name mapping
    service_names = {
        "02668": "02668 - Programação, elaboração de programas de computadores, inclusive jogos eletrônicos",
        "02670": "02670 - Planejamento, confecção e manutenção de páginas eletrônicas",
        "02690": "02690 - Outros serviços de consultoria em tecnologia da informação",
    }
    cod_serv_desc = service_names.get(cod_serv, f"{cod_serv} - Serviços de Tecnologia da Informação")

    return {
        "numero_nfe": str(nfe_num).zfill(8),
        "data_emissao": data_emissao_fmt,
        "codigo_verificacao": cod_verif,
        "chave_nota_nacional": chave_nac,
        "is_canceled": is_canceled,
        "data_cancelamento": data_canc_fmt,
        "prestador": {
            "razao_social": nome_prest,
            "cnpj": cnpj_prest,
            "inscricao_municipal": im_prest,
            "endereco": endereco_prest_str,
            "municipio": "São Paulo",
            "uf": end_p_uf,
            "cep": end_p_cep,
            "email": email_prest,
        },
        "tomador": {
            "razao_social": nome_toma,
            "cpf_cnpj": cnpj_toma_str,
            "inscricao_municipal": im_toma,
            "endereco": endereco_toma_str,
            "email": email_toma,
        },
        "discriminacao": discriminacao,
        "valor_servicos": _format_currency(v_serv),
        "retencoes": {
            "inss": _format_currency(v_inss),
            "irrf": _format_currency(v_ir),
            "csll": _format_currency(v_csll),
            "cofins": _format_currency(v_cofins),
            "pis": _format_currency(v_pis),
        },
        "codigo_servico": cod_serv_desc,
        "deducoes": _format_currency(v_dedu),
        "base_calculo": _format_currency(bc_dec),
        "aliquota": aliq_fmt,
        "valor_iss": _format_currency(v_iss),
        "valor_credito": _format_currency(v_cred),
        "iss_retido": "Sim" if iss_retido else "Não",
        "municipio_prestacao": "São Paulo - SP",
        "is_export": is_export,
        "tributacao_nfe": trib_nfe,
    }


def render_paulistana_debug_pdf(xml_content: str) -> bytes:
    """Renders a PDF from Paulistana tpNFe XML using WeasyPrint and official layout."""
    import weasyprint

    context = parse_paulistana_nfse_xml_for_pdf(xml_content)
    html_content = render_to_string("core/paulistana_nfse_pdf.html", context)
    return weasyprint.HTML(string=html_content).write_pdf()
