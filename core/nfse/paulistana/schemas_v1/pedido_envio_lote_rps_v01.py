from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate

from core.nfse.paulistana.schemas_v1.tipos_nfe_v01 import (
    TpCpfcnpj,
    TpRps,
)
from core.nfse.paulistana.schemas_v1.xmldsig_core_schema_v01 import Signature

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class PedidoEnvioLoteRps:
    """
    Schema utilizado para PEDIDO de envio de lote de RPS.

    Este Schema XML é utilizado pelos prestadores de serviços para
    substituição em lote de RPS por NFS-e.

    :ivar cabecalho: Cabeçalho do pedido.
    :ivar rps: Informe os RPS a serem substituidos por NFS-e.
    :ivar signature: Assinatura digital do contribuinte que gerou os RPS
        contidos na mensagem XML.
    """

    class Meta:
        name = "PedidoEnvioLoteRPS"
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: PedidoEnvioLoteRps.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
    )
    rps: list[TpRps] = field(
        default_factory=list,
        metadata={
            "name": "RPS",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
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
        :ivar transacao: Informe se os RPS a serem substituídos por
            NFS-e farão parte de uma mesma transação. True - Os RPS só
            serão substituídos por NFS-e se não ocorrer nenhum evento de
            erro durante o processamento de todo o lote; False - Os RPS
            válidos serão substituídos por NFS-e, mesmo que ocorram
            eventos de erro durante processamento de outros RPS deste
            lote.
        :ivar dt_inicio: Informe a data de início do período transmitido
            (AAAA-MM-DD).
        :ivar dt_fim: Informe a data final do período transmitido (AAAA-
            MM-DD).
        :ivar qtd_rps: Informe o total de RPS contidos na mensagem XML.
        :ivar valor_total_servicos: Informe o valor total dos serviços
            prestados dos RPS contidos na mensagem XML.
        :ivar valor_total_deducoes: Informe o valor total das deduções
            dos RPS contidos na mensagem XML.
        :ivar versao: Informe a Versão do Schema XML utilizado.
        """

        cpfcnpjremetente: TpCpfcnpj = field(
            metadata={
                "name": "CPFCNPJRemetente",
                "type": "Element",
                "namespace": "",
            }
        )
        transacao: None | bool = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "",
            },
        )
        dt_inicio: XmlDate = field(
            metadata={
                "name": "dtInicio",
                "type": "Element",
                "namespace": "",
            }
        )
        dt_fim: XmlDate = field(
            metadata={
                "name": "dtFim",
                "type": "Element",
                "namespace": "",
            }
        )
        qtd_rps: str = field(
            metadata={
                "name": "QtdRPS",
                "type": "Element",
                "namespace": "",
                "pattern": r"[0-9]{1,15}",
            }
        )
        valor_total_servicos: str = field(
            metadata={
                "name": "ValorTotalServicos",
                "type": "Element",
                "namespace": "",
                "min_inclusive": "0",
                "total_digits": 15,
                "fraction_digits": 2,
                "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
            }
        )
        valor_total_deducoes: None | str = field(
            default=None,
            metadata={
                "name": "ValorTotalDeducoes",
                "type": "Element",
                "namespace": "",
                "min_inclusive": "0",
                "total_digits": 15,
                "fraction_digits": 2,
                "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
            },
        )
        versao: str = field(
            init=False,
            default="1",
            metadata={
                "name": "Versao",
                "type": "Attribute",
                "required": True,
                "pattern": r"[0-9]{1,3}",
            },
        )
