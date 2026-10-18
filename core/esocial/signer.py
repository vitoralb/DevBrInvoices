import logging
from lxml import etree
from signxml import XMLSigner, methods

logger = logging.getLogger(__name__)


def assinar_xml_esocial(xml_content, key_pem, cert_pem):
    """Assina digitalmente o documento XML do eSocial conforme MOD v1.16:
    - Padrão: XML Digital Signature, Enveloped
    - Algoritmo de assinatura: RSA-SHA256 (http://www.w3.org/2001/04/xmldsig-more#rsa-sha256)
    - Algoritmo de resumo: SHA-256 (http://www.w3.org/2001/04/xmlenc#sha256)
    - Canonicalização: C14N (http://www.w3.org/TR/2001/REC-xml-c14n-20010315)
    - Reference URI: "" (enveloped signature do documento inteiro)
    """
    if isinstance(xml_content, str):
        xml_root = etree.fromstring(xml_content.encode("utf-8"))
    elif isinstance(xml_content, bytes):
        xml_root = etree.fromstring(xml_content)
    else:
        xml_root = xml_content

    key_bytes = key_pem.encode("utf-8") if isinstance(key_pem, str) else key_pem
    cert_bytes = cert_pem.encode("utf-8") if isinstance(cert_pem, str) else cert_pem

    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )

    signed_root = signer.sign(xml_root, key=key_bytes, cert=cert_bytes)
    return etree.tostring(signed_root, encoding="utf-8").decode("utf-8")

