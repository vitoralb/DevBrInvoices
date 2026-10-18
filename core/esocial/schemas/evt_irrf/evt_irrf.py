from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from core.esocial.schemas.evt_irrf.tipos import (
    TsCrdia,
    TsCrmen,
    TIdeEmpregador,
    TIdeEventoRetornoMensal,
)
from core.esocial.schemas.evt_irrf.xmldsig_core_schema import Signature

__NAMESPACE__ = "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00"


class InfoIrrfIndExistInfo(Enum):
    """
    Indicativo de existência de valores de bases ou de tributos.
    "

    :cvar VALUE_1: Há informações de IRRF
    :cvar VALUE_2: Há movimento, porém não há informações de IRRF
    :cvar VALUE_3: Não há movimento no período informado em
        {perApur}(5012_ideEvento_perApur)
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
@dataclass
class ESocial:
    """S-5012 - Imposto de Renda Retido na Fonte Consolidado por Contribuinte"

    :ivar evt_irrf: Evento IRRF Consolidado por Contribuinte.
        DESCRICAO_COMPLETA:Evento Imposto de Renda Retido na Fonte
        Consolidado por Contribuinte. CHAVE_GRUPO: {Id}
    :ivar signature:
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00"

    evt_irrf: Optional["ESocial.EvtIrrf"] = field(
        default=None,
        metadata={
            "name": "evtIrrf",
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
    class EvtIrrf:
        """

        "

        :ivar ide_evento:
        :ivar ide_empregador:
        :ivar info_irrf: Informações relativas ao Imposto de Renda.
        :ivar id:
        """
        ide_evento: Optional[TIdeEventoRetornoMensal] = field(
            default=None,
            metadata={
                "name": "ideEvento",
                "type": "Element",
                "required": True,
            }
        )
        ide_empregador: Optional[TIdeEmpregador] = field(
            default=None,
            metadata={
                "name": "ideEmpregador",
                "type": "Element",
                "required": True,
            }
        )
        info_irrf: Optional["ESocial.EvtIrrf.InfoIrrf"] = field(
            default=None,
            metadata={
                "name": "infoIRRF",
                "type": "Element",
                "required": True,
            }
        )
        id: Optional[str] = field(
            default=None,
            metadata={
                "name": "Id",
                "type": "Attribute",
                "required": True,
                "length": 36,
                "pattern": r"ID\d{34}",
            }
        )

        @dataclass
        class InfoIrrf:
            """

            "

            :ivar nr_rec_arq_base:
            :ivar ind_exist_info:
            :ivar info_crmen: Totalizador do IRRF por CR mensal.
                DESCRICAO_COMPLETA:Informações consolidadas do IRRF, por
                Código de Receita - CR mensal. Evento de origem: S-5002.
                CHAVE_GRUPO: {CRMen} CONDICAO_GRUPO: OC
            :ivar info_crdia: Totalizador do IRRF por CR diário.
                DESCRICAO_COMPLETA:Informações consolidadas do IRRF, por
                Código de Receita - CR diário. Evento de origem: S-5002.
                CHAVE_GRUPO: {perApurDia}, {CRDia} CONDICAO_GRUPO: OC
            """
            nr_rec_arq_base: Optional[str] = field(
                default=None,
                metadata={
                    "name": "nrRecArqBase",
                    "type": "Element",
                    "required": True,
                    "length": 23,
                    "pattern": r"[1]{1}\.\d{1}\.\d{19}",
                }
            )
            ind_exist_info: Optional[InfoIrrfIndExistInfo] = field(
                default=None,
                metadata={
                    "name": "indExistInfo",
                    "type": "Element",
                    "required": True,
                }
            )
            info_crmen: List["ESocial.EvtIrrf.InfoIrrf.InfoCrmen"] = field(
                default_factory=list,
                metadata={
                    "name": "infoCRMen",
                    "type": "Element",
                    "max_occurs": 50,
                }
            )
            info_crdia: List["ESocial.EvtIrrf.InfoIrrf.InfoCrdia"] = field(
                default_factory=list,
                metadata={
                    "name": "infoCRDia",
                    "type": "Element",
                    "max_occurs": 350,
                }
            )

            @dataclass
            class InfoCrmen:
                """

                "

                :ivar crmen:
                :ivar vr_crmen: Valor correspondente ao Código de
                    Receita - CR indicado em {CRMen}(./CRMen).
                """
                crmen: Optional[TsCrmen] = field(
                    default=None,
                    metadata={
                        "name": "CRMen",
                        "type": "Element",
                        "required": True,
                    }
                )
                vr_crmen: Optional[Decimal] = field(
                    default=None,
                    metadata={
                        "name": "vrCRMen",
                        "type": "Element",
                        "required": True,
                        "min_exclusive": Decimal('0'),
                        "max_inclusive": Decimal('999999999999.99'),
                        "total_digits": 14,
                        "fraction_digits": 2,
                    }
                )

            @dataclass
            class InfoCrdia:
                """

                "

                :ivar per_apur_dia: Período de apuração diário do Código
                    de Receita - CR.
                :ivar crdia:
                :ivar vr_crdia: Valor relativo ao Imposto de Renda
                    Retido na Fonte sobre rendimentos do trabalho pagos
                    a residente, para fins fiscais, no exterior.
                """
                per_apur_dia: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "perApurDia",
                        "type": "Element",
                        "required": True,
                        "min_inclusive": "0",
                        "max_inclusive": "31",
                        "pattern": r"\d{1,2}",
                    }
                )
                crdia: Optional[TsCrdia] = field(
                    default=None,
                    metadata={
                        "name": "CRDia",
                        "type": "Element",
                        "required": True,
                    }
                )
                vr_crdia: Optional[Decimal] = field(
                    default=None,
                    metadata={
                        "name": "vrCRDia",
                        "type": "Element",
                        "required": True,
                        "min_exclusive": Decimal('0'),
                        "max_inclusive": Decimal('999999999999.99'),
                        "total_digits": 14,
                        "fraction_digits": 2,
                    }
                )