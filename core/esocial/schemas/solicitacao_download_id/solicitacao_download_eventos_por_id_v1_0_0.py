from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from core.esocial.schemas.solicitacao_download_id.xmldsig_core_schema import Signature

__NAMESPACE__ = "http://www.esocial.gov.br/schema/download/solicitacao/id/v1_0_0"


class TideEmpregadorTpInsc(Enum):
    """Tipo de empregador.

    1-CNPJ; 2-CPF;
    """

    VALUE_1 = 1
    VALUE_2 = 2
@dataclass
class TsolicitacaoDownloadPorIdEvento:
    """
    Define os parâmetros para consulta por Id do evento.
    "

    :ivar id: Identificação única do evento. Atributo Id que fica na tag
        evtXXXXX de cada evento.
    """
    class Meta:
        name = "TSolicitacaoDownloadPorIdEvento"

    id: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/id/v1_0_0",
            "min_occurs": 1,
        }
    )
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
            "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/id/v1_0_0",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/id/v1_0_0",
            "required": True,
            "pattern": r"\d{8,15}",
        }
    )
@dataclass
class ESocial:
    """
    Elemento raiz do eSocial.
    "

    :ivar download: Elemento de  informacoes relativas ao download.
    :ivar signature:
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/download/solicitacao/id/v1_0_0"

    download: Optional["ESocial.Download"] = field(
        default=None,
        metadata={
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
    class Download:
        """

        "

        :ivar ide_empregador: Identificação do empregador.
        :ivar solic_download_evts_por_id: Contém  os parâmetros para
            solicitar download por Id do evento.
        """
        ide_empregador: Optional[TideEmpregador] = field(
            default=None,
            metadata={
                "name": "ideEmpregador",
                "type": "Element",
                "required": True,
            }
        )
        solic_download_evts_por_id: Optional[TsolicitacaoDownloadPorIdEvento] = field(
            default=None,
            metadata={
                "name": "solicDownloadEvtsPorId",
                "type": "Element",
                "required": True,
            }
        )