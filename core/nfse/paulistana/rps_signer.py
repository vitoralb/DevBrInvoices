import re
import base64
from decimal import Decimal, ROUND_HALF_UP
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpRps as TpRpsV2
from core.nfse.paulistana.schemas_v1.tipos_nfe_v01 import TpRps as TpRpsV1


def _to_cents_int(val) -> int:
    """Convert string/float/Decimal to integer cents without floating point precision issues."""
    if not val:
        return 0
    d = Decimal(str(val))
    return int((d * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _is_retido(val) -> str:
    """Return 'S' if retention is indicated, otherwise 'N'."""
    return "S" if str(val).strip().lower() in ("true", "s", "1", "sim") else "N"


def assinar_rps(rps: TpRpsV2, key_pem: bytes) -> str:
    """Gera a assinatura digital (Hash SHA1 + RSA) para a string do RPS na versão 2."""
    s_inscricao = str(rps.chave_rps.inscricao_prestador or "").zfill(12)
    s_serie = str(rps.chave_rps.serie_rps or "").ljust(5, " ")
    s_numero = str(rps.chave_rps.numero_rps or "").zfill(12)
    s_data = str(rps.data_emissao or "").replace("-", "")[:8]
    s_tributacao = (
        rps.tributacao_rps.value
        if hasattr(rps.tributacao_rps, "value")
        else str(rps.tributacao_rps or "")
    )
    s_status = (
        rps.status_rps.value
        if hasattr(rps.status_rps, "value")
        else str(rps.status_rps or "")
    )

    s_iss_retido = _is_retido(rps.issretido)

    val_cobrado = rps.valor_inicial_cobrado or rps.valor_final_cobrado or "0.0"
    s_valor_cobrado = str(_to_cents_int(val_cobrado)).zfill(15)
    s_valor_deducoes = str(_to_cents_int(rps.valor_deducoes or "0.0")).zfill(15)
    s_cod_servico = str(rps.codigo_servico or "").zfill(5)

    # Tomador
    ind_tomador = "3"
    s_cpf_cnpj_tomador = "".zfill(14)
    if rps.cpfcnpjtomador:
        cpf_cnpj = rps.cpfcnpjtomador.cpf or rps.cpfcnpjtomador.cnpj
        if cpf_cnpj:
            clean_digits = re.sub(r"\D", "", str(cpf_cnpj))
            ind_tomador = "1" if len(clean_digits) == 11 else "2"
            s_cpf_cnpj_tomador = clean_digits.zfill(14)
        elif rps.cpfcnpjtomador.nif:
            ind_tomador = "4"
            s_cpf_cnpj_tomador = "".zfill(14)

    string_to_sign = (
        s_inscricao
        + s_serie
        + s_numero
        + s_data
        + s_tributacao
        + s_status
        + s_iss_retido
        + s_valor_cobrado
        + s_valor_deducoes
        + s_cod_servico
        + ind_tomador
        + s_cpf_cnpj_tomador
    )

    # Intermediario
    if rps.cpfcnpjintermediario:
        cpf_cnpj_inter = rps.cpfcnpjintermediario.cpf or rps.cpfcnpjintermediario.cnpj
        if cpf_cnpj_inter:
            clean_inter = re.sub(r"\D", "", str(cpf_cnpj_inter))
            ind_inter = "1" if len(clean_inter) == 11 else "2"
            s_cpf_cnpj_inter = clean_inter.zfill(14)
            s_iss_ret_inter = _is_retido(rps.issretido_intermediario)
            string_to_sign += ind_inter + s_cpf_cnpj_inter + s_iss_ret_inter

    if rps.cpfcnpjtomador and rps.cpfcnpjtomador.nif:
        string_to_sign += str(rps.cpfcnpjtomador.nif)
    elif rps.cpfcnpjtomador and rps.cpfcnpjtomador.nao_nif:
        string_to_sign += str(rps.cpfcnpjtomador.nao_nif)

    private_key = load_pem_private_key(key_pem, password=None)
    signature = private_key.sign(
        string_to_sign.encode("utf-8"), padding.PKCS1v15(), hashes.SHA1()
    )
    return base64.b64encode(signature).decode("ascii")


def assinar_rps_v1(rps: TpRpsV1, key_pem: bytes) -> str:
    """Gera a assinatura digital (Hash SHA1 + RSA) para a string do RPS na versão 1."""
    s_inscricao = str(rps.chave_rps.inscricao_prestador or "").zfill(8)
    s_serie = str(rps.chave_rps.serie_rps or "").ljust(5, " ")
    s_numero = str(rps.chave_rps.numero_rps or "").zfill(12)
    s_data = str(rps.data_emissao or "").replace("-", "")[:8]
    s_tributacao = (
        rps.tributacao_rps.value
        if hasattr(rps.tributacao_rps, "value")
        else str(rps.tributacao_rps or "")
    )
    s_status = (
        rps.status_rps.value
        if hasattr(rps.status_rps, "value")
        else str(rps.status_rps or "")
    )

    s_iss_retido = _is_retido(rps.issretido)
    s_valor_servicos = str(_to_cents_int(rps.valor_servicos or "0.0")).zfill(15)
    s_valor_deducoes = str(_to_cents_int(rps.valor_deducoes or "0.0")).zfill(15)
    s_cod_servico = str(rps.codigo_servico or "").zfill(5)

    # Tomador
    ind_tomador = "3"
    s_cpf_cnpj_tomador = "".zfill(14)
    if rps.cpfcnpjtomador:
        cpf_cnpj = rps.cpfcnpjtomador.cpf or rps.cpfcnpjtomador.cnpj
        if cpf_cnpj:
            clean_digits = re.sub(r"\D", "", str(cpf_cnpj))
            ind_tomador = "1" if len(clean_digits) == 11 else "2"
            s_cpf_cnpj_tomador = clean_digits.zfill(14)

    string_to_sign = (
        s_inscricao
        + s_serie
        + s_numero
        + s_data
        + s_tributacao
        + s_status
        + s_iss_retido
        + s_valor_servicos
        + s_valor_deducoes
        + s_cod_servico
        + ind_tomador
        + s_cpf_cnpj_tomador
    )

    private_key = load_pem_private_key(key_pem, password=None)
    signature = private_key.sign(
        string_to_sign.encode("utf-8"), padding.PKCS1v15(), hashes.SHA1()
    )
    return base64.b64encode(signature).decode("ascii")


def assinar_cancelamento(
    inscricao_municipal: str, nf_number: str, key_pem: bytes
) -> bytes:
    """Gera a assinatura digital (Hash SHA1 + RSA) para o cancelamento de NFS-e (Paulistana)."""
    s_inscricao = str(inscricao_municipal or "").zfill(8)
    s_numero = str(nf_number or "").zfill(12)

    string_to_sign = s_inscricao + s_numero

    private_key = load_pem_private_key(key_pem, password=None)
    signature = private_key.sign(
        string_to_sign.encode("utf-8"), padding.PKCS1v15(), hashes.SHA1()
    )
    return signature
