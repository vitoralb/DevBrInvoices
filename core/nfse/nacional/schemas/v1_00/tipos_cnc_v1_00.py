from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.nacional.schemas.v1_00.tipos_simples_v1_00 import (
    TssituacaoCadastroContribuinteCnc,
    TssituacaoEmissaoNfse,
    TstipoAmbiente,
)

__NAMESPACE__ = "http://www.sped.fazenda.gov.br/nfse"


@dataclass(kw_only=True)
class TcenderContribuinteCnc:
    """
    :ivar cep: Código de endereçamento postal do estabelecimento do
        contribuinte
    :ivar x_lgr: Nome do logradouro
    :ivar nro: Número do estabelecimento no logradouro informado
    :ivar x_cpl: Informação complementar para identificação do endereço
        do contribuinte
    :ivar x_bairro: Nome do bairro
    """

    class Meta:
        name = "TCEnderContribuinteCNC"

    cep: str = field(
        metadata={
            "name": "CEP",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{8}",
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


@dataclass(kw_only=True)
class TcinfoContribuinteCnc:
    """
    Informações para cadastramento de novos contribuintes CNC.

    :ivar cnpj: Número do CNPJ do contribuinte.
    :ivar cpf: Número do CPF do contribuinte.
    :ivar im: Número da inscrição municipal
    :ivar d_im: Data da Inscrição Municipal: Dia, mês e ano (AAAAMMDD)
    :ivar x_fantasia: Nome fantasia do contribuinte.
    :ivar ender: Grupo de informações do endereço do contribuinte do CNC
    :ivar fone: Número do telefone do prestador: Preencher com o Código
        DDD + número do telefone. Nas operações com exterior é permitido
        informar o código do país + código da localidade + número do
        telefone)
    :ivar email: Endereço de e-mail para contato com o contribuinte
    :ivar d_aut_emiss: Data de autorização de uso dos emissores
        públicos: Dia, mês e ano (AAAAMMDD)
    :ivar c_stat_emiss: Situação Emissão NFS-e: 0 - Não Habilitado; 1 -
        Habilitado;
    :ivar c_sit_cnc: Identificação da situação do cadastro do
        contribuinte
    :ivar x_sit_cad_mun: Identificação da situação do cadastro do
        contribuinte
    :ivar x_motivo_sit_cad_mun: Motivo pelo qual o contribuinte se
        enquadra na situação informada
    """

    class Meta:
        name = "TCInfoContribuinteCNC"

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
    im: str = field(
        metadata={
            "name": "IM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 15,
            "white_space": "preserve",
        }
    )
    d_im: str = field(
        metadata={
            "name": "dIM",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"(((19|20)(([02468][048])|[13579][26]|0[48]|[13579]2|[2468]0)-02-29)|((19|20)[0-9][0-9])-((((0[1-9])|(1[0-2]))-((0[1-9])|(1\d)|(2[0-8])))|(((0[13578])|(1[02]))-31)|(((0[1,3-9])|(1[0-2]))-(29|30))))",
        }
    )
    x_fantasia: None | str = field(
        default=None,
        metadata={
            "name": "xFantasia",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 150,
            "white_space": "preserve",
        },
    )
    ender: None | TcenderContribuinteCnc = field(
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
    d_aut_emiss: str = field(
        metadata={
            "name": "dAutEmiss",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"(((19|20)(([02468][048])|[13579][26]|0[48]|[13579]2|[2468]0)-02-29)|((19|20)[0-9][0-9])-((((0[1-9])|(1[0-2]))-((0[1-9])|(1\d)|(2[0-8])))|(((0[13578])|(1[02]))-31)|(((0[1,3-9])|(1[0-2]))-(29|30))))",
        }
    )
    c_stat_emiss: TssituacaoEmissaoNfse = field(
        metadata={
            "name": "cStatEmiss",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    c_sit_cnc: TssituacaoCadastroContribuinteCnc = field(
        metadata={
            "name": "cSitCNC",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    x_sit_cad_mun: None | str = field(
        default=None,
        metadata={
            "name": "xSitCadMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 150,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    x_motivo_sit_cad_mun: None | str = field(
        default=None,
        metadata={
            "name": "xMotivoSitCadMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 255,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )


@dataclass(kw_only=True)
class TcinfCnc:
    """
    :ivar c_mun: Código do Municipio
    :ivar cnpj_mun: CNPJ do Municipio
    :ivar cpfag_trib: CPF do agente tributário
    :ivar tp_amb: Identificação do Ambiente: 1 - Produção; 2 -
        Homologação
    :ivar ver_aplic: Versão do aplicativo que gerou Informações para
        cadastramento de novos contribuintes CNC
    :ivar inf_contrib: Grupo de informações cadastramento de novo
        contribuinte CNC
    :ivar id:
    """

    class Meta:
        name = "TCInfCNC"

    c_mun: str = field(
        metadata={
            "name": "cMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"[0-9]{7}",
        }
    )
    cnpj_mun: str = field(
        metadata={
            "name": "cnpjMun",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "max_length": 14,
            "white_space": "preserve",
            "pattern": r"[0-9]{14}",
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
    inf_contrib: TcinfoContribuinteCnc = field(
        metadata={
            "name": "infContrib",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    id: str = field(
        metadata={
            "name": "Id",
            "type": "Attribute",
            "max_length": 26,
            "white_space": "preserve",
            "pattern": r"CNC[0-9]{8}.{1,15}",
        }
    )


@dataclass(kw_only=True)
class Tcnc:
    class Meta:
        name = "TCNC"

    inf_cnc: TcinfCnc = field(
        metadata={
            "name": "infCNC",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    versao: str = field(
        metadata={
            "type": "Attribute",
            "white_space": "preserve",
            "pattern": r"1\.00",
        }
    )
