from dataclasses import dataclass, field
from typing import List, Optional
from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0"


@dataclass
class TarquivoEsocial:
    """
    Define os dados de um arquivo do eSocial (evento).
    "

    :ivar any_element: Contém xml com o retorno do processamento do
        evento. (conforme Xsd retornoEvento)
    """
    class Meta:
        name = "TArquivoEsocial"

    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "process_contents": "skip",
        }
    )
@dataclass
class TdadosProcessamento:
    """
    Define os dados de processamento de um lote de eventos.
    "

    :ivar versao_aplicativo_processamento_lote: Versão do aplicativo de
        processamento do lote.
    """
    class Meta:
        name = "TDadosProcessamento"

    versao_aplicativo_processamento_lote: Optional[str] = field(
        default=None,
        metadata={
            "name": "versaoAplicativoProcessamentoLote",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "max_length": 30,
        }
    )
@dataclass
class TdadosRecepcao:
    """
    Define os dados de recepção de um arquivo de lote.
    "

    :ivar dh_recepcao: Data hora recepção.
    :ivar versao_aplicativo_recepcao: Versão do aplicativo de recepção.
    :ivar protocolo_envio: Código de retorno para localização do lote.
        Número sequencial único produzido no instante de recepção da
        mensagem originada no empregador. São válidos os seguintes
        intervalos, expressos na base decimal:
        A.B.AAAAMM.NNNNNNNNNNNNNNNNNNN A = Agente de recepção: Serpro=1
        ou Caixa=2 (1 posição) B = Ambiente de recepção: Produção=1;
        Pré-produção - dados reais=2; Pré-produção - dados fictícios=3;
        Homologação=6; Validação=7; Testes=8; Desenvolvimento=9 AAAAMM =
        Ano e Mês em que o lote foi recebido. N = Número sequencial (19
        posições) Exemplo: SERPRO: 1.1.201605.0000000000000000001 Caixa:
        2.1.201605.0000000000000000001
    """
    class Meta:
        name = "TDadosRecepcao"

    dh_recepcao: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "dhRecepcao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "required": True,
        }
    )
    versao_aplicativo_recepcao: Optional[str] = field(
        default=None,
        metadata={
            "name": "versaoAplicativoRecepcao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "required": True,
            "max_length": 30,
        }
    )
    protocolo_envio: Optional[str] = field(
        default=None,
        metadata={
            "name": "protocoloEnvio",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "required": True,
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
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "required": True,
            "max_length": 15,
        }
    )
@dataclass
class TideTransmissor:
    """
    Define a identificação do transmissor.
    """

    class Meta:
        name = "TIdeTransmissor"

    tp_insc: Optional[int] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "required": True,
            "max_length": 15,
        }
    )
@dataclass
class Tocorrencias:
    """
    Define uma ocorrências encontrada no processamento de um arquivo.
    """

    class Meta:
        name = "TOcorrencias"

    ocorrencia: List["Tocorrencias.Ocorrencia"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "min_occurs": 1,
        }
    )

    @dataclass
    class Ocorrencia:
        """

        "

        :ivar codigo: Código da ocorrência
        :ivar descricao: Descrição da ocorrência
        :ivar tipo: Contém o tipo da ocorrência: 1 - Erro, 2 -
            Advertência
        :ivar localizacao: Contém o caminho do registro e/ou campo em
            que ocorreu o erro.
        """
        codigo: Optional[int] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
                "required": True,
            }
        )
        descricao: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
                "required": True,
                "max_length": 2048,
            }
        )
        tipo: Optional[int] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
                "required": True,
            }
        )
        localizacao: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
                "max_length": 2048,
            }
        )
@dataclass
class Tstatus:
    """
    Contém o status atual do lote ou do Evento.
    "

    :ivar cd_resposta: Código de resposta do processamento do lote.
    :ivar desc_resposta: Contém a descrição correspondente ao código de
        resposta.
    :ivar tempo_estimado_conclusao: Contém o tempo estimado de conclusão
        do processamento do lote em segundos.
    :ivar ocorrencias: Contém as ocorrências encontradas durante a
        validação do evento.
    """
    class Meta:
        name = "TStatus"

    cd_resposta: Optional[int] = field(
        default=None,
        metadata={
            "name": "cdResposta",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "required": True,
        }
    )
    desc_resposta: Optional[str] = field(
        default=None,
        metadata={
            "name": "descResposta",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
            "required": True,
            "max_length": 2048,
        }
    )
    tempo_estimado_conclusao: Optional[int] = field(
        default=None,
        metadata={
            "name": "tempoEstimadoConclusao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
        }
    )
    ocorrencias: Optional[Tocorrencias] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0",
        }
    )
