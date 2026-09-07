from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_async_v02 import (
    TpEventoAsync,
    TpInformacoesLoteAsync,
)

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class RetornoEnvioLoteRpsasync:
    """
    Schema utilizado para RETORNO de Pedidos de Envio de lote de RPS
    Assincrono.

    Este Schema XML é utilizado pelo Web Service para informar aos
    prestadores de serviços o resultado do pedido de envio de lote de RPS
    Assincrono.

    :ivar cabecalho: Cabeçalho do retorno.
    :ivar erro: Elemento que representa a ocorrência de eventos de erro
        durante o processamento da mensagem XML.
    """

    class Meta:
        name = "RetornoEnvioLoteRPSAsync"
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: RetornoEnvioLoteRpsasync.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
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
    class Cabecalho:
        """
        :ivar sucesso: Campo indicativo do sucesso do pedido do serviço.
        :ivar informacoes_lote: Informações sobre o lote processado.
        :ivar versao: Versão do Schema XML utilizado.
        """

        sucesso: bool = field(
            metadata={
                "name": "Sucesso",
                "type": "Element",
                "namespace": "",
            }
        )
        informacoes_lote: None | TpInformacoesLoteAsync = field(
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
