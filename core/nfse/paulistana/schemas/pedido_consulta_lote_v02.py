from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpCpfcnpj
from core.nfse.paulistana.schemas.xmldsig_core_schema_v02 import Signature

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class PedidoConsultaLote:
    """
    Schema utilizado para PEDIDO de consultas de Lote.

    Este Schema XML é utilizado pelos prestadores de serviços consultarem
    as NFS-e geradas a partir de um lote de RPS.

    :ivar cabecalho: Cabeçalho do pedido.
    :ivar signature: Assinatura digital do contribuinte que gerou o lote
        de RPS.
    """

    class Meta:
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: PedidoConsultaLote.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
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
        :ivar numero_lote: Informe o número do Lote que deseja
            consultar.
        :ivar versao: Informe a Versão do Schema XML utilizado.
        """

        cpfcnpjremetente: TpCpfcnpj = field(
            metadata={
                "name": "CPFCNPJRemetente",
                "type": "Element",
                "namespace": "",
            }
        )
        numero_lote: str = field(
            metadata={
                "name": "NumeroLote",
                "type": "Element",
                "namespace": "",
                "pattern": r"[0-9]{1,12}",
            }
        )
        versao: str = field(
            metadata={
                "name": "Versao",
                "type": "Attribute",
                "pattern": r"[0-9]{1,3}",
            }
        )
