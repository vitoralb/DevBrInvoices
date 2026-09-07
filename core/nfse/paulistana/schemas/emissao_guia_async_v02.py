from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate

from core.nfse.paulistana.schemas.tipos_nfe_async_v02 import (
    TpEmissaoGuia,
    TpEventoAsync,
    TpInformacoesGuiaAsync,
)
from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpCpfcnpj
from core.nfse.paulistana.schemas.xmldsig_core_schema_v02 import Signature

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class PedidoEmissaoGuiaAsync:
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
    tipo_emissao_guia: TpEmissaoGuia = field(
        metadata={
            "name": "TipoEmissaoGuia",
            "type": "Element",
            "namespace": "",
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
    data_pagamento: XmlDate = field(
        metadata={
            "name": "DataPagamento",
            "type": "Element",
            "namespace": "",
        }
    )
    signature: Signature = field(
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )


@dataclass(kw_only=True)
class RetornoEmissaoGuiaAsync:
    class Meta:
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: RetornoEmissaoGuiaAsync.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
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
        informacoes_guia: None | TpInformacoesGuiaAsync = field(
            default=None,
            metadata={
                "name": "InformacoesGuia",
                "type": "Element",
                "namespace": "",
            },
        )
        versao: str = field(
            metadata={
                "name": "Versao",
                "type": "Attribute",
                "pattern": r"[0-9]{1,3}",
            }
        )