@dataclass
class ESocial:
    """
    Elemento raiz do eSocial.
    "

    :ivar retorno_processamento_lote_eventos: Xml que contém o retorno
        do processamento dos eventos do lote.
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/lote/eventos/envio/retornoProcessamento/v1_3_0"

    retorno_processamento_lote_eventos: Optional["ESocial.RetornoProcessamentoLoteEventos"] = field(
        default=None,
        metadata={
            "name": "retornoProcessamentoLoteEventos",
            "type": "Element",
            "required": True,
        }
    )

    @dataclass
    class RetornoProcessamentoLoteEventos:
        """

        "

        :ivar ide_empregador: Identificação do empregador.
        :ivar ide_transmissor: Identificação do transmissor.
        :ivar status: Contém o status atual do lote.
        :ivar dados_recepcao_lote: Contém os dados de recepção do lote.
        :ivar dados_processamento_lote: Contém os dados de processamento
            do lote.
        :ivar retorno_eventos: Contém o(s) resultado(s) do processamento
            dos eventos do lote.
        """
        ide_empregador: Optional[TideEmpregador] = field(
            default=None,
            metadata={
                "name": "ideEmpregador",
                "type": "Element",
            }
        )
        ide_transmissor: Optional[TideTransmissor] = field(
            default=None,
            metadata={
                "name": "ideTransmissor",
                "type": "Element",
            }
        )
        status: Optional[Tstatus] = field(
            default=None,
            metadata={
                "type": "Element",
                "required": True,
            }
        )
        dados_recepcao_lote: Optional[TdadosRecepcao] = field(
            default=None,
            metadata={
                "name": "dadosRecepcaoLote",
                "type": "Element",
            }
        )
        dados_processamento_lote: Optional[TdadosProcessamento] = field(
            default=None,
            metadata={
                "name": "dadosProcessamentoLote",
                "type": "Element",
            }
        )
        retorno_eventos: Optional["ESocial.RetornoProcessamentoLoteEventos.RetornoEventos"] = field(
            default=None,
            metadata={
                "name": "retornoEventos",
                "type": "Element",
            }
        )

        @dataclass
        class RetornoEventos:
            evento: List["ESocial.RetornoProcessamentoLoteEventos.RetornoEventos.Evento"] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "min_occurs": 1,
                    "max_occurs": 50,
                }
            )

            @dataclass
            class Evento:
                """

                "

                :ivar retorno_evento: Contém o recibo do evento se o
                    mesmo foi recebido com sucesso, ou as
                    inconsistências caso não tenha sido recebido.
                :ivar tot:
                :ivar id: É através deste atributo que o empregador
                    conseguirá fazer o mapeamento entre o evento que ele
                    enviou e o resultado do processamento de cada
                    evento.
                :ivar evt_dupl: Este atributo indica se o recibo que
                    está sendo retornado é de um evento que já foi
                    recebido anteriormente ou não. Ele somente será
                    preenchido no caso de ser true.
                """
                retorno_evento: Optional[TarquivoEsocial] = field(
                    default=None,
                    metadata={
                        "name": "retornoEvento",
                        "type": "Element",
                        "required": True,
                    }
                )
                tot: List["ESocial.RetornoProcessamentoLoteEventos.RetornoEventos.Evento.Tot"] = field(
                    default_factory=list,
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
                evt_dupl: Optional[bool] = field(
                    default=None,
                    metadata={
                        "name": "evtDupl",
                        "type": "Attribute",
                    }
                )

                @dataclass
                class Tot:
                    """

                    "

                    :ivar any_element: Contém xml com o evento
                        totalizador do tipo especificado no atributo
                        tipo.
                    :ivar tipo: É neste atributo que será informado o
                        tipo do totalizador que será retornado.
                    """
                    any_element: Optional[object] = field(
                        default=None,
                        metadata={
                            "type": "Wildcard",
                            "namespace": "##any",
                            "process_contents": "skip",
                        }
                    )
                    tipo: Optional[object] = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "required": True,
                        }
                    )