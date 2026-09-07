from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_v02 import (
    TpEvento,
    TpNfe,
)

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class RetornoConsulta:
    """
    Schema utilizado para RETORNO de pedidos de consulta de NFS-e/RPS,
    consultade NFS-e recebidas e consulta de lote.

    Este Schema XML é utilizado pelo Web Service para informar aos
    tomadores e/ou prestadores de serviços o resultado de pedidos de
    consulta de NFS-e/RPS, consultade NFS-e recebidas e consulta de lote.

    :ivar cabecalho: Cabeçalho do retorno.
    :ivar alerta: Elemento que representa a ocorrência de eventos de
        alerta durante o processamento da mensagem XML.
    :ivar erro: Elemento que representa a ocorrência de eventos de erro
        durante o processamento da mensagem XML.
    :ivar nfe: Elemento NFe - Cada item será um NFS-e.
    """

    class Meta:
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: RetornoConsulta.Cabecalho = field(
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
    nfe: list[TpNfe] = field(
        default_factory=list,
        metadata={
            "name": "NFe",
            "type": "Element",
            "namespace": "",
            "max_occurs": 50,
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
