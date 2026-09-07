from __future__ import annotations

from dataclasses import dataclass, field

from core.nfse.nacional.schemas.v1_01.tipos_simples_v1_01 import (
    TsregEspTrib,
    TssituacaoEmissaoNfse,
    TstipoAmbiente,
)

__NAMESPACE__ = "http://www.sped.fazenda.gov.br/nfse"


@dataclass(kw_only=True)
class TcenderContribuinteCnc:
    """
    :ivar cep: Código de endereçamento postal do estabelecimento do
        contribuinte
    :ivar nro: Número do estabelecimento no logradouro informado
    :ivar x_cpl: Informação complementar para identificação do endereço
        do contribuinte
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


@dataclass(kw_only=True)
class TcinfoContribuinteCnc:
    """
    Informações para cadastramento de novos contribuintes CNC.

    :ivar cnpj: Número do CNPJ
    :ivar cpf: Número do CPF
    :ivar im: Número da inscrição municipal
    :ivar d_inscricao_municipal: Data da Inscrição Municipal: Dia, mês e
        ano (AAAAMMDD)
    :ivar ender_contribuinte_cnc: Grupo de informações do endereço do
        contribuinte do CNC
    :ivar fone: Número do telefone do prestador: Preencher com o Código
        DDD + número do telefone. Nas operações com exterior é permitido
        informar o código do país + código da localidade + número do
        telefone)
    :ivar email: Endereço de e-mail para contato com o contribuinte
    :ivar reg_esp_trib_contribuinte_cnc: Tipos de Regimes Especiais de
        Tributação: 0 - Nenhum; 1 - Ato Cooperado (Cooperativa); 2 -
        Estimativa; 3 - Microempresa Municipal; 4 - Notário ou
        Registrador; 5 - Profissional Autônomo; 6 - Sociedade de
        Profissionais;
    :ivar situacao_cadastro_contribuinte: Identificação da situação do
        cadastro do contribuinte
    :ivar motivo_situacao_cadastro_contribuinte: Motivo pelo qual o
        contribuinte se enquadra na situação informada
    :ivar situacao_emissao_nfse: Situação Emissão NFS-e: 0 - Não
        Habilitado; 1 - Habilitado;
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
    d_inscricao_municipal: str = field(
        metadata={
            "name": "dInscricaoMunicipal",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "white_space": "preserve",
            "pattern": r"(((20(([02468][048])|([13579][26]))-02-29))|(20[0-9][0-9])-((((0[1-9])|(1[0-2]))-((0[1-9])|(1\d)|(2[0-8])))|((((0[13578])|(1[02]))-31)|(((0[1,3-9])|(1[0-2]))-(29|30)))))",
        }
    )
    ender_contribuinte_cnc: TcenderContribuinteCnc = field(
        metadata={
            "name": "enderContribuinteCNC",
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
    reg_esp_trib_contribuinte_cnc: TsregEspTrib = field(
        metadata={
            "name": "regEspTribContribuinteCNC",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    situacao_cadastro_contribuinte: None | str = field(
        default=None,
        metadata={
            "name": "situacaoCadastroContribuinte",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "max_length": 150,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    motivo_situacao_cadastro_contribuinte: None | str = field(
        default=None,
        metadata={
            "name": "motivoSituacaoCadastroContribuinte",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
            "min_length": 1,
            "white_space": "preserve",
            "pattern": r"[!-ÿ]{1}[ -ÿ]{0,}[!-ÿ]{1}|[!-ÿ]{1}",
        },
    )
    situacao_emissao_nfse: TssituacaoEmissaoNfse = field(
        metadata={
            "name": "situacaoEmissaoNFSE",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )


@dataclass(kw_only=True)
class TcinfCnc:
    """
    :ivar tp_amb: Identificação do Ambiente: 1 - Produção; 2 -
        Homologação
    :ivar dh_geracao_arquivo: Data e hora da geração do arquivo CNC.
        Data e hora no formato UTC (Universal Coordinated Time): AAAA-
        MM-DDThh:mm:ssTZD
    :ivar ver_aplic: Versão do aplicativo que gerou Informações para
        cadastramento de novos contribuintes CNC
    :ivar contribuintes_cnc:
    """

    class Meta:
        name = "TCInfCNC"

    tp_amb: TstipoAmbiente = field(
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )
    dh_geracao_arquivo: str = field(
        metadata={
            "name": "dhGeracaoArquivo",
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
    contribuintes_cnc: TcinfCnc.ContribuintesCnc = field(
        metadata={
            "name": "contribuintesCnc",
            "type": "Element",
            "namespace": "http://www.sped.fazenda.gov.br/nfse",
        }
    )

    @dataclass(kw_only=True)
    class ContribuintesCnc:
        """
        :ivar contribuinte_cnc: Grupo de informações cadastramento de
            novos contribuintes CNC
        """

        contribuinte_cnc: list[TcinfoContribuinteCnc] = field(
            default_factory=list,
            metadata={
                "name": "contribuinteCnc",
                "type": "Element",
                "namespace": "http://www.sped.fazenda.gov.br/nfse",
                "min_occurs": 1,
            },
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
