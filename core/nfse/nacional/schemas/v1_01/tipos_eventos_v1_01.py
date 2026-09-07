from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from core.nfse.nacional.schemas.v1_01.tipos_simples_v1_01 import (
    TsambGeradorEvt,
    TscodigoEventoNfse,
    TscodJustAnaliseFiscalCanc,
    TscodJustAnaliseFiscalCancDef,
    TscodJustAnaliseFiscalCancIndef,
    TscodJustCanc,
    TscodJustSubst,
    TscodMotivoRejeicao,
    TstipoAmbiente,
)
from core.nfse.nacional.schemas.v1_01.xmldsig_core_schema import Signature

__NAMESPACE__ = "http://www.sped.fazenda.gov.br/nfse"


class Te101101XDesc(Enum):
    CANCELAMENTO_DE_NFS_E = "Cancelamento de NFS-e"


class Te101103XDesc(Enum):
    SOLICITA_O_DE_AN_LISE_FISCAL_PARA_CANCELAMENTO_DE_NFS_E = (
        "Solicitação de Análise Fiscal para Cancelamento de NFS-e"
    )


class Te105102XDesc(Enum):
    CANCELAMENTO_DE_NFS_E_POR_SUBSTITUI_O = "Cancelamento de NFS-e por Substituição"


class Te105104XDesc(Enum):
    CANCELAMENTO_DE_NFS_E_DEFERIDO_POR_AN_LISE_FISCAL = (
        "Cancelamento de NFS-e Deferido por Análise Fiscal"
    )


class Te105105XDesc(Enum):
    CANCELAMENTO_DE_NFS_E_INDEFERIDO_POR_AN_LISE_FISCAL = (
        "Cancelamento de NFS-e Indeferido por Análise Fiscal"
    )


class Te202201XDesc(Enum):
    MANIFESTA_O_DE_NFS_E_CONFIRMA_O_DO_PRESTADOR = (
        "Manifestação de NFS-e - Confirmação do Prestador"
    )


class Te202205XDesc(Enum):
    MANIFESTA_O_DE_NFS_E_REJEI_O_DO_PRESTADOR = (
        "Manifestação de NFS-e - Rejeição do Prestador"
    )


class Te203202XDesc(Enum):
    MANIFESTA_O_DE_NFS_E_CONFIRMA_O_DO_TOMADOR = (
        "Manifestação de NFS-e - Confirmação do Tomador"
    )


class Te203206XDesc(Enum):
    MANIFESTA_O_DE_NFS_E_REJEI_O_DO_TOMADOR = (
        "Manifestação de NFS-e - Rejeição do Tomador"
    )


class Te204203XDesc(Enum):
    MANIFESTA_O_DE_NFS_E_CONFIRMA_O_DO_INTERMEDI_RIO = (
        "Manifestação de NFS-e - Confirmação do Intermediário"
    )


class Te204207XDesc(Enum):
    MANIFESTA_O_DE_NFS_E_REJEI_O_DO_INTERMEDI_RIO = (
        "Manifestação de NFS-e - Rejeição do Intermediário"
    )


class Te205204XDesc(Enum):
    MANIFESTA_O_DE_NFS_E_CONFIRMA_O_T_CITA = (
        "Manifestação de NFS-e - Confirmação Tácita"
    )


class Te205208XDesc(Enum):
    MANIFESTA_O_DE_NFS_E_ANULA_O_DA_REJEI_O = (
        "Manifestação de NFS-e - Anulação da Rejeição"
    )


class Te305101XDesc(Enum):
    CANCELAMENTO_DE_NFS_E_POR_OF_CIO = "Cancelamento de NFS-e por Ofício"


class Te305102XDesc(Enum):
    BLOQUEIO_DE_NFS_E_POR_OF_CIO = "Bloqueio de NFS-e por Ofício"


class Te305103XDesc(Enum):
    DESBLOQUEIO_DE_NFS_E_POR_OF_CIO = "Desbloqueio de NFS-e por Ofício"


@dataclass(kw_only=True)
class Te101101:
    """
    :ivar x_desc: Descrição do Evento: Descrição do evento:
        "Cancelamento de NFS-e".
    :ivar c_motivo: Código de justificativa de cancelamento: 1 - Erro na
        Emissão; 2 - Serviço não Prestado; 9 - Outros;
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento
    """

    class Meta:
        name = "TE101101"

    x_desc: Te101101XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    c_motivo: TscodJustCanc = field(
        metadata={
            "name": "cMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_motivo: str = field(
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )


@dataclass(kw_only=True)
class Te101103:
    """
    :ivar x_desc: Descrição do evento: "Solicitação de Análise Fiscal
        para Cancelamento de NFS-e"
    :ivar c_motivo: Código do motivo da solicitação de análise fiscal
        para cancelamento de NFS-e: 1 - Erro na Emissão; 2 - Serviço não
        Prestado; 9 - Outros;
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento
    """

    class Meta:
        name = "TE101103"

    x_desc: Te101103XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    c_motivo: TscodJustAnaliseFiscalCanc = field(
        metadata={
            "name": "cMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_motivo: str = field(
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )


@dataclass(kw_only=True)
class Te105102:
    """
    :ivar x_desc: Descrição do Evento: Descrição do evento:
        "Cancelamento de NFS-e por Substituição".
    :ivar c_motivo: Código de justificativa de cancelamento
        substituição: 01 - Desenquadramento de NFS-e do Simples
        Nacional; 02 - Enquadramento de NFS-e no Simples Nacional; 03 -
        Inclusão Retroativa de Imunidade/Isenção para NFS-e; 04 -
        Exclusão Retroativa de Imunidade/Isenção para NFS-e; 05 -
        Rejeição de NFS-e pelo tomador ou pelo intermediário se
        responsável pelo recolhimento do tributo; 99 - Outros; Obtido do
        campo da DPS "DPS/infDPS/subst/cMotivo"
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento. Obtido do campo da DPS "DPS/infDPS/subst/xMotivo".
    :ivar ch_substituta: Chave de Acesso da NFS-e substituta
    """

    class Meta:
        name = "TE105102"

    x_desc: Te105102XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    c_motivo: TscodJustSubst = field(
        metadata={
            "name": "cMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_motivo: None | str = field(
        default=None,
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    ch_substituta: str = field(
        metadata={
            "name": "chSubstituta",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 50,
            "white_space": "preserve",
            "pattern": r"[0-9]{50}",
        }
    )


@dataclass(kw_only=True)
class Te105104:
    """
    :ivar x_desc: Descrição do evento: "Cancelamento de NFS-e Deferido
        por Análise Fiscal"
    :ivar cpfag_trib: CPF do agente da administração tributária
        municipal que efetuou o deferimento da solicitação de análise
        fiscal para cancelamento de NFS-e.
    :ivar n_proc_adm: Número do processo administrativo municipal
        vinculado à solicitação de análise fiscal para cancelamento de
        NFS-e.
    :ivar c_motivo: Resposta da solicitação de análise fiscal para
        cancelamento de NFS-e: 1 - Cancelamento de NFS-e Deferido.
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento
    """

    class Meta:
        name = "TE105104"

    x_desc: Te105104XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    cpfag_trib: str = field(
        metadata={
            "name": "CPFAgTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        }
    )
    n_proc_adm: None | str = field(
        default=None,
        metadata={
            "name": "nProcAdm",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 30,
            "white_space": "preserve",
            "pattern": r"[0-9]{1,30}",
        },
    )
    c_motivo: TscodJustAnaliseFiscalCancDef = field(
        metadata={
            "name": "cMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_motivo: str = field(
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )


@dataclass(kw_only=True)
class Te105105:
    """
    :ivar x_desc: Descrição do evento: "Cancelamento de NFS-e Indeferido
        por Análise Fiscal".
    :ivar cpfag_trib: CPF do agente da administração tributária
        municipal que efetuou o indeferimento da solicitação de análise
        fiscal para cancelamento de NFS-e.
    :ivar n_proc_adm: Número do processo administrativo municipal
        vinculado à solicitação de análise fiscal para cancelamento de
        NFS-e.
    :ivar c_motivo: Resposta da solicitação de análise fiscal para
        cancelamento de NFS-e: 1 - Cancelamento de NFS-e Indeferido; 2 -
        Cancelamento de NFS-e Indeferido Sem Análise de Mérito.
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento
    """

    class Meta:
        name = "TE105105"

    x_desc: Te105105XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    cpfag_trib: str = field(
        metadata={
            "name": "CPFAgTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        }
    )
    n_proc_adm: None | str = field(
        default=None,
        metadata={
            "name": "nProcAdm",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 30,
            "white_space": "preserve",
            "pattern": r"[0-9]{1,30}",
        },
    )
    c_motivo: TscodJustAnaliseFiscalCancIndef = field(
        metadata={
            "name": "cMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_motivo: str = field(
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )


@dataclass(kw_only=True)
class Te202201:
    """
    :ivar x_desc: Descrição do evento: "Manifestação de NFS-e -
        Confirmação do Prestador".
    """

    class Meta:
        name = "TE202201"

    x_desc: Te202201XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )


@dataclass(kw_only=True)
class Te202205:
    """
    :ivar x_desc: Descrição do evento: "Manifestação de NFS-e - Rejeição
        do Prestador".
    :ivar c_motivo: Motivo da Rejeição da NFS-e: 1 - NFS-e em
        duplicidade; 2 - NFS-e já emitida pelo tomador; 3 - Não
        ocorrência do fato gerador; 4 - Erro quanto a responsabilidade
        tributária; 5 - Erro quanto ao valor do serviço, valor das
        deduções ou serviço prestado ou data do fato gerador; 9 -
        Outros;
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento
    """

    class Meta:
        name = "TE202205"

    x_desc: Te202205XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    c_motivo: TscodMotivoRejeicao = field(
        metadata={
            "name": "cMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_motivo: None | str = field(
        default=None,
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )


@dataclass(kw_only=True)
class Te203202:
    """
    :ivar x_desc: Descrição do evento: "Manifestação de NFS-e -
        Confirmação do Tomador".
    """

    class Meta:
        name = "TE203202"

    x_desc: Te203202XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )


@dataclass(kw_only=True)
class Te203206:
    """
    :ivar x_desc: Descrição do evento: "Manifestação de NFS-e - Rejeição
        do Tomador".
    :ivar c_motivo: Motivo da Rejeição da NFS-e: 1 - NFS-e em
        duplicidade; 2 - NFS-e já emitida pelo tomador; 3 - Não
        ocorrência do fato gerador; 4 - Erro quanto a responsabilidade
        tributária; 5 - Erro quanto ao valor do serviço, valor das
        deduções ou serviço prestado ou data do fato gerador; 9 -
        Outros;
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento
    """

    class Meta:
        name = "TE203206"

    x_desc: Te203206XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    c_motivo: TscodMotivoRejeicao = field(
        metadata={
            "name": "cMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_motivo: None | str = field(
        default=None,
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )


@dataclass(kw_only=True)
class Te204203:
    """
    :ivar x_desc: Descrição do evento: "Manifestação de NFS-e -
        Confirmação do Intermediário".
    """

    class Meta:
        name = "TE204203"

    x_desc: Te204203XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )


@dataclass(kw_only=True)
class Te204207:
    """
    :ivar x_desc: Descrição do evento: "Manifestação de NFS-e - Rejeição
        do Intermediário".
    :ivar c_motivo: Motivo da Rejeição da NFS-e: 1 - NFS-e em
        duplicidade; 2 - NFS-e já emitida pelo tomador; 3 - Não
        ocorrência do fato gerador; 4 - Erro quanto a responsabilidade
        tributária; 5 - Erro quanto ao valor do serviço, valor das
        deduções ou serviço prestado ou data do fato gerador; 9 -
        Outros;
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento
    """

    class Meta:
        name = "TE204207"

    x_desc: Te204207XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    c_motivo: TscodMotivoRejeicao = field(
        metadata={
            "name": "cMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_motivo: None | str = field(
        default=None,
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )


@dataclass(kw_only=True)
class Te205204:
    """
    :ivar x_desc: Descrição do evento: "Manifestação de NFS-e -
        Confirmação Tácita".
    """

    class Meta:
        name = "TE205204"

    x_desc: Te205204XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )


@dataclass(kw_only=True)
class Te205208:
    """
    :ivar x_desc: Descrição do evento: "Manifestação de NFS-e - Anulação
        da Rejeição".
    :ivar cpfag_trib: CPF do agente da administração tributária
        municipal que efetuou o anulação da manifestação de rejeição da
        NFS-e
    :ivar id_ev_manif_rej: Referência ao "id" do Evento de Manifestação
        de NFS-e - Rejeição, que originou o presente evento de anulação
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento
    """

    class Meta:
        name = "TE205208"

    x_desc: Te205208XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    cpfag_trib: str = field(
        metadata={
            "name": "CPFAgTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        }
    )
    id_ev_manif_rej: str = field(
        metadata={
            "name": "idEvManifRej",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{59}",
        }
    )
    x_motivo: str = field(
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )


@dataclass(kw_only=True)
class Te305101:
    """
    :ivar x_desc: Descrição do evento: "Cancelamento de NFS-e por
        Ofício"
    :ivar cpfag_trib: CPF do agente da administração tributária
        municipal que efetuou o cancelamento por ofício de NFS-e
    :ivar n_proc_adm: Número do processo administrativo municipal
        vinculado ao cancelamento de NFS-e por ofício
    :ivar x_proc_adm: Descrição para explicitar o motivo do processo
        administrativo municipal indicado neste evento
    """

    class Meta:
        name = "TE305101"

    x_desc: Te305101XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    cpfag_trib: str = field(
        metadata={
            "name": "CPFAgTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        }
    )
    n_proc_adm: str = field(
        metadata={
            "name": "nProcAdm",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 30,
            "white_space": "preserve",
            "pattern": r"[0-9]{1,30}",
        }
    )
    x_proc_adm: str = field(
        metadata={
            "name": "xProcAdm",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )


@dataclass(kw_only=True)
class Te305102:
    """
    :ivar x_desc: Descrição do evento: "Bloqueio de NFS-e por Ofício".
    :ivar cpfag_trib: CPF do agente da administração tributária
        municipal que efetuou o bloqueio de NFS-e por ofício
    :ivar cod_evento: Eventos que podem ser escolhidos pelo município
        emissor para serem rejeitados após emissão e vinculação do
        evento de bloqueio por ofício em uma NFS-e: e101101 -
        Cancelamento de NFS-e; e105102 - Cancelamento de NFS-e por
        Substituição; e105104 - Cancelamento de NFS-e Deferido por
        Análise Fiscal; e105105 - Cancelamento de NFS-e Indeferido por
        Análise Fiscal; e305101 - Cancelamento de NFS-e por Ofício;
    :ivar x_motivo: Descrição para explicitar o motivo indicado neste
        evento
    """

    class Meta:
        name = "TE305102"

    x_desc: Te305102XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    cpfag_trib: str = field(
        metadata={
            "name": "CPFAgTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        }
    )
    cod_evento: TscodigoEventoNfse = field(
        metadata={
            "name": "codEvento",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_motivo: str = field(
        metadata={
            "name": "xMotivo",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 15,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )


@dataclass(kw_only=True)
class Te305103:
    """
    :ivar x_desc: Descrição do evento: "Desbloqueio de NFS-e por
        Ofício".
    :ivar cpfag_trib: CPF do agente da administração tributária
        municipal que efetuou o desbloqueio de NFS-e por ofício
    :ivar id_bloq_ofic: Referência ao "id" do "Bloqueio de ofício" que
        originou o presente evento de desbloqueio
    """

    class Meta:
        name = "TE305103"

    x_desc: Te305103XDesc = field(
        metadata={
            "name": "xDesc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
        }
    )
    cpfag_trib: str = field(
        metadata={
            "name": "CPFAgTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        }
    )
    id_bloq_ofic: str = field(
        metadata={
            "name": "idBloqOfic",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{59}",
        }
    )


@dataclass(kw_only=True)
class TcinfPedReg:
    """
    :ivar tp_amb: Tipo de ambiente: 1 - Produção; 2 - Homologação;
    :ivar ver_aplic: Versão do aplicativo que gerou o pedido de registro
        de evento
    :ivar dh_evento: Data e hora do evento no formato AAAA-MM-
        DDThh:mm:ssTZD (UTC - Universal Coordinated Time, onde TZD pode
        ser -02:00 (Fernando de Noronha), -03:00 (Brasília) ou -04:00
        (Manaus), no horário de verão serão -01:00, -02:00 e -03:00.
        Ex.: 2010-08-19T13:00:15-03:00.
    :ivar cnpjautor: Número de inscrição federal (CNPJ) do autor do
        evento. CNPJ do autor do evento (parte interessada ou pessoa que
        figure na NFS-e. O autor do evento não é o procurador)
    :ivar cpfautor: Número de inscrição federal (CPF) do autor do
        evento. CPF do autor do evento (parte interessada ou pessoa que
        figure na NFS-e como prestador, tomador, intermediário. O autor
        do evento poderá ser o procurador)
    :ivar ch_nfse: Identificador da NFS-e à qual o evento será vinculado
    :ivar e101101: Evento de cancelamento
    :ivar e105102: Evento de cancelamento por substituição
    :ivar e101103: Solicitação de Análise Fiscal para Cancelamento de
        NFS-e
    :ivar e105104: Cancelamento de NFS-e Deferido por Análise Fiscal
    :ivar e105105: Cancelamento de NFS-e Indeferido por Análise Fiscal
    :ivar e202201: Confirmação do Prestador
    :ivar e203202: Confirmação do Tomador
    :ivar e204203: Confirmação do Intermediário
    :ivar e205204: Confirmação Tácita
    :ivar e202205: Rejeição do Prestador
    :ivar e203206: Rejeição do Tomador
    :ivar e204207: Rejeição do Intermediário
    :ivar e205208: Anulação da Rejeição
    :ivar e305101: Cancelamento de NFS-e por Ofício
    :ivar e305102: Bloqueio de NFS-e por Ofício
    :ivar e305103: Desbloqueio de NFS-e por Ofício
    :ivar id:
    """

    class Meta:
        name = "TCInfPedReg"

    tp_amb: TstipoAmbiente = field(
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    ver_aplic: str = field(
        metadata={
            "name": "verAplic",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 20,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    dh_evento: str = field(
        metadata={
            "name": "dhEvento",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"(((20(([02468][048])|([13579][26]))-02-29))|(20[0-9][0-9])-((((0[1-9])|(1[0-2]))-((0[1-9])|(1\d)|(2[0-8])))|((((0[13578])|(1[02]))-31)|(((0[1,3-9])|(1[0-2]))-(29|30)))))T(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d([\-,\+](0[0-9]|10|11):00|([\+](12):00))",
        }
    )
    cnpjautor: None | str = field(
        default=None,
        metadata={
            "name": "CNPJAutor",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 14,
            "white_space": "preserve",
            "pattern": r"[0-9]{14}",
        },
    )
    cpfautor: None | str = field(
        default=None,
        metadata={
            "name": "CPFAutor",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        },
    )
    ch_nfse: str = field(
        metadata={
            "name": "chNFSe",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 50,
            "white_space": "preserve",
            "pattern": r"[0-9]{50}",
        }
    )
    e101101: None | Te101101 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e105102: None | Te105102 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e101103: None | Te101103 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e105104: None | Te105104 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e105105: None | Te105105 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e202201: None | Te202201 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e203202: None | Te203202 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e204203: None | Te204203 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e205204: None | Te205204 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e202205: None | Te202205 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e203206: None | Te203206 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e204207: None | Te204207 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e205208: None | Te205208 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e305101: None | Te305101 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e305102: None | Te305102 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    e305103: None | Te305103 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    id: str = field(
        metadata={
            "name": "Id",
            "type": "Attribute",
            "max_length": 59,
            "white_space": "preserve",
            "pattern": r"PRE[0-9]{56}",
        }
    )


@dataclass(kw_only=True)
class TcpedRegEvt:
    class Meta:
        name = "TCPedRegEvt"

    inf_ped_reg: TcinfPedReg = field(
        metadata={
            "name": "infPedReg",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    signature: None | Signature = field(
        default=None,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        },
    )
    versao: str = field(
        metadata={
            "type": "Attribute",
            "max_length": 4,
            "white_space": "preserve",
            "pattern": r"1\.00|1\.01",
        }
    )


@dataclass(kw_only=True)
class TcinfEvento:
    """
    :ivar ver_aplic: Versão do aplicativo que gerou o evento
    :ivar amb_ger: Ambiente gerador do evento: 1 - Sistema próprio do
        município; 2 - Sefin Nacional NFS-e; 3 - ADN NFS-e;
    :ivar n_seq_evento: Número sequencial do evento para o mesmo tipo de
        evento. Para os eventos que ocorrem somente uma vez, como é o
        caso do cancelamento, o nSeqEvento = 001. Para os eventos que
        possam existir mais de um evento do mesmo tipo o ambiente
        gerador deverá numerar de forma sequencial.
    :ivar dh_proc: Data/Hora do registro do evento. Data e hora no
        formato UTC (Universal Coordinated Time): AAAA-MM-DDThh:mm:ssTZD
    :ivar n_dfse: Número sequencial do documento gerado por ambiente
        gerador de DFSe do município
    :ivar ped_reg_evento: Leiaute do pedido de registro do evento gerado
        pelo autor do evento
    :ivar id:
    """

    class Meta:
        name = "TCInfEvento"

    ver_aplic: str = field(
        metadata={
            "name": "verAplic",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 20,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    amb_ger: TsambGeradorEvt = field(
        metadata={
            "name": "ambGer",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    n_seq_evento: str = field(
        metadata={
            "name": "nSeqEvento",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 3,
            "white_space": "preserve",
            "pattern": r"[0-9]{1}[0-9]{0,2}",
        }
    )
    dh_proc: str = field(
        metadata={
            "name": "dhProc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"(((20(([02468][048])|([13579][26]))-02-29))|(20[0-9][0-9])-((((0[1-9])|(1[0-2]))-((0[1-9])|(1\d)|(2[0-8])))|((((0[13578])|(1[02]))-31)|(((0[1,3-9])|(1[0-2]))-(29|30)))))T(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d([\-,\+](0[0-9]|10|11):00|([\+](12):00))",
        }
    )
    n_dfse: str = field(
        metadata={
            "name": "nDFSe",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{1,13}",
        }
    )
    ped_reg_evento: TcpedRegEvt = field(
        metadata={
            "name": "pedRegEvento",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    id: str = field(
        metadata={
            "name": "Id",
            "type": "Attribute",
            "max_length": 62,
            "white_space": "preserve",
            "pattern": r"EVT[0-9]{59}",
        }
    )


@dataclass(kw_only=True)
class Tcevento:
    class Meta:
        name = "TCEvento"

    inf_evento: TcinfEvento = field(
        metadata={
            "name": "infEvento",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    signature: Signature = field(
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )
    versao: str = field(
        metadata={
            "type": "Attribute",
            "max_length": 4,
            "white_space": "preserve",
            "pattern": r"1\.00|1\.01",
        }
    )
