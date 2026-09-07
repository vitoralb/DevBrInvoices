from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

from core.nfse.paulistana.schemas_v1.tipos_nfe_async_v01 import (
    TpEventoAsync,
    TpSituacaoLote,
)
from core.nfse.paulistana.schemas_v1.tipos_nfe_v01 import TpCpfcnpj

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class PedidoConsultaSituacaoLote:
    """
    :ivar cpfcnpjremetente: Informe o CPF/CNPJ do Remetente autorizado a
        transmitir a mensagem XML.
    :ivar numero_protocolo: Número do protocolo do lote.
    """

    class Meta:
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cpfcnpjremetente: TpCpfcnpj = field(
        metadata={
            "name": "CPFCNPJRemetente",
            "type": "Element",
            "namespace": "",
        }
    )
    numero_protocolo: str = field(
        metadata={
            "name": "NumeroProtocolo",
            "type": "Element",
            "namespace": "",
            "min_length": 32,
            "max_length": 32,
            "white_space": "collapse",
        }
    )


@dataclass(kw_only=True)
class RetornoConsultaSituacaoLote:
    """
    :ivar sucesso: Campo indicativo do sucesso do pedido do serviço.
    :ivar situacao:
    :ivar numero_lote: Número do lote após processamento.
    :ivar data_recebimento:
    :ivar data_processamento:
    :ivar resultado_operacao:
    :ivar erro: Elemento que representa a ocorrência de eventos de erro
        durante o processamento da mensagem XML.
    """

    class Meta:
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    sucesso: bool = field(
        metadata={
            "name": "Sucesso",
            "type": "Element",
            "namespace": "",
        }
    )
    situacao: RetornoConsultaSituacaoLote.Situacao = field(
        metadata={
            "name": "Situacao",
            "type": "Element",
            "namespace": "",
        }
    )
    numero_lote: None | str = field(
        default=None,
        metadata={
            "name": "NumeroLote",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    data_recebimento: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "DataRecebimento",
            "type": "Element",
            "namespace": "",
        },
    )
    data_processamento: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "DataProcessamento",
            "type": "Element",
            "namespace": "",
        },
    )
    resultado_operacao: None | str = field(
        default=None,
        metadata={
            "name": "ResultadoOperacao",
            "type": "Element",
            "namespace": "",
        },
    )
    erro: list[TpEventoAsync] = field(
        default_factory=list,
        metadata={
            "name": "Erro",
            "type": "Element",
            "namespace": "",
        },
    )

    @dataclass(kw_only=True)
    class Situacao:
        value: int = field()
        nome: None | TpSituacaoLote = field(
            default=None,
            metadata={
                "type": "Attribute",
            },
        )
