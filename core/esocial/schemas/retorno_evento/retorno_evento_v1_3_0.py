from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from xsdata.models.datatype import XmlDate, XmlDateTime
from core.esocial.schemas.retorno_evento.xmldsig_core_schema import Signature

__NAMESPACE__ = "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0"


@dataclass
class TdadosRecepcao:
    """
    Define os dados de recepção do evento.
    "

    :ivar tp_amb: Identificação do ambiente que recebeu o arquivo.
    :ivar dh_recepcao: Data hora recepção.
    :ivar versao_app_recepcao: Versão do aplicativo de recepção.
    :ivar protocolo_envio_lote: Código de retorno do lote.
    """
    class Meta:
        name = "TDadosRecepcao"

    tp_amb: Optional[int] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
        }
    )
    dh_recepcao: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "dhRecepcao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
        }
    )
    versao_app_recepcao: Optional[str] = field(
        default=None,
        metadata={
            "name": "versaoAppRecepcao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
            "max_length": 30,
        }
    )
    protocolo_envio_lote: Optional[str] = field(
        default=None,
        metadata={
            "name": "protocoloEnvioLote",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "max_length": 30,
        }
    )
@dataclass
class TideEmpregador:
    """
    Define a identificação do empregador.
    """

    class Meta:
        name = "TIdeEmpregador"

    tp_insc: Optional[int] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
            "max_length": 15,
        }
    )
@dataclass
class Tocorrencias:
    """
    Define uma ocorrência encontrada no processamento do evento.
    """

    class Meta:
        name = "TOcorrencias"

    ocorrencia: List["Tocorrencias.Ocorrencia"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "min_occurs": 1,
        }
    )

    @dataclass
    class Ocorrencia:
        """

        "

        :ivar tipo: Contém o tipo da ocorrência.
        :ivar codigo: Código da ocorrência
        :ivar descricao: Descrição da ocorrência
        :ivar localizacao: Contém a localização do erro no evento.
        """
        tipo: Optional[int] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
            }
        )
        codigo: Optional[int] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
            }
        )
        descricao: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
                "max_length": 2048,
            }
        )
        localizacao: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "max_length": 2048,
            }
        )
class RubricaTpR(Enum):
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
@dataclass
class TdadosProcessamentoEvento:
    """
    Define os dados de processamento dos eventos.
    "

    :ivar cd_resposta: Código de resposta da recepção do evento.
    :ivar desc_resposta: Contém a descrição correspondente ao código de
        resposta.
    :ivar versao_app_processamento: Contém a versão do aplicativo de
        processamento de eventos.
    :ivar dh_processamento: Contém a data e horário do processamento do
        eventos
    :ivar ocorrencias: Contém as ocorrências encontradas durante a
        validação do evento.
    """
    class Meta:
        name = "TDadosProcessamentoEvento"

    cd_resposta: Optional[int] = field(
        default=None,
        metadata={
            "name": "cdResposta",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
        }
    )
    desc_resposta: Optional[str] = field(
        default=None,
        metadata={
            "name": "descResposta",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
            "max_length": 2048,
        }
    )
    versao_app_processamento: Optional[str] = field(
        default=None,
        metadata={
            "name": "versaoAppProcessamento",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
            "max_length": 30,
        }
    )
    dh_processamento: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "dhProcessamento",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
        }
    )
    ocorrencias: Optional[Tocorrencias] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
        }
    )
@dataclass
class TdadosRecibo:
    """
    Define os dados do recibo do evento.
    "

    :ivar nr_recibo: Número do recibo do evento
    :ivar hash: Hash do arquivo recebido.
    :ivar contrato: Elemento raiz do retrato do contrato de trabalho.
    :ivar info_contribuinte: Informação do Contribuinte.
    :ivar info_estabelecimento: Retorno de Informações do
        Estabelecimento.
    :ivar info_lotacao: Informação do Contribuinte.
    :ivar rubricas:
    :ivar cpfs:
    """
    class Meta:
        name = "TDadosRecibo"

    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
            "max_length": 40,
        }
    )
    hash: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "required": True,
        }
    )
    contrato: Optional["TdadosRecibo.Contrato"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
        }
    )
    info_contribuinte: Optional["TdadosRecibo.InfoContribuinte"] = field(
        default=None,
        metadata={
            "name": "infoContribuinte",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
        }
    )
    info_estabelecimento: Optional["TdadosRecibo.InfoEstabelecimento"] = field(
        default=None,
        metadata={
            "name": "infoEstabelecimento",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
        }
    )
    info_lotacao: Optional["TdadosRecibo.InfoLotacao"] = field(
        default=None,
        metadata={
            "name": "infoLotacao ",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
        }
    )
    rubricas: Optional["TdadosRecibo.Rubricas"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
        }
    )
    cpfs: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            "pattern": r"([0-9]{1,11}(\|(\d{0,19}|(\d{1,19})(,\d{1,19})*)){4}\n)+",
        }
    )

    @dataclass
    class Contrato:
        """

        "

        :ivar ide_empregador: Informações de identificação do
            empregador.
        :ivar trabalhador: Identificação do Trabalhador.
        :ivar info_deficiencia: Pessoa com Deficiência.
        :ivar vinculo: Informações do Vínculo.
        :ivar info_celetista: Informações de Trabalhador Celetista.
        :ivar info_estatutario: Informações de Trabalhador Estatutário.
        :ivar info_contrato: Informações do Contrato de Trabalho.
        :ivar remuneracao: Informações da remuneração.
        :ivar duracao: Duração do Contrato de Trabalho.
        :ivar local_trab_geral: Estabelecimento onde o trabalhador
            exercerá suas atividades.
        :ivar hor_contratual: Informações do horário contratual.
        """
        ide_empregador: Optional["TdadosRecibo.Contrato.IdeEmpregador"] = field(
            default=None,
            metadata={
                "name": "ideEmpregador",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
            }
        )
        trabalhador: Optional["TdadosRecibo.Contrato.Trabalhador"] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
            }
        )
        info_deficiencia: Optional["TdadosRecibo.Contrato.InfoDeficiencia"] = field(
            default=None,
            metadata={
                "name": "infoDeficiencia",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            }
        )
        vinculo: Optional["TdadosRecibo.Contrato.Vinculo"] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            }
        )
        info_celetista: Optional["TdadosRecibo.Contrato.InfoCeletista"] = field(
            default=None,
            metadata={
                "name": "infoCeletista",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            }
        )
        info_estatutario: Optional["TdadosRecibo.Contrato.InfoEstatutario"] = field(
            default=None,
            metadata={
                "name": "infoEstatutario",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            }
        )
        info_contrato: Optional["TdadosRecibo.Contrato.InfoContrato"] = field(
            default=None,
            metadata={
                "name": "infoContrato",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
            }
        )
        remuneracao: Optional["TdadosRecibo.Contrato.Remuneracao"] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
            }
        )
        duracao: Optional["TdadosRecibo.Contrato.Duracao"] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            }
        )
        local_trab_geral: Optional["TdadosRecibo.Contrato.LocalTrabGeral"] = field(
            default=None,
            metadata={
                "name": "localTrabGeral",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            }
        )
        hor_contratual: Optional["TdadosRecibo.Contrato.HorContratual"] = field(
            default=None,
            metadata={
                "name": "horContratual",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
            }
        )

        @dataclass
        class IdeEmpregador:
            """

            "

            :ivar tp_insc: Preencher com o código correspondente ao tipo
                de inscrição, conforme tabela 5Validação: Deve ser igual
                a [1] (CNPJ) ou [2] (CPF).
            :ivar nr_insc: Informar o número de inscrição do
                contribuinte de acordo com o tipo de inscrição indicado
                no campo {tpInsc}. Se for um CNPJ deve ser informada
                apenas a Raiz/Base de oito posições, exceto se natureza
                jurídica de administração pública direta federal
                ([101-5], [104-0], [107-4], [116-3], situação em que o
                campo deve ser preenchido com o CNPJ completo (14
                posições).Validação: Se {tpInsc} for igual a [1], deve
                ser um número de CNPJ válido. Se {tpInsc} for igual a
                [2], deve ser um CPF válido.
            """
            tp_insc: Optional[int] = field(
                default=None,
                metadata={
                    "name": "tpInsc",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            nr_insc: Optional[int] = field(
                default=None,
                metadata={
                    "name": "nrInsc",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )

        @dataclass
        class Trabalhador:
            """

            "

            :ivar cpf_trab: Preencher com o número do CPF do
                trabalhador.
            :ivar nis_trab: Preencher com o número de inscrição do
                segurado - NIS, o qual pode ser o PIS, PASEP ou NIT.
            :ivar nm_trab: Nome do trabalhador.
            """
            cpf_trab: Optional[int] = field(
                default=None,
                metadata={
                    "name": "cpfTrab",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            nis_trab: Optional[int] = field(
                default=None,
                metadata={
                    "name": "nisTrab",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            nm_trab: Optional[str] = field(
                default=None,
                metadata={
                    "name": "nmTrab",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )

        @dataclass
        class InfoDeficiencia:
            """

            "

            :ivar info_cota: Informar se o trabalhador preenche cota de
                pessoas com deficiência habilitadas ou de beneficiários
                reabilitados.Valores Válidos: S, N.
            """
            info_cota: Optional[str] = field(
                default=None,
                metadata={
                    "name": "infoCota",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )

        @dataclass
        class Vinculo:
            matricula: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )

        @dataclass
        class InfoCeletista:
            """

            "

            :ivar dt_adm: Preencher com a data de admissão do
                trabalhador no respectivo vínculo.
            :ivar tp_reg_jor: Identifica o regime de jornada do
                empregado.
            :ivar dt_base: Mês relativo à data base da categoria
                profissional do trabalhador.
            :ivar cnpj_sind_categ_prof: Preencher com o CNPJ do
                sindicato representativo da categoria (Preponderante ou
                Diferenciada).
            """
            dt_adm: Optional[XmlDate] = field(
                default=None,
                metadata={
                    "name": "dtAdm",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            tp_reg_jor: Optional[int] = field(
                default=None,
                metadata={
                    "name": "tpRegJor",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            dt_base: Optional[int] = field(
                default=None,
                metadata={
                    "name": "dtBase",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                }
            )
            cnpj_sind_categ_prof: Optional[int] = field(
                default=None,
                metadata={
                    "name": "cnpjSindCategProf",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )

        @dataclass
        class InfoEstatutario:
            """

            "

            :ivar dt_posse: Data da posse do servidor.
            :ivar dt_exercicio: Data da entrada em exercício pelo
                servidor.
            """
            dt_posse: Optional[XmlDate] = field(
                default=None,
                metadata={
                    "name": "dtPosse",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            dt_exercicio: Optional[XmlDate] = field(
                default=None,
                metadata={
                    "name": "dtExercicio",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )

        @dataclass
        class InfoContrato:
            """

            "

            :ivar cargo: Informações do cargo.
            :ivar funcao: Informações da função.
            :ivar cod_categ: Preencher com o código da categoria do
                trabalhador.
            """
            cargo: Optional["TdadosRecibo.Contrato.InfoContrato.Cargo"] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                }
            )
            funcao: Optional["TdadosRecibo.Contrato.InfoContrato.Funcao"] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                }
            )
            cod_categ: Optional[int] = field(
                default=None,
                metadata={
                    "name": "codCateg",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )

            @dataclass
            class Cargo:
                """

                "

                :ivar cod_cargo: Preencher com o código do cargo.
                :ivar nm_cargo: Preencher com o nome do cargo
                :ivar cod_cbo: Classificação Brasileira de Ocupação -
                    CBO.
                """
                cod_cargo: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "codCargo",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                nm_cargo: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "nmCargo",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                cod_cbo: Optional[int] = field(
                    default=None,
                    metadata={
                        "name": "codCBO",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )

            @dataclass
            class Funcao:
                """

                "

                :ivar cod_funcao: Preencher com o código da função.
                :ivar dsc_funcao: Descrição da Função de confiança/Cargo
                    em Comissão.
                :ivar cod_cbo: Classificação Brasileira de Ocupação -
                    CBO.
                """
                cod_funcao: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "codFuncao",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                dsc_funcao: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "dscFuncao",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                cod_cbo: Optional[int] = field(
                    default=None,
                    metadata={
                        "name": "codCBO",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )

        @dataclass
        class Remuneracao:
            """

            "

            :ivar vr_sal_fx: Salário base do trabalhador, correspondente
                à parte fixa da remuneração.
            :ivar und_sal_fixo: Unidade de pagamento da parte fixa da
                remuneração, conforme opções abaixo:1 - Por Hora;2 - Por
                Dia;3 - Por Semana;4 - Por Quinzena;5 - Por Mês;6 - Por
                Tarefa;7 - Não aplicável - salário exclusivamente
                variável.Valores Válidos: 1, 2, 3, 4, 5, 6, 7.
            :ivar dsc_sal_var: Descrição do salário variável e como este
                é calculado. Ex.: Comissões pagas no percentual de 10%
                sobre as vendas.
            """
            vr_sal_fx: Optional[Decimal] = field(
                default=None,
                metadata={
                    "name": "vrSalFx",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            und_sal_fixo: Optional[int] = field(
                default=None,
                metadata={
                    "name": "undSalFixo",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            dsc_sal_var: Optional[str] = field(
                default=None,
                metadata={
                    "name": "dscSalVar",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                }
            )

        @dataclass
        class Duracao:
            """

            "

            :ivar tp_contr: Tipo de contrato de trabalho conforme opções
                abaixo:1 - Prazo indeterminado;2 - Prazo
                determinado.Valores Válidos: 1, 2..
            :ivar dt_term: Data do Término do contrato.
            :ivar clau_asseg: Indicacao de clausula asseguratoria.
            """
            tp_contr: Optional[int] = field(
                default=None,
                metadata={
                    "name": "tpContr",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            dt_term: Optional[XmlDate] = field(
                default=None,
                metadata={
                    "name": "dtTerm",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                }
            )
            clau_asseg: Optional[str] = field(
                default=None,
                metadata={
                    "name": "clauAsseg",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                }
            )

        @dataclass
        class LocalTrabGeral:
            """

            "

            :ivar tp_insc: Preencher com o código correspondente ao tipo
                de inscrição, conforme tabela 5.
            :ivar nr_insc: Número de inscrição do contribuinte.
            :ivar cnae:
            """
            tp_insc: Optional[int] = field(
                default=None,
                metadata={
                    "name": "tpInsc",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            nr_insc: Optional[int] = field(
                default=None,
                metadata={
                    "name": "nrInsc",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            cnae: Optional[int] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )

        @dataclass
        class HorContratual:
            """

            "

            :ivar qtd_hrs_sem: Quantidade média de horas relativas à
                jornada semanal do trabalhador.
            :ivar tp_jornada: Tipo da Jornada. Preencher com uma das
                opções:1 - Jornada Semanal (segunda a domingo) com
                apenas um horário padrão por dia da semana e folga
                fixa;2 - Jornada 12 x 36 (12 horas de trabalho seguidas
                de 36 horas ininterruptas de descanso);9 - Demais tipos
                de jornada (escala, turno de revezamento, permutas,
                horários rotativos, etc.).Valores Válidos: 1, 2, 9.
            :ivar dsc_tp_jorn: Descrição do tipo de jornada.
            :ivar tmp_parc: Contrato de trabalho em regime de tempo
                parcial, ou seja, aquele cuja jornada semanal não exceda
                25 horas semanais.Valores Válidos: S, N.
            :ivar horario: Informações diárias do horário contratual.
            """
            qtd_hrs_sem: Optional[Decimal] = field(
                default=None,
                metadata={
                    "name": "qtdHrsSem",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                }
            )
            tp_jornada: Optional[int] = field(
                default=None,
                metadata={
                    "name": "tpJornada",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            dsc_tp_jorn: Optional[str] = field(
                default=None,
                metadata={
                    "name": "dscTpJorn",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                }
            )
            tmp_parc: Optional[str] = field(
                default=None,
                metadata={
                    "name": "tmpParc",
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "required": True,
                }
            )
            horario: List["TdadosRecibo.Contrato.HorContratual.Horario"] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                    "max_occurs": 99,
                }
            )

            @dataclass
            class Horario:
                """

                "

                :ivar dia: Preencher com o código relativo ao dia do
                    horário:1 - Segunda-Feira;2 - Terça-Feira;3 -
                    Quarta-Feira;4 - Quinta-Feira;5 - Sexta-Feira;6 -
                    Sábado;7 - Domingo;8 - Dia variável.Valores Válidos:
                    1, 2, 3, 4, 5, 6, 7, 8.
                :ivar cod_hor_contrat: Preencher com o código atribuído
                    pela empresa para o Horário Contratual.
                :ivar hr_entr: Informar hora da entrada, no formato
                    HHMM.
                :ivar hr_saida: Informar hora da saída, no formato HHMM.
                :ivar dur_jornada: Preencher com o tempo de duração da
                    jornada, em minutos. Devem ser consideradas as horas
                    reduzidas noturnas, se houver.
                :ivar per_hor_flexivel: Indicar se é permitida a
                    flexibilidade:S - Sim;N - Não.Valores Válidos: S, N.
                :ivar horario_intervalo: Registro que detalha os
                    intervalos para a jornada. O preenchimento do
                    registro é obrigatório se existir ao menos um
                    intervalo.
                """
                dia: Optional[int] = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                cod_hor_contrat: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "codHorContrat",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                hr_entr: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "hrEntr",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                hr_saida: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "hrSaida",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                dur_jornada: Optional[int] = field(
                    default=None,
                    metadata={
                        "name": "durJornada",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                per_hor_flexivel: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "perHorFlexivel",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "required": True,
                    }
                )
                horario_intervalo: List["TdadosRecibo.Contrato.HorContratual.Horario.HorarioIntervalo"] = field(
                    default_factory=list,
                    metadata={
                        "name": "horarioIntervalo",
                        "type": "Element",
                        "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        "max_occurs": 99,
                    }
                )

                @dataclass
                class HorarioIntervalo:
                    """

                    "

                    :ivar tp_interv: Tipo de Intervalo da Jornada:1 -
                        Intervalo em Horário Fixo;2 - Intervalo em
                        Horário Variável.Valores Válidos: 1, 2.
                    :ivar dur_interv: Preencher com o tempo de duração
                        do intervalo, em minutos.
                    :ivar ini_interv: Informar a hora de início do
                        intervalo, no formato HHMM.
                    :ivar term_interv: Informar a hora de termino do
                        intervalo, no formato HHMM.
                    """
                    tp_interv: Optional[int] = field(
                        default=None,
                        metadata={
                            "name": "tpInterv",
                            "type": "Element",
                            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                            "required": True,
                        }
                    )
                    dur_interv: Optional[int] = field(
                        default=None,
                        metadata={
                            "name": "durInterv",
                            "type": "Element",
                            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                            "required": True,
                        }
                    )
                    ini_interv: Optional[str] = field(
                        default=None,
                        metadata={
                            "name": "iniInterv",
                            "type": "Element",
                            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        }
                    )
                    term_interv: Optional[str] = field(
                        default=None,
                        metadata={
                            "name": "termInterv",
                            "type": "Element",
                            "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                        }
                    )

    @dataclass
    class InfoContribuinte:
        nat_jurid: Optional[str] = field(
            default=None,
            metadata={
                "name": "natJurid",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
                "length": 4,
            }
        )

    @dataclass
    class InfoEstabelecimento:
        aliq_rat: Optional[int] = field(
            default=None,
            metadata={
                "name": "aliqRat",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
            }
        )
        uf: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
                "length": 2,
            }
        )

    @dataclass
    class InfoLotacao:
        nr_insc_prop: Optional[str] = field(
            default=None,
            metadata={
                "name": "nrInscProp",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "required": True,
                "length": 4,
            }
        )

    @dataclass
    class Rubricas:
        rubrica: List["TdadosRecibo.Rubricas.Rubrica"] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0",
                "min_occurs": 1,
            }
        )

        @dataclass
        class Rubrica:
            nr_r: Optional[str] = field(
                default=None,
                metadata={
                    "name": "nrR",
                    "type": "Attribute",
                    "pattern": r"[1]{1}\.\d{1}\.\d{19}",
                }
            )
            id_e: Optional[str] = field(
                default=None,
                metadata={
                    "name": "idE",
                    "type": "Attribute",
                    "pattern": r"ID\d{34}",
                }
            )
            in_v: Optional[XmlDate] = field(
                default=None,
                metadata={
                    "name": "inV",
                    "type": "Attribute",
                }
            )
            pr_a: Optional[str] = field(
                default=None,
                metadata={
                    "name": "prA",
                    "type": "Attribute",
                    "required": True,
                    "pattern": r"[2]{1}\d{3}-(1[0-2]|0[1-9])|[2]{1}\d{3}",
                }
            )
            pr_r: Optional[str] = field(
                default=None,
                metadata={
                    "name": "prR",
                    "type": "Attribute",
                    "pattern": r"[2]{1}\d{3}-(1[0-2]|0[1-9])(;[2]{1}\d{3}-(1[0-2]|0[1-9]))*",
                }
            )
            id_t: Optional[str] = field(
                default=None,
                metadata={
                    "name": "idT",
                    "type": "Attribute",
                    "required": True,
                    "min_length": 1,
                    "max_length": 8,
                }
            )
            cd_r: Optional[str] = field(
                default=None,
                metadata={
                    "name": "cdR",
                    "type": "Attribute",
                    "required": True,
                    "min_length": 1,
                    "max_length": 30,
                }
            )
            nt_r: Optional[str] = field(
                default=None,
                metadata={
                    "name": "ntR",
                    "type": "Attribute",
                    "required": True,
                    "pattern": r"\d{4}",
                }
            )
            tp_r: Optional[RubricaTpR] = field(
                default=None,
                metadata={
                    "name": "tpR",
                    "type": "Attribute",
                    "required": True,
                }
            )
            in_cp: Optional[str] = field(
                default=None,
                metadata={
                    "name": "inCP",
                    "type": "Attribute",
                    "pattern": r"\d{1,2}",
                }
            )
            in_ir: Optional[str] = field(
                default=None,
                metadata={
                    "name": "inIR",
                    "type": "Attribute",
                    "pattern": r"\d{1,4}",
                }
            )
            in_fgts: Optional[str] = field(
                default=None,
                metadata={
                    "name": "inFGTS",
                    "type": "Attribute",
                    "pattern": r"\d{1,2}",
                }
            )
            in_cprp: Optional[str] = field(
                default=None,
                metadata={
                    "name": "inCPRP",
                    "type": "Attribute",
                    "pattern": r"\d{1,2}",
                }
            )
            in_pis: Optional[str] = field(
                default=None,
                metadata={
                    "name": "inPIS",
                    "type": "Attribute",
                    "pattern": r"\d{1,2}",
                }
            )
@dataclass
class ESocial:
    """
    Elemento raiz do eSocial.
    "

    :ivar retorno_evento: Define a estrutura do retorno do processamento
        do evento.
    :ivar signature:
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/evt/retornoEvento/v1_3_0"

    retorno_evento: Optional["ESocial.RetornoEvento"] = field(
        default=None,
        metadata={
            "name": "retornoEvento",
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
        }
    )

    @dataclass
    class RetornoEvento:
        """

        "

        :ivar ide_empregador: Identificação do empregador.
        :ivar recepcao: Dados de recepção do evento.
        :ivar processamento: Dados de processamento do evento.
        :ivar recibo: Dados do recibo do evento.
        :ivar id: Identificação única do evento. É mesma identificação
            do evento, gerada pelo empregador.
        """
        ide_empregador: Optional[TideEmpregador] = field(
            default=None,
            metadata={
                "name": "ideEmpregador",
                "type": "Element",
                "required": True,
            }
        )
        recepcao: Optional[TdadosRecepcao] = field(
            default=None,
            metadata={
                "type": "Element",
                "required": True,
            }
        )
        processamento: Optional[TdadosProcessamentoEvento] = field(
            default=None,
            metadata={
                "type": "Element",
                "required": True,
            }
        )
        recibo: Optional[TdadosRecibo] = field(
            default=None,
            metadata={
                "type": "Element",
            }
        )
        id: Optional[str] = field(
            default=None,
            metadata={
                "name": "Id",
                "type": "Attribute",
                "required": True,
            }
        )