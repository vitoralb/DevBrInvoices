from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from core.esocial.schemas.consulta_empregador.xmldsig_core_schema import Signature

__NAMESPACE__ = "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/empregador/v1_0_0"


@dataclass
class TconsultaEventosEmpregador:
    """
    Define o filtro para consulta aos eventos do empregador que não sejam eventos
    de tabela e trabalhistas.
    """

    class Meta:
        name = "TConsultaEventosEmpregador"

    tp_evt: Optional[str] = field(
        default=None,
        metadata={
            "name": "tpEvt",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/empregador/v1_0_0",
            "required": True,
            "length": 6,
        }
    )
    per_apur: Optional[str] = field(
        default=None,
        metadata={
            "name": "perApur",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/empregador/v1_0_0",
            "required": True,
            "min_length": 4,
            "max_length": 7,
        }
    )
class TideEmpregadorTpInsc(Enum):
    """Tipo de empregador.

    1-CNPJ; 2-CPF;
    """

    VALUE_1 = 1
    VALUE_2 = 2
@dataclass
class TideEmpregador:
    """Define a identificação do empregador.

    1-CNPJ; 2-CPF;
    """

    class Meta:
        name = "TIdeEmpregador"

    tp_insc: Optional[TideEmpregadorTpInsc] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/empregador/v1_0_0",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/empregador/v1_0_0",
            "required": True,
            "pattern": r"\d{8,15}",
        }
    )
@dataclass
class ESocial:
    """
    Elemento raiz do eSocial.
    "

    :ivar consulta_identificadores_evts: Elemento de  informacoes
        relativas a consulta de eventos.
    :ivar signature:
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/consulta/identificadores-eventos/empregador/v1_0_0"

    consulta_identificadores_evts: Optional["ESocial.ConsultaIdentificadoresEvts"] = field(
        default=None,
        metadata={
            "name": "consultaIdentificadoresEvts",
            "type": "Element",
            "required": True,
        }
    )
    signature: Optional[Signature] = field(
        default=None,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
        }
    )

    @dataclass
    class ConsultaIdentificadoresEvts:
        """

        "

        :ivar ide_empregador: Identificação do empregador.
        :ivar consulta_evts_empregador: Contém o filtro para consulta
            aos eventos do empregador que não sejam eventos de tabela e
            trabalhistas..
        """
        ide_empregador: Optional[TideEmpregador] = field(
            default=None,
            metadata={
                "name": "ideEmpregador",
                "type": "Element",
                "required": True,
            }
        )
        consulta_evts_empregador: Optional[TconsultaEventosEmpregador] = field(
            default=None,
            metadata={
                "name": "consultaEvtsEmpregador",
                "type": "Element",
                "required": True,
            }
        )