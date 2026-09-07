from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_v02 import (
    TpChaveNfe,
    TpChaveRps,
    TpCpfcnpj,
)
from core.nfse.paulistana.schemas.xmldsig_core_schema_v02 import Signature

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class PedidoConsultaNfe:
    """
    Schema utilizado para PEDIDO de consultas de NFS-e.

    Este Schema XML é utilizado pelos prestadores de serviços consultarem
    NFS-e geradas por eles.

    :ivar cabecalho: Cabeçalho do pedido.
    :ivar detalhe: Detalhe do pedido. Cada item de detalhe deverá conter
        a chave de uma NFS-e ou a chave de um RPS.
    :ivar signature: Assinatura digital do contribuinte que gerou as
        NFS-e/RPS.
    """

    class Meta:
        name = "PedidoConsultaNFe"
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: PedidoConsultaNfe.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
    )
    detalhe: list[PedidoConsultaNfe.Detalhe] = field(
        default_factory=list,
        metadata={
            "name": "Detalhe",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
            "max_occurs": 50,
        },
    )
    signature: Signature = field(
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )

    @dataclass(kw_only=True)
    class Cabecalho:
        """
        :ivar cpfcnpjremetente: Informe o CPF/CNPJ do Remetente
            autorizado a transmitir a mensagem XML.
        :ivar versao: Informe a Versão do Schema XML utilizado.
        """

        cpfcnpjremetente: TpCpfcnpj = field(
            metadata={
                "name": "CPFCNPJRemetente",
                "type": "Element",
                "namespace": "",
            }
        )
        versao: str = field(
            metadata={
                "name": "Versao",
                "type": "Attribute",
                "pattern": r"[0-9]{1,3}",
            }
        )

    @dataclass(kw_only=True)
    class Detalhe:
        chave_rps: None | TpChaveRps = field(
            default=None,
            metadata={
                "name": "ChaveRPS",
                "type": "Element",
                "namespace": "",
            },
        )
        chave_nfe: None | TpChaveNfe = field(
            default=None,
            metadata={
                "name": "ChaveNFe",
                "type": "Element",
                "namespace": "",
            },
        )
