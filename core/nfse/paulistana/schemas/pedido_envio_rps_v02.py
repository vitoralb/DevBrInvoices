from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_v02 import (
    TpCpfcnpj,
    TpRps,
)
from core.nfse.paulistana.schemas.xmldsig_core_schema_v02 import Signature

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class PedidoEnvioRps:
    """
    Schema utilizado para PEDIDO de envio de RPS.

    Este Schema XML é utilizado pelos prestadores de serviços para
    substituição online e individual de RPS por NFS-e.

    :ivar cabecalho: Cabeçalho do pedido.
    :ivar rps: Informe o RPS a ser substituido por NFS-e.
    :ivar signature: Assinatura digital do contribuinte que gerou o RPS
        contido da mensagem XML.
    """

    class Meta:
        name = "PedidoEnvioRPS"
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: PedidoEnvioRps.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
    )
    rps: TpRps = field(
        metadata={
            "name": "RPS",
            "type": "Element",
            "namespace": "",
        }
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
