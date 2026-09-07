from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_v02 import (
    TpEvento,
    TpInformacoesLote,
)

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class RetornoInformacoesLote:
    """
    Schema utilizado para RETORNO de Pedidos de Informações de Lote.

    Este Schema XML é utilizado pelo Web Service para informar aos
    prestadores de serviços o resultado do pedido de informações de lote.

    :ivar cabecalho: Cabeçalho do retorno.
    :ivar alerta: Elemento que representa a ocorrência de eventos de
        alerta durante o processamento da mensagem XML.
    :ivar erro: Elemento que representa a ocorrência de eventos de erro
        durante o processamento da mensagem XML.
    """

    class Meta:
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: RetornoInformacoesLote.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
    )
    alerta: list[TpEvento] = field(
        default_factory=list,
        metadata={
            "name": "Alerta",
            "type": "Element",
            "namespace": "",
        },
    )
    erro: list[TpEvento] = field(
        default_factory=list,
        metadata={
            "name": "Erro",
            "type": "Element",
            "namespace": "",
        },
    )

    @dataclass(kw_only=True)
    class Cabecalho:
        """
        :ivar sucesso: Campo indicativo do sucesso do pedido do serviço.
        :ivar informacoes_lote: Informações do lote consultado.
        :ivar versao: Versão do Schema XML utilizado.
        """

        sucesso: bool = field(
            metadata={
                "name": "Sucesso",
                "type": "Element",
                "namespace": "",
            }
        )
        informacoes_lote: None | TpInformacoesLote = field(
            default=None,
            metadata={
                "name": "InformacoesLote",
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
