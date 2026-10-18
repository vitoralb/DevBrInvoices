from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from core.esocial.schemas.solicitacao_download_recibo.xmldsig_core_schema import Signature

__NAMESPACE__ = "http://www.esocial.gov.br/schema/download/solicitacao/nrRecibo/v1_0_0"


class TideEmpregadorTpInsc(Enum):
    """Tipo de empregador.

    1-CNPJ; 2-CPF;
    """

    VALUE_1 = 1
    VALUE_2 = 2
@dataclass
class TsolicitacaoDownloadPorNrRecibo:
    """
    Define os parâmetros para consulta por número de recibo do evento.
    "

    :ivar nr_rec: Número do recibo do evento
    """
    class Meta:
        name = "TSolicitacaoDownloadPorNrRecibo"

    nr_rec: List[str] = field(
        default_factory=list,
        metadata={
            "name": "nrRec",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/nrRecibo/v1_0_0",
            "min_occurs": 1,
            "max_length": 40,
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
            "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/nrRecibo/v1_0_0",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/download/solicitacao/nrRecibo/v1_0_0",
            "required": True,
            "pattern": r"\d{8,15}",
        }
    )
@dataclass
class ESocial:
    """
    Elemento raiz do eSocial.
    "

    :ivar download: Elemento de  informacoes relativas ao download
        cirurgico.
    :ivar signature:
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/download/solicitacao/nrRecibo/v1_0_0"

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
        :ivar solic_download_eventos_por_nr_recibo: Contém os parâmetros
            para consulta por número de recibo do evento.
        """
        ide_empregador: Optional[TideEmpregador] = field(
            default=None,
            metadata={
                "name": "ideEmpregador",
                "type": "Element",
                "required": True,
            }
        )
        solic_download_eventos_por_nr_recibo: Optional[TsolicitacaoDownloadPorNrRecibo] = field(
            default=None,
            metadata={
                "name": "solicDownloadEventosPorNrRecibo",
                "type": "Element",
                "required": True,
            }
        )