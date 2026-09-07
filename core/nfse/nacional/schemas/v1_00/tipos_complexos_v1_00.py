from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate

from core.nfse.nacional.schemas.v1_00.tipos_simples_v1_00 import (
    TcobjetoLocacao,
    TsambGeradorNfse,
    TscategoriaServico,
    TscategVeic,
    TscodJustSubst,
    TscodNaoNif,
    TsemitenteDps,
    TsenvMdic,
    TsideDedRed,
    TsmecAfcomExPrest,
    TsmecAfcomExToma,
    TsmodoPrestacao,
    TsmovTempBens,
    TsopExigSuspensa,
    TsopSimpNac,
    TsopTipoBm,
    TsprocEmissao,
    TsregEspTrib,
    TsregimeApuracaoSimpNac,
    Tsrodagem,
    Tstat,
    TstipoAmbiente,
    TstipoCst,
    TstipoEmissao,
    TstipoImunidadeIssqn,
    TstipoIndTotTrib,
    TstipoRetIssqn,
    TstipoRetPiscofins,
    TstribIssqn,
    Tsuf,
    TsvincPrest,
)
from core.nfse.nacional.schemas.v1_00.xmldsig_core_schema import Signature

__NAMESPACE__ = "http://www.sped.fazenda.gov.br/nfse"


@dataclass(kw_only=True)
class Tccserv:
    """
    :ivar c_trib_nac: Código de tributação nacional do ISSQN: Regra de
        formação - 6 dígitos numéricos sendo: 2 para Item (LC 116/2003),
        2 para Subitem (LC 116/2003) e 2 para Desdobro Nacional
    :ivar c_trib_mun: Código de tributação municipal do ISSQN
    :ivar x_desc_serv: Descrição completa do serviço prestado
    :ivar c_nbs: Código NBS (Nomenclatura Brasileira de Serviços,
        Intangíveis e outras Operações que produzam Variações no
        Patrimônio) correspondente ao serviço prestado
    :ivar c_int_contrib: Código interno do contribuinte
    """

    class Meta:
        name = "TCCServ"

    c_trib_nac: str = field(
        metadata={
            "name": "cTribNac",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{6}",
        }
    )
    c_trib_mun: None | str = field(
        default=None,
        metadata={
            "name": "cTribMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{3}",
        },
    )
    x_desc_serv: str = field(
        metadata={
            "name": "xDescServ",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 2000,
            "white_space": "preserve",
            "pattern": r"[\s\S!-ÿ]{1}[\s\S -ÿ]{0,}[\s\S!-ÿ]{1}|[\s\S!-ÿ]{1}",
        }
    )
    c_nbs: None | str = field(
        default=None,
        metadata={
            "name": "cNBS",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{9}",
        },
    )
    c_int_contrib: None | str = field(
        default=None,
        metadata={
            "name": "cIntContrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 20,
            "white_space": "preserve",
            "pattern": r"[a-zA-Z0-9]{1,20}",
        },
    )


@dataclass(kw_only=True)
class TcdocNfnfs:
    """
    :ivar n_nfs: Número da Nota Fiscal NF ou NFS
    :ivar mod_nfs: Modelo da Nota Fiscal NF ou NFS
    :ivar serie_nfs: Série Nota Fiscal NF ou NFS
    """

    class Meta:
        name = "TCDocNFNFS"

    n_nfs: str = field(
        metadata={
            "name": "nNFS",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 7,
            "white_space": "preserve",
            "pattern": r"[0-9]{7}",
        }
    )
    mod_nfs: str = field(
        metadata={
            "name": "modNFS",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 15,
            "white_space": "preserve",
            "pattern": r"[0-9]{15}",
        }
    )
    serie_nfs: str = field(
        metadata={
            "name": "serieNFS",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 15,
            "white_space": "preserve",
            "pattern": r"[a-zA-Z0-9]{1,15}",
        }
    )


@dataclass(kw_only=True)
class TcdocOutNfse:
    """
    :ivar c_mun_nfse_mun: Código Município emissor da nota eletrônica
        municipal (Tabela do IBGE)
    :ivar n_nfse_mun: Número da nota eletrônica municipal
    :ivar c_verif_nfse_mun: Código de Verificação da nota eletrônica
        municipal
    """

    class Meta:
        name = "TCDocOutNFSe"

    c_mun_nfse_mun: str = field(
        metadata={
            "name": "cMunNFSeMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{7}",
        }
    )
    n_nfse_mun: str = field(
        metadata={
            "name": "nNFSeMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 15,
            "white_space": "preserve",
            "pattern": r"[0-9]{15}",
        }
    )
    c_verif_nfse_mun: str = field(
        metadata={
            "name": "cVerifNFSeMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 9,
            "white_space": "preserve",
            "pattern": r"[a-zA-Z0-9]{1,9}",
        }
    )


@dataclass(kw_only=True)
class TcenderExt:
    """
    :ivar c_pais: Código do país (Tabela de Países ISO)
    :ivar c_end_post: Código alfanumérico do Endereçamento Postal no
        exterior do prestador do serviço.
    :ivar x_cidade: Nome da cidade no exterior do prestador do serviço.
    :ivar x_est_prov_reg: Estado, província ou região da cidade no
        exterior do prestador do serviço.
    """

    class Meta:
        name = "TCEnderExt"

    c_pais: str = field(
        metadata={
            "name": "cPais",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[A-Z]{2}",
        }
    )
    c_end_post: str = field(
        metadata={
            "name": "cEndPost",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 11,
            "white_space": "preserve",
        }
    )
    x_cidade: str = field(
        metadata={
            "name": "xCidade",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
        }
    )
    x_est_prov_reg: str = field(
        metadata={
            "name": "xEstProvReg",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
        }
    )


@dataclass(kw_only=True)
class TcenderExtSimples:
    """
    :ivar c_end_post: Código alfanumérico do Endereçamento Postal no
        exterior do prestador do serviço.
    :ivar x_cidade: Nome da cidade no exterior do prestador do serviço.
    :ivar x_est_prov_reg: Estado, província ou região da cidade no
        exterior do prestador do serviço.
    """

    class Meta:
        name = "TCEnderExtSimples"

    c_end_post: str = field(
        metadata={
            "name": "cEndPost",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 11,
            "white_space": "preserve",
        }
    )
    x_cidade: str = field(
        metadata={
            "name": "xCidade",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
        }
    )
    x_est_prov_reg: str = field(
        metadata={
            "name": "xEstProvReg",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
        }
    )


@dataclass(kw_only=True)
class TcenderNac:
    """
    :ivar c_mun: Código do município, conforme Tabela do IBGE
    :ivar cep: Número do CEP
    """

    class Meta:
        name = "TCEnderNac"

    c_mun: str = field(
        metadata={
            "name": "cMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{7}",
        }
    )
    cep: str = field(
        metadata={
            "name": "CEP",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{8}",
        }
    )


@dataclass(kw_only=True)
class TcenderObraEvento:
    """
    :ivar c_end_post: Código de endereçamento postal
    :ivar x_lgr: Tipo e nome do logradouro da localização do imóvel
    :ivar nro: Número do imóvel
    :ivar x_cpl: Complemento do endereço
    :ivar x_bairro: Bairro
    :ivar x_cidade: Cidade
    :ivar x_est_prov_reg: Estado, província ou região
    """

    class Meta:
        name = "TCEnderObraEvento"

    c_end_post: str = field(
        metadata={
            "name": "cEndPost",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 11,
            "white_space": "preserve",
        }
    )
    x_lgr: str = field(
        metadata={
            "name": "xLgr",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    nro: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    x_cpl: None | str = field(
        default=None,
        metadata={
            "name": "xCpl",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 156,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    x_bairro: str = field(
        metadata={
            "name": "xBairro",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    x_cidade: str = field(
        metadata={
            "name": "xCidade",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
        }
    )
    x_est_prov_reg: str = field(
        metadata={
            "name": "xEstProvReg",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
        }
    )


@dataclass(kw_only=True)
class TcinfoCompl:
    """
    :ivar id_doc_tec: Identificador de Documento de Responsabilidade
        Técnica: ART, RRT, DRT, Outros.
    :ivar doc_ref: Chave da nota, número identificador da nota, número
        do contrato ou outro identificador de documento emitido pelo
        prestador de serviços, que subsidia a emissão dessa nota pelo
        tomador do serviço ou intermediário (preenchimento obrigatório
        caso a nota esteja sendo emitida pelo Tomador ou intermediário
        do serviço).
    :ivar x_inf_comp: Informações complementares
    """

    class Meta:
        name = "TCInfoCompl"

    id_doc_tec: None | str = field(
        default=None,
        metadata={
            "name": "idDocTec",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 40,
            "white_space": "preserve",
        },
    )
    doc_ref: None | str = field(
        default=None,
        metadata={
            "name": "docRef",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    x_inf_comp: None | str = field(
        default=None,
        metadata={
            "name": "xInfComp",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 2000,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )


@dataclass(kw_only=True)
class TclocPrest:
    """
    :ivar c_loc_prestacao: Código do município onde o serviço foi
        prestado (tabela do IBGE)
    :ivar c_pais_prestacao: Código do país onde o serviço foi prestado
        (Tabela de Países ISO)
    """

    class Meta:
        name = "TCLocPrest"

    c_loc_prestacao: None | str = field(
        default=None,
        metadata={
            "name": "cLocPrestacao",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{7}",
        },
    )
    c_pais_prestacao: None | str = field(
        default=None,
        metadata={
            "name": "cPaisPrestacao",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[A-Z]{2}",
        },
    )


@dataclass(kw_only=True)
class TctribTotalMonet:
    """
    :ivar v_tot_trib_fed: Valor monetário total aproximado dos tributos
        federais (R$).
    :ivar v_tot_trib_est: Valor monetário total aproximado dos tributos
        estaduais (R$).
    :ivar v_tot_trib_mun: Valor monetário total aproximado dos tributos
        municipais (R$).
    """

    class Meta:
        name = "TCTribTotalMonet"

    v_tot_trib_fed: str = field(
        metadata={
            "name": "vTotTribFed",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        }
    )
    v_tot_trib_est: str = field(
        metadata={
            "name": "vTotTribEst",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        }
    )
    v_tot_trib_mun: str = field(
        metadata={
            "name": "vTotTribMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        }
    )


@dataclass(kw_only=True)
class TctribTotalPercent:
    """
    :ivar p_tot_trib_fed: Valor percentual total aproximado dos tributos
        federais (%).
    :ivar p_tot_trib_est: Valor percentual total aproximado dos tributos
        estaduais (%).
    :ivar p_tot_trib_mun: Valor percentual total aproximado dos tributos
        municipais (%).
    """

    class Meta:
        name = "TCTribTotalPercent"

    p_tot_trib_fed: str = field(
        metadata={
            "name": "pTotTribFed",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,2}(\.[0-9]{2})?",
        }
    )
    p_tot_trib_est: str = field(
        metadata={
            "name": "pTotTribEst",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,2}(\.[0-9]{2})?",
        }
    )
    p_tot_trib_mun: str = field(
        metadata={
            "name": "pTotTribMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,2}(\.[0-9]{2})?",
        }
    )


@dataclass(kw_only=True)
class TcvdescCondIncond:
    """
    :ivar v_desc_incond: Valor monetário do desconto incondicionado (R$)
    :ivar v_desc_cond: Valor monetário do desconto condicionado (R$)
    """

    class Meta:
        name = "TCVDescCondIncond"

    v_desc_incond: None | str = field(
        default=None,
        metadata={
            "name": "vDescIncond",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    v_desc_cond: None | str = field(
        default=None,
        metadata={
            "name": "vDescCond",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )


@dataclass(kw_only=True)
class TcvservPrest:
    """
    :ivar v_receb: Valor monetário recebido pelo intermediário do
        serviço (R$)
    :ivar v_serv: Valor dos serviços em R$
    """

    class Meta:
        name = "TCVServPrest"

    v_receb: None | str = field(
        default=None,
        metadata={
            "name": "vReceb",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    v_serv: str = field(
        metadata={
            "name": "vServ",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        }
    )


@dataclass(kw_only=True)
class TcvaloresNfse:
    """
    :ivar v_calc_dr: Valor monetário (R$) de dedução/redução da base de
        cálculo (BC) do ISSQN.
    :ivar tp_bm: Tipo de Benefício Municipal (BM)
    :ivar v_calc_bm: Valor monetário (R$) do percentual de redução da
        base de cálculo (BC) do ISSQN devido a um benefício municipal
        (BM).
    :ivar v_bc: Valor monetário (R$) do percentual de redução da base de
        cálculo (BC) do ISSQN devido a um benefício municipal (BM).
    :ivar p_aliq_aplic: Alíquota aplicada sobre a base de cálculo para
        apuração do ISSQN.
    :ivar v_issqn: Valor do ISSQN (R$) = Valor da Base de Cálculo x
        Alíquota ISSQN = vBC x pAliqAplic
    :ivar v_total_ret: Valor total das retenções de tributos da NFS-e.
        Valor total de retenções (R$) = Σ(vRetCP + vRetIRRF+ vRetCSLL +
        ISSQN*)
    :ivar v_liq: Valor líquido da NFS-e. Valor líquido (R$) = Valor do
        serviço - Desconto condicionado - Desconto incondicionado -
        Valores retidos
    :ivar x_out_inf: Uso da Administração Tributária Municipal.
    """

    class Meta:
        name = "TCValoresNFSe"

    v_calc_dr: None | str = field(
        default=None,
        metadata={
            "name": "vCalcDR",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    tp_bm: None | str = field(
        default=None,
        metadata={
            "name": "tpBM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 40,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    v_calc_bm: None | str = field(
        default=None,
        metadata={
            "name": "vCalcBM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    v_bc: None | str = field(
        default=None,
        metadata={
            "name": "vBC",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    p_aliq_aplic: None | str = field(
        default=None,
        metadata={
            "name": "pAliqAplic",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|[0-9]{1}(\.[0-9]{2})?",
        },
    )
    v_issqn: None | str = field(
        default=None,
        metadata={
            "name": "vISSQN",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    v_total_ret: None | str = field(
        default=None,
        metadata={
            "name": "vTotalRet",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    v_liq: str = field(
        metadata={
            "name": "vLiq",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        }
    )
    x_out_inf: None | str = field(
        default=None,
        metadata={
            "name": "xOutInf",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 2000,
            "white_space": "preserve",
            "pattern": r"[\s\S!-ÿ]{1}[\s\S -ÿ]{0,}[\s\S!-ÿ]{1}|[\s\S!-ÿ]{1}",
        },
    )


@dataclass(kw_only=True)
class TcbeneficioMunicipal:
    """
    :ivar tp_bm: Identificação da Lei parametrizada pelo município que
        define o benefício. Trata-se de um identificador único que foi
        gerado pelo Sistema Nacional no momento em que o município de
        incidência do ISSQN incluiu o benefício no sistema. Tem a
        seguinte regra de formação: 7 dígitos com o código IBGE do
        município + 4 dígitos com número sequencial. Deve ser obtido da
        parametrização do município de incidência do ISSQN.
    :ivar n_bm: Identificador do benefício municipal parametrizado pelo
        município.
    :ivar v_red_bcbm: Valor monetário informado pelo emitente para
        redução da base de cálculo (BC) do ISSQN devido a um Benefício
        Municipal (BM).
    :ivar p_red_bcbm: Valor percentual informado pelo emitente para
        redução da base de cálculo (BC) do ISSQN devido a um Benefício
        Municipal (BM).
    """

    class Meta:
        name = "TCBeneficioMunicipal"

    tp_bm: TsopTipoBm = field(
        metadata={
            "name": "tpBM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    n_bm: str = field(
        metadata={
            "name": "nBM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "pattern": r"[0-9]{14}",
        }
    )
    v_red_bcbm: None | str = field(
        default=None,
        metadata={
            "name": "vRedBCBM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    p_red_bcbm: None | str = field(
        default=None,
        metadata={
            "name": "pRedBCBM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,2}(\.[0-9]{2})?",
        },
    )


@dataclass(kw_only=True)
class TccomExterior:
    """
    :ivar md_prestacao: Modo de Prestação: 0 - Desconhecido (tipo não
        informado na nota de origem); 1 - Transfronteiriço; 2 - Consumo
        no Brasil; 3 - Presença Comercial no Exterior; 4 - Movimento
        Temporário de Pessoas Físicas;
    :ivar vinc_prest: Vínculo entre as partes no negócio: 0 - Sem
        vínculo com o Tomador/Prestador 1 - Controlada; 2 -
        Controladora; 3 - Coligada; 4 - Matriz; 5 - Filial ou sucursal;
        6 - Outro vínculo; 9 - Desconhecido;
    :ivar tp_moeda: Identifica a moeda da transação comercial
    :ivar v_serv_moeda: Valor do serviço prestado expresso em moeda
        estrangeira especificada em tpmoeda
    :ivar mec_afcomex_p: Mecanismo de apoio/fomento ao Comércio Exterior
        utilizado pelo prestador do serviço: 00 - Desconhecido (tipo não
        informado na nota de origem); 01 - Nenhum; 02 - ACC -
        Adiantamento sobre Contrato de Câmbio – Redução a Zero do IR e
        do IOF; 03 - ACE – Adiantamento sobre Cambiais Entregues -
        Redução a Zero do IR e do IOF; 04 - BNDES-Exim Pós-Embarque –
        Serviços; 05 - BNDES-Exim Pré-Embarque - Serviços; 06 - FGE -
        Fundo de Garantia à Exportação; 07 - PROEX - EQUALIZAÇÃO 08 -
        PROEX - Financiamento;
    :ivar mec_afcomex_t: Mecanismo de apoio/fomento ao Comércio Exterior
        utilizado pelo tomador do serviço: 00 - Desconhecido (tipo não
        informado na nota de origem); 01 - Nenhum; 02 - Adm. Pública e
        Repr. Internacional; 03 - Alugueis e Arrend. Mercantil de
        maquinas, equip., embarc. e aeronaves; 04 - Arrendamento
        Mercantil de aeronave para empresa de transporte aéreo público;
        05 - Comissão a agentes externos na exportação; 06 - Despesas de
        armazenagem, mov. e transporte de carga no exterior; 07 -
        Eventos FIFA (subsidiária); 08 - Eventos FIFA; 09 - Fretes,
        arrendamentos de embarcações ou aeronaves e outros; 10 -
        Material Aeronáutico; 11 - Promoção de Bens no Exterior; 12 -
        Promoção de Dest. Turísticos Brasileiros; 13 - Promoção do
        Brasil no Exterior; 14 - Promoção Serviços no Exterior; 15 -
        RECINE; 16 - RECOPA; 17 - Registro e Manutenção de marcas,
        patentes e cultivares; 18 - REICOMP; 19 - REIDI; 20 - REPENEC;
        21 - REPES; 22 - RETAERO; 23 - RETID; 24 - Royalties,
        Assistência Técnica, Científica e Assemelhados; 25 - Serviços de
        avaliação da conformidade vinculados aos Acordos da OMC; 26 -
        ZPE;
    :ivar mov_temp_bens: Operação está vinculada à Movimentação
        Temporária de Bens: 0 - Desconhecido (tipo não informado na nota
        de origem); 1 - Não 2 - Vinculada - Declaração de Importação 3 -
        Vinculada - Declaração de Exportação
    :ivar n_di: Número da Declaração de Importação (DI/DSI/DA/DRI-E)
        averbado
    :ivar n_re: Número do Registro de Exportação (RE) averbado
    :ivar mdic: Compartilhar as informações da NFS-e gerada a partir
        desta DPS com a Secretaria de Comércio Exterior: 0 - Não enviar
        para o MDIC; 1 - Enviar para o MDIC;
    """

    class Meta:
        name = "TCComExterior"

    md_prestacao: TsmodoPrestacao = field(
        metadata={
            "name": "mdPrestacao",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    vinc_prest: TsvincPrest = field(
        metadata={
            "name": "vincPrest",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    tp_moeda: str = field(
        metadata={
            "name": "tpMoeda",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 3,
            "white_space": "preserve",
            "pattern": r"[0-9]{3}",
        }
    )
    v_serv_moeda: str = field(
        metadata={
            "name": "vServMoeda",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        }
    )
    mec_afcomex_p: TsmecAfcomExPrest = field(
        metadata={
            "name": "mecAFComexP",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    mec_afcomex_t: TsmecAfcomExToma = field(
        metadata={
            "name": "mecAFComexT",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    mov_temp_bens: TsmovTempBens = field(
        metadata={
            "name": "movTempBens",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    n_di: None | str = field(
        default=None,
        metadata={
            "name": "nDI",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 12,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    n_re: None | str = field(
        default=None,
        metadata={
            "name": "nRE",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 12,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    mdic: TsenvMdic = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )


@dataclass(kw_only=True)
class Tcendereco:
    """
    :ivar end_nac: Grupo de informações específicas de endereço nacional
    :ivar end_ext: Grupo de informações específicas de endereço no
        exterior
    :ivar x_lgr: Tipo e nome do logradouro da localização do imóvel
    :ivar nro: Número do imóvel
    :ivar x_cpl: Complemento do endereço
    :ivar x_bairro: Bairro
    """

    class Meta:
        name = "TCEndereco"

    end_nac: None | TcenderNac = field(
        default=None,
        metadata={
            "name": "endNac",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    end_ext: None | TcenderExt = field(
        default=None,
        metadata={
            "name": "endExt",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    x_lgr: str = field(
        metadata={
            "name": "xLgr",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    nro: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    x_cpl: None | str = field(
        default=None,
        metadata={
            "name": "xCpl",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 156,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    x_bairro: str = field(
        metadata={
            "name": "xBairro",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )


@dataclass(kw_only=True)
class TcenderecoEmitente:
    """
    :ivar x_lgr: Tipo e nome do logradouro da localização do imóvel
    :ivar nro: Número do imóvel
    :ivar x_cpl: Complemento do endereço
    :ivar x_bairro: Bairro
    :ivar c_mun: Código do município, conforme Tabela do IBGE
    :ivar uf: Sigla da unidade da federação do município do endereço do
        emitente.
    :ivar cep: Número do CEP
    """

    class Meta:
        name = "TCEnderecoEmitente"

    x_lgr: str = field(
        metadata={
            "name": "xLgr",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    nro: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    x_cpl: None | str = field(
        default=None,
        metadata={
            "name": "xCpl",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 156,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    x_bairro: str = field(
        metadata={
            "name": "xBairro",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    c_mun: str = field(
        metadata={
            "name": "cMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{7}",
        }
    )
    uf: Tsuf = field(
        metadata={
            "name": "UF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    cep: str = field(
        metadata={
            "name": "CEP",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{8}",
        }
    )


@dataclass(kw_only=True)
class TcenderecoSimples:
    """
    :ivar cep: Número do CEP
    :ivar end_ext: Grupo de informações específicas de endereço no
        exterior
    :ivar x_lgr: Tipo e nome do logradouro da localização do imóvel
    :ivar nro: Número do imóvel
    :ivar x_cpl: Complemento do endereço
    :ivar x_bairro: Bairro
    """

    class Meta:
        name = "TCEnderecoSimples"

    cep: None | str = field(
        default=None,
        metadata={
            "name": "CEP",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{8}",
        },
    )
    end_ext: None | TcenderExtSimples = field(
        default=None,
        metadata={
            "name": "endExt",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    x_lgr: str = field(
        metadata={
            "name": "xLgr",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    nro: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    x_cpl: None | str = field(
        default=None,
        metadata={
            "name": "xCpl",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 156,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    x_bairro: str = field(
        metadata={
            "name": "xBairro",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 60,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )


@dataclass(kw_only=True)
class TcexigSuspensa:
    """
    :ivar tp_susp: Opção para Exigibilidade Suspensa: 1 - Exigibilidade
        Suspensa por Decisão Judicial; 2 - Exigibilidade Suspensa por
        Processo Administrativo;
    :ivar n_processo: Número do processo judicial ou administrativo de
        suspensão da exigibilidade
    """

    class Meta:
        name = "TCExigSuspensa"

    tp_susp: TsopExigSuspensa = field(
        metadata={
            "name": "tpSusp",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    n_processo: str = field(
        metadata={
            "name": "nProcesso",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "pattern": r"[0-9]{30}",
        }
    )


@dataclass(kw_only=True)
class TcexploracaoRodoviaria:
    """
    :ivar categ_veic: Categorias de veículos para cobrança: 00 -
        Categoria de veículos (tipo não informado na nota de origem) 01
        - Automóvel, caminhonete e furgão; 02 - Caminhão leve, ônibus,
        caminhão trator e furgão; 03 - Automóvel e caminhonete com
        semireboque; 04 - Caminhão, caminhão-trator, caminhão-trator com
        semi-reboque e ônibus; 05 - Automóvel e caminhonete com reboque;
        06 - Caminhão com reboque; 07 - Caminhão trator com semi-
        reboque; 08 - Motocicletas, motonetas e bicicletas motorizadas;
        09 - Veículo especial; 10 - Veículo Isento;
    :ivar n_eixos: Número de eixos para fins de cobrança
    :ivar rodagem: Tipo de rodagem
    :ivar sentido: Placa do veículo
    :ivar placa: Placa do veículo
    :ivar cod_acesso_ped: Código de acesso gerado automaticamente pelo
        sistema emissor da concessionária.
    :ivar cod_contrato: Código de contrato gerado automaticamente pelo
        sistema nacional no cadastro da concessionária.
    """

    class Meta:
        name = "TCExploracaoRodoviaria"

    categ_veic: TscategVeic = field(
        metadata={
            "name": "categVeic",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    n_eixos: str = field(
        metadata={
            "name": "nEixos",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{1,2}",
        }
    )
    rodagem: Tsrodagem = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    sentido: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{1,3}",
        }
    )
    placa: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[A-Z]{2,3}[0-9]{4}|[A-Z]{3,4}[0-9]{3}",
        }
    )
    cod_acesso_ped: str = field(
        metadata={
            "name": "codAcessoPed",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[a-zA-Z0-9]{10}",
        }
    )
    cod_contrato: str = field(
        metadata={
            "name": "codContrato",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[a-zA-Z0-9]{4}",
        }
    )


@dataclass(kw_only=True)
class TclocacaoSublocacao:
    """
    :ivar categ: Categoria do serviço
    :ivar objeto: Tipo de objetos da locação, sublocação, arrendamento,
        direito de passagem ou permissão de uso
    :ivar extensao: Extensão total da ferrovia, rodovia, cabos, dutos ou
        condutos
    :ivar n_postes: Número total de postes
    """

    class Meta:
        name = "TCLocacaoSublocacao"

    categ: TscategoriaServico = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    objeto: TcobjetoLocacao = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    extensao: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 5,
            "white_space": "preserve",
            "pattern": r"[0-9]{1,5}",
        }
    )
    n_postes: str = field(
        metadata={
            "name": "nPostes",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 6,
            "white_space": "preserve",
            "pattern": r"[0-9]{1,6}",
        }
    )


@dataclass(kw_only=True)
class TcregTrib:
    """
    :ivar op_simp_nac: Situação perante o Simples Nacional: 1 - Não
        Optante; 2 - Optante - Microempreendedor Individual (MEI); 3 -
        Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP);
    :ivar reg_ap_trib_sn: Opção para que o contribuinte optante pelo
        Simples Nacional ME/EPP (opSimpNac = 3) possa indicar, ao emitir
        o documento fiscal, em qual regime de apuração os tributos
        federais e municipal estão inseridos, caso tenha ultrapassado
        algum sublimite ou limite definido para o Simples Nacional. 1 –
        Regime de apuração dos tributos federais e municipal pelo SN; 2
        – Regime de apuração dos tributos federais pelo SN e ISSQN  por
        fora do SN conforme respectiva legislação municipal do tributo;
        3 – Regime de apuração dos tributos federais e municipal por
        fora do SN conforme respectivas legislações federal e municipal
        de cada tributo;
    :ivar reg_esp_trib: Tipos de Regimes Especiais de Tributação: 0 -
        Nenhum; 1 - Ato Cooperado (Cooperativa); 2 - Estimativa; 3 -
        Microempresa Municipal; 4 - Notário ou Registrador; 5 -
        Profissional Autônomo; 6 - Sociedade de Profissionais;
    """

    class Meta:
        name = "TCRegTrib"

    op_simp_nac: TsopSimpNac = field(
        metadata={
            "name": "opSimpNac",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    reg_ap_trib_sn: None | TsregimeApuracaoSimpNac = field(
        default=None,
        metadata={
            "name": "regApTribSN",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    reg_esp_trib: TsregEspTrib = field(
        metadata={
            "name": "regEspTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )


@dataclass(kw_only=True)
class Tcsubstituicao:
    """
    :ivar ch_substda: Chave de acesso da NFS-e a ser substituída
    :ivar c_motivo: Código de justificativa para substituição de NFS-e:
        01 - Desenquadramento de NFS-e do Simples Nacional; 02 -
        Enquadramento de NFS-e no Simples Nacional; 03 - Inclusão
        Retroativa de Imunidade/Isenção para NFS-e; 04 - Exclusão
        Retroativa de Imunidade/Isenção para NFS-e; 05 - Rejeição de
        NFS-e pelo tomador ou pelo intermediário se responsável pelo
        recolhimento do tributo; 99 - Outros;
    :ivar x_motivo: Descrição do motivo da substituição da NFS-e
    """

    class Meta:
        name = "TCSubstituicao"

    ch_substda: str = field(
        metadata={
            "name": "chSubstda",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 50,
            "white_space": "preserve",
            "pattern": r"[0-9]{50}",
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


@dataclass(kw_only=True)
class TctribOutrosPisCofins:
    """
    :ivar cst: Código de Situação Tributária do PIS/COFINS (CST): 00 -
        Nenhum; 01 - Operação Tributável com Alíquota Básica; 02 -
        Operação Tributável com Alíquota Diferenciada; 03 - Operação
        Tributável com Alíquota por Unidade de Medida de Produto; 04 -
        Operação Tributável monofásica - Revenda a Alíquota Zero; 05 -
        Operação Tributável por Substituição Tributária; 06 - Operação
        Tributável a Alíquota Zero; 07 - Operação Tributável da
        Contribuição; 08 - Operação sem Incidência da Contribuição; 09 -
        Operação com Suspensão da Contribuição; 49 - Outras Operações de
        Saída; 50 - Operação com Direito a Crédito – Vinculada
        Exclusivamente a Receita Tributada no Mercado Interno; 51 -
        Operação com Direito a Crédito – Vinculada Exclusivamente a
        Receita Não-Tributada no Mercado Interno; 52 - Operação com
        Direito a Crédito – Vinculada Exclusivamente a Receita de
        Exportação; 53 - Operação com Direito a Crédito – Vinculada a
        Receitas Tributadas e Não-Tributadas no Mercado Interno; 54 -
        Operação com Direito a Crédito – Vinculada a Receitas Tributadas
        no Mercado Interno e de Exportação; 55 - Operação com Direito a
        Crédito – Vinculada a Receitas Não Tributadas no Mercado Interno
        e de Exportação; 56 - Operação com Direito a Crédito – Vinculada
        a Receitas Tributadas e Não-Tributadas no Mercado Interno e de
        Exportação; 60 - Crédito Presumido – Operação de Aquisição
        Vinculada Exclusivamente a Receita Tributada no Mercado Interno;
        61 - Crédito Presumido – Operação de Aquisição Vinculada
        Exclusivamente a Receita Não-Tributada no Mercado Interno; 62 -
        Crédito Presumido – Operação de Aquisição Vinculada
        Exclusivamente a Receita de Exportação; 63 - Crédito Presumido –
        Operação de Aquisição Vinculada a Receitas Tributadas e Não-
        Tributadas no Mercado Interno; 64 - Crédito Presumido – Operação
        de Aquisição Vinculada a Receitas Tributadas no Mercado Interno
        e de Exportação; 65 - Crédito Presumido – Operação de Aquisição
        Vinculada a Receitas Não-Tributadas no Mercado Interno e de
        Exportação; 66 - Crédito Presumido – Operação de Aquisição
        Vinculada a Receitas Tributadas e Não-Tributadas no Mercado
        Interno e de Exportação; 67 - Crédito Presumido – Outras
        Operações; 70 - Operação de Aquisição sem Direito a Crédito; 71
        - Operação de Aquisição com Isenção; 72 - Operação de Aquisição
        com Suspensão; 73 - Operação de Aquisição a Alíquota Zero; 74 -
        Operação de Aquisição sem Incidência da Contribuição; 75 -
        Operação de Aquisição por Substituição Tributária; 98 - Outras
        Operações de Entrada; 99 - Outras Operações;
    :ivar v_bcpis_cofins: Valor da Base de Cálculo do PIS/COFINS,
        relativo à apuração própria (R$).
    :ivar p_aliq_pis: Alíquota do PIS, relativa à apuração própria (%).
    :ivar p_aliq_cofins: Alíquota da COFINS, relativa à apuração própria
        (%).
    :ivar v_pis: Valor do débito de PIS apuração própria (R$).
    :ivar v_cofins: Valor do débito de COFINS apuração própria (R$).
    :ivar tp_ret_pis_cofins: Tipo de retenção do PIS/COFINS: 0 -
        PIS/COFINS/CSLL Não Retidos; 1 - PIS/COFINS Retidos; 2 -
        PIS/COFINS Não Retidos; 3 - PIS/COFINS/CSLL Retidos; 4 -
        PIS/COFINS Retidos, CSLL Não Retido; 5 - PIS Retido, COFINS/CSLL
        Não Retido; 6 - COFINS Retido, PIS/CSLL Não Retido; 7 - PIS Não
        Retido, COFINS/CSLL Retidos; 8 - PIS/COFINS Não Retidos, CSLL
        Retido; 9 - COFINS Não Retido, PIS/CSLL Retidos;
    """

    class Meta:
        name = "TCTribOutrosPisCofins"

    cst: TstipoCst = field(
        metadata={
            "name": "CST",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    v_bcpis_cofins: None | str = field(
        default=None,
        metadata={
            "name": "vBCPisCofins",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    p_aliq_pis: None | str = field(
        default=None,
        metadata={
            "name": "pAliqPis",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,1}(\.[0-9]{2})?",
        },
    )
    p_aliq_cofins: None | str = field(
        default=None,
        metadata={
            "name": "pAliqCofins",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,1}(\.[0-9]{2})?",
        },
    )
    v_pis: None | str = field(
        default=None,
        metadata={
            "name": "vPis",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    v_cofins: None | str = field(
        default=None,
        metadata={
            "name": "vCofins",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    tp_ret_pis_cofins: None | TstipoRetPiscofins = field(
        default=None,
        metadata={
            "name": "tpRetPisCofins",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )


@dataclass(kw_only=True)
class TctribTotal:
    """
    :ivar v_tot_trib: Valor monetário total aproximado dos tributos, em
        conformidade com o artigo 1o da Lei no 12.741/2012
    :ivar p_tot_trib: Valor percentual total aproximado dos tributos, em
        conformidade com o artigo 1o da Lei no 12.741/2012
    :ivar ind_tot_trib: Indicador de informação de valor total de
        tributos. Possui valor fixo igual a zero (indTotTrib=0). Não
        informar nenhum valor estimado para os Tributos (Decreto
        8.264/2014). 0 - Não;
    :ivar p_tot_trib_sn: Valor percentual aproximado do total dos
        tributos da alíquota do Simples Nacional (%)
    """

    class Meta:
        name = "TCTribTotal"

    v_tot_trib: None | TctribTotalMonet = field(
        default=None,
        metadata={
            "name": "vTotTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    p_tot_trib: None | TctribTotalPercent = field(
        default=None,
        metadata={
            "name": "pTotTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    ind_tot_trib: None | TstipoIndTotTrib = field(
        default=None,
        metadata={
            "name": "indTotTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    p_tot_trib_sn: None | str = field(
        default=None,
        metadata={
            "name": "pTotTribSN",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,1}(\.[0-9]{2})?",
        },
    )


@dataclass(kw_only=True)
class TcatvEvento:
    """
    :ivar desc: Descrição do evento Artístico, Cultural, Esportivo, etc
    :ivar dt_ini: Data de início da atividade de evento. Ano, Mês e Dia
        (AAAA-MM-DD)
    :ivar dt_fim: Data de fim da atividade de evento. Ano, Mês e Dia
        (AAAA-MM-DD)
    :ivar id: Identificação da Atividade de Evento (código identificador
        de evento determinado pela Administração Tributária Municipal)
    :ivar end: Grupo de informações relativas ao endereço da atividade,
        evento ou local do serviço prestado
    """

    class Meta:
        name = "TCAtvEvento"

    desc: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    dt_ini: XmlDate = field(
        metadata={
            "name": "dtIni",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    dt_fim: XmlDate = field(
        metadata={
            "name": "dtFim",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 30,
            "white_space": "preserve",
        },
    )
    end: None | TcenderecoSimples = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )


@dataclass(kw_only=True)
class Tcemitente:
    """
    :ivar cnpj: Número do CNPJ do emitente da NFS-e.
    :ivar cpf: Número do CPF do emitente da NFS-e.
    :ivar im: Número da inscrição municipal
    :ivar x_nome: Nome / Razão Social do emitente.
    :ivar x_fant: Nome / Fantasia do emitente.
    :ivar ender_nac: Grupo de informações do endereço nacional do
        Emitente da NFS-e
    :ivar fone: Número do telefone do emitente. (Preencher com o Código
        DDD + número do telefone. Nas operações com exterior é permitido
        informar o código do país + código da localidade + número do
        telefone)
    :ivar email: E-mail do emitente.
    """

    class Meta:
        name = "TCEmitente"

    cnpj: None | str = field(
        default=None,
        metadata={
            "name": "CNPJ",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 14,
            "white_space": "preserve",
            "pattern": r"[0-9]{14}",
        },
    )
    cpf: None | str = field(
        default=None,
        metadata={
            "name": "CPF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        },
    )
    im: None | str = field(
        default=None,
        metadata={
            "name": "IM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 15,
            "white_space": "preserve",
        },
    )
    x_nome: str = field(
        metadata={
            "name": "xNome",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 300,
            "white_space": "preserve",
        }
    )
    x_fant: None | str = field(
        default=None,
        metadata={
            "name": "xFant",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 150,
            "white_space": "preserve",
        },
    )
    ender_nac: TcenderecoEmitente = field(
        metadata={
            "name": "enderNac",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    fone: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{6,20}",
        },
    )
    email: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 80,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )


@dataclass(kw_only=True)
class TcinfoObra:
    """
    :ivar c_obra: Número de identificação da obra. Cadastro Nacional de
        Obras (CNO) ou Cadastro Específico do INSS (CEI).
    :ivar insc_imob_fisc: Inscrição imobiliária fiscal (código fornecido
        pela Prefeitura Municipal para a identificação da obra ou para
        fins de recolhimento do IPTU)
    :ivar end: Grupo de informações do endereço da obra do serviço
        prestado
    """

    class Meta:
        name = "TCInfoObra"

    c_obra: None | str = field(
        default=None,
        metadata={
            "name": "cObra",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 30,
            "white_space": "preserve",
        },
    )
    insc_imob_fisc: None | str = field(
        default=None,
        metadata={
            "name": "inscImobFisc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 30,
            "white_space": "preserve",
        },
    )
    end: None | TcenderecoSimples = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )


@dataclass(kw_only=True)
class TcinfoPessoa:
    """
    Informações das pessoas envolvidas na NFS-e.

    Pode ser o tomador, o intermediário ou o fornecedor (dedução/redução).

    :ivar cnpj: Número do CNPJ
    :ivar cpf: Número do CPF
    :ivar nif: Número de Identificação Fiscal fornecido por órgão de
        administração tributária no exterior
    :ivar c_nao_nif: Motivo para não informação do NIF: 0 - Não
        informado na nota de origem; 1 - Dispensado do NIF; 2 - Não
        exigência do NIF;
    :ivar caepf: Número do Cadastro de Atividade Econômica da Pessoa
        Física (CAEPF)
    :ivar im: Número da inscrição municipal
    :ivar x_nome: Nome/Nome Empresarial
    :ivar end: Dados de endereço
    :ivar fone: Número do telefone do prestador: Preencher com o Código
        DDD + número do telefone. Nas operações com exterior é permitido
        informar o código do país + código da localidade + número do
        telefone)
    :ivar email: E-mail
    """

    class Meta:
        name = "TCInfoPessoa"

    cnpj: None | str = field(
        default=None,
        metadata={
            "name": "CNPJ",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 14,
            "white_space": "preserve",
            "pattern": r"[0-9]{14}",
        },
    )
    cpf: None | str = field(
        default=None,
        metadata={
            "name": "CPF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        },
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 40,
            "white_space": "preserve",
        },
    )
    c_nao_nif: None | TscodNaoNif = field(
        default=None,
        metadata={
            "name": "cNaoNIF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    caepf: None | str = field(
        default=None,
        metadata={
            "name": "CAEPF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 14,
            "white_space": "preserve",
            "pattern": r"[0-9]{14}",
        },
    )
    im: None | str = field(
        default=None,
        metadata={
            "name": "IM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 15,
            "white_space": "preserve",
        },
    )
    x_nome: str = field(
        metadata={
            "name": "xNome",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 300,
            "white_space": "preserve",
        }
    )
    end: None | Tcendereco = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    fone: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{6,20}",
        },
    )
    email: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 80,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )


@dataclass(kw_only=True)
class TcinfoPrestador:
    """
    Informações do prestador da NFS-e.

    Difere das demais pessoas por causa das informações de regimes de
    tributação.

    :ivar cnpj: Número do CNPJ
    :ivar cpf: Número do CPF
    :ivar nif: Número de Identificação Fiscal fornecido por órgão de
        administração tributária no exterior
    :ivar c_nao_nif: Motivo para não informação do NIF: 1 - Dispensado
        do NIF; 2 - Não exigência do NIF;
    :ivar caepf: Número do Cadastro de Atividade Econômica da Pessoa
        Física (CAEPF) do prestador do serviço.
    :ivar im: Número da inscrição municipal
    :ivar x_nome: Nome/Nome Empresarial do prestador
    :ivar end: Dados de endereço do prestador
    :ivar fone: Número do telefone do prestador: Preencher com o Código
        DDD + número do telefone. Nas operações com exterior é permitido
        informar o código do país + código da localidade + número do
        telefone)
    :ivar email: E-mail
    :ivar reg_trib: Grupo de informações relativas aos regimes de
        tributação do prestador de serviços
    """

    class Meta:
        name = "TCInfoPrestador"

    cnpj: None | str = field(
        default=None,
        metadata={
            "name": "CNPJ",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 14,
            "white_space": "preserve",
            "pattern": r"[0-9]{14}",
        },
    )
    cpf: None | str = field(
        default=None,
        metadata={
            "name": "CPF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 11,
            "white_space": "preserve",
            "pattern": r"[0-9]{11}",
        },
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 40,
            "white_space": "preserve",
        },
    )
    c_nao_nif: None | TscodNaoNif = field(
        default=None,
        metadata={
            "name": "cNaoNIF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    caepf: None | str = field(
        default=None,
        metadata={
            "name": "CAEPF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 14,
            "white_space": "preserve",
            "pattern": r"[0-9]{14}",
        },
    )
    im: None | str = field(
        default=None,
        metadata={
            "name": "IM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 15,
            "white_space": "preserve",
        },
    )
    x_nome: None | str = field(
        default=None,
        metadata={
            "name": "xNome",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 300,
            "white_space": "preserve",
        },
    )
    end: None | Tcendereco = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    fone: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{6,20}",
        },
    )
    email: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 80,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    reg_trib: TcregTrib = field(
        metadata={
            "name": "regTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )


@dataclass(kw_only=True)
class TctribFederal:
    """
    :ivar piscofins: Grupo de informações dos tributos PIS/COFINS
    :ivar v_ret_cp: Valor monetário do CP(R$).
    :ivar v_ret_irrf: Valor monetário do IRRF (R$).
    :ivar v_ret_csll: Valor monetário do CSLL (R$).
    """

    class Meta:
        name = "TCTribFederal"

    piscofins: None | TctribOutrosPisCofins = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    v_ret_cp: None | str = field(
        default=None,
        metadata={
            "name": "vRetCP",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    v_ret_irrf: None | str = field(
        default=None,
        metadata={
            "name": "vRetIRRF",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    v_ret_csll: None | str = field(
        default=None,
        metadata={
            "name": "vRetCSLL",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )


@dataclass(kw_only=True)
class TctribMunicipal:
    """
    :ivar trib_issqn: Tributação do ISSQN sobre o serviço prestado: 1 -
        Operação tributável; 2 - Exportação de serviço; 3 - Não
        Incidência; 4 - Imunidade;
    :ivar c_pais_result: Código do país onde se verficou o resultado da
        prestação do serviço para o caso de Exportação de
        Serviço.(Tabela de Países ISO)
    :ivar bm: Tributação do ISSQN sobre o serviço prestado: 1 - Operação
        tributável; 2 - Exportação de serviço; 3 - Não Incidência; 4 -
        Imunidade;
    :ivar exig_susp: Informações para a suspensão da Exigibilidade do
        ISSQN
    :ivar tp_imunidade: Identificação da Imunidade do ISSQN – somente
        para o caso de Imunidade: 0 - Imunidade (tipo não informado na
        nota de origem); 1 - Patrimônio, renda ou serviços, uns dos
        outros (CF88, Art 150, VI, a); 2 - Templos de qualquer culto
        (CF88, Art 150, VI, b); 3 - Patrimônio, renda ou serviços dos
        partidos políticos, inclusive suas fundações, das entidades
        sindicais dos trabalhadores, das instituições de educação e de
        assistência social, sem fins lucrativos, atendidos os requisitos
        da lei (CF88, Art 150, VI, c); 4 - Livros, jornais, periódicos e
        o papel destinado a sua impressão (CF88, Art 150, VI, d);
    :ivar p_aliq: Valor da alíquota (%) do serviço prestado relativo ao
        município sujeito ativo (município de incidência) do ISSQN. Se o
        município de incidência pertence ao Sistema Nacional NFS-e a
        alíquota estará parametrizada e, portanto, será fornecida pelo
        sistema. Se o município de incidência não pertence ao Sistema
        Nacional NFS-e a alíquota não estará parametrizada e, por isso,
        deverá ser fornecida pelo emitente.
    :ivar tp_ret_issqn: Tipo de retencao do ISSQN: 1 - Não Retido; 2 -
        Retido pelo Tomador; 3 - Retido pelo Intermediario;
    """

    class Meta:
        name = "TCTribMunicipal"

    trib_issqn: TstribIssqn = field(
        metadata={
            "name": "tribISSQN",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    c_pais_result: None | str = field(
        default=None,
        metadata={
            "name": "cPaisResult",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[A-Z]{2}",
        },
    )
    bm: None | TcbeneficioMunicipal = field(
        default=None,
        metadata={
            "name": "BM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    exig_susp: None | TcexigSuspensa = field(
        default=None,
        metadata={
            "name": "exigSusp",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    tp_imunidade: None | TstipoImunidadeIssqn = field(
        default=None,
        metadata={
            "name": "tpImunidade",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    p_aliq: None | str = field(
        default=None,
        metadata={
            "name": "pAliq",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|[0-9]{1}(\.[0-9]{2})?",
        },
    )
    tp_ret_issqn: TstipoRetIssqn = field(
        metadata={
            "name": "tpRetISSQN",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )


@dataclass(kw_only=True)
class TcdocDedRed:
    """
    :ivar ch_nfse: Chave de Acesso da NFS-e (Padrão Nacional)
    :ivar ch_nfe: Chave de Acesso da NF-e
    :ivar nfse_mun: Grupo de informações de Outras NFS-e (Padrão
        anterior de NFS-e)
    :ivar nfnfs: Grupo de informações de NF ou NFS (Modelo não
        eletrônico)
    :ivar n_doc_fisc: Número de documento fiscal
    :ivar n_doc: Número de documento não fiscal
    :ivar tp_ded_red: Identificação da Dedução/Redução: 1 – Alimentação
        e bebidas/frigobar; 2 – Materiais; 3 – Produção externa; 4 –
        Reembolso de despesas; 5 – Repasse consorciado; 6 – Repasse
        plano de saúde; 7 – Serviços; 8 – Subempreitada de mão de obra;
        9 - Profissional parceiro; 99 – Outras deduções;
    :ivar x_desc_out_ded: Descrição da Dedução/Redução quando a opção é
        "99 – Outras Deduções"
    :ivar dt_emi_doc: Data da emissão do documento dedutível. Ano, mês e
        dia (AAAA-MM-DD)
    :ivar v_dedutivel_redutivel: Valor monetário total
        dedutível/redutível no documento informado (R$). Este é o valor
        total no documento informado que é passível de dedução/redução.
    :ivar v_deducao_reducao: Valor monetário utilizado para
        dedução/redução do valor do serviço da NFS-e que está sendo
        emitida (R$). Deve ser menor ou igual ao valor
        deduzível/redutível (vDedutivelRedutivel).
    :ivar fornec: Grupo de informações do Fornecedor em Deduções de
        Serviços
    """

    class Meta:
        name = "TCDocDedRed"

    ch_nfse: None | str = field(
        default=None,
        metadata={
            "name": "chNFSe",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 50,
            "white_space": "preserve",
            "pattern": r"[0-9]{50}",
        },
    )
    ch_nfe: None | str = field(
        default=None,
        metadata={
            "name": "chNFe",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 44,
            "white_space": "preserve",
            "pattern": r"[0-9]{44}",
        },
    )
    nfse_mun: None | TcdocOutNfse = field(
        default=None,
        metadata={
            "name": "NFSeMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    nfnfs: None | TcdocNfnfs = field(
        default=None,
        metadata={
            "name": "NFNFS",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    n_doc_fisc: None | str = field(
        default=None,
        metadata={
            "name": "nDocFisc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    n_doc: None | str = field(
        default=None,
        metadata={
            "name": "nDoc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    tp_ded_red: TsideDedRed = field(
        metadata={
            "name": "tpDedRed",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_desc_out_ded: None | str = field(
        default=None,
        metadata={
            "name": "xDescOutDed",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 150,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    dt_emi_doc: XmlDate = field(
        metadata={
            "name": "dtEmiDoc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    v_dedutivel_redutivel: str = field(
        metadata={
            "name": "vDedutivelRedutivel",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        }
    )
    v_deducao_reducao: str = field(
        metadata={
            "name": "vDeducaoReducao",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        }
    )
    fornec: None | TcinfoPessoa = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )


@dataclass(kw_only=True)
class TcinfoTributacao:
    """
    :ivar trib_mun: Grupo de informações relacionados ao Imposto Sobre
        Serviços de Qualquer Natureza - ISSQN
    :ivar trib_fed: Grupo de informações de outros tributos relacionados
        ao serviço prestado
    :ivar tot_trib: Grupo de informações para totais aproximados dos
        tributos relacionados ao serviço prestado
    """

    class Meta:
        name = "TCInfoTributacao"

    trib_mun: TctribMunicipal = field(
        metadata={
            "name": "tribMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    trib_fed: None | TctribFederal = field(
        default=None,
        metadata={
            "name": "tribFed",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    tot_trib: TctribTotal = field(
        metadata={
            "name": "totTrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )


@dataclass(kw_only=True)
class Tcserv:
    """
    :ivar loc_prest: Grupo de informações relativas ao local da
        prestação do serviço
    :ivar c_serv: Grupo de informações relativas ao código do serviço
        prestado
    :ivar com_ext: Grupo de informações relativas à
        exportação/importação de serviço prestado
    :ivar lsadppu: Grupo de informações relativas a atividades de
        Locação, sublocação, arrendamento, direito de passagem ou
        permissão de uso, compartilhado ou não, de ferrovia, rodovia,
        postes, cabos, dutos e condutos de qualquer natureza
    :ivar obra: Grupo de informações do DPS relativas à serviço de obra
    :ivar atv_evento: Grupo de informações do DPS relativas à Evento
    :ivar expl_rod: Grupo de informações relativas a pedágio
    :ivar info_compl: Grupo de informações complementares disponível
        para todos os serviços prestados
    """

    class Meta:
        name = "TCServ"

    loc_prest: TclocPrest = field(
        metadata={
            "name": "locPrest",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    c_serv: Tccserv = field(
        metadata={
            "name": "cServ",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    com_ext: None | TccomExterior = field(
        default=None,
        metadata={
            "name": "comExt",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    lsadppu: None | TclocacaoSublocacao = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    obra: None | TcinfoObra = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    atv_evento: None | TcatvEvento = field(
        default=None,
        metadata={
            "name": "atvEvento",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    expl_rod: None | TcexploracaoRodoviaria = field(
        default=None,
        metadata={
            "name": "explRod",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    info_compl: None | TcinfoCompl = field(
        default=None,
        metadata={
            "name": "infoCompl",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )


@dataclass(kw_only=True)
class TclistaDocDedRed:
    """
    :ivar doc_ded_red: Grupo de informações de documento utilizado para
        Dedução/Redução do valor do serviço
    """

    class Meta:
        name = "TCListaDocDedRed"

    doc_ded_red: list[TcdocDedRed] = field(
        default_factory=list,
        metadata={
            "name": "docDedRed",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_occurs": 1,
            "max_occurs": 1000,
        },
    )


@dataclass(kw_only=True)
class TcinfoDedRed:
    """
    :ivar p_dr: Valor percentual padrão para dedução/redução do valor do
        serviço
    :ivar v_dr: Valor monetário padrão para dedução/redução do valor do
        serviço
    :ivar documentos: Grupo de informações de documento utilizado para
        Dedução/Redução do valor do serviço
    """

    class Meta:
        name = "TCInfoDedRed"

    p_dr: None | str = field(
        default=None,
        metadata={
            "name": "pDR",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,2}(\.[0-9]{2})?",
        },
    )
    v_dr: None | str = field(
        default=None,
        metadata={
            "name": "vDR",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,14}(\.[0-9]{2})?",
        },
    )
    documentos: None | TclistaDocDedRed = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )


@dataclass(kw_only=True)
class TcinfoValores:
    """
    :ivar v_serv_prest: Grupo de informações relativas aos valores do
        serviço prestado
    :ivar v_desc_cond_incond: Grupo de informações relativas aos
        descontos condicionados e incondicionados
    :ivar v_ded_red: Grupo de informações relativas ao valores para
        dedução/redução do valor da base de cálculo (valor do serviço)
    :ivar trib: Grupo de informações relacionados aos tributos
        relacionados ao serviço prestado
    """

    class Meta:
        name = "TCInfoValores"

    v_serv_prest: TcvservPrest = field(
        metadata={
            "name": "vServPrest",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    v_desc_cond_incond: None | TcvdescCondIncond = field(
        default=None,
        metadata={
            "name": "vDescCondIncond",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    v_ded_red: None | TcinfoDedRed = field(
        default=None,
        metadata={
            "name": "vDedRed",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    trib: TcinfoTributacao = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )


@dataclass(kw_only=True)
class TcinfDps:
    """
    :ivar tp_amb: Identificação do Ambiente: 1 - Produção; 2 -
        Homologação
    :ivar dh_emi: Data e hora da emissão do DPS. Data e hora no formato
        UTC (Universal Coordinated Time): AAAA-MM-DDThh:mm:ssTZD
    :ivar ver_aplic: Versão do aplicativo que gerou o DPS
    :ivar serie: Número do equipamento emissor do DPS ou série do DPS
    :ivar n_dps: Número do DPS
    :ivar d_compet: Data em que se iniciou a prestação do serviço: Dia,
        mês e ano (AAAAMMDD)
    :ivar tp_emit: Emitente da DPS: 1 - Prestador; 2 - Tomador; 3 -
        Intermediário
    :ivar c_loc_emi: O código de município utilizado pelo Sistema
        Nacional NFS-e é o código definido para cada município
        pertencente ao ""Anexo V – Tabela de Código de Municípios do
        IBGE"", que consta ao final do Manual de Orientação ao
        Contribuinte do ISSQN para a Sefin Nacional NFS-e. O município
        emissor da NFS-e é aquele município em que o emitente da DPS
        está cadastrado e autorizado a "emitir uma NFS-e", ou seja,
        emitir uma DPS para que o sistema nacional valide as informações
        nela prestadas e gere a NFS-e correspondente para o emitente.
        Para que o sistema nacional emita a NFS-e o município emissor
        deve ser conveniado e estar ativo no sistema nacional. Além
        disso o convênio do município deve permitir que os contribuintes
        do município utilize os emissores públicos do Sistema Nacional
        NFS-e
    :ivar subst: Dados da NFS-e a ser substituída
    :ivar prest: Grupo de informações do DPS relativas ao Prestador de
        Serviços
    :ivar toma: Grupo de informações do DPS relativas ao Tomador de
        Serviços
    :ivar interm: Grupo de informações do DPS relativas ao Intermediário
        de Serviços
    :ivar serv: Grupo de informações do DPS relativas ao Serviço
        Prestado
    :ivar valores: Grupo de informações relativas à valores do serviço
        prestado
    :ivar id:
    """

    class Meta:
        name = "TCInfDPS"

    tp_amb: TstipoAmbiente = field(
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    dh_emi: str = field(
        metadata={
            "name": "dhEmi",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"(((20(([02468][048])|([13579][26]))-02-29))|(20[0-9][0-9])-((((0[1-9])|(1[0-2]))-((0[1-9])|(1\d)|(2[0-8])))|((((0[13578])|(1[02]))-31)|(((0[1,3-9])|(1[0-2]))-(29|30)))))T(20|21|22|23|[0-1]\d):[0-5]\d:[0-5]\d([\-,\+](0[0-9]|10|11):00|([\+](12):00))",
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
    serie: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 5,
            "white_space": "preserve",
        }
    )
    n_dps: str = field(
        metadata={
            "name": "nDPS",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 15,
            "white_space": "preserve",
            "pattern": r"[1-9]{1}[0-9]{0,14}",
        }
    )
    d_compet: str = field(
        metadata={
            "name": "dCompet",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"(((20(([02468][048])|([13579][26]))-02-29))|(20[0-9][0-9])-((((0[1-9])|(1[0-2]))-((0[1-9])|(1\d)|(2[0-8])))|((((0[13578])|(1[02]))-31)|(((0[1,3-9])|(1[0-2]))-(29|30)))))",
        }
    )
    tp_emit: TsemitenteDps = field(
        metadata={
            "name": "tpEmit",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    c_loc_emi: str = field(
        metadata={
            "name": "cLocEmi",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{7}",
        }
    )
    subst: None | Tcsubstituicao = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    prest: TcinfoPrestador = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    toma: None | TcinfoPessoa = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    interm: None | TcinfoPessoa = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    serv: Tcserv = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    valores: TcinfoValores = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    id: str = field(
        metadata={
            "name": "Id",
            "type": "Attribute",
            "max_length": 45,
            "white_space": "preserve",
            "pattern": r"DPS[0-9]{42}",
        }
    )


@dataclass(kw_only=True)
class Tcdps:
    class Meta:
        name = "TCDPS"

    inf_dps: TcinfDps = field(
        metadata={
            "name": "infDPS",
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
            "white_space": "preserve",
            "pattern": r"1\.00",
        }
    )


@dataclass(kw_only=True)
class TcinfNfse:
    """
    :ivar x_loc_emi: Descrição do código do IBGE do município emissor da
        NFS-e.
    :ivar x_loc_prestacao: Descrição do local da prestação do serviço.
    :ivar n_nfse: Número sequencial por tipo de emitente da NFS-e. A
        Sefin Nacional NFS-e irá gerar o número da NFS-e de forma
        sequencial por emitente. Por se tratar de um ambiente altamente
        transacional, a Sefin Nacional NFS-e não irá reutilizar números
        inutilizados durante a geração da NFS-e.
    :ivar c_loc_incid: O código de município utilizado pelo Sistema
        Nacional NFS-e é o código definido para cada município
        pertencente ao ""Anexo V – Tabela de Código de Municípios do
        IBGE"", que consta ao final do Manual de Orientação ao
        Contribuinte do ISSQN para a Sefin Nacional NFS-e. O município
        de incidência do ISSQN é determinado automaticamente pelo
        sistema, conforme regras do aspecto espacial da lei complementar
        federal (LC 116/03) que são válidas para todos  os municípios.
        http://www.planalto.gov.br/ccivil_03/Leis/LCP/Lcp116.htm
    :ivar x_loc_incid: A descrição do código de município utilizado pelo
        Sistema Nacional NFS-e é o nome de cada município pertencente ao
        "Anexo V – Tabela de Código de Municípios do IBGE", que consta
        ao final do Manual de Orientação ao Contribuinte do ISSQN para a
        Sefin Nacional NFS-e.
    :ivar x_trib_nac: Descrição do código de tributação nacional do
        ISSQN.
    :ivar x_trib_mun: Descrição do código de tributação municipal do
        ISSQN.
    :ivar x_nbs: Descrição do código da NBS.
    :ivar ver_aplic: Versão do aplicativo que gerou a NFS-e
    :ivar amb_ger: Ambiente gerador da NFS-e
    :ivar tp_emis: Processo de Emissão da DPS: 1 - Emissão com
        aplicativo do contribuinte (via Web Service); 2 - Emissão com
        aplicativo disponibilizado pelo fisco (Web); 3 - Emissão com
        aplicativo disponibilizado pelo fisco (App);
    :ivar proc_emi: Processo de Emissão da DPS: 1 - Emissão com
        aplicativo do contribuinte (via Web Service); 2 - Emissão com
        aplicativo disponibilizado pelo fisco (Web); 3 - Emissão com
        aplicativo disponibilizado pelo fisco (App);
    :ivar c_stat: Código do Status da mensagem
    :ivar dh_proc: Data/Hora da validação da DPS e geração da NFS-e.
        Data e hora no formato UTC (Universal Coordinated Time):AAAA-MM-
        DDThh:mm:ssTZD
    :ivar n_dfse: Número sequencial do documento gerado por ambiente
        gerador de DFSe do múnicípio.
    :ivar emit: Grupo de informações da DPS relativas ao emitente da
        NFS-e
    :ivar valores: Grupo de valores referentes ao Serviço Prestado
    :ivar dps: Grupo de informações da DPS relativas ao serviço prestado
    :ivar id:
    """

    class Meta:
        name = "TCInfNFSe"

    x_loc_emi: str = field(
        metadata={
            "name": "xLocEmi",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 150,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    x_loc_prestacao: str = field(
        metadata={
            "name": "xLocPrestacao",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 150,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    n_nfse: str = field(
        metadata={
            "name": "nNFSe",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 13,
            "white_space": "preserve",
            "pattern": r"[1-9]{1}[0-9]{0,12}",
        }
    )
    c_loc_incid: None | str = field(
        default=None,
        metadata={
            "name": "cLocIncid",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{7}",
        },
    )
    x_loc_incid: None | str = field(
        default=None,
        metadata={
            "name": "xLocIncid",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 150,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    x_trib_nac: str = field(
        metadata={
            "name": "xTribNac",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 600,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        }
    )
    x_trib_mun: None | str = field(
        default=None,
        metadata={
            "name": "xTribMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 600,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    x_nbs: None | str = field(
        default=None,
        metadata={
            "name": "xNBS",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 600,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
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
    amb_ger: TsambGeradorNfse = field(
        metadata={
            "name": "ambGer",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    tp_emis: TstipoEmissao = field(
        metadata={
            "name": "tpEmis",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    proc_emi: None | TsprocEmissao = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        },
    )
    c_stat: Tstat = field(
        metadata={
            "name": "cStat",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
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
            "max_length": 13,
            "white_space": "preserve",
            "pattern": r"[1-9]{1}[0-9]{0,12}",
        }
    )
    emit: Tcemitente = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    valores: TcvaloresNfse = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    dps: Tcdps = field(
        metadata={
            "name": "DPS",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    id: str = field(
        metadata={
            "name": "Id",
            "type": "Attribute",
            "max_length": 53,
            "white_space": "preserve",
            "pattern": r"NFS[0-9]{50}",
        }
    )


@dataclass(kw_only=True)
class Tcnfse:
    class Meta:
        name = "TCNFSe"

    inf_nfse: TcinfNfse = field(
        metadata={
            "name": "infNFSe",
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
            "white_space": "preserve",
            "pattern": r"1\.00",
        }
    )
