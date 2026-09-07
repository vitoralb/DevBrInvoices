from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_v02 import (
    TpChaveNfe,
    TpCpfcnpj,
)
from core.nfse.paulistana.schemas.xmldsig_core_schema_v02 import Signature

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class PedidoCancelamentoNfe:
    """
    Schema utilizado para PEDIDO de Cancelamento de NFS-e.

    Este Schema XML é utilizado pelos Prestadores de serviços cancelarem
    NFS-e emitidas por eles.

    :ivar cabecalho: Cabeçalho do pedido.
    :ivar detalhe: Detalhe do pedido de cancelamento de NFS-e. Cada
        detalhe deverá conter a Chave de uma NFS-e e sua respectiva
        assinatura de cancelamento.
    :ivar signature: Assinatura digital do CNPJ emissor das NFS-e
    """

    class Meta:
        name = "PedidoCancelamentoNFe"
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: PedidoCancelamentoNfe.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
    )
    detalhe: list[PedidoCancelamentoNfe.Detalhe] = field(
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
        :ivar transacao: Informe se as NFS-e a serem canceladas farão
            parte de uma mesma transação. True - As NFS-e só serão
            canceladas se não ocorrer nenhum evento de erro durante o
            processamento de todo o lote; False - As NFS-e aptas a serem
            canceladas serão canceladas, mesmo que ocorram eventos de
            erro durante processamento do cancelamento de outras NFS-e
            deste lote.
        :ivar versao: Informe a Versão do Schema XML utilizado.
        """

        cpfcnpjremetente: TpCpfcnpj = field(
            metadata={
                "name": "CPFCNPJRemetente",
                "type": "Element",
                "namespace": "",
            }
        )
        transacao: bool = field(
            default=True,
            metadata={
                "type": "Element",
                "namespace": "",
            },
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
        """
        :ivar chave_nfe: Chave da NFS-e a ser cancelada.
        :ivar assinatura_cancelamento: Assinatura da NFS-e a ser
            cancelada.
        """

        chave_nfe: TpChaveNfe = field(
            metadata={
                "name": "ChaveNFe",
                "type": "Element",
                "namespace": "",
            }
        )
        assinatura_cancelamento: bytes = field(
            metadata={
                "name": "AssinaturaCancelamento",
                "type": "Element",
                "namespace": "",
                "format": "base64",
            }
        )
