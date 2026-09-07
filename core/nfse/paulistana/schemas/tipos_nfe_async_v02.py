from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe/tipos"


class TpEmissaoGuia(Enum):
    """
    :cvar VALUE_1: Guia de NFS-e emitidas
    :cvar VALUE_2: Guia de NFS-e recebidas (exceto rejeitadas)
    :cvar VALUE_3: Guia de NFS-e Emitidas e Recebidas (exceto
        rejeitadas)
    :cvar VALUE_4: Guia de NFS-e recebidas aceitas
    :cvar VALUE_5: Guia de NFS-e recebidas sem manifestação do tomador
    :cvar VALUE_6: Guia de NFS-e recebidas rejeitadas
    :cvar VALUE_7: Guia de NFTS emitidas
    :cvar VALUE_8: Todas (NFS-e emitidas, NFTS emitidas e NFS-e
        recebidas, exceto rejeitadas)
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_6 = 6
    VALUE_7 = 7
    VALUE_8 = 8


@dataclass(kw_only=True)
class TpEventoAsync:
    """
    :ivar codigo: Código do evento.
    :ivar descricao: Descrição do evento.
    """

    class Meta:
        name = "tpEventoAsync"

    codigo: str = field(
        metadata={
            "name": "Codigo",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{3,4}",
        }
    )
    descricao: None | str = field(
        default=None,
        metadata={
            "name": "Descricao",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 300,
            "white_space": "collapse",
        },
    )


@dataclass(kw_only=True)
class TpInformacoesGuiaAsync:
    class Meta:
        name = "tpInformacoesGuiaAsync"

    numero_protocolo: str = field(
        metadata={
            "name": "NumeroProtocolo",
            "type": "Element",
            "namespace": "",
            "min_length": 32,
            "max_length": 32,
            "white_space": "collapse",
        }
    )
    data_recebimento: XmlDateTime = field(
        metadata={
            "name": "DataRecebimento",
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass(kw_only=True)
class TpInformacoesLoteAsync:
    """
    Informações do lote processado.

    :ivar numero_protocolo: Número do protocolo do lote.
    :ivar data_recebimento: Data/hora de envio do lote.
    """

    class Meta:
        name = "tpInformacoesLoteAsync"

    numero_protocolo: str = field(
        metadata={
            "name": "NumeroProtocolo",
            "type": "Element",
            "namespace": "",
            "min_length": 32,
            "max_length": 32,
            "white_space": "collapse",
        }
    )
    data_recebimento: XmlDateTime = field(
        metadata={
            "name": "DataRecebimento",
            "type": "Element",
            "namespace": "",
        }
    )


class TpSituacaoGuia(Enum):
    """
    Tipo referente as possíveis situações da emissão de guia assíncrona.

    :cvar SOLICITADA: Emissao solicitada (0).
    :cvar INVALIDADA: Emissao invalidada (1).
    :cvar VERIFICADA: Emissao verificada (2).
    :cvar PROCESSADA: Emissao processada (3).
    """

    SOLICITADA = "solicitada"
    INVALIDADA = "invalidada"
    VERIFICADA = "verificada"
    PROCESSADA = "processada"


class TpSituacaoLote(Enum):
    """
    Tipo referente as possíveis situações do lote assíncrono.

    :cvar ENVIADO: Lote enviado (0).
    :cvar INVALIDADO: Lote invalidado (1).
    :cvar VERIFICADO: Lote verificado (2).
    :cvar PROCESSADO: Lote processado (3).
    """

    ENVIADO = "enviado"
    INVALIDADO = "invalidado"
    VERIFICADO = "verificado"
    PROCESSADO = "processado"
