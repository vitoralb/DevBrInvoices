import os
import logging
import datetime
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization
from signxml import XMLSigner, methods

logger = logging.getLogger(__name__)


class XMLSignerComSHA1(XMLSigner):
    def check_deprecated_methods(self):
        # Passa ignorando o bloqueio do SHA-1 (exigência estrita da Prefeitura de SP)
        pass


from core.nfse.cert import carregar_certificado_pfx


def assinar_xml(xml_root, key_pem, cert_pem):
    """Assina o XML no padrão exigido pela Prefeitura (XML Digital Signature, Enveloped)."""
    signer = XMLSignerComSHA1(
        method=methods.enveloped,
        signature_algorithm="rsa-sha1",
        digest_algorithm="sha1",
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )
    signed_root = signer.sign(xml_root, key=key_pem, cert=cert_pem)
    return signed_root
