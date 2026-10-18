from dataclasses import dataclass, field
from typing import List, Optional
from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0"


@dataclass
class TretornoConsultaIdentificadoresEventos:
    """
    Define os campos de retorno a consulta de eventos.
    "

    :ivar qtde_tot_evts_consulta: Quantidade total de eventos
        encontrados de acordo com o filtro informado. Porém somente os
        50 primeiros serão retornados na tag identificadoresEvts
    :ivar dh_ultimo_evt_retornado: Data/Hora de envio do último evento
        retornado na tag metadadosEvts.
    :ivar identificadores_evts:
    """
    class Meta:
        name = "TRetornoConsultaIdentificadoresEventos"

    qtde_tot_evts_consulta: Optional[int] = field(
        default=None,
        metadata={
            "name": "qtdeTotEvtsConsulta",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0",
            "required": True,
        }
    )
    dh_ultimo_evt_retornado: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "dhUltimoEvtRetornado",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0",
        }
    )
    identificadores_evts: Optional["TretornoConsultaIdentificadoresEventos.IdentificadoresEvts"] = field(
        default=None,
        metadata={
            "name": "identificadoresEvts",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0",
        }
    )

    @dataclass
    class IdentificadoresEvts:
        identificador_evt: List["TretornoConsultaIdentificadoresEventos.IdentificadoresEvts.IdentificadorEvt"] = field(
            default_factory=list,
            metadata={
                "name": "identificadorEvt",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0",
                "min_occurs": 1,
                "max_occurs": 50,
            }
        )

        @dataclass
        class IdentificadorEvt:
            """

            "

            :ivar id: Identificação única do evento. Atributo Id que
                fica na tag evtXXXXX de cada evento.
            :ivar nr_rec: Número do recibo do evento
            """
            id: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0",
                    "required": True,
                }
            )
            nr_rec: Optional[str] = field(
                default=None,
                metadata={
                    "name": "nrRec",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0",
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
            "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0",
            "required": True,
        }
    )
    desc_resposta: Optional[str] = field(
        default=None,
        metadata={
            "name": "descResposta",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0",
            "required": True,
            "max_length": 2048,
        }
    )
@dataclass
class ESocial:
    """
    Elemento raiz do eSocial.
    "

    :ivar retorno_consulta_identificadores_evts: Elemento de
        informacoes relativas ao download.
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/retorno/v1_0_0"

    retorno_consulta_identificadores_evts: Optional["ESocial.RetornoConsultaIdentificadoresEvts"] = field(
        default=None,
        metadata={
            "name": "retornoConsultaIdentificadoresEvts",
            "type": "Element",
            "required": True,
        }
    )

    @dataclass
    class RetornoConsultaIdentificadoresEvts:
        """

        "

        :ivar status: Contém o status da consulta.
        :ivar retorno_identificadores_evts: Contém o retorno da consulta
            aos eventos.
        """
        status: Optional[Tstatus] = field(
            default=None,
            metadata={
                "type": "Element",
                "required": True,
            }
        )
        retorno_identificadores_evts: Optional[TretornoConsultaIdentificadoresEventos] = field(
            default=None,
            metadata={
                "name": "retornoIdentificadoresEvts",
                "type": "Element",
            }
        )