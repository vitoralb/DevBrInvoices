from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.w3.org/2000/09/xmldsig#"


@dataclass(kw_only=True)
class KeyValueType:
    rsakey_value: KeyValueType.RsakeyValue = field(
        metadata={
            "name": "RSAKeyValue",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )

    @dataclass(kw_only=True)
    class RsakeyValue:
        modulus: bytes = field(
            metadata={
                "name": "Modulus",
                "type": "Element",
                "namespace": "http://www.w3.org/2000/09/xmldsig#",
                "format": "base64",
            }
        )
        exponent: bytes = field(
            metadata={
                "name": "Exponent",
                "type": "Element",
                "namespace": "http://www.w3.org/2000/09/xmldsig#",
                "format": "base64",
            }
        )


@dataclass(kw_only=True)
class SignatureValueType:
    value: bytes = field(
        default=b"",
        metadata={
            "format": "base64",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class TransformType:
    xpath: list[str] = field(
        default_factory=list,
        metadata={
            "name": "XPath",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        },
    )
    algorithm: str = field(
        metadata={
            "name": "Algorithm",
            "type": "Attribute",
        }
    )


@dataclass(kw_only=True)
class X509DataType:
    x509_certificate: bytes = field(
        metadata={
            "name": "X509Certificate",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "format": "base64",
        }
    )


@dataclass(kw_only=True)
class KeyInfoType:
    x509_data: X509DataType = field(
        metadata={
            "name": "X509Data",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class TransformsType:
    transform: list[TransformType] = field(
        default_factory=list,
        metadata={
            "name": "Transform",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "min_occurs": 1,
        },
    )


@dataclass(kw_only=True)
class ReferenceType:
    transforms: TransformsType = field(
        metadata={
            "name": "Transforms",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )
    digest_method: ReferenceType.DigestMethod = field(
        metadata={
            "name": "DigestMethod",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )
    digest_value: bytes = field(
        metadata={
            "name": "DigestValue",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "format": "base64",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )
    uri: None | str = field(
        default=None,
        metadata={
            "name": "URI",
            "type": "Attribute",
        },
    )
    type_value: None | str = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
        },
    )

    @dataclass(kw_only=True)
    class DigestMethod:
        algorithm: str = field(
            metadata={
                "name": "Algorithm",
                "type": "Attribute",
            }
        )


@dataclass(kw_only=True)
class SignedInfoType:
    canonicalization_method: SignedInfoType.CanonicalizationMethod = field(
        metadata={
            "name": "CanonicalizationMethod",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )
    signature_method: SignedInfoType.SignatureMethod = field(
        metadata={
            "name": "SignatureMethod",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )
    reference: list[ReferenceType] = field(
        default_factory=list,
        metadata={
            "name": "Reference",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "min_occurs": 1,
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )

    @dataclass(kw_only=True)
    class CanonicalizationMethod:
        algorithm: str = field(
            metadata={
                "name": "Algorithm",
                "type": "Attribute",
            }
        )

    @dataclass(kw_only=True)
    class SignatureMethod:
        algorithm: str = field(
            metadata={
                "name": "Algorithm",
                "type": "Attribute",
            }
        )


@dataclass(kw_only=True)
class SignatureType:
    signed_info: SignedInfoType = field(
        metadata={
            "name": "SignedInfo",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )
    signature_value: SignatureValueType = field(
        metadata={
            "name": "SignatureValue",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )
    key_info: KeyInfoType = field(
        metadata={
            "name": "KeyInfo",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class Signature(SignatureType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"
