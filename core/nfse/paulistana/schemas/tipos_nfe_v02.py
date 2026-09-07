from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe/tipos"


@dataclass(kw_only=True)
class TpCpfcnpj:
    """
    Tipo que representa um CPF/CNPJ.
    """

    class Meta:
        name = "tpCPFCNPJ"

    cpf: None | str = field(
        default=None,
        metadata={
            "name": "CPF",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{0}|[0-9]{11}",
        },
    )
    cnpj: None | str = field(
        default=None,
        metadata={
            "name": "CNPJ",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9A-Z]{12}[0-9]{2}",
        },
    )


@dataclass(kw_only=True)
class TpChaveNfe:
    """
    Chave de identificação da NFS-e.

    :ivar inscricao_prestador: Inscrição municipal do prestador de
        serviços.
    :ivar numero_nfe: Número da NFS-e.
    :ivar codigo_verificacao: Código de verificação da NFS-e.
    :ivar chave_nota_nacional: Chave da Nota Nacional.
    """

    class Meta:
        name = "tpChaveNFe"

    inscricao_prestador: str = field(
        metadata={
            "name": "InscricaoPrestador",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        }
    )
    numero_nfe: str = field(
        metadata={
            "name": "NumeroNFe",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        }
    )
    codigo_verificacao: None | str = field(
        default=None,
        metadata={
            "name": "CodigoVerificacao",
            "type": "Element",
            "namespace": "",
            "min_length": 8,
            "max_length": 8,
            "white_space": "collapse",
        },
    )
    chave_nota_nacional: None | str = field(
        default=None,
        metadata={
            "name": "ChaveNotaNacional",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9A-Z]{50}",
        },
    )


@dataclass(kw_only=True)
class TpChaveRps:
    """
    Tipo que define a chave identificadora de um RPS.

    :ivar inscricao_prestador: Inscrição municipal do prestador de
        serviços.
    :ivar serie_rps: Série do RPS.
    :ivar numero_rps: Número do RPS.
    """

    class Meta:
        name = "tpChaveRPS"

    inscricao_prestador: str = field(
        metadata={
            "name": "InscricaoPrestador",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        }
    )
    serie_rps: None | str = field(
        default=None,
        metadata={
            "name": "SerieRPS",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 5,
            "white_space": "collapse",
        },
    )
    numero_rps: str = field(
        metadata={
            "name": "NumeroRPS",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        }
    )


@dataclass(kw_only=True)
class TpDocFiscalOutro:
    """
    Grupo de informações de documento fiscais, eletrônicos ou não, que não
    se encontram no repositório nacional.

    :ivar c_mun_doc_fiscal: Código do município emissor do documento
        fiscal que não se encontra no repositório nacional.
    :ivar n_doc_fiscal: Número do documento fiscal que não se encontra
        no repositório nacional.
    :ivar x_doc_fiscal: Descrição do documento fiscal.
    """

    class Meta:
        name = "tpDocFiscalOutro"

    c_mun_doc_fiscal: str = field(
        metadata={
            "name": "cMunDocFiscal",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7}",
        }
    )
    n_doc_fiscal: str = field(
        metadata={
            "name": "nDocFiscal",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 255,
            "white_space": "collapse",
        }
    )
    x_doc_fiscal: str = field(
        metadata={
            "name": "xDocFiscal",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 255,
            "white_space": "collapse",
        }
    )


@dataclass(kw_only=True)
class TpDocOutro:
    """
    Grupo de informações de documento não fiscal.

    :ivar n_doc: Número do documento não fiscal.
    :ivar x_doc: Descrição do documento não fiscal.
    """

    class Meta:
        name = "tpDocOutro"

    n_doc: str = field(
        metadata={
            "name": "nDoc",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 255,
            "white_space": "collapse",
        }
    )
    x_doc: str = field(
        metadata={
            "name": "xDoc",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 255,
            "white_space": "collapse",
        }
    )


@dataclass(kw_only=True)
class TpEnderecoExterior:
    """
    Tipo endereço no exterior.

    :ivar c_pais: Código do país (Tabela de Países ISO).
    :ivar c_end_post: Código alfanumérico do Endereçamento Postal no
        exterior do prestador do serviço.
    :ivar x_cidade: Nome da cidade no exterior do prestador do serviço.
    :ivar x_est_prov_reg: Estado, província ou região da cidade no
        exterior do prestador do serviço.
    """

    class Meta:
        name = "tpEnderecoExterior"

    c_pais: str = field(
        metadata={
            "name": "cPais",
            "type": "Element",
            "namespace": "",
            "pattern": r"[A-Z]{2}",
        }
    )
    c_end_post: str = field(
        metadata={
            "name": "cEndPost",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 11,
            "white_space": "collapse",
        }
    )
    x_cidade: str = field(
        metadata={
            "name": "xCidade",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 60,
            "white_space": "collapse",
        }
    )
    x_est_prov_reg: str = field(
        metadata={
            "name": "xEstProvReg",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 60,
            "white_space": "collapse",
        }
    )


@dataclass(kw_only=True)
class TpEnderecoNacional:
    """
    Tipo endereço no nacional.
    """

    class Meta:
        name = "tpEnderecoNacional"

    c_mun: str = field(
        metadata={
            "name": "cMun",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7}",
        }
    )
    cep: str = field(
        metadata={
            "name": "CEP",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7,8}",
        }
    )


class TpEnteGov(Enum):
    """
    Tipo do ente da compra governamental.

    :cvar VALUE_1: União.
    :cvar VALUE_2: Estados.
    :cvar VALUE_3: Distrito Federal.
    :cvar VALUE_4: Municípios.
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4


class TpFinNfse(Enum):
    """
    Indicador da finalidade da emissão de NFS-e.

    :cvar VALUE_0: 0 = NFS-e regular.
    """

    VALUE_0 = 0


@dataclass(kw_only=True)
class TpGrefNfse:
    """
    Grupo com Ids da nota nacional referenciadas, associadas a NFSE.
    """

    class Meta:
        name = "tpGRefNFSe"

    ref_nfse: list[str] = field(
        default_factory=list,
        metadata={
            "name": "refNFSe",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
            "max_occurs": 99,
            "pattern": r"[0-9A-Z]{50}",
        },
    )


@dataclass(kw_only=True)
class TpGtribRegular:
    """
    Informações relacionadas à tributação regular.

    :ivar c_class_trib_reg: Código de classificação Tributária do IBS e
        da CBS.
    """

    class Meta:
        name = "tpGTribRegular"

    c_class_trib_reg: str = field(
        metadata={
            "name": "cClassTribReg",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{6}",
        }
    )


class TpIndDest(Enum):
    """
    Indica o Destinatário dos serviços.

    :cvar VALUE_0: O destinatário é o próprio tomador/adquirente
        identificado na NFS-e (tomador = adquirente = destinatário).
    :cvar VALUE_1: O destinatário não é o próprio adquirente, podendo
        ser outra pessoa, física ou jurídica (ou equiparada), ou um
        estabelecimento diferente do indicado como tomador (tomador =
        adquirente ≠ destinatário).
    """

    VALUE_0 = 0
    VALUE_1 = 1


class TpNaoNif(Enum):
    """
    Tipo do motivo para não informação do NIF.

    :cvar VALUE_0: 0 - Não informado na nota de origem;
    :cvar VALUE_1: 1 - Dispensado do NIF;
    :cvar VALUE_2: 2 - Não exigência do NIF;
    """

    VALUE_0 = 0
    VALUE_1 = 1
    VALUE_2 = 2


class TpNaoSim(Enum):
    """
    Tipo de Não ou Sim.

    :cvar VALUE_0: Não.
    :cvar VALUE_1: Sim.
    """

    VALUE_0 = 0
    VALUE_1 = 1


class TpOpcaoSimples(Enum):
    """
    Tipo referente às possíveis opções de escolha pelo Simples.

    :cvar VALUE_0: Não-optante pelo Simples Federal nem Municipal.
    :cvar VALUE_1: Optante pelo Simples Federal (Alíquota de 1,0%).
    :cvar VALUE_2: Optante pelo Simples Federal (Alíquota de 0,5%).
    :cvar VALUE_3: Optante pelo Simples Municipal.
    :cvar VALUE_4: Optante pelo Simples Nacional - DAS.
    :cvar VALUE_6: Optante pelo Simples Nacional - DAMSP.
    """

    VALUE_0 = "0"
    VALUE_1 = "1"
    VALUE_2 = "2"
    VALUE_3 = "3"
    VALUE_4 = "4"
    VALUE_6 = "6"


class TpOper(Enum):
    """
    Tipo de Operação com Entes Governamentais ou outros serviços sobre bens
    imóveis.

    :cvar VALUE_1: Fornecimento com pagamento posterior.
    :cvar VALUE_2: Recebimento do pagamento com fornecimento já
        realizado.
    :cvar VALUE_3: Fornecimento com pagamento já realizado.
    :cvar VALUE_4: Recebimento do pagamento com fornecimento posterior.
    :cvar VALUE_5: Fornecimento e recebimento do pagamento
        concomitantes.
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5


