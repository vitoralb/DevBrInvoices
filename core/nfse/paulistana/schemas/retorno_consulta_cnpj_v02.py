from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpEvento

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class RetornoConsultaCnpj:
    """
    Schema utilizado para RETORNO de Pedidos de Consultas de CNPJ.

    Este Schema XML é utilizado pelo Web Service para informar aos
    tomadores e/ou prestadores de serviços quais Inscrições Municipais
    (CCM) estão vinculadas a um determinado CNPJ e se estes CCM emitem
    NFS-e ou não.

    :ivar cabecalho: Cabeçalho do retorno.
    :ivar alerta: Elemento que representa a ocorrência de eventos de
        alerta durante o processamento da mensagem XML.
    :ivar erro: Elemento que representa a ocorrência de eventos de erro
        durante o processamento da mensagem XML.
    :ivar detalhe:
    """

    class Meta:
        name = "RetornoConsultaCNPJ"
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: RetornoConsultaCnpj.Cabecalho = field(
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
    detalhe: list[RetornoConsultaCnpj.Detalhe] = field(
        default_factory=list,
        metadata={
            "name": "Detalhe",
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

    @dataclass(kw_only=True)
    class Detalhe:
        """
        :ivar inscricao_municipal: Inscrição Municipal vinculada ao CNPJ
            consultado.
        :ivar emite_nfe: Campo que indica se o CCM vinculado ao CNPJ
            consultado emite NFS-e ou não.
        """

        inscricao_municipal: str = field(
            metadata={
                "name": "InscricaoMunicipal",
                "type": "Element",
                "namespace": "",
                "pattern": r"[0-9]{1,12}",
            }
        )
        emite_nfe: bool = field(
            metadata={
                "name": "EmiteNFe",
                "type": "Element",
                "namespace": "",
            }
        )
