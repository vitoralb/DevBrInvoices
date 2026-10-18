from dataclasses import dataclass, field
from typing import List, Optional

__NAMESPACE__ = "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0"


@dataclass
class TeventoeSocial:
    """
    Define os dados de um arquivo do eSocial (evento).
    "

    :ivar any_element: Contém o xml do evento.
    :ivar id: Identificação única do evento. Atributo Id que fica na tag
        evtXXXXX de cada evento.
    """
    class Meta:
        name = "TEventoeSocial"

    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "process_contents": "skip",
        }
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
            "required": True,
        }
    )
@dataclass
class TreciboeSocial:
    """
    Define os dados de um arquivo do eSocial (recibo).
    "

    :ivar any_element: Contém o xml do evento.
    :ivar nr_rec: Número do recibo do evento
    """
    class Meta:
        name = "TReciboeSocial"

    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "process_contents": "skip",
        }
    )
    nr_rec: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRec",
            "type": "Attribute",
            "required": True,
            "max_length": 40,
        }
    )
@dataclass
class Tstatus:
    """
    Contém o status da solicitação realizada.
    "

    :ivar cd_resposta: Código de resposta da solicitação realizada.
    :ivar desc_resposta: Contém a descrição correspondente ao código de
        resposta.
    """
    class Meta:
        name = "TStatus"

    cd_resposta: Optional[int] = field(
        default=None,
        metadata={
            "name": "cdResposta",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0",
            "required": True,
        }
    )
    desc_resposta: Optional[str] = field(
        default=None,
        metadata={
            "name": "descResposta",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0",
            "required": True,
            "max_length": 2048,
        }
    )
@dataclass
class TretornoSolicitacaoDownloadEvento:
    """
    Define os campos de retorno a solicitação de download de eventos.
    """

    class Meta:
        name = "TRetornoSolicitacaoDownloadEvento"

    arquivos: Optional["TretornoSolicitacaoDownloadEvento.Arquivos"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0",
            "required": True,
        }
    )

    @dataclass
    class Arquivos:
        arquivo: List["TretornoSolicitacaoDownloadEvento.Arquivos.Arquivo"] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0",
                "min_occurs": 1,
                "max_occurs": 50,
            }
        )

        @dataclass
        class Arquivo:
            """

            "

            :ivar status: Contém o status para o arquivo.
            :ivar evt: Identificação única do evento. Atributo Id que
                fica na tag evtXXXXX de cada evento.
            :ivar rec: Número do recibo do evento
            """
            status: Optional[Tstatus] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0",
                    "required": True,
                }
            )
            evt: Optional[TeventoeSocial] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0",
                }
            )
            rec: Optional[TreciboeSocial] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0",
                }
            )
@dataclass
class ESocial:
    """
    Elemento raiz do eSocial.
    "

    :ivar download: Elemento de  informacoes relativas ao download
        cirurgico.
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/download/solicitacao/retorno/v1_0_0"

    download: Optional["ESocial.Download"] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
        }
    )

    @dataclass
    class Download:
        """

        "

        :ivar status: Contém o status da solicitação.
        :ivar retorno_solic_download_evts: Contém o retorno da
            solicitação de download dos eventos.
        """
        status: Optional[Tstatus] = field(
            default=None,
            metadata={
                "type": "Element",
                "required": True,
            }
        )
        retorno_solic_download_evts: Optional[TretornoSolicitacaoDownloadEvento] = field(
            default=None,
            metadata={
                "name": "retornoSolicDownloadEvts",
                "type": "Element",
            }
        )