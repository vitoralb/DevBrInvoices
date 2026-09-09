import datetime
import logging
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

logger = logging.getLogger(__name__)


def carregar_certificado_pfx_bytes(pfx_data, password):
    pwd_bytes = (
        password.encode("utf-8") if isinstance(password, str) else (password or b"")
    )
    private_key, certificate, _ = pkcs12.load_key_and_certificates(pfx_data, pwd_bytes)

    if not private_key or not certificate:
        raise ValueError(
            "Chave privada ou certificado ausente no arquivo PFX fornecido."
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    exp = getattr(certificate, "not_valid_after_utc", None)
    if exp and exp < now:
        logger.warning("Certificado digital está expirado desde %s", exp)

    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    cert_pem = certificate.public_bytes(serialization.Encoding.PEM)

    return key_pem, cert_pem, exp


def carregar_certificado_pfx(pfx_path, password):
    """Reads a PKCS#12 (.pfx) file and extracts the private key and public certificate as PEM bytes."""
    if not os.path.exists(pfx_path):
        raise FileNotFoundError(
            f"Certificado digital não encontrado no caminho: {pfx_path}"
        )

    with open(pfx_path, "rb") as f:
        pfx_data = f.read()
    key_pem, cert_pem, exp = carregar_certificado_pfx_bytes(pfx_data, password)
    return key_pem, cert_pem
