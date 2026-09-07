from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xsdata.models.datatype import XmlDate

from core.nfse.paulistana.schemas.tipos_nfe_async_v02 import (
    TpEmissaoGuia,
    TpEventoAsync,
)
from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpCpfcnpj

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


class TpConsultaSituacaoGuias(Enum):
    """
    :cvar VALUE_1: Guias pendentes de pagamento
    :cvar VALUE_2: Guias quitadas
    :cvar VALUE_3: Guias canceladas
    :cvar VALUE_4: Guias pendente de emissao
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4


class TpStatusGuiaEnum(Enum):
    """
    :cvar VALUE_0: Normal
    :cvar VALUE_1: Cancelada
    :cvar VALUE_2: Quitada
    :cvar VALUE_3: Aproveitada
    :cvar VALUE_4: Alterada
    :cvar VALUE_5: QuitadaPorRDT
    :cvar VALUE_6: QuitadaPorSubstituicao
    :cvar VALUE_7: QuitadaPorRetificacao
    """

    VALUE_0 = 0
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_6 = 6
    VALUE_7 = 7


@dataclass(kw_only=True)
class PedidoConsultaGuia:
    class Meta:
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cpfcnpjremetente: TpCpfcnpj = field(
        metadata={
            "name": "CPFCNPJRemetente",
            "type": "Element",
            "namespace": "",
        }
    )
    inscricao_prestador: str = field(
        metadata={
            "name": "InscricaoPrestador",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        }
    )
    incidencia: str = field(
        metadata={
            "name": "Incidencia",
            "type": "Element",
            "namespace": "",
            "pattern": r"^((19|20)\d\d)-(0?[1-9]|1[012])$",
        }
    )
    situacao: TpConsultaSituacaoGuias = field(
        metadata={
            "name": "Situacao",
            "type": "Element",
            "namespace": "",
        }
    )
    tipo_emissao: None | TpEmissaoGuia = field(
        default=None,
        metadata={
            "name": "TipoEmissao",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass(kw_only=True)
class TpStatusGuia:
    class Meta:
        name = "tpStatusGuia"

    value: TpStatusGuiaEnum = field()
    nome: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass(kw_only=True)
class TpGuia:
    class Meta:
        name = "tpGuia"

    inscricao_prestador: str = field(
        metadata={
            "name": "InscricaoPrestador",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        }
    )
    numero_guia: None | str = field(
        default=None,
        metadata={
            "name": "NumeroGuia",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    incidencia: str = field(
        metadata={
            "name": "Incidencia",
            "type": "Element",
            "namespace": "",
            "pattern": r"^((19|20)\d\d)-(0?[1-9]|1[012])$",
        }
    )
    valor_total: None | str = field(
        default=None,
        metadata={
            "name": "ValorTotal",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_iss: None | str = field(
        default=None,
        metadata={
            "name": "ValorIss",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_total_pagamento: None | str = field(
        default=None,
        metadata={
            "name": "ValorTotalPagamento",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    status: None | TpStatusGuia = field(
        default=None,
        metadata={
            "name": "Status",
            "type": "Element",
            "namespace": "",
        },
    )
    situacao: TpConsultaSituacaoGuias = field(
        metadata={
            "name": "Situacao",
            "type": "Element",
            "namespace": "",
        }
    )
    referencia: None | TpEmissaoGuia = field(
        default=None,
        metadata={
            "name": "Referencia",
            "type": "Element",
            "namespace": "",
        },
    )
    data_emissao: None | XmlDate = field(
        default=None,
        metadata={
            "name": "DataEmissao",
            "type": "Element",
            "namespace": "",
        },
    )
    data_vencimento: None | XmlDate = field(
        default=None,
        metadata={
            "name": "DataVencimento",
            "type": "Element",
            "namespace": "",
        },
    )
    data_pagamento: None | XmlDate = field(
        default=None,
        metadata={
            "name": "DataPagamento",
            "type": "Element",
            "namespace": "",
        },
    )
    data_quitacao: None | XmlDate = field(
        default=None,
        metadata={
            "name": "DataQuitacao",
            "type": "Element",
            "namespace": "",
        },
    )
    data_cancelamento: None | XmlDate = field(
        default=None,
        metadata={
            "name": "DataCancelamento",
            "type": "Element",
            "namespace": "",
        },
    )
    linha_digitavel: None | str = field(
        default=None,
        metadata={
            "name": "LinhaDigitavel",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass(kw_only=True)
class RetornoConsultaGuia:
    class Meta:
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: RetornoConsultaGuia.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
    )
    guia: list[TpGuia] = field(
        default_factory=list,
        metadata={
            "name": "Guia",
            "type": "Element",
            "namespace": "",
        },
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
class TpGuias:
    class Meta:
        name = "tpGuias"

    guia: list[TpGuia] = field(
        default_factory=list,
        metadata={
            "name": "Guia",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        },
    )
