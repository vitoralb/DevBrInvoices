import datetime
import logging
import os
import tempfile
from contextlib import contextmanager

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from lxml import etree

logger = logging.getLogger(__name__)

# Secure XML parser with disabled entity resolution and external network access
SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)


@contextmanager
def _temp_cert_file(cert_pem: bytes, key_pem: bytes):
    """Context manager that writes cert/key to a short-lived temp file,
    yields the path, then securely deletes it. Used for requests mTLS."""
    fd, path = tempfile.mkstemp(suffix=".pem")
    try:
        os.chmod(path, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(cert_pem + b"\n" + key_pem)
        yield path
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


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
