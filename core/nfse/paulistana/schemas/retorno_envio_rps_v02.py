from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_v02 import (
    TpChaveNfeRps,
    TpEvento,
)

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class RetornoEnvioRps:
    """
    Schema utilizado para RETORNO de Pedidos de Envio de RPS.

    Este Schema XML é utilizado pelo Web Service para informar aos
    prestadores de serviços o resultado do pedido de envio de RPS.

    :ivar cabecalho: Cabeçalho do retorno.
    :ivar alerta: Elemento que representa a ocorrência de eventos de
        alerta durante o processamento da mensagem XML.
    :ivar erro: Elemento que representa a ocorrência de eventos de erro
        durante o processamento da mensagem XML.
    :ivar chave_nfe_rps: Chave da NFS-e e Chave do RPS que esta
        substitui.
    """

    class Meta:
        name = "RetornoEnvioRPS"
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: RetornoEnvioRps.Cabecalho = field(
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
    chave_nfe_rps: None | TpChaveNfeRps = field(
        default=None,
        metadata={
            "name": "ChaveNFeRPS",
            "type": "Element",
            "namespace": "",
        },
    )

    @dataclass(kw_only=True)
    class Cabecalho:
        """
        :ivar sucesso: Campo indicativo do sucesso do pedido do serviço.
        :ivar versao: Versão do Schema XML utilizado.
        """

        sucesso: bool = field(
            metadata={
                "name": "Sucesso",
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