class TpReeRepRes(Enum):
    """
    Tipo de valor incluído neste documento, recebido por motivo de estarem
    relacionadas a operações de terceiros, objeto de reembolso, repasse ou
    ressarcimento pelo recebedor, já tributados e aqui referenciados. 01 =
    Repasse de remuneração por intermediação de imóveis a demais corretores
    envolvidos na operação. 02 = Repasse de valores a fornecedor relativo a
    fornecimento intermediado por agência de turismo. 03 = Reembolso ou
    ressarcimento recebido por agência de propaganda e publicidade por
    valores pagos relativos a serviços de produção externa por conta e
    ordem de terceiro. 04 = Reembolso ou ressarcimento recebido por agência
    de propaganda e publicidade por valores pagos relativos a serviços de
    mídia por conta e ordem de terceiro. 99 = Outros reembolsos ou
    ressarcimentos recebidos por valores pagos relativos a operações por
    conta e ordem de terceiro.

    :cvar VALUE_1: 01 = Repasse de remuneração por intermediação de
        imóveis a demais corretores envolvidos na operação
    :cvar VALUE_2: 02 = Repasse de valores a fornecedor relativo a
        fornecimento intermediado por agência de turismo.
    :cvar VALUE_3: 03 = Reembolso ou ressarcimento recebido por agência
        de propaganda e publicidade por valores pagos relativos a
        serviços de produção externa por conta e ordem de terceiro.
    :cvar VALUE_4: 04 = Reembolso ou ressarcimento recebido por agência
        de propaganda e publicidade por valores pagos relativos a
        serviços de mídia por conta e ordem de terceiro.
    :cvar VALUE_99: 99 = Outros reembolsos ou ressarcimentos recebidos
        por valores pagos relativos a operações por conta e ordem de
        terceiro
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_99 = 99


class TpRetencaoPisCofins(Enum):
    """
    Tipo de retenção para os tributos federais conforme numerados.

    :cvar VALUE_0: PIS/COFINS/CSLL Não Retidos.
    :cvar VALUE_3: PIS/COFINS/CSLL Retidos.
    :cvar VALUE_4: PIS/COFINS Retidos, CSLL Não Retido.
    :cvar VALUE_5: PIS Retido, COFINS/CSLL Não Retido.
    :cvar VALUE_6: COFINS Retido, PIS/CSLL Não Retidos.
    :cvar VALUE_7: PIS Não Retido, COFINS/CSLL Retidos.
    :cvar VALUE_8: PIS/COFINS Não Retidos, CSLL Retido.
    :cvar VALUE_9: COFINS Não Retido, PIS/CSLL Retidos.
    """

    VALUE_0 = "0"
    VALUE_3 = "3"
    VALUE_4 = "4"
    VALUE_5 = "5"
    VALUE_6 = "6"
    VALUE_7 = "7"
    VALUE_8 = "8"
    VALUE_9 = "9"


class TpStatusNfe(Enum):
    """
    Tipo referente aos possíveis status de NFS-e.

    :cvar N: Normal.
    :cvar C: Cancelada.
    :cvar E: Extraviada.
    """

    N = "N"
    C = "C"
    E = "E"


class TpTipoChaveDfe(Enum):
    """
    Documento fiscal a que se refere a chaveDfe que seja um dos documentos
    do Repositório Nacional: 1 - NFS-e. 2 - NF-e. 3 - CT-e. 9 - Outro.

    :cvar VALUE_1: NFS-e.
    :cvar VALUE_2: NF-e.
    :cvar VALUE_3: CT-e.
    :cvar VALUE_9: Outro.
    """

    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_9 = 9


class TpTipoRps(Enum):
    """
    Tipo referente aos possíveis tipos de RPS.

    :cvar RPS: Recibo Provisório de Serviços.
    :cvar RPS_M: Recibo Provisório de Serviços proveniente de Nota
        Fiscal Conjugada (Mista).
    :cvar RPS_C: Cupom.
    """

    RPS = "RPS"
    RPS_M = "RPS-M"
    RPS_C = "RPS-C"


@dataclass(kw_only=True)
class TpCpfcnpjnif:
    """
    Tipo que representa um CPF/CNPJ/NIF.
    """

    class Meta:
        name = "tpCPFCNPJNIF"

    cpf: None | str = field(
        default=None,
        metadata={
            "name": "CPF",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{0}|[0-9]{11}",
        },
    )
    cnpj: None | str = field(
        default=None,
        metadata={
            "name": "CNPJ",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9A-Z]{12}[0-9]{2}",
        },
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 40,
            "white_space": "collapse",
        },
    )
    nao_nif: None | TpNaoNif = field(
        default=None,
        metadata={
            "name": "NaoNIF",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass(kw_only=True)
class TpChaveNfeRps:
    """
    Tipo que representa a chave de uma NFS-e e a Chave do RPS que a mesma
    substitui.

    :ivar chave_nfe: Chave da NFS-e gerada.
    :ivar chave_rps: Chave do RPS substituído.
    """

    class Meta:
        name = "tpChaveNFeRPS"

    chave_nfe: TpChaveNfe = field(
        metadata={
            "name": "ChaveNFe",
            "type": "Element",
            "namespace": "",
        }
    )
    chave_rps: TpChaveRps = field(
        metadata={
            "name": "ChaveRPS",
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass(kw_only=True)
class TpDfeNacional:
    """
    Tipo de documento do repositório nacional.
    """

    class Meta:
        name = "tpDFeNacional"

    tipo_chave_dfe: TpTipoChaveDfe = field(
        metadata={
            "name": "tipoChaveDFe",
            "type": "Element",
            "namespace": "",
        }
    )
    x_tipo_chave_dfe: None | str = field(
        default=None,
        metadata={
            "name": "xTipoChaveDFe",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 255,
            "white_space": "collapse",
        },
    )
    chave_dfe: str = field(
        metadata={
            "name": "chaveDFe",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 50,
            "white_space": "collapse",
        }
    )


@dataclass(kw_only=True)
class TpEndereco:
    """
    Tipo Endereço.
    """

    class Meta:
        name = "tpEndereco"

    tipo_logradouro: None | str = field(
        default=None,
        metadata={
            "name": "TipoLogradouro",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 3,
            "white_space": "collapse",
        },
    )
    logradouro: None | str = field(
        default=None,
        metadata={
            "name": "Logradouro",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 50,
            "white_space": "collapse",
        },
    )
    numero_endereco: None | str = field(
        default=None,
        metadata={
            "name": "NumeroEndereco",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 10,
            "white_space": "collapse",
        },
    )
    complemento_endereco: None | str = field(
        default=None,
        metadata={
            "name": "ComplementoEndereco",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 30,
            "white_space": "collapse",
        },
    )
    bairro: None | str = field(
        default=None,
        metadata={
            "name": "Bairro",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 30,
            "white_space": "collapse",
        },
    )
    cidade: None | str = field(
        default=None,
        metadata={
            "name": "Cidade",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7}",
        },
    )
    uf: None | str = field(
        default=None,
        metadata={
            "name": "UF",
            "type": "Element",
            "namespace": "",
            "min_length": 2,
            "max_length": 2,
            "white_space": "collapse",
        },
    )
    cep: None | str = field(
        default=None,
        metadata={
            "name": "CEP",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7,8}",
        },
    )
    endereco_exterior: None | TpEnderecoExterior = field(
        default=None,
        metadata={
            "name": "EnderecoExterior",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass(kw_only=True)
class TpEnderecoIbscbs:
    """
    Tipo Endereço para o IBSCBS.
    """

    class Meta:
        name = "tpEnderecoIBSCBS"

    end_nac: None | TpEnderecoNacional = field(
        default=None,
        metadata={
            "name": "endNac",
            "type": "Element",
            "namespace": "",
        },
    )
    end_ext: None | TpEnderecoExterior = field(
        default=None,
        metadata={
            "name": "endExt",
            "type": "Element",
            "namespace": "",
        },
    )
    x_lgr: str = field(
        metadata={
            "name": "xLgr",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 50,
            "white_space": "collapse",
        }
    )
    nro: str = field(
        metadata={
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 10,
            "white_space": "collapse",
        }
    )
    x_cpl: None | str = field(
        default=None,
        metadata={
            "name": "xCpl",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 30,
            "white_space": "collapse",
        },
    )
    x_bairro: str = field(
        metadata={
            "name": "xBairro",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 30,
            "white_space": "collapse",
        }
    )


@dataclass(kw_only=True)
class TpEnderecoSimplesIbscbs:
    """
    Tipo Endereço simplificado para o IBSCBS.
    """

    class Meta:
        name = "tpEnderecoSimplesIBSCBS"

    cep: None | str = field(
        default=None,
        metadata={
            "name": "CEP",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7,8}",
        },
    )
    end_ext: None | TpEnderecoExterior = field(
        default=None,
        metadata={
            "name": "endExt",
            "type": "Element",
            "namespace": "",
        },
    )
    x_lgr: str = field(
        metadata={
            "name": "xLgr",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 50,
            "white_space": "collapse",
        }
    )
    nro: str = field(
        metadata={
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 10,
            "white_space": "collapse",
        }
    )
    x_cpl: None | str = field(
        default=None,
        metadata={
            "name": "xCpl",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 30,
            "white_space": "collapse",
        },
    )
    x_bairro: str = field(
        metadata={
            "name": "xBairro",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 30,
            "white_space": "collapse",
        }
    )


@dataclass(kw_only=True)
class TpEvento:
    """
    :ivar codigo: Código do evento.
    :ivar descricao: Descrição do evento.
    :ivar chave_rps: Chave do RPS.
    :ivar chave_nfe: Chave da NFe.
    """

    class Meta:
        name = "tpEvento"

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
    chave_rps: None | TpChaveRps = field(
        default=None,
        metadata={
            "name": "ChaveRPS",
            "type": "Element",
            "namespace": "",
        },
    )
    chave_nfe: None | TpChaveNfe = field(
        default=None,
        metadata={
            "name": "ChaveNFe",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass(kw_only=True)
class TpFornecedor:
    """
    Grupo de informações do fornecedor do documento referenciado.

    :ivar cpf:
    :ivar cnpj:
    :ivar nif:
    :ivar nao_nif:
    :ivar x_nome: Nome do fornecedor.
    """

    class Meta:
        name = "tpFornecedor"

    cpf: None | str = field(
        default=None,
        metadata={
            "name": "CPF",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{0}|[0-9]{11}",
        },
    )
    cnpj: None | str = field(
        default=None,
        metadata={
            "name": "CNPJ",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9A-Z]{12}[0-9]{2}",
        },
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 40,
            "white_space": "collapse",
        },
    )
    nao_nif: None | TpNaoNif = field(
        default=None,
        metadata={
            "name": "NaoNIF",
            "type": "Element",
            "namespace": "",
        },
    )
    x_nome: str = field(
        metadata={
            "name": "xNome",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 75,
            "white_space": "collapse",
        }
    )


@dataclass(kw_only=True)
class TpGibscbs:
    """
    Informações relacionadas ao IBS e à CBS.

    :ivar c_class_trib: Código de classificação Tributária do IBS e da
        CBS.
    :ivar g_trib_regular:
    """

    class Meta:
        name = "tpGIBSCBS"

    c_class_trib: str = field(
        metadata={
            "name": "cClassTrib",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{6}",
        }
    )
    g_trib_regular: None | TpGtribRegular = field(
        default=None,
        metadata={
            "name": "gTribRegular",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass(kw_only=True)
class TpInformacoesLote:
    """
    Informações do lote processado.

    :ivar numero_lote: Número de lote.
    :ivar inscricao_prestador: Inscrição municipal do prestador dos RPS
        contidos no lote.
    :ivar cpfcnpjremetente: CNPJ do remetente autorizado a transmitir a
        mensagem XML.
    :ivar data_envio_lote: Data/hora de envio do lote.
    :ivar qtd_notas_processadas: Quantidade de RPS do lote.
    :ivar tempo_processamento: Tempo de processamento do lote.
    :ivar valor_total_servicos: Valor total dos serviços dos RPS
        contidos na mensagem XML.
    :ivar valor_total_deducoes: Valor total das deduções dos RPS
        contidos na mensagem XML.
    """

    class Meta:
        name = "tpInformacoesLote"

    numero_lote: None | str = field(
        default=None,
        metadata={
            "name": "NumeroLote",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    inscricao_prestador: str = field(
        metadata={
            "name": "InscricaoPrestador",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        }
    )
    cpfcnpjremetente: TpCpfcnpj = field(
        metadata={
            "name": "CPFCNPJRemetente",
            "type": "Element",
            "namespace": "",
        }
    )
    data_envio_lote: XmlDateTime = field(
        metadata={
            "name": "DataEnvioLote",
            "type": "Element",
            "namespace": "",
        }
    )
    qtd_notas_processadas: str = field(
        metadata={
            "name": "QtdNotasProcessadas",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,15}",
        }
    )
    tempo_processamento: str = field(
        metadata={
            "name": "TempoProcessamento",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,15}",
        }
    )
    valor_total_servicos: str = field(
        metadata={
            "name": "ValorTotalServicos",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    valor_total_deducoes: None | str = field(
        default=None,
        metadata={
            "name": "ValorTotalDeducoes",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )


@dataclass(kw_only=True)
class TpAtividadeEvento:
    """
    Tipo de informações relativas à atividades de eventos.

    :ivar x_nome_evt: Nome do evento cultural, artístico, esportivo.
    :ivar dt_ini_evt: Data de início da atividade de evento. Ano, Mês e
        Dia (AAAA-MM-DD).
    :ivar dt_fim_evt: Data de fim da atividade de evento. Ano, Mês e Dia
        (AAAA-MM-DD).
    :ivar end: Endereço do Evento.
    """

    class Meta:
        name = "tpAtividadeEvento"

    x_nome_evt: str = field(
        metadata={
            "name": "xNomeEvt",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 255,
            "white_space": "collapse",
        }
    )
    dt_ini_evt: XmlDate = field(
        metadata={
            "name": "dtIniEvt",
            "type": "Element",
            "namespace": "",
        }
    )
    dt_fim_evt: XmlDate = field(
        metadata={
            "name": "dtFimEvt",
            "type": "Element",
            "namespace": "",
        }
    )
    end: TpEnderecoSimplesIbscbs = field(
        metadata={
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass(kw_only=True)
class TpDocumento:
    """
    Tipo de documento referenciado nos casos de reembolso, repasse e
    ressarcimento que serão considerados na base de cálculo do ISSQN, do
    IBS e da CBS.

    :ivar d_fe_nacional:
    :ivar doc_fiscal_outro:
    :ivar doc_outro:
    :ivar fornec:
    :ivar dt_emi_doc: Data da emissão do documento dedutível. Ano, mês e
        dia (AAAA-MM-DD).
    :ivar dt_comp_doc: Data da competência do documento dedutível. Ano,
        mês e dia (AAAA-MM-DD).
    :ivar tp_ree_rep_res: Tipo de valor incluído neste documento,
        recebido por motivo de estarem relacionadas a operações de
        terceiros, objeto de reembolso, repasse ou ressarcimento pelo
        recebedor, já tributados e aqui referenciado.
    :ivar x_tp_ree_rep_res: Descrição do reembolso ou ressarcimento
        quando a opção é "99 - Outros reembolsos ou ressarcimentos
        recebidos por valores pagos relativos a operações por conta e
        ordem de terceiro"
    :ivar vlr_ree_rep_res: Valor monetário (total ou parcial, conforme
        documento informado) utilizado para não inclusão na base de
        cálculo do ISS e do IBS e da CBS da NFS-e que está sendo emitida
        (R$).
    """

    class Meta:
        name = "tpDocumento"

    d_fe_nacional: None | TpDfeNacional = field(
        default=None,
        metadata={
            "name": "dFeNacional",
            "type": "Element",
            "namespace": "",
        },
    )
    doc_fiscal_outro: None | TpDocFiscalOutro = field(
        default=None,
        metadata={
            "name": "docFiscalOutro",
            "type": "Element",
            "namespace": "",
        },
    )
    doc_outro: None | TpDocOutro = field(
        default=None,
        metadata={
            "name": "docOutro",
            "type": "Element",
            "namespace": "",
        },
    )
    fornec: None | TpFornecedor = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    dt_emi_doc: XmlDate = field(
        metadata={
            "name": "dtEmiDoc",
            "type": "Element",
            "namespace": "",
        }
    )
    dt_comp_doc: XmlDate = field(
        metadata={
            "name": "dtCompDoc",
            "type": "Element",
            "namespace": "",
        }
    )
    tp_ree_rep_res: TpReeRepRes = field(
        metadata={
            "name": "tpReeRepRes",
            "type": "Element",
            "namespace": "",
        }
    )
    x_tp_ree_rep_res: None | str = field(
        default=None,
        metadata={
            "name": "xTpReeRepRes",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 150,
            "white_space": "collapse",
        },
    )
    vlr_ree_rep_res: str = field(
        metadata={
            "name": "vlrReeRepRes",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )


@dataclass(kw_only=True)
class TpImovelObra:
    """
    Tipo de imovel/obra.
    """

    class Meta:
        name = "tpImovelObra"

    insc_imob_fisc: None | str = field(
        default=None,
        metadata={
            "name": "inscImobFisc",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 30,
            "white_space": "collapse",
        },
    )
    c_cib: None | str = field(
        default=None,
        metadata={
            "name": "cCIB",
            "type": "Element",
            "namespace": "",
            "white_space": "preserve",
            "pattern": r"[0-9A-Z]{8}",
        },
    )
    c_obra: None | str = field(
        default=None,
        metadata={
            "name": "cObra",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 30,
            "white_space": "collapse",
        },
    )
    end: None | TpEnderecoSimplesIbscbs = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass(kw_only=True)
class TpInformacoesPessoa:
    """
    Tipo de informações de pessoa.

    :ivar cpf:
    :ivar cnpj:
    :ivar nif:
    :ivar nao_nif:
    :ivar x_nome: Nome.
    :ivar end: Endereço.
    :ivar email: Endereço eletrônico.
    """

    class Meta:
        name = "tpInformacoesPessoa"

    cpf: None | str = field(
        default=None,
        metadata={
            "name": "CPF",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{0}|[0-9]{11}",
        },
    )
    cnpj: None | str = field(
        default=None,
        metadata={
            "name": "CNPJ",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9A-Z]{12}[0-9]{2}",
        },
    )
    nif: None | str = field(
        default=None,
        metadata={
            "name": "NIF",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 40,
            "white_space": "collapse",
        },
    )
    nao_nif: None | TpNaoNif = field(
        default=None,
        metadata={
            "name": "NaoNIF",
            "type": "Element",
            "namespace": "",
        },
    )
    x_nome: str = field(
        metadata={
            "name": "xNome",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 75,
            "white_space": "collapse",
        }
    )
    end: None | TpEnderecoIbscbs = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    email: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 75,
            "white_space": "collapse",
        },
    )


@dataclass(kw_only=True)
class TpTrib:
    """
    Informações relacionadas aos tributos IBS e à CBS.
    """

    class Meta:
        name = "tpTrib"

    g_ibscbs: TpGibscbs = field(
        metadata={
            "name": "gIBSCBS",
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass(kw_only=True)
class TpGrupoReeRepRes:
    """
    Grupo de informações relativas a valores incluídos neste documento e
    recebidos por motivo de estarem relacionadas a operações de terceiros,
    objeto de reembolso, repasse ou ressarcimento pelo recebedor, já
    tributados e aqui referenciados.
    """

    class Meta:
        name = "tpGrupoReeRepRes"

    documentos: list[TpDocumento] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
            "max_occurs": 100,
        },
    )


@dataclass(kw_only=True)
class TpRetornoComplementarIbscbs:
    """
    Informações complementares referente ao IBS e à CBS.

    :ivar adquirente: Adquirente.
    :ivar valor_bcibscbs: Valor da base de cálculo (BC) do IBS/CBS antes
        das reducões para cálculo do tributo bruto.
    :ivar valor_aliq_estadual_ibs: Alíquota do IBS de competência do
        Estado.
    :ivar valor_perc_red_estadual_ibs: Percentual de redução de alíquota
        estadual do IBS.
    :ivar valor_aliq_efetiva_estadual_ibs: Alíquota efetiva estadual do
        IBS.
    :ivar valor_estadual_ibs: Valor do Tributo do IBS da UF calculado.
    :ivar valor_aliq_municipal_ibs: Alíquota do IBS de competência do
        Município.
    :ivar valor_perc_red_municipal_ibs: Percentual de redução de
        aliquota municipal.
    :ivar valor_aliq_efetiva_municipal_ibs: Alíquota efetiva municipal
        do IBS.
    :ivar valor_municipal_ibs: Valor do Tributo do IBS do Município
        calculado.
    :ivar valor_ibs: Valor do IBS Total.
    :ivar valor_aliq_cbs: Alíquota da CBS.
    :ivar valor_perc_red_cbs: Percentual da redução de alíquota para a
        CBS.
    :ivar valor_aliq_efetiva_cbs: Alíquota efetiva CBS.
    :ivar valor_cbs: Valor do Tributo da CBS calculado. Total Valor da
        CBS da União.
    :ivar valor_perc_diferimento_estadual: Percentual de diferimento
        estadual.
    :ivar valor_diferimento_estadual: Total do Diferimento do IBS
        estadual.
    :ivar valor_perc_diferimento_municipal: Percentual de diferimento
        municipal.
    :ivar valor_diferimento_municipal: Total do Diferimento do IBS
        municipal.
    :ivar valor_perc_diferimento_cbs: Percentual de diferimento da CBS.
    :ivar valor_diferimento_cbs: Total do Diferimento CBS.
    :ivar codigo_class_cred_presumido_ibs: Código e classificação do
        crédito presumido IBS.
    :ivar valor_perc_cred_presumido_ibs: Alíquota do Crédito Presumido
        para o IBS.
    :ivar valor_cred_presumido_ibs: Valor do Crédito Presumido para o
        IBS.
    :ivar codigo_class_cred_presumido_cbs: Código de Classificação do
        Crédito Presumido CBS.
    :ivar valor_perc_cred_presumido_cbs: Alíquota de crédito presumido
        para a CBS.
    :ivar valor_cred_presumido_cbs: Valor do Crédito Presumido CBS.
    :ivar valor_aliq_estadual_regular_ibs: Alíquota efetiva de
        tributação regular do IBS estadual.
    :ivar valor_aliq_municipal_regular_ibs: Alíquota efetiva de
        tributação regular do IBS municipal.
    :ivar valor_aliq_regular_cbs: Alíquota efetiva de tributação regular
        da CBS.
    :ivar valor_estadual_regular_ibs: Valor da tributação regular do IBS
        estadual.
    :ivar valor_municipal_regular_ibs: Valor da tributação regular do
        IBS municipal.
    :ivar valor_regular_cbs: Valor da tributação regular da CBS.
    :ivar valor_total_ree_rep_res: Valor total dos valores não inclusos
        na base de cálculo, somatória dos valores informados pelo
        contribuinte no campo vlrReeRepRes.
    :ivar valor_aliq_estadual_ibscompra_gov: Valor da alíquota estadual
        para o IBS, referente a compra governamental.
    :ivar valor_estadual_bscompra_gov: Valor do IBS estadual referente a
        compra governamental
    :ivar valor_aliq_municipal_ibscompra_gov: Valor da alíquota
        municipal para o IBS, referente a compra governamental.
    :ivar valor_municipal_ibscompra_gov: Valor do IBS municipal
        referente a compra governamental
    :ivar valor_aliq_cbscompra_gov: Valor da alíquota da CBS, referente
        a compra governamental.
    :ivar valor_cbscompra_gov: Valor da CBS referente a compra
        governamental
    """

    class Meta:
        name = "tpRetornoComplementarIBSCBS"

    adquirente: None | TpInformacoesPessoa = field(
        default=None,
        metadata={
            "name": "Adquirente",
            "type": "Element",
            "namespace": "",
        },
    )
    valor_bcibscbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorBCIBSCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_estadual_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqEstadualIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_perc_red_estadual_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorPercRedEstadualIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_efetiva_estadual_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqEfetivaEstadualIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_estadual_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorEstadualIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_municipal_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqMunicipalIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_perc_red_municipal_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorPercRedMunicipalIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_efetiva_municipal_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqEfetivaMunicipalIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_municipal_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorMunicipalIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_perc_red_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorPercRedCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_efetiva_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqEfetivaCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_perc_diferimento_estadual: None | str = field(
        default=None,
        metadata={
            "name": "ValorPercDiferimentoEstadual",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_diferimento_estadual: None | str = field(
        default=None,
        metadata={
            "name": "ValorDiferimentoEstadual",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_perc_diferimento_municipal: None | str = field(
        default=None,
        metadata={
            "name": "ValorPercDiferimentoMunicipal",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_diferimento_municipal: None | str = field(
        default=None,
        metadata={
            "name": "ValorDiferimentoMunicipal",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_perc_diferimento_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorPercDiferimentoCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_diferimento_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorDiferimentoCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    codigo_class_cred_presumido_ibs: None | str = field(
        default=None,
        metadata={
            "name": "CodigoClassCredPresumidoIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_perc_cred_presumido_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorPercCredPresumidoIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_cred_presumido_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorCredPresumidoIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    codigo_class_cred_presumido_cbs: None | str = field(
        default=None,
        metadata={
            "name": "CodigoClassCredPresumidoCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_perc_cred_presumido_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorPercCredPresumidoCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_cred_presumido_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorCredPresumidoCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_estadual_regular_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqEstadualRegularIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_municipal_regular_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqMunicipalRegularIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_regular_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqRegularCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_estadual_regular_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorEstadualRegularIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_municipal_regular_ibs: None | str = field(
        default=None,
        metadata={
            "name": "ValorMunicipalRegularIBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_regular_cbs: None | str = field(
        default=None,
        metadata={
            "name": "ValorRegularCBS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_total_ree_rep_res: None | str = field(
        default=None,
        metadata={
            "name": "ValorTotalReeRepRes",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_estadual_ibscompra_gov: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqEstadualIBSCompraGov",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_estadual_bscompra_gov: None | str = field(
        default=None,
        metadata={
            "name": "ValorEstadualBSCompraGov",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_municipal_ibscompra_gov: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqMunicipalIBSCompraGov",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_municipal_ibscompra_gov: None | str = field(
        default=None,
        metadata={
            "name": "ValorMunicipalIBSCompraGov",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_aliq_cbscompra_gov: None | str = field(
        default=None,
        metadata={
            "name": "ValorAliqCBSCompraGov",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_cbscompra_gov: None | str = field(
        default=None,
        metadata={
            "name": "ValorCBSCompraGov",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )


@dataclass(kw_only=True)
class TpValores:
    """
    Informações relacionadas aos valores do serviço prestado para IBS e à
    CBS.

    :ivar g_ree_rep_res: Grupo de informações relativas a valores
        incluídos neste documento e recebidos por motivo de estarem
        relacionadas a operações de terceiros, objeto de reembolso,
        repasse ou ressarcimento pelo recebedor, já tributados e aqui
        referenciados.
    :ivar trib: Grupo de informações relacionados aos tributos IBS e
        CBS.
    """

    class Meta:
        name = "tpValores"

    g_ree_rep_res: None | TpGrupoReeRepRes = field(
        default=None,
        metadata={
            "name": "gReeRepRes",
            "type": "Element",
            "namespace": "",
        },
    )
    trib: TpTrib = field(
        metadata={
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass(kw_only=True)
class TpIbscbs:
    """
    Tipo das informações do IBS/CBS.

    :ivar fin_nfse: Indicador da finalidade da emissão de NFS-e. 0 =
        NFS-e regular.
    :ivar ind_final: Indica operação de uso ou consumo pessoal. (0-Não
        ou 1-Sim). 0 - Não. 1 - Sim.
    :ivar c_ind_op: Código indicador da operação de fornecimento,
        conforme tabela "código indicador de operação". Referente à
        tabela de indicador da operação publicada no ANEXO AnexoVII-
        IndOp_IBSCBS_V1.00.00-.xlsx.
    :ivar tp_oper: Tipo de Operação com Entes Governamentais ou outros
        serviços sobre bens imóveis.
    :ivar g_ref_nfse: Grupo de NFS-e referenciadas.
    :ivar tp_ente_gov: Tipo do ente da compra governamental.
    :ivar ind_dest: Indica o Destinatário dos serviços.
    :ivar dest: Destinatário.
    :ivar valores: Informações relacionadas aos valores do serviço
        prestado para IBS e à CBS.
    :ivar imovelobra: Informações sobre o Tipo de Imóvel/Obra.
    """

    class Meta:
        name = "tpIBSCBS"

    fin_nfse: TpFinNfse = field(
        metadata={
            "name": "finNFSe",
            "type": "Element",
            "namespace": "",
        }
    )
    ind_final: TpNaoSim = field(
        metadata={
            "name": "indFinal",
            "type": "Element",
            "namespace": "",
        }
    )
    c_ind_op: str = field(
        metadata={
            "name": "cIndOp",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{6}",
        }
    )
    tp_oper: None | TpOper = field(
        default=None,
        metadata={
            "name": "tpOper",
            "type": "Element",
            "namespace": "",
        },
    )
    g_ref_nfse: None | TpGrefNfse = field(
        default=None,
        metadata={
            "name": "gRefNFSe",
            "type": "Element",
            "namespace": "",
        },
    )
    tp_ente_gov: None | TpEnteGov = field(
        default=None,
        metadata={
            "name": "tpEnteGov",
            "type": "Element",
            "namespace": "",
        },
    )
    ind_dest: TpIndDest = field(
        metadata={
            "name": "indDest",
            "type": "Element",
            "namespace": "",
        }
    )
    dest: None | TpInformacoesPessoa = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    valores: TpValores = field(
        metadata={
            "type": "Element",
            "namespace": "",
        }
    )
    imovelobra: None | TpImovelObra = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass(kw_only=True)
class TpNfe:
    """
    Tipo que representa uma NFS-e.

    :ivar assinatura: Assinatura digital da NFS-e.
    :ivar chave_nfe: Chave de identificação da NFS-e.
    :ivar data_emissao_nfe: Data de emissão da NFS-e
    :ivar numero_lote: Número de lote gerador da NFS-e.
    :ivar chave_rps: Chave do RPS que originou a NFS-e.
    :ivar tipo_rps: Tipo do RPS emitido.
    :ivar data_emissao_rps: Data de emissão do RPS que originou a NFS-e.
    :ivar data_fato_gerador_nfe: Data do fato gerador da NFS-e.
    :ivar cpfcnpjprestador: CPF/CNPJ do Prestador do serviço.
    :ivar razao_social_prestador: Nome/Razão Social do Prestador.
    :ivar endereco_prestador: Endereço do Prestador.
    :ivar email_prestador: E-mail do Prestador.
    :ivar status_nfe: Status da NFS-e.
    :ivar data_cancelamento: Data de cancelamento da NFS-e.
    :ivar tributacao_nfe: Tributação da NFS-e.
    :ivar opcao_simples: Opção pelo Simples.
    :ivar numero_guia: Número da guia vinculada a NFS-e.
    :ivar data_quitacao_guia: Data de quitação da guia vinculada a
        NFS-e.
    :ivar valor_servicos: Valor dos serviços prestados.
    :ivar valor_deducoes: Valor das deduções.
    :ivar valor_pis: Valor da retenção do PIS.
    :ivar valor_cofins: Valor da retenção do COFINS.
    :ivar valor_inss: Valor da retenção do INSS.
    :ivar valor_ir: Valor da retenção do IR.
    :ivar valor_csll: Valor da retenção do CSLL.
    :ivar codigo_servico: Código do serviço.
    :ivar aliquota_servicos: Valor da alíquota.
    :ivar valor_iss: Valor do ISS.
    :ivar valor_credito: Valor do crédito gerado.
    :ivar issretido: Retenção do ISS.
    :ivar cpfcnpjtomador: CPF/CNPJ do tomador do serviço.
    :ivar inscricao_municipal_tomador: Inscrição Municipal do Tomador.
    :ivar inscricao_estadual_tomador: Inscrição Estadual do tomador.
    :ivar razao_social_tomador: Nome/Razão Social do tomador.
    :ivar endereco_tomador: Endereço do tomador.
    :ivar email_tomador: E-mail do tomador.
    :ivar cpfcnpjintermediario: CNPJ do intermediário de serviço.
    :ivar inscricao_municipal_intermediario: Inscrição Municipal do
        intermediário de serviço.
    :ivar issretido_intermediario: Retenção do ISS pelo intermediário de
        serviço.
    :ivar email_intermediario: E-mail do intermediário de serviço.
    :ivar discriminacao: Descrição dos serviços.
    :ivar valor_carga_tributaria: Valor da carga tributária total em R$.
    :ivar percentual_carga_tributaria: Valor percentual da carga
        tributária.
    :ivar fonte_carga_tributaria: Fonte de informação da carga
        tributária.
    :ivar codigo_cei: Código do CEI - Cadastro específico do INSS.
    :ivar matricula_obra: Código que representa a matrícula da obra no
        sistema de cadastro de obras.
    :ivar municipio_prestacao: Código da cidade do município da
        prestação do serviço.
    :ivar numero_encapsulamento: Código que representa o número do
        encapsulamento da obra.
    :ivar valor_total_recebido: Valor do total recebido.
    :ivar retencao_pis_cofins: Tipo de retenção para os tributos
        federais PIS/COFINS e CSLL
    :ivar valor_inicial_cobrado: Valor inicial cobrado pela prestação do
        serviço, antes de tributos, multa e juros. "Valor dos serviços
        antes dos tributos". Corresponde ao valor cobrado pela prestação
        do serviço, antes de tributos, multa e juros. Informado para
        realizar o cálculo dos tributos do início para o fim.
    :ivar valor_final_cobrado: Valor final cobrado pela prestação do
        serviço, incluindo todos os tributos. "Valor total na nota".
        Corresponde ao valor final cobrado pela prestação do serviço,
        incluindo todos os tributos, multa e juros. Informado para
        realizar o cálculo dos impostos do fim para o início.
    :ivar valor_multa: Valor da multa.
    :ivar valor_juros: Valor dos juros.
    :ivar valor_ipi: Valor de IPI.
    :ivar exigibilidade_suspensa: Indica se é uma emissão com
        exigibilidade suspensa.
    :ivar pagamento_parcelado_antecipado: Indica de nota fiscal de
        pagamento parcelado antecipado (realizado antes do
        fornecimento).
    :ivar ncm: Informe o número NCM (Nomenclatura Comum do Mercosul).
    :ivar nbs: Informe o número NBS (Nomenclatura Brasileira de
        Serviços).
    :ivar atv_evento: Informações dos Tipos de evento.
    :ivar c_loc_prestacao:
    :ivar c_pais_prestacao:
    :ivar ibscbs: Informações declaradas pelo emitente referentes ao IBS
        e à CBS.
    :ivar retorno_complementar_ibscbs: Informações complementares
        referentes ao IBS e à CBS.
    """

    class Meta:
        name = "tpNFe"

    assinatura: None | bytes = field(
        default=None,
        metadata={
            "name": "Assinatura",
            "type": "Element",
            "namespace": "",
            "format": "base64",
        },
    )
    chave_nfe: TpChaveNfe = field(
        metadata={
            "name": "ChaveNFe",
            "type": "Element",
            "namespace": "",
        }
    )
    data_emissao_nfe: XmlDateTime = field(
        metadata={
            "name": "DataEmissaoNFe",
            "type": "Element",
            "namespace": "",
        }
    )
    numero_lote: None | str = field(
        default=None,
        metadata={
            "name": "NumeroLote",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    chave_rps: None | TpChaveRps = field(
        default=None,
        metadata={
            "name": "ChaveRPS",
            "type": "Element",
            "namespace": "",
        },
    )
    tipo_rps: None | TpTipoRps = field(
        default=None,
        metadata={
            "name": "TipoRPS",
            "type": "Element",
            "namespace": "",
        },
    )
    data_emissao_rps: None | XmlDate = field(
        default=None,
        metadata={
            "name": "DataEmissaoRPS",
            "type": "Element",
            "namespace": "",
        },
    )
    data_fato_gerador_nfe: XmlDateTime = field(
        metadata={
            "name": "DataFatoGeradorNFe",
            "type": "Element",
            "namespace": "",
        }
    )
    cpfcnpjprestador: TpCpfcnpj = field(
        metadata={
            "name": "CPFCNPJPrestador",
            "type": "Element",
            "namespace": "",
        }
    )
    razao_social_prestador: str = field(
        metadata={
            "name": "RazaoSocialPrestador",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 75,
            "white_space": "collapse",
        }
    )
    endereco_prestador: TpEndereco = field(
        metadata={
            "name": "EnderecoPrestador",
            "type": "Element",
            "namespace": "",
        }
    )
    email_prestador: None | str = field(
        default=None,
        metadata={
            "name": "EmailPrestador",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 75,
            "white_space": "collapse",
        },
    )
    status_nfe: TpStatusNfe = field(
        metadata={
            "name": "StatusNFe",
            "type": "Element",
            "namespace": "",
        }
    )
    data_cancelamento: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "DataCancelamento",
            "type": "Element",
            "namespace": "",
        },
    )
    tributacao_nfe: str = field(
        metadata={
            "name": "TributacaoNFe",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 1,
            "white_space": "collapse",
        }
    )
    opcao_simples: TpOpcaoSimples = field(
        metadata={
            "name": "OpcaoSimples",
            "type": "Element",
            "namespace": "",
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
    data_quitacao_guia: None | XmlDate = field(
        default=None,
        metadata={
            "name": "DataQuitacaoGuia",
            "type": "Element",
            "namespace": "",
        },
    )
    valor_servicos: str = field(
        metadata={
            "name": "ValorServicos",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    valor_deducoes: None | str = field(
        default=None,
        metadata={
            "name": "ValorDeducoes",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_pis: None | str = field(
        default=None,
        metadata={
            "name": "ValorPIS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_cofins: None | str = field(
        default=None,
        metadata={
            "name": "ValorCOFINS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_inss: None | str = field(
        default=None,
        metadata={
            "name": "ValorINSS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_ir: None | str = field(
        default=None,
        metadata={
            "name": "ValorIR",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_csll: None | str = field(
        default=None,
        metadata={
            "name": "ValorCSLL",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    codigo_servico: str = field(
        metadata={
            "name": "CodigoServico",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{4,5}",
        }
    )
    aliquota_servicos: Decimal = field(
        metadata={
            "name": "AliquotaServicos",
            "type": "Element",
            "namespace": "",
            "min_inclusive": Decimal("0"),
            "total_digits": 5,
            "fraction_digits": 4,
        }
    )
    valor_iss: str = field(
        metadata={
            "name": "ValorISS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    valor_credito: str = field(
        metadata={
            "name": "ValorCredito",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    issretido: bool = field(
        metadata={
            "name": "ISSRetido",
            "type": "Element",
            "namespace": "",
        }
    )
    cpfcnpjtomador: None | TpCpfcnpjnif = field(
        default=None,
        metadata={
            "name": "CPFCNPJTomador",
            "type": "Element",
            "namespace": "",
        },
    )
    inscricao_municipal_tomador: None | str = field(
        default=None,
        metadata={
            "name": "InscricaoMunicipalTomador",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    inscricao_estadual_tomador: None | str = field(
        default=None,
        metadata={
            "name": "InscricaoEstadualTomador",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,19}",
        },
    )
    razao_social_tomador: None | str = field(
        default=None,
        metadata={
            "name": "RazaoSocialTomador",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 75,
            "white_space": "collapse",
        },
    )
    endereco_tomador: None | TpEndereco = field(
        default=None,
        metadata={
            "name": "EnderecoTomador",
            "type": "Element",
            "namespace": "",
        },
    )
    email_tomador: None | str = field(
        default=None,
        metadata={
            "name": "EmailTomador",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 75,
            "white_space": "collapse",
        },
    )
    cpfcnpjintermediario: None | TpCpfcnpj = field(
        default=None,
        metadata={
            "name": "CPFCNPJIntermediario",
            "type": "Element",
            "namespace": "",
        },
    )
    inscricao_municipal_intermediario: None | str = field(
        default=None,
        metadata={
            "name": "InscricaoMunicipalIntermediario",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    issretido_intermediario: None | str = field(
        default=None,
        metadata={
            "name": "ISSRetidoIntermediario",
            "type": "Element",
            "namespace": "",
        },
    )
    email_intermediario: None | str = field(
        default=None,
        metadata={
            "name": "EmailIntermediario",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 75,
            "white_space": "collapse",
        },
    )
    discriminacao: str = field(
        metadata={
            "name": "Discriminacao",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 2000,
            "white_space": "collapse",
        }
    )
    valor_carga_tributaria: None | str = field(
        default=None,
        metadata={
            "name": "ValorCargaTributaria",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    percentual_carga_tributaria: None | Decimal = field(
        default=None,
        metadata={
            "name": "PercentualCargaTributaria",
            "type": "Element",
            "namespace": "",
            "min_inclusive": Decimal("0"),
            "total_digits": 7,
            "fraction_digits": 4,
        },
    )
    fonte_carga_tributaria: None | str = field(
        default=None,
        metadata={
            "name": "FonteCargaTributaria",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 10,
            "white_space": "collapse",
        },
    )
    codigo_cei: None | str = field(
        default=None,
        metadata={
            "name": "CodigoCEI",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    matricula_obra: None | str = field(
        default=None,
        metadata={
            "name": "MatriculaObra",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    municipio_prestacao: None | str = field(
        default=None,
        metadata={
            "name": "MunicipioPrestacao",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7}",
        },
    )
    numero_encapsulamento: None | str = field(
        default=None,
        metadata={
            "name": "NumeroEncapsulamento",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    valor_total_recebido: None | str = field(
        default=None,
        metadata={
            "name": "ValorTotalRecebido",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    retencao_pis_cofins: None | TpRetencaoPisCofins = field(
        default=None,
        metadata={
            "name": "RetencaoPisCofins",
            "type": "Element",
            "namespace": "",
        },
    )
    valor_inicial_cobrado: None | str = field(
        default=None,
        metadata={
            "name": "ValorInicialCobrado",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_final_cobrado: None | str = field(
        default=None,
        metadata={
            "name": "ValorFinalCobrado",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_multa: None | str = field(
        default=None,
        metadata={
            "name": "ValorMulta",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_juros: None | str = field(
        default=None,
        metadata={
            "name": "ValorJuros",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_ipi: None | str = field(
        default=None,
        metadata={
            "name": "ValorIPI",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    exigibilidade_suspensa: TpNaoSim = field(
        metadata={
            "name": "ExigibilidadeSuspensa",
            "type": "Element",
            "namespace": "",
        }
    )
    pagamento_parcelado_antecipado: None | TpNaoSim = field(
        default=None,
        metadata={
            "name": "PagamentoParceladoAntecipado",
            "type": "Element",
            "namespace": "",
        },
    )
    ncm: None | str = field(
        default=None,
        metadata={
            "name": "NCM",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{8}",
        },
    )
    nbs: None | str = field(
        default=None,
        metadata={
            "name": "NBS",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{9}",
        },
    )
    atv_evento: None | TpAtividadeEvento = field(
        default=None,
        metadata={
            "name": "atvEvento",
            "type": "Element",
            "namespace": "",
        },
    )
    c_loc_prestacao: None | str = field(
        default=None,
        metadata={
            "name": "cLocPrestacao",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7}",
        },
    )
    c_pais_prestacao: None | str = field(
        default=None,
        metadata={
            "name": "cPaisPrestacao",
            "type": "Element",
            "namespace": "",
            "pattern": r"[A-Z]{2}",
        },
    )
    ibscbs: None | TpIbscbs = field(
        default=None,
        metadata={
            "name": "IBSCBS",
            "type": "Element",
            "namespace": "",
        },
    )
    retorno_complementar_ibscbs: None | TpRetornoComplementarIbscbs = field(
        default=None,
        metadata={
            "name": "RetornoComplementarIBSCBS",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass(kw_only=True)
class TpRps:
    """
    Tipo que representa um RPS.

    :ivar assinatura: Assinatura digital do RPS.
    :ivar chave_rps: Informe a chave do RPS emitido.
    :ivar tipo_rps: Informe o Tipo do RPS emitido.
    :ivar data_emissao: Informe a Data de emissão do RPS.
    :ivar status_rps: Informe o Status do RPS.
    :ivar tributacao_rps: Informe o tipo de tributação do RPS.
    :ivar valor_deducoes: Informe o valor das deduções.
    :ivar valor_pis: Informe o valor da retenção do PIS.
    :ivar valor_cofins: Informe o valor da retenção do COFINS.
    :ivar valor_inss: Informe o valor da retenção do INSS.
    :ivar valor_ir: Informe o valor da retenção do IR.
    :ivar valor_csll: Informe o valor da retenção do CSLL.
    :ivar codigo_servico: Informe o código do serviço do RPS. Este
        código deve pertencer à lista de serviços.
    :ivar aliquota_servicos: Informe o valor da alíquota. Obs. O
        conteúdo deste campo será ignorado caso a tributação ocorra no
        município (Situação do RPS = T ).
    :ivar issretido: Informe a retenção.
    :ivar cpfcnpjtomador: Informe o CPF/CNPJ do tomador do serviço. O
        conteúdo deste campo será ignorado caso o campo
        InscricaoMunicipalTomador esteja preenchido.
    :ivar inscricao_municipal_tomador: Informe a Inscrição Municipal do
        Tomador. ATENÇÃO: Este campo só deverá ser preenchido para
        tomadores estabelecidos no município de São Paulo (CCM). Quando
        este campo for preenchido, seu conteúdo será considerado como
        prioritário com relação ao campo de CPF/CNPJ do Tomador, sendo
        utilizado para identificar o Tomador e recuperar seus dados da
        base de dados da Prefeitura.
    :ivar inscricao_estadual_tomador: Informe a inscrição estadual do
        tomador. Este campo será ignorado caso seja fornecido um
        CPF/CNPJ ou a Inscrição Municipal do tomador pertença ao
        município de São Paulo.
    :ivar razao_social_tomador: Informe o Nome/Razão Social do tomador.
        Este campo é obrigatório apenas para tomadores Pessoa Jurídica
        (CNPJ). Este campo será ignorado caso seja fornecido um CPF/CNPJ
        ou a Inscrição Municipal do tomador pertença ao município de São
        Paulo.
    :ivar endereco_tomador: Informe o endereço do tomador. Os campos do
        endereço são obrigatórios apenas para tomadores pessoa jurídica
        (CNPJ informado). O conteúdo destes campos será ignorado caso
        seja fornecido um CPF/CNPJ ou a Inscrição Municipal do tomador
        pertença ao município de São Paulo.
    :ivar email_tomador: Informe o e-mail do tomador.
    :ivar cpfcnpjintermediario: CNPJ do intermediário de serviço.
    :ivar inscricao_municipal_intermediario: Inscrição Municipal do
        intermediário de serviço.
    :ivar issretido_intermediario: Retenção do ISS pelo intermediário de
        serviço.
    :ivar email_intermediario: E-mail do intermediário de serviço.
    :ivar discriminacao: Informe a discriminação dos serviços.
    :ivar valor_carga_tributaria: Valor da carga tributária total em R$.
    :ivar percentual_carga_tributaria: Valor percentual da carga
        tributária.
    :ivar fonte_carga_tributaria: Fonte de informação da carga
        tributária.
    :ivar codigo_cei: Código do CEI - Cadastro específico do INSS.
    :ivar matricula_obra: Código que representa a matrícula da obra no
        sistema de cadastro de obras.
    :ivar municipio_prestacao: Código da cidade do município da
        prestação do serviço.
    :ivar numero_encapsulamento: Código que representa o número do
        encapsulamento da obra.
    :ivar valor_total_recebido: Valor do total recebido.
    :ivar retencao_pis_cofins: Tipo de retenção para os tributos
        federais PIS/COFINS e CSLL
    :ivar valor_inicial_cobrado: Valor inicial cobrado pela prestação do
        serviço, antes de tributos, multa e juros. "Valor dos serviços
        antes dos tributos". Corresponde ao valor cobrado pela prestação
        do serviço, antes de tributos, multa e juros. Informado para
        realizar o cálculo dos tributos do início para o fim.
    :ivar valor_final_cobrado: Valor final cobrado pela prestação do
        serviço, incluindo todos os tributos. "Valor total na nota".
        Corresponde ao valor final cobrado pela prestação do serviço,
        incluindo todos os tributos, multa e juros. Informado para
        realizar o cálculo dos impostos do fim para o início.
    :ivar valor_multa: Valor da multa.
    :ivar valor_juros: Valor dos juros.
    :ivar valor_ipi: Valor de IPI.
    :ivar exigibilidade_suspensa: Informe se é uma emissão com
        exigibilidade suspensa. 0 - Não. 1 - Sim.
    :ivar pagamento_parcelado_antecipado: Informe a nota fiscal de
        pagamento parcelado antecipado (realizado antes do
        fornecimento). 0 - Não. 1 - Sim.
    :ivar ncm: Informe o número NCM (Nomenclatura Comum do Mercosul).
    :ivar nbs: Informe o número NBS (Nomenclatura Brasileira de
        Serviços).
    :ivar atv_evento: Informações dos Tipos de evento.
    :ivar c_loc_prestacao:
    :ivar c_pais_prestacao:
    :ivar ibscbs: Informações declaradas pelo emitente referentes ao IBS
        e à CBS.
    """

    class Meta:
        name = "tpRPS"

    assinatura: bytes = field(
        metadata={
            "name": "Assinatura",
            "type": "Element",
            "namespace": "",
            "format": "base64",
        }
    )
    chave_rps: TpChaveRps = field(
        metadata={
            "name": "ChaveRPS",
            "type": "Element",
            "namespace": "",
        }
    )
    tipo_rps: TpTipoRps = field(
        metadata={
            "name": "TipoRPS",
            "type": "Element",
            "namespace": "",
        }
    )
    data_emissao: XmlDate = field(
        metadata={
            "name": "DataEmissao",
            "type": "Element",
            "namespace": "",
        }
    )
    status_rps: TpStatusNfe = field(
        metadata={
            "name": "StatusRPS",
            "type": "Element",
            "namespace": "",
        }
    )
    tributacao_rps: str = field(
        metadata={
            "name": "TributacaoRPS",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 1,
            "white_space": "collapse",
        }
    )
    valor_deducoes: str = field(
        metadata={
            "name": "ValorDeducoes",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    valor_pis: str = field(
        metadata={
            "name": "ValorPIS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    valor_cofins: str = field(
        metadata={
            "name": "ValorCOFINS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    valor_inss: str = field(
        metadata={
            "name": "ValorINSS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    valor_ir: str = field(
        metadata={
            "name": "ValorIR",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    valor_csll: str = field(
        metadata={
            "name": "ValorCSLL",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    codigo_servico: str = field(
        metadata={
            "name": "CodigoServico",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{4,5}",
        }
    )
    aliquota_servicos: Decimal = field(
        metadata={
            "name": "AliquotaServicos",
            "type": "Element",
            "namespace": "",
            "min_inclusive": Decimal("0"),
            "total_digits": 5,
            "fraction_digits": 4,
        }
    )
    issretido: bool = field(
        metadata={
            "name": "ISSRetido",
            "type": "Element",
            "namespace": "",
        }
    )
    cpfcnpjtomador: None | TpCpfcnpjnif = field(
        default=None,
        metadata={
            "name": "CPFCNPJTomador",
            "type": "Element",
            "namespace": "",
        },
    )
    inscricao_municipal_tomador: None | str = field(
        default=None,
        metadata={
            "name": "InscricaoMunicipalTomador",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    inscricao_estadual_tomador: None | str = field(
        default=None,
        metadata={
            "name": "InscricaoEstadualTomador",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,19}",
        },
    )
    razao_social_tomador: None | str = field(
        default=None,
        metadata={
            "name": "RazaoSocialTomador",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 75,
            "white_space": "collapse",
        },
    )
    endereco_tomador: None | TpEndereco = field(
        default=None,
        metadata={
            "name": "EnderecoTomador",
            "type": "Element",
            "namespace": "",
        },
    )
    email_tomador: None | str = field(
        default=None,
        metadata={
            "name": "EmailTomador",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 75,
            "white_space": "collapse",
        },
    )
    cpfcnpjintermediario: None | TpCpfcnpj = field(
        default=None,
        metadata={
            "name": "CPFCNPJIntermediario",
            "type": "Element",
            "namespace": "",
        },
    )
    inscricao_municipal_intermediario: None | str = field(
        default=None,
        metadata={
            "name": "InscricaoMunicipalIntermediario",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    issretido_intermediario: None | str = field(
        default=None,
        metadata={
            "name": "ISSRetidoIntermediario",
            "type": "Element",
            "namespace": "",
        },
    )
    email_intermediario: None | str = field(
        default=None,
        metadata={
            "name": "EmailIntermediario",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 75,
            "white_space": "collapse",
        },
    )
    discriminacao: str = field(
        metadata={
            "name": "Discriminacao",
            "type": "Element",
            "namespace": "",
            "min_length": 1,
            "max_length": 2000,
            "white_space": "collapse",
        }
    )
    valor_carga_tributaria: None | str = field(
        default=None,
        metadata={
            "name": "ValorCargaTributaria",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    percentual_carga_tributaria: None | Decimal = field(
        default=None,
        metadata={
            "name": "PercentualCargaTributaria",
            "type": "Element",
            "namespace": "",
            "min_inclusive": Decimal("0"),
            "total_digits": 7,
            "fraction_digits": 4,
        },
    )
    fonte_carga_tributaria: None | str = field(
        default=None,
        metadata={
            "name": "FonteCargaTributaria",
            "type": "Element",
            "namespace": "",
            "min_length": 0,
            "max_length": 10,
            "white_space": "collapse",
        },
    )
    codigo_cei: None | str = field(
        default=None,
        metadata={
            "name": "CodigoCEI",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    matricula_obra: None | str = field(
        default=None,
        metadata={
            "name": "MatriculaObra",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    municipio_prestacao: None | str = field(
        default=None,
        metadata={
            "name": "MunicipioPrestacao",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7}",
        },
    )
    numero_encapsulamento: None | str = field(
        default=None,
        metadata={
            "name": "NumeroEncapsulamento",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{1,12}",
        },
    )
    valor_total_recebido: None | str = field(
        default=None,
        metadata={
            "name": "ValorTotalRecebido",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    retencao_pis_cofins: None | TpRetencaoPisCofins = field(
        default=None,
        metadata={
            "name": "RetencaoPisCofins",
            "type": "Element",
            "namespace": "",
        },
    )
    valor_inicial_cobrado: None | str = field(
        default=None,
        metadata={
            "name": "ValorInicialCobrado",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_final_cobrado: None | str = field(
        default=None,
        metadata={
            "name": "ValorFinalCobrado",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_multa: None | str = field(
        default=None,
        metadata={
            "name": "ValorMulta",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_juros: None | str = field(
        default=None,
        metadata={
            "name": "ValorJuros",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        },
    )
    valor_ipi: str = field(
        metadata={
            "name": "ValorIPI",
            "type": "Element",
            "namespace": "",
            "min_inclusive": "0",
            "total_digits": 15,
            "fraction_digits": 2,
            "pattern": r"0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,12}(\.[0-9]{0,2})?",
        }
    )
    exigibilidade_suspensa: TpNaoSim = field(
        metadata={
            "name": "ExigibilidadeSuspensa",
            "type": "Element",
            "namespace": "",
        }
    )
    pagamento_parcelado_antecipado: None | TpNaoSim = field(
        default=None,
        metadata={
            "name": "PagamentoParceladoAntecipado",
            "type": "Element",
            "namespace": "",
        },
    )
    ncm: None | str = field(
        default=None,
        metadata={
            "name": "NCM",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{8}",
        },
    )
    nbs: str = field(
        metadata={
            "name": "NBS",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{9}",
        }
    )
    atv_evento: None | TpAtividadeEvento = field(
        default=None,
        metadata={
            "name": "atvEvento",
            "type": "Element",
            "namespace": "",
        },
    )
    c_loc_prestacao: None | str = field(
        default=None,
        metadata={
            "name": "cLocPrestacao",
            "type": "Element",
            "namespace": "",
            "pattern": r"[0-9]{7}",
        },
    )
    c_pais_prestacao: None | str = field(
        default=None,
        metadata={
            "name": "cPaisPrestacao",
            "type": "Element",
            "namespace": "",
            "pattern": r"[A-Z]{2}",
        },
    )
    ibscbs: TpIbscbs = field(
        metadata={
            "name": "IBSCBS",
            "type": "Element",
            "namespace": "",
        }
    )
