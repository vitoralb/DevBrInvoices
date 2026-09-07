from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpCpfcnpj
from core.nfse.paulistana.schemas.xmldsig_core_schema_v02 import Signature

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class PedidoConsultaCnpj:
    """
    Schema utilizado para PEDIDO de consultas de CNPJ.

    Este Schema XML é utilizado pelos tomadores e/ou prestadores de
    serviços consultarem quais Inscrições Municipais (CCM) estão vinculadas
    a um determinado CNPJ e se estes CCM emitem NFS-e ou não.

    :ivar cabecalho: Cabeçalho do pedido.
    :ivar cnpjcontribuinte: Informe o CNPJ do Contribuinte que se deseja
        consultar.
    :ivar signature: Assinatura digital do CNPJ tomador/prestador que
        gerou a mensagem XML.
    """

    class Meta:
        name = "PedidoConsultaCNPJ"
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: PedidoConsultaCnpj.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
    )
    cnpjcontribuinte: TpCpfcnpj = field(
        metadata={
            "name": "CNPJContribuinte",
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
