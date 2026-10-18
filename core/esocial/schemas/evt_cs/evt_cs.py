from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from core.esocial.schemas.evt_cs.tipos import (
    TsAliqRat,
    TsIndComerc,
    TsIndConstr,
    TsIndCoop,
    TsIndSubstPatr,
    TsIndSubstPatrObra,
    TsPercTransf,
    TsTpInsc12,
    TsTpInsc1234,
    TIdeEmpregador,
    TIdeEventoRetornoContrib,
)
from core.esocial.schemas.evt_cs.xmldsig_core_schema import Signature

__NAMESPACE__ = "http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00"


class BasesAquisIndAquis(Enum):
    """Indicativo da aquisição.

    Origem: campo {indAquis} de S-1250.
    "

    :cvar VALUE_1: Aquisição da produção de produtor rural pessoa física
        ou segurado especial em geral
    :cvar VALUE_2: Aquisição da produção de produtor rural pessoa física
        ou segurado especial em geral por entidade do PAA
    :cvar VALUE_3: Aquisição da produção de produtor rural pessoa
        jurídica por entidade do PAA
    :cvar VALUE_4: Aquisição da produção de produtor rural pessoa física
        ou segurado especial em geral - Produção isenta (Lei
        13.606/2018)
    :cvar VALUE_5: Aquisição da produção de produtor rural pessoa física
        ou segurado especial em geral por entidade do PAA - Produção
        isenta (Lei 13.606/2018)
    :cvar VALUE_6: Aquisição da produção de produtor rural pessoa
        jurídica por entidade do PAA - Produção isenta (Lei 13.606/2018)
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_6 = 6
class BasesRemunIndIncid(Enum):
    """Preencher com o código correspondente ao tipo de incidência para fins de apuração da contribuição previdenciária.
    Validação: a) Para empresas com {classTrib}(5011_infoCS_infoContrib_classTrib) = [01, 70, 80], todas as bases de cálculo devem ser totalizadas com {indIncid}(./indIncid) = [9], EXCETO para {classTrib}(5011_infoCS_infoContrib_classTrib) = [01] E {ideEstab/tpInsc}(5011_infoCS_ideEstab_tpInsc) = [4], que deve ser totalizada com {indIncid}(./indIncid) = [1].
    b) Para empresas com {classTrib}(5011_infoCS_infoContrib_classTrib) = [03], considerar a informação prestada no campo {indSimples}(5001_infoCp_ideEstabLot_infoCategIncid_indSimples) do evento S-5001, conforme abaixo:
    - Se o {indSimples}(5001_infoCp_ideEstabLot_infoCategIncid_indSimples) em S-5001 = [1] (contrib. subst. integralmente), a base de cálculo do respectivo trabalhador deve ser totalizada com {indIncid}(./indIncid) = [9];
    - Se o {indSimples}(5001_infoCp_ideEstabLot_infoCategIncid_indSimples) em S-5001 = [2] (contrib. não substituída), a base de cálculo do respectivo trabalhador deve ser totalizada com {indIncid}(./indIncid) = [1] (normal);
    - Se o {indSimples}(5001_infoCp_ideEstabLot_infoCategIncid_indSimples) em S-5001 = [3] (ativ. concomitante), a base de cálculo do respectivo trabalhador deve ser totalizada com {indIncid}(./indIncid) = [2].
    c) Para empresas com {classTrib}(5011_infoCS_infoContrib_classTrib) = [10] (sindicato de avulsos não portuários), as bases de cálculo dos trabalhadores avulsos da categoria [202] devem ser totalizadas com {indIncid}(./indIncid) = [9].
    d) Para {classTrib}(5011_infoCS_infoContrib_classTrib) = [22] (segurado especial), as bases de cálculo dos trabalhadores devem ser totalizadas com {indIncid}(./indIncid) = [9], EXCETO para a categoria [104] (empregado doméstico) ou se {ideEstab/tpInsc}(5011_infoCS_ideEstab_tpInsc) = [4], que deve ser totalizada com {indIncid}(./indIncid) = [1].
    e) Para contribuinte com {classTrib}(5011_infoCS_infoContrib_classTrib) = [99] e com {indCoop}(5011_infoCS_infoContrib_infoPJ_indCoop) = [1] (cooperativa de trabalho), as remunerações dos cooperados (categoria [731, 734]) cuja lotação esteja classificada com {tpLotacao}(1020_infoLotacao_inclusao_dadosLotacao_tpLotacao) em S-1020 = [05, 06, 07] devem ser totalizadas com {indIncid}(./indIncid) = [9]. Nos demais casos, {indIncid}(./indIncid) = [1].
    f) Para contribuintes com {classTrib}(5011_infoCS_infoContrib_classTrib) = [11], as bases de cálculo dos trabalhadores devem ser totalizadas com {indIncid}(./indIncid) = [9], EXCETO para as categorias de contribuinte individual, que devem ser totalizadas com {indIncid}(./indIncid) = [1].
    g) Para {tpLotacao}(1020_infoLotacao_inclusao_dadosLotacao_tpLotacao) em S-1020 = [91, 92], todas as bases de cálculo devem ser totalizadas com {indIncid}(./indIncid) = [9].

    :cvar VALUE_1: Normal
    :cvar VALUE_2: Atividade concomitante
    :cvar VALUE_9: Substituída ou isenta
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_9 = 9
class InfoCsIndExistInfo(Enum):
    """
    Indicativo de existência de valores de bases e de contribuições sociais.
    "

    :cvar VALUE_1: Há informações com apuração de contribuições sociais
    :cvar VALUE_2: Há movimento, porém sem apuração de contribuições
        sociais
    :cvar VALUE_3: Não há movimento no período informado em
        {perApur}(5011_ideEvento_perApur)
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
class InfoPjIndTribFolhaPisPasep(Enum):
    """Indicador de tributação sobre a folha de pagamento - PIS e PASEP.
    Evento de origem: S-1000."

    :cvar S: Sim
    """
    S = 'S'
@dataclass
class ESocial:
    """S-5011 - Informações das Contribuições Sociais Consolidadas por Contribuinte"

    :ivar evt_cs: Evento Informações das Contribuições Sociais
        Consolidadas por Contribuinte. CHAVE_GRUPO: {Id}
    :ivar signature:
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/evt/evtCS/v_S_01_03_00"

    evt_cs: Optional["ESocial.EvtCs"] = field(
        default=None,
        metadata={
            "name": "evtCS",
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
            "required": True,
        }
    )

    @dataclass
    class EvtCs:
        """

        "

        :ivar ide_evento:
        :ivar ide_empregador:
        :ivar info_cs: Informações relativas às contribuições sociais
            DESCRICAO_COMPLETA:Informações relativas às contribuições
            sociais devidas à Previdência Social e a Outras Entidades e
            Fundos.
        :ivar id:
        """
        ide_evento: Optional[TIdeEventoRetornoContrib] = field(
            default=None,
            metadata={
                "name": "ideEvento",
                "type": "Element",
                "required": True,
            }
        )
        ide_empregador: Optional[TIdeEmpregador] = field(
            default=None,
            metadata={
                "name": "ideEmpregador",
                "type": "Element",
                "required": True,
            }
        )
        info_cs: Optional["ESocial.EvtCs.InfoCs"] = field(
            default=None,
            metadata={
                "name": "infoCS",
                "type": "Element",
                "required": True,
            }
        )
        id: Optional[str] = field(
            default=None,
            metadata={
                "name": "Id",
                "type": "Attribute",
                "required": True,
                "length": 36,
                "pattern": r"ID\d{34}",
            }
        )

        @dataclass
        class InfoCs:
            """

            "

            :ivar nr_rec_arq_base:
            :ivar ind_exist_info:
            :ivar info_cpseg: Informações de contribuição previdenciária
                do segurado. CONDICAO_GRUPO: OC
            :ivar info_contrib: Informações gerais do contribuinte
                DESCRICAO_COMPLETA:Informações gerais do contribuinte
                necessárias à apuração das contribuições sociais.
            :ivar ide_estab: Identificação do estabelecimento/obra
                DESCRICAO_COMPLETA:Informações de identificação do
                estabelecimento ou obra de construção civil.
                CHAVE_GRUPO: {tpInsc}, {nrInsc} CONDICAO_GRUPO: OC
            :ivar info_crcontrib: Totalizador dos Códigos de Receita do
                contribuinte DESCRICAO_COMPLETA:Informações consolidadas
                das contribuições sociais devidas à Previdência Social e
                Outras Entidades e Fundos, por Código de Receita - CR.
                CHAVE_GRUPO: {tpCR} CONDICAO_GRUPO: OC
            """
            nr_rec_arq_base: Optional[str] = field(
                default=None,
                metadata={
                    "name": "nrRecArqBase",
                    "type": "Element",
                    "required": True,
                    "length": 23,
                    "pattern": r"[1]{1}\.\d{1}\.\d{19}",
                }
            )
            ind_exist_info: Optional[InfoCsIndExistInfo] = field(
                default=None,
                metadata={
                    "name": "indExistInfo",
                    "type": "Element",
                    "required": True,
                }
            )
            info_cpseg: Optional["ESocial.EvtCs.InfoCs.InfoCpseg"] = field(
                default=None,
                metadata={
                    "name": "infoCPSeg",
                    "type": "Element",
                }
            )
            info_contrib: Optional["ESocial.EvtCs.InfoCs.InfoContrib"] = field(
                default=None,
                metadata={
                    "name": "infoContrib",
                    "type": "Element",
                    "required": True,
                }
            )
            ide_estab: List["ESocial.EvtCs.InfoCs.IdeEstab"] = field(
                default_factory=list,
                metadata={
                    "name": "ideEstab",
                    "type": "Element",
                }
            )
            info_crcontrib: List["ESocial.EvtCs.InfoCs.InfoCrcontrib"] = field(
                default_factory=list,
                metadata={
                    "name": "infoCRContrib",
                    "type": "Element",
                    "max_occurs": 99,
                }
            )

            @dataclass
            class InfoCpseg:
                """

                "

                :ivar vr_desc_cp: Valor total da contribuição descontada
                    dos segurados. Origem: campo
                    {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                    de S-5001, quando
                    {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                    em S-5001 = [21].
                :ivar vr_cp_seg: Valor total calculado relativo à
                    contribuição dos segurados. Origem: campo
                    {vrCpSeg}(5001_infoCpCalc_vrCpSeg) de S-5001.
                """
                vr_desc_cp: Optional[Decimal] = field(
                    default=None,
                    metadata={
                        "name": "vrDescCP",
                        "type": "Element",
                        "required": True,
                        "min_inclusive": Decimal('0'),
                        "max_inclusive": Decimal('999999999999.99'),
                        "total_digits": 14,
                        "fraction_digits": 2,
                    }
                )
                vr_cp_seg: Optional[Decimal] = field(
                    default=None,
                    metadata={
                        "name": "vrCpSeg",
                        "type": "Element",
                        "required": True,
                        "min_inclusive": Decimal('0'),
                        "max_inclusive": Decimal('999999999999.99'),
                        "total_digits": 14,
                        "fraction_digits": 2,
                    }
                )

            @dataclass
            class InfoContrib:
                """

                "

                :ivar class_trib:
                :ivar info_pj: Informações exclusivas da PJ
                    DESCRICAO_COMPLETA:Informações complementares,
                    exclusivas da Pessoa Jurídica. CONDICAO_GRUPO: O (se
                    {ideEmpregador/tpInsc}(5011_ideEmpregador_tpInsc) =
                    [1]); N (nos demais casos)
                """
                class_trib: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "classTrib",
                        "type": "Element",
                        "required": True,
                        "pattern": r"\d{2}",
                    }
                )
                info_pj: Optional["ESocial.EvtCs.InfoCs.InfoContrib.InfoPj"] = field(
                    default=None,
                    metadata={
                        "name": "infoPJ",
                        "type": "Element",
                    }
                )

                @dataclass
                class InfoPj:
                    """

                    "

                    :ivar ind_coop: Indicativo de cooperativa. Evento de
                        origem: S-1000.
                    :ivar ind_constr: Indicativo de construtora. Evento
                        de origem: S-1000.
                    :ivar ind_subst_patr: Indicativo de substituição da
                        contribuição previdenciária patronal. Origem:
                        campo
                        {indSubstPatr}(1280_infoSubstPatr_indSubstPatr)
                        de S-1280.
                    :ivar perc_red_contrib: Percentual de redução da
                        contribuição prevista na Lei 12.546/2011. Evento
                        de origem: S-1280.
                    :ivar perc_transf: Percentual de contribuição social
                        - Lei 11.096/2005. Evento de origem: S-1280.
                    :ivar ind_trib_folha_pis_pasep:
                    :ivar info_at_conc: Informações de atividades
                        concomitantes DESCRICAO_COMPLETA:Informações
                        prestadas por empresa enquadrada no regime de
                        tributação Simples Nacional com tributação
                        previdenciária substituída e não substituída.
                        CONDICAO_GRUPO: O (se
                        {classTrib}(../../classTrib) = [03]; N (nos
                        demais casos)
                    """
                    ind_coop: Optional[TsIndCoop] = field(
                        default=None,
                        metadata={
                            "name": "indCoop",
                            "type": "Element",
                        }
                    )
                    ind_constr: Optional[TsIndConstr] = field(
                        default=None,
                        metadata={
                            "name": "indConstr",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    ind_subst_patr: Optional[TsIndSubstPatr] = field(
                        default=None,
                        metadata={
                            "name": "indSubstPatr",
                            "type": "Element",
                        }
                    )
                    perc_red_contrib: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "percRedContrib",
                            "type": "Element",
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('100'),
                            "total_digits": 5,
                            "fraction_digits": 2,
                        }
                    )
                    perc_transf: Optional[TsPercTransf] = field(
                        default=None,
                        metadata={
                            "name": "percTransf",
                            "type": "Element",
                        }
                    )
                    ind_trib_folha_pis_pasep: Optional[InfoPjIndTribFolhaPisPasep] = field(
                        default=None,
                        metadata={
                            "name": "indTribFolhaPisPasep",
                            "type": "Element",
                        }
                    )
                    info_at_conc: Optional["ESocial.EvtCs.InfoCs.InfoContrib.InfoPj.InfoAtConc"] = field(
                        default=None,
                        metadata={
                            "name": "infoAtConc",
                            "type": "Element",
                        }
                    )

                    @dataclass
                    class InfoAtConc:
                        """

                        "

                        :ivar fator_mes: Informe o fator a ser utilizado
                            para cálculo da contribuição patronal do mês
                            dos trabalhadores envolvidos na execução das
                            atividades enquadradas no Anexo IV em
                            conjunto com as dos Anexos I a III e V da
                            Lei Complementar 123/2006. Evento de origem:
                            S-1280.
                        :ivar fator13: Informe o fator a ser utilizado
                            para cálculo da contribuição patronal do
                            décimo terceiro dos trabalhadores envolvidos
                            na execução das atividades enquadradas no
                            Anexo IV em conjunto com as dos Anexos I a
                            III e V da Lei Complementar 123/2006. Evento
                            de origem: S-1280.
                        """
                        fator_mes: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "name": "fatorMes",
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0'),
                                "max_inclusive": Decimal('100'),
                                "total_digits": 5,
                                "fraction_digits": 2,
                            }
                        )
                        fator13: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0'),
                                "max_inclusive": Decimal('100'),
                                "total_digits": 5,
                                "fraction_digits": 2,
                            }
                        )

            @dataclass
            class IdeEstab:
                """

                "

                :ivar tp_insc:
                :ivar nr_insc: Informar o número de inscrição do
                    contribuinte de acordo com o tipo de inscrição
                    indicado no campo {ideEstab/tpInsc}(./tpInsc).
                    Evento de origem: S-1260, S-1270 ou S-5001.
                :ivar info_estab: Informações do estabelecimento
                    DESCRICAO_COMPLETA:Informações relativas a cada
                    estabelecimento, necessárias à apuração das
                    contribuições sociais. CONDICAO_GRUPO: N (se
                    {ideEstab/tpInsc}(../tpInsc) = [2] OU (se
                    {ideEstab/tpInsc}(../tpInsc) = [3] e se tratar de
                    empregador doméstico) OU se não existir informação
                    em S-1200, S-1270, S-2299 ou S-2399 relativas ao
                    estabelecimento); O (nos demais casos)
                :ivar ide_lotacao: Identificação da lotação tributária.
                    CHAVE_GRUPO: {codLotacao} CONDICAO_GRUPO: O (se
                    existir informação em S-1200, S-1270, S-2299 ou
                    S-2399 relativas ao estabelecimento identificado em
                    {ideEstab/nrInsc}(../nrInsc)); N (nos demais casos)
                :ivar bases_aquis: Informações sobre aquisição rural
                    DESCRICAO_COMPLETA:Informações de bases de cálculo
                    relativas à aquisição de produção rural. Evento de
                    origem: S-1250 (existente até a versão 2.5 do
                    leiaute). CHAVE_GRUPO: {indAquis} CONDICAO_GRUPO: O
                    (se existir informação em S-1250 relativa ao
                    estabelecimento identificado em
                    {ideEstab/nrInsc}(../nrInsc) e se não houver
                    informação de
                    {indExcApur1250}(1299_infoFech_indExcApur1250) em
                    S-1299); N (nos demais casos)
                :ivar bases_comerc: Informações da comercialização da
                    produção DESCRICAO_COMPLETA:Informações de bases de
                    cálculo relativas à comercialização da produção
                    rural da Pessoa Física. Informações desse grupo
                    conforme informado pelo contribuinte em S-1260.
                    CHAVE_GRUPO: {indComerc} CONDICAO_GRUPO: O (se
                    houver evento S-1260 válido na competência relativo
                    ao estabelecimento identificado em
                    {ideEstab/nrInsc}(../nrInsc)); N (nos demais casos)
                :ivar info_crestab: Códigos de Receita por
                    estabelecimento DESCRICAO_COMPLETA:Informações das
                    contribuições sociais devidas à Previdência Social e
                    Outras Entidades e Fundos, consolidadas por
                    estabelecimento e por Código de Receita - CR.
                    CHAVE_GRUPO: {tpCR} CONDICAO_GRUPO: OC
                :ivar bases_pis_pasep: Bases da contribuição do
                    PIS/PASEP DESCRICAO_COMPLETA:Valores correspondentes
                    às bases da contribuição do PIS/PASEP.
                    CONDICAO_GRUPO: O (se
                    {}(5011_infoCS_infoContrib_infoPJ_indTribFolhaPisPasep)
                    = [S], {}(5011_ideEvento_perApur) &gt;= [2025-01] e
                    {ideEmpregador/tpInsc}(5011_ideEmpregador_tpInsc)=
                    [1]; N (nos demais casos) O cálculo do CR 8301-02 e
                    do CR 8301-22 dependem da versão e do período de
                    apuração do fechamento. Se a versão for S-1.3 e
                    {}(1299_ideEvento_perApur) &gt;= [2025-01], então o
                    CR será calculado sobre
                    {}(5011_infoCS_ideEstab_basesPisPasep); em caso
                    contrário, o CR será calculado com as bases da
                    previdência.
                """
                tp_insc: Optional[TsTpInsc1234] = field(
                    default=None,
                    metadata={
                        "name": "tpInsc",
                        "type": "Element",
                        "required": True,
                    }
                )
                nr_insc: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "nrInsc",
                        "type": "Element",
                        "required": True,
                        "pattern": r"\d{11}|\d{12}|\d{14}",
                    }
                )
                info_estab: Optional["ESocial.EvtCs.InfoCs.IdeEstab.InfoEstab"] = field(
                    default=None,
                    metadata={
                        "name": "infoEstab",
                        "type": "Element",
                    }
                )
                ide_lotacao: List["ESocial.EvtCs.InfoCs.IdeEstab.IdeLotacao"] = field(
                    default_factory=list,
                    metadata={
                        "name": "ideLotacao",
                        "type": "Element",
                    }
                )
                bases_aquis: List["ESocial.EvtCs.InfoCs.IdeEstab.BasesAquis"] = field(
                    default_factory=list,
                    metadata={
                        "name": "basesAquis",
                        "type": "Element",
                        "max_occurs": 6,
                    }
                )
                bases_comerc: List["ESocial.EvtCs.InfoCs.IdeEstab.BasesComerc"] = field(
                    default_factory=list,
                    metadata={
                        "name": "basesComerc",
                        "type": "Element",
                        "max_occurs": 5,
                    }
                )
                info_crestab: List["ESocial.EvtCs.InfoCs.IdeEstab.InfoCrestab"] = field(
                    default_factory=list,
                    metadata={
                        "name": "infoCREstab",
                        "type": "Element",
                        "max_occurs": 99,
                    }
                )
                bases_pis_pasep: Optional["ESocial.EvtCs.InfoCs.IdeEstab.BasesPisPasep"] = field(
                    default=None,
                    metadata={
                        "name": "basesPisPasep",
                        "type": "Element",
                    }
                )

                @dataclass
                class InfoEstab:
                    """

                    "

                    :ivar cnae_prep: Preencher com o código CNAE,
                        conforme informado em S-1005. Evento de origem:
                        S-1005.
                    :ivar cnpj_resp: Preencher com o CNPJ responsável
                        pela inscrição no cadastro de obras da RFB.
                        Evento de origem: S-1005.
                    :ivar aliq_rat: Informar a alíquota RAT. Validação:
                        Deve corresponder à alíquota declarada no evento
                        S-1005. Caso não haja informação, retornar a
                        alíquota definida na legislação vigente para o
                        código CNAE informado.
                    :ivar fap: Fator Acidentário de Prevenção - FAP.
                        Validação: Informação obrigatória e exclusiva se
                        {ideEmpregador/tpInsc}(5011_ideEmpregador_tpInsc)
                        = [1]. Deve corresponder ao FAP estabelecido
                        para a empresa pelo órgão governamental
                        competente, exceto se: a)
                        {ideEstab/tpInsc}(5011_infoCS_ideEstab_tpInsc) =
                        [4] e se não existir o campo
                        {cnpjResp}(./cnpjResp); ou b)
                        {ideEstab/tpInsc}(5011_infoCS_ideEstab_tpInsc) =
                        [1, 4] e se houver informação de
                        {procAdmJudFap}(1005_infoEstab_inclusao_dadosEstab_aliqGilrat_procAdmJudFap)
                        em S-1005; ou c)
                        {ideEstab/tpInsc}(5011_infoCS_ideEstab_tpInsc) =
                        [1, 4] e o estabelecimento ou o CNPJ responsável
                        pela inscrição no CNO não for encontrado na
                        tabela FAP referente ao ano de
                        {perApur}(5011_ideEvento_perApur). Caso haja
                        alguma exceção acima, retornar o FAP declarado
                        no evento S-1005.
                    :ivar aliq_rat_ajust:
                    :ivar info_estab_ref: Informações de RAT e FAP de
                        referência DESCRICAO_COMPLETA: Informações de
                        RAT e FAP de referência, nos casos de processo
                        administrativo ou judicial que altere a(s)
                        alíquota(s). CONDICAO_GRUPO: OC (se houver
                        informação de
                        {procAdmJudRat}(1005_infoEstab_inclusao_dadosEstab_aliqGilrat_procAdmJudRat)
                        em S-1005 ou de
                        {procAdmJudFap}(1005_infoEstab_inclusao_dadosEstab_aliqGilrat_procAdmJudFap)
                        em S-1005); N (nos demais casos)
                    :ivar info_compl_obra: Informações complementares
                        relativas a obras DESCRICAO_COMPLETA:Informações
                        complementares relativas a obras de construção
                        civil. CONDICAO_GRUPO: O (se houver informação
                        de
                        {infoObra}(1005_infoEstab_inclusao_dadosEstab_infoObra)
                        em S-1005); N (nos demais casos)
                    """
                    cnae_prep: Optional[str] = field(
                        default=None,
                        metadata={
                            "name": "cnaePrep",
                            "type": "Element",
                            "required": True,
                            "pattern": r"\d{7}",
                        }
                    )
                    cnpj_resp: Optional[str] = field(
                        default=None,
                        metadata={
                            "name": "cnpjResp",
                            "type": "Element",
                            "pattern": r"\d{14}",
                        }
                    )
                    aliq_rat: Optional[TsAliqRat] = field(
                        default=None,
                        metadata={
                            "name": "aliqRat",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    fap: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "type": "Element",
                            "min_inclusive": Decimal('0.5'),
                            "max_inclusive": Decimal('2'),
                            "total_digits": 5,
                            "fraction_digits": 4,
                        }
                    )
                    aliq_rat_ajust: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "aliqRatAjust",
                            "type": "Element",
                            "min_inclusive": Decimal('0.5'),
                            "max_inclusive": Decimal('6'),
                            "total_digits": 5,
                            "fraction_digits": 4,
                        }
                    )
                    info_estab_ref: Optional["ESocial.EvtCs.InfoCs.IdeEstab.InfoEstab.InfoEstabRef"] = field(
                        default=None,
                        metadata={
                            "name": "infoEstabRef",
                            "type": "Element",
                        }
                    )
                    info_compl_obra: Optional["ESocial.EvtCs.InfoCs.IdeEstab.InfoEstab.InfoComplObra"] = field(
                        default=None,
                        metadata={
                            "name": "infoComplObra",
                            "type": "Element",
                        }
                    )

                    @dataclass
                    class InfoEstabRef:
                        """

                        "

                        :ivar aliq_rat: Retornar a alíquota RAT definida
                            na legislação vigente. Validação: Deve
                            corresponder à alíquota definida na
                            legislação vigente para o código CNAE
                            informado em S-1005.
                        :ivar fap: Fator Acidentário de Prevenção - FAP
                            estabelecido pelo órgão governamental
                            competente. Validação: Informação
                            obrigatória e exclusiva se
                            {ideEmpregador/tpInsc}(5011_ideEmpregador_tpInsc)
                            = [1]. Deve corresponder ao FAP estabelecido
                            para a empresa pelo órgão governamental
                            competente.
                        :ivar aliq_rat_ajust:
                        """
                        aliq_rat: Optional[TsAliqRat] = field(
                            default=None,
                            metadata={
                                "name": "aliqRat",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        fap: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "type": "Element",
                                "min_inclusive": Decimal('0.5'),
                                "max_inclusive": Decimal('2'),
                                "total_digits": 5,
                                "fraction_digits": 4,
                            }
                        )
                        aliq_rat_ajust: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "name": "aliqRatAjust",
                                "type": "Element",
                                "min_inclusive": Decimal('0.5'),
                                "max_inclusive": Decimal('6'),
                                "total_digits": 5,
                                "fraction_digits": 4,
                            }
                        )

                    @dataclass
                    class InfoComplObra:
                        """

                        "

                        :ivar ind_subst_patr_obra: Indicativo de
                            substituição da contribuição patronal de
                            obra de construção civil. Origem: campo
                            {indSubstPatrObra}(1005_infoEstab_inclusao_dadosEstab_infoObra_indSubstPatrObra)
                            de S-1005.
                        """
                        ind_subst_patr_obra: Optional[TsIndSubstPatrObra] = field(
                            default=None,
                            metadata={
                                "name": "indSubstPatrObra",
                                "type": "Element",
                                "required": True,
                            }
                        )

                @dataclass
                class IdeLotacao:
                    """

                    "

                    :ivar cod_lotacao: Informar o código atribuído pelo
                        empregador para a lotação tributária. Evento de
                        origem: S-1270 ou S-5001.
                    :ivar fpas: Preencher com o código relativo ao FPAS.
                        Evento de origem: S-1020.
                    :ivar cod_tercs: Preencher com o código de
                        Terceiros, conforme Tabela 04. Evento de origem:
                        S-1020.
                    :ivar cod_tercs_susp: Informar o código combinado
                        dos Terceiros para os quais o recolhimento está
                        suspenso em virtude de processos judiciais.
                        Evento de origem: S-1020.
                    :ivar info_terc_susp: Informações de suspensão de
                        contribuição a Terceiros
                        DESCRICAO_COMPLETA:Informações de suspensão de
                        contribuições destinadas a Outras Entidades e
                        Fundos (Terceiros). CHAVE_GRUPO: {codTerc}
                        CONDICAO_GRUPO: OC
                    :ivar info_empr_parcial: Informação complementar de
                        obra de construção civil
                        DESCRICAO_COMPLETA:Informação complementar que
                        apresenta identificação do contratante e do
                        proprietário de obra de construção civil
                        contratada sob regime de empreitada parcial ou
                        subempreitada. Evento de origem: S-1020.
                        CONDICAO_GRUPO: O (se
                        {tpLotacao}(1020_infoLotacao_inclusao_dadosLotacao_tpLotacao)
                        em S-1020 relativo a {codLotacao}(../codLotacao)
                        for igual a [02]); N (nos demais casos)
                    :ivar dados_op_port: Informações relativas ao
                        operador portuário. CONDICAO_GRUPO: O (se
                        {tpLotacao}(1020_infoLotacao_inclusao_dadosLotacao_tpLotacao)
                        em S-1020 relativo a {codLotacao}(../codLotacao)
                        for igual a [08]); N (nos demais casos)
                    :ivar bases_remun: Bases de cálculo por categoria
                        DESCRICAO_COMPLETA:Bases de cálculo da
                        contribuição previdenciária incidente sobre
                        remunerações, por categoria. CHAVE_GRUPO:
                        {indIncid}, {codCateg} CONDICAO_GRUPO: O (se
                        houver evento S-1200/S-2299/S-2399 com
                        informações de remuneração válido na competência
                        relativo ao estabelecimento identificado em
                        {ideEstab/nrInsc}(../../nrInsc)); N (nos demais
                        casos)
                    :ivar bases_av_nport: Contratação de avulsos não
                        portuários DESCRICAO_COMPLETA:Informações de
                        bases de cálculo relativas à contratação de
                        trabalhadores avulsos não portuários.
                        Informações desse grupo conforme informado pelo
                        contribuinte em S-1270. CONDICAO_GRUPO: O (se
                        houver evento S-1270 válido na competência
                        relativo ao estabelecimento identificado em
                        {ideEstab/nrInsc}(../../nrInsc)); N (nos demais
                        casos)
                    :ivar info_subst_patr_op_port: Informação de
                        substituição prevista na Lei 12.546/2011
                        DESCRICAO_COMPLETA:Grupo preenchido
                        exclusivamente pelo Órgão Gestor de Mão de Obra
                        - OGMO
                        ({classTrib}(5011_infoCS_infoContrib_classTrib)
                        = [09]), relativamente a operador portuário
                        enquadrado nos arts. 7º a 9º da Lei 12.546/2011.
                        CONDICAO_GRUPO: OC (se
                        {classTrib}(5011_infoCS_infoContrib_classTrib) =
                        [09]; N (nos demais casos)
                    """
                    cod_lotacao: Optional[str] = field(
                        default=None,
                        metadata={
                            "name": "codLotacao",
                            "type": "Element",
                            "required": True,
                            "min_length": 1,
                            "max_length": 30,
                            "pattern": r".*[^\s].*",
                        }
                    )
                    fpas: Optional[str] = field(
                        default=None,
                        metadata={
                            "type": "Element",
                            "required": True,
                            "pattern": r"\d{3}",
                        }
                    )
                    cod_tercs: Optional[str] = field(
                        default=None,
                        metadata={
                            "name": "codTercs",
                            "type": "Element",
                            "required": True,
                            "pattern": r"\d{4}",
                        }
                    )
                    cod_tercs_susp: Optional[str] = field(
                        default=None,
                        metadata={
                            "name": "codTercsSusp",
                            "type": "Element",
                            "pattern": r"\d{4}",
                        }
                    )
                    info_terc_susp: List["ESocial.EvtCs.InfoCs.IdeEstab.IdeLotacao.InfoTercSusp"] = field(
                        default_factory=list,
                        metadata={
                            "name": "infoTercSusp",
                            "type": "Element",
                            "max_occurs": 15,
                        }
                    )
                    info_empr_parcial: Optional["ESocial.EvtCs.InfoCs.IdeEstab.IdeLotacao.InfoEmprParcial"] = field(
                        default=None,
                        metadata={
                            "name": "infoEmprParcial",
                            "type": "Element",
                        }
                    )
                    dados_op_port: Optional["ESocial.EvtCs.InfoCs.IdeEstab.IdeLotacao.DadosOpPort"] = field(
                        default=None,
                        metadata={
                            "name": "dadosOpPort",
                            "type": "Element",
                        }
                    )
                    bases_remun: List["ESocial.EvtCs.InfoCs.IdeEstab.IdeLotacao.BasesRemun"] = field(
                        default_factory=list,
                        metadata={
                            "name": "basesRemun",
                            "type": "Element",
                            "max_occurs": 99,
                        }
                    )
                    bases_av_nport: Optional["ESocial.EvtCs.InfoCs.IdeEstab.IdeLotacao.BasesAvNport"] = field(
                        default=None,
                        metadata={
                            "name": "basesAvNPort",
                            "type": "Element",
                        }
                    )
                    info_subst_patr_op_port: Optional["ESocial.EvtCs.InfoCs.IdeEstab.IdeLotacao.InfoSubstPatrOpPort"] = field(
                        default=None,
                        metadata={
                            "name": "infoSubstPatrOpPort",
                            "type": "Element",
                        }
                    )

                    @dataclass
                    class InfoTercSusp:
                        """

                        "

                        :ivar cod_terc: Informar o código de Terceiro.
                            Origem: campo
                            {codTerc}(1020_infoLotacao_inclusao_dadosLotacao_fpasLotacao_infoProcJudTerceiros_procJudTerceiro_codTerc)
                            de S-1020.
                        """
                        cod_terc: Optional[str] = field(
                            default=None,
                            metadata={
                                "name": "codTerc",
                                "type": "Element",
                                "required": True,
                                "pattern": r"\d{4}",
                            }
                        )

                    @dataclass
                    class InfoEmprParcial:
                        """

                        "

                        :ivar tp_insc_contrat: Tipo de inscrição do
                            contratante.
                        :ivar nr_insc_contrat: Número de inscrição
                            (CNPJ/CPF) do contratante.
                        :ivar tp_insc_prop: Tipo de inscrição do
                            proprietário do CNO. Validação: Retornar o
                            tipo de inscrição do proprietário no CNO.
                            Caso não tenha sido encontrado, retornar
                            {tpInscProp}(1020_infoLotacao_inclusao_dadosLotacao_infoEmprParcial_tpInscProp)
                            de S-1020. Se o tipo de inscrição do
                            proprietário no CNO não for encontrado e se
                            não houver informação de
                            {tpInscProp}(1020_infoLotacao_inclusao_dadosLotacao_infoEmprParcial_tpInscProp)
                            em S-1020, retornar
                            {tpInscContrat}(5011_infoCS_ideEstab_ideLotacao_infoEmprParcial_tpInscContrat).
                        :ivar nr_insc_prop: Preencher com o número de
                            inscrição (CNPJ/CPF) do proprietário do CNO.
                            Validação: Retornar o número de inscrição do
                            proprietário no CNO. Caso não tenha sido
                            encontrado, retornar
                            {nrInscProp}(1020_infoLotacao_inclusao_dadosLotacao_infoEmprParcial_nrInscProp)
                            de S-1020. Se o número de inscrição do
                            proprietário no CNO não for encontrado e se
                            não houver informação de
                            {nrInscProp}(1020_infoLotacao_inclusao_dadosLotacao_infoEmprParcial_nrInscProp)
                            em S-1020, retornar
                            {nrInscContrat}(5011_infoCS_ideEstab_ideLotacao_infoEmprParcial_nrInscContrat).
                        :ivar cno_obra:
                        """
                        tp_insc_contrat: Optional[TsTpInsc12] = field(
                            default=None,
                            metadata={
                                "name": "tpInscContrat",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        nr_insc_contrat: Optional[str] = field(
                            default=None,
                            metadata={
                                "name": "nrInscContrat",
                                "type": "Element",
                                "required": True,
                                "pattern": r"\d{11}|\d{14}",
                            }
                        )
                        tp_insc_prop: Optional[TsTpInsc12] = field(
                            default=None,
                            metadata={
                                "name": "tpInscProp",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        nr_insc_prop: Optional[str] = field(
                            default=None,
                            metadata={
                                "name": "nrInscProp",
                                "type": "Element",
                                "required": True,
                                "pattern": r"\d{11}|\d{14}",
                            }
                        )
                        cno_obra: Optional[str] = field(
                            default=None,
                            metadata={
                                "name": "cnoObra",
                                "type": "Element",
                                "required": True,
                                "pattern": r"\d{12}",
                            }
                        )

                    @dataclass
                    class DadosOpPort:
                        """

                        "

                        :ivar cnpj_op_portuario: Preencher com o CNPJ do
                            operador portuário. Origem: campo
                            {dadosLotacao/nrInsc}(1020_infoLotacao_inclusao_dadosLotacao_nrInsc)
                            de S-1020.
                        :ivar aliq_rat: Informar a alíquota RAT. Origem:
                            campo
                            {dadosOpPort/aliqRat}(1020_infoLotacao_inclusao_dadosLotacao_dadosOpPort_aliqRat)
                            de S-1020.
                        :ivar fap: Fator Acidentário de Prevenção - FAP.
                            Origem: campo
                            {dadosOpPort/fap}(1020_infoLotacao_inclusao_dadosLotacao_dadosOpPort_fap)
                            de S-1020.
                        :ivar aliq_rat_ajust:
                        """
                        cnpj_op_portuario: Optional[str] = field(
                            default=None,
                            metadata={
                                "name": "cnpjOpPortuario",
                                "type": "Element",
                                "required": True,
                                "pattern": r"\d{14}",
                            }
                        )
                        aliq_rat: Optional[TsAliqRat] = field(
                            default=None,
                            metadata={
                                "name": "aliqRat",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        fap: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0.5'),
                                "max_inclusive": Decimal('2'),
                                "total_digits": 5,
                                "fraction_digits": 4,
                            }
                        )
                        aliq_rat_ajust: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "name": "aliqRatAjust",
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0.5'),
                                "max_inclusive": Decimal('6'),
                                "total_digits": 5,
                                "fraction_digits": 4,
                            }
                        )

                    @dataclass
                    class BasesRemun:
                        """

                        "

                        :ivar ind_incid:
                        :ivar cod_categ: Preencher com o código da
                            categoria do trabalhador, conforme definido
                            em S-5001.
                        :ivar bases_cp: Bases, contribuições do segurado
                            e deduções da CP DESCRICAO_COMPLETA:Valores
                            correspondentes às bases, contribuições do
                            segurado e deduções da contribuição
                            previdenciária.
                        :ivar bases_cp13: Valores correspondentes às
                            remunerações a título de 13º salário
                            incluídas em folha mensal - Empresas
                            desoneradas. CONDICAO_GRUPO: OC (se
                            {indDesFolha}(1000_infoEmpregador_inclusao_infoCadastro_indDesFolha)
                            em S-1000 = [1], exceto para CNO com
                            {indSubstPatrObra}(5011_infoCS_ideEstab_infoEstab_infoComplObra_indSubstPatrObra)
                            = [2]); N (nos demais casos)
                        """
                        ind_incid: Optional[BasesRemunIndIncid] = field(
                            default=None,
                            metadata={
                                "name": "indIncid",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        cod_categ: Optional[str] = field(
                            default=None,
                            metadata={
                                "name": "codCateg",
                                "type": "Element",
                                "required": True,
                                "pattern": r"\d{3}",
                            }
                        )
                        bases_cp: Optional["ESocial.EvtCs.InfoCs.IdeEstab.IdeLotacao.BasesRemun.BasesCp"] = field(
                            default=None,
                            metadata={
                                "name": "basesCp",
                                "type": "Element",
                                "required": True,
                            }
                        )
                        bases_cp13: Optional["ESocial.EvtCs.InfoCs.IdeEstab.IdeLotacao.BasesRemun.BasesCp13"] = field(
                            default=None,
                            metadata={
                                "name": "basesCp13",
                                "type": "Element",
                            }
                        )

                        @dataclass
                        class BasesCp:
                            """

                            "

                            :ivar vr_bc_cp00: Preencher com a base de
                                cálculo da contribuição previdenciária
                                sobre a remuneração. Origem: para
                                {codCateg}(../codCateg) diferente de
                                [104]: somatório do campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [11, 15]; para
                                {codCateg}(../codCateg) = [104]:
                                somatório do campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [11, 15], limitado ao teto
                                do salário de contribuição. OBS.: A
                                contribuição previdenciária patronal do
                                empregador doméstico tem como base de
                                cálculo o somatório do salário de
                                contribuição de cada empregado.
                            :ivar vr_bc_cp15: Preencher com a base de
                                cálculo da contribuição adicional para o
                                financiamento dos benefícios de
                                aposentadoria especial após 15 anos de
                                contribuição. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, se
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [12, 16].
                            :ivar vr_bc_cp20: Preencher com a base de
                                cálculo da contribuição adicional para o
                                financiamento dos benefícios de
                                aposentadoria especial após 20 anos de
                                contribuição. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [13, 17].
                            :ivar vr_bc_cp25: Preencher com a base de
                                cálculo da contribuição adicional para o
                                financiamento dos benefícios de
                                aposentadoria especial após 25 anos de
                                contribuição. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [14, 18].
                            :ivar vr_susp_bc_cp00: Valor da BC com
                                incidência suspensa em decorrência de
                                decisão judicial. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [91, 95].
                            :ivar vr_susp_bc_cp15: Valor da base de
                                cálculo da contribuição previdenciária
                                adicional correspondente a exposição a
                                agente nocivo que dá ao trabalhador
                                direito a aposentadoria especial aos 15
                                anos de trabalho, com incidência
                                suspensa em decorrência de decisão
                                judicial. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [92, 96].
                            :ivar vr_susp_bc_cp20: Valor da base de
                                cálculo da contribuição previdenciária
                                adicional correspondente a exposição a
                                agente nocivo que dá ao trabalhador
                                expectativa de aposentadoria especial
                                aos 20 anos de trabalho, com incidência
                                suspensa em decorrência de decisão
                                judicial. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [93, 97].
                            :ivar vr_susp_bc_cp25: Valor da base de
                                cálculo da contribuição previdenciária
                                adicional correspondente a exposição a
                                agente nocivo que dá ao trabalhador
                                direito a aposentadoria especial aos 25
                                anos de trabalho, com incidência
                                suspensa em decorrência de decisão
                                judicial. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [94, 98].
                            :ivar vr_bc_cp00_va: Preencher com a base de
                                cálculo da contribuição previdenciária
                                sobre a remuneração - Contrato Verde e
                                Amarelo. Origem: somatório do campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [41, 45].
                            :ivar vr_bc_cp15_va: Preencher com a base de
                                cálculo da contribuição adicional para o
                                financiamento dos benefícios de
                                aposentadoria especial após 15 anos de
                                contribuição - Contrato Verde e Amarelo.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, se
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [42, 46].
                            :ivar vr_bc_cp20_va: Preencher com a base de
                                cálculo da contribuição adicional para o
                                financiamento dos benefícios de
                                aposentadoria especial após 20 anos de
                                contribuição - Contrato Verde e Amarelo.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [43, 47].
                            :ivar vr_bc_cp25_va: Preencher com a base de
                                cálculo da contribuição adicional para o
                                financiamento dos benefícios de
                                aposentadoria especial após 25 anos de
                                contribuição - Contrato Verde e Amarelo.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [44, 48].
                            :ivar vr_susp_bc_cp00_va: Valor da BC com
                                incidência suspensa em decorrência de
                                decisão judicial - Contrato Verde e
                                Amarelo. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [81, 85].
                            :ivar vr_susp_bc_cp15_va: Valor da base de
                                cálculo da contribuição previdenciária
                                adicional correspondente a exposição a
                                agente nocivo que dá ao trabalhador
                                direito a aposentadoria especial aos 15
                                anos de trabalho, com incidência
                                suspensa em decorrência de decisão
                                judicial - Contrato Verde e Amarelo.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [82, 86].
                            :ivar vr_susp_bc_cp20_va: Valor da base de
                                cálculo da contribuição previdenciária
                                adicional correspondente a exposição a
                                agente nocivo que dá ao trabalhador
                                expectativa de aposentadoria especial
                                aos 20 anos de trabalho, com incidência
                                suspensa em decorrência de decisão
                                judicial - Contrato Verde e Amarelo.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [83, 87].
                            :ivar vr_susp_bc_cp25_va: Valor da base de
                                cálculo da contribuição previdenciária
                                adicional correspondente a exposição a
                                agente nocivo que dá ao trabalhador
                                direito a aposentadoria especial aos 25
                                anos de trabalho, com incidência
                                suspensa em decorrência de decisão
                                judicial - Contrato Verde e Amarelo.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [84, 88].
                            :ivar vr_desc_sest: Valor total descontado
                                do trabalhador para recolhimento ao
                                SEST. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [22].
                            :ivar vr_calc_sest: Valor calculado relativo
                                à contribuição devida pelo trabalhador
                                para recolhimento ao SEST. Origem: campo
                                {vrCsSegTerc}(5001_infoCp_ideEstabLot_infoCategIncid_calcTerc_vrCsSegTerc)
                                de S-5001, quando
                                {calcTerc/tpCR}(5001_infoCp_ideEstabLot_infoCategIncid_calcTerc_tpCR)
                                em S-5001 = [121802], exceto se houver
                                informação de processo judicial do
                                trabalhador, quando deve ser utilizado o
                                valor apurado em
                                {vrDescSest}(./vrDescSest).
                            :ivar vr_desc_senat: Valor total descontado
                                do trabalhador para recolhimento ao
                                SENAT. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [23].
                            :ivar vr_calc_senat: Valor calculado
                                relativo à contribuição devida pelo
                                trabalhador para recolhimento ao SENAT.
                                Origem: campo
                                {vrCsSegTerc}(5001_infoCp_ideEstabLot_infoCategIncid_calcTerc_vrCsSegTerc)
                                de S-5001, quando
                                {calcTerc/tpCR}(5001_infoCp_ideEstabLot_infoCategIncid_calcTerc_tpCR)
                                em S-5001 = [122102], exceto se houver
                                informação de processo judicial do
                                trabalhador, quando deve ser utilizado o
                                valor apurado em
                                {vrDescSenat}(./vrDescSenat).
                            :ivar vr_sal_fam: Valor total do salário-
                                família para a categoria indicada.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [31].
                            :ivar vr_sal_mat: Valor total do salário-
                                maternidade para a categoria indicada.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [32].
                            """
                            vr_bc_cp00: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp00",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp15: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp15",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp20: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp20",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp25: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp25",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp00: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp00",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp15: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp15",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp20: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp20",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp25: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp25",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp00_va: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp00VA",
                                    "type": "Element",
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp15_va: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp15VA",
                                    "type": "Element",
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp20_va: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp20VA",
                                    "type": "Element",
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp25_va: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp25VA",
                                    "type": "Element",
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp00_va: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp00VA",
                                    "type": "Element",
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp15_va: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp15VA",
                                    "type": "Element",
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp20_va: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp20VA",
                                    "type": "Element",
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp25_va: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp25VA",
                                    "type": "Element",
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_desc_sest: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrDescSest",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_calc_sest: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrCalcSest",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_desc_senat: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrDescSenat",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_calc_senat: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrCalcSenat",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_sal_fam: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSalFam",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_sal_mat: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSalMat",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )

                        @dataclass
                        class BasesCp13:
                            """

                            "

                            :ivar vr_bc_cp00: Preencher com a base de
                                cálculo da contribuição previdenciária -
                                Remuneração a título de 13º salário.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [51].
                            :ivar vr_bc_cp15: Preencher com a base de
                                cálculo da contribuição adicional para o
                                financiamento dos benefícios de
                                aposentadoria especial após 15 anos de
                                contribuição - Remuneração a título de
                                13º salário. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [52].
                            :ivar vr_bc_cp20: Preencher com a base de
                                cálculo da contribuição adicional para o
                                financiamento dos benefícios de
                                aposentadoria especial após 20 anos de
                                contribuição - Remuneração a título de
                                13º salário. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [53].
                            :ivar vr_bc_cp25: Preencher com a base de
                                cálculo da contribuição adicional para o
                                financiamento dos benefícios de
                                aposentadoria especial após 25 anos de
                                contribuição - Remuneração a título de
                                13º salário. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [54].
                            :ivar vr_susp_bc_cp00: Valor da base de
                                cálculo com incidência suspensa em
                                decorrência de decisão judicial -
                                Remuneração a título de 13º salário.
                                Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [71].
                            :ivar vr_susp_bc_cp15: Valor da base de
                                cálculo da contribuição previdenciária
                                adicional correspondente a exposição a
                                agente nocivo que dá ao trabalhador
                                direito a aposentadoria especial aos 15
                                anos de trabalho, com incidência
                                suspensa em decorrência de decisão
                                judicial - Remuneração a título de 13º
                                salário. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [72].
                            :ivar vr_susp_bc_cp20: Valor da base de
                                cálculo da contribuição previdenciária
                                adicional correspondente a exposição a
                                agente nocivo que dá ao trabalhador
                                expectativa de aposentadoria especial
                                aos 20 anos de trabalho, com incidência
                                suspensa em decorrência de decisão
                                judicial - Remuneração a título de 13º
                                salário. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [73].
                            :ivar vr_susp_bc_cp25: Valor da base de
                                cálculo da contribuição previdenciária
                                adicional correspondente a exposição a
                                agente nocivo que dá ao trabalhador
                                direito a aposentadoria especial aos 25
                                anos de trabalho, com incidência
                                suspensa em decorrência de decisão
                                judicial - Remuneração a título de 13º
                                salário. Origem: campo
                                {valor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_valor)
                                de S-5001, quando
                                {tpValor}(5001_infoCp_ideEstabLot_infoCategIncid_infoBaseCS_tpValor)
                                em S-5001 = [74].
                            """
                            vr_bc_cp00: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp00",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp15: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp15",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp20: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp20",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_bc_cp25: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrBcCp25",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp00: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp00",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp15: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp15",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp20: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp20",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )
                            vr_susp_bc_cp25: Optional[Decimal] = field(
                                default=None,
                                metadata={
                                    "name": "vrSuspBcCp25",
                                    "type": "Element",
                                    "required": True,
                                    "min_inclusive": Decimal('0'),
                                    "max_inclusive": Decimal('999999999999.99'),
                                    "total_digits": 14,
                                    "fraction_digits": 2,
                                }
                            )

                    @dataclass
                    class BasesAvNport:
                        """

                        "

                        :ivar vr_bc_cp00: Valor da base de cálculo da
                            contribuição previdenciária sobre a
                            remuneração dos trabalhadores avulsos não
                            portuários. Origem: campo
                            {vrBcCp00}(1270_remunAvNP_vrBcCp00) de
                            S-1270.
                        :ivar vr_bc_cp15: Valor da base de cálculo da
                            contribuição adicional para o financiamento
                            dos benefícios de aposentadoria especial
                            após 15 anos de contribuição. Origem: campo
                            {vrBcCp15}(1270_remunAvNP_vrBcCp15) de
                            S-1270.
                        :ivar vr_bc_cp20: Valor da base de cálculo da
                            contribuição adicional para o financiamento
                            dos benefícios de aposentadoria especial
                            após 20 anos de contribuição. Origem: campo
                            {vrBcCp20}(1270_remunAvNP_vrBcCp20) de
                            S-1270.
                        :ivar vr_bc_cp25: Valor da base de cálculo da
                            contribuição adicional para o financiamento
                            dos benefícios de aposentadoria especial
                            após 25 anos de contribuição. Origem: campo
                            {vrBcCp25}(1270_remunAvNP_vrBcCp25) de
                            S-1270.
                        :ivar vr_bc_cp13: Valor da base de cálculo da
                            contribuição previdenciária sobre o 13°
                            salário dos trabalhadores avulsos não
                            portuários contratados. Origem: campo
                            {vrBcCp13}(1270_remunAvNP_vrBcCp13) de
                            S-1270.
                        :ivar vr_desc_cp: Preencher com o valor total da
                            contribuição descontada dos trabalhadores
                            avulsos não portuários. Origem: campo
                            {vrDescCP}(1270_remunAvNP_vrDescCP) de
                            S-1270.
                        """
                        vr_bc_cp00: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "name": "vrBcCp00",
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0'),
                                "max_inclusive": Decimal('999999999999.99'),
                                "total_digits": 14,
                                "fraction_digits": 2,
                            }
                        )
                        vr_bc_cp15: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "name": "vrBcCp15",
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0'),
                                "max_inclusive": Decimal('999999999999.99'),
                                "total_digits": 14,
                                "fraction_digits": 2,
                            }
                        )
                        vr_bc_cp20: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "name": "vrBcCp20",
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0'),
                                "max_inclusive": Decimal('999999999999.99'),
                                "total_digits": 14,
                                "fraction_digits": 2,
                            }
                        )
                        vr_bc_cp25: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "name": "vrBcCp25",
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0'),
                                "max_inclusive": Decimal('999999999999.99'),
                                "total_digits": 14,
                                "fraction_digits": 2,
                            }
                        )
                        vr_bc_cp13: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "name": "vrBcCp13",
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0'),
                                "max_inclusive": Decimal('999999999999.99'),
                                "total_digits": 14,
                                "fraction_digits": 2,
                            }
                        )
                        vr_desc_cp: Optional[Decimal] = field(
                            default=None,
                            metadata={
                                "name": "vrDescCP",
                                "type": "Element",
                                "required": True,
                                "min_inclusive": Decimal('0'),
                                "max_inclusive": Decimal('999999999999.99'),
                                "total_digits": 14,
                                "fraction_digits": 2,
                            }
                        )

                    @dataclass
                    class InfoSubstPatrOpPort:
                        """

                        "

                        :ivar cnpj_op_portuario: Preencher com o CNPJ do
                            operador portuário. Origem: campo
                            {dadosLotacao/nrInsc}(1020_infoLotacao_inclusao_dadosLotacao_nrInsc)
                            de S-1020 relativo a
                            {codLotacao}(1280_infoSubstPatrOpPort_codLotacao)
                            em S-1280.
                        """
                        cnpj_op_portuario: Optional[str] = field(
                            default=None,
                            metadata={
                                "name": "cnpjOpPortuario",
                                "type": "Element",
                                "required": True,
                                "pattern": r"\d{14}",
                            }
                        )

                @dataclass
                class BasesAquis:
                    """

                    "

                    :ivar ind_aquis:
                    :ivar vlr_aquis: Valor total da aquisição de
                        produção rural de produtor rural. Origem: campo
                        {vlrTotAquis} de S-1250.
                    :ivar vr_cpdesc_pr: Preencher com o valor da
                        contribuição previdenciária descontada pelo
                        adquirente de produção de produtor rural - sub-
                        rogação. Origem: somatório do campo {vrCpDescPR}
                        de S-1250.
                    :ivar vr_cpnret: Valor da contribuição
                        previdenciária que deixou de ser retida pelo
                        declarante em decorrência de decisão/sentença
                        judicial.
                    :ivar vr_rat_nret: Valor da GILRAT, incidente sobre
                        a aquisição de produção rural de produtor rural,
                        cuja retenção deixou de ser efetuada em
                        decorrência de decisão/sentença judicial.
                    :ivar vr_senar_nret: Valor da contribuição destinada
                        ao SENAR, incidente sobre a aquisição de
                        produção rural de produtor rural pessoa
                        física/segurado especial, que deixou de ser
                        retida em decorrência de decisão/sentença
                        judicial.
                    :ivar vr_cpcalc_pr: Valor calculado relativo à
                        contribuição previdenciária do produtor rural,
                        de acordo com {indAquis}(./indAquis), conforme
                        segue: a) {indAquis}(./indAquis) = [1, 2]:
                        {vlrAquis}(./vlrAquis) x 1,2%; b)
                        {indAquis}(./indAquis) = [3]:
                        {vlrAquis}(./vlrAquis) x 1,7%; c)
                        {indAquis}(./indAquis) = [4, 5, 6]: 0 (zero).
                    :ivar vr_rat_desc_pr: Valor da contribuição
                        destinada ao financiamento dos benefícios
                        concedidos em razão do grau de incidência da
                        incapacidade laborativa decorrente dos riscos
                        ambientais do trabalho, incidente sobre a
                        aquisição de produção rural de produtor rural.
                    :ivar vr_rat_calc_pr: Valor calculado relativo à
                        contribuição GILRAT devida pelo produtor rural,
                        de acordo com {indAquis}(./indAquis), conforme
                        segue: a) {indAquis}(./indAquis) = [1, 2, 3]:
                        {vlrAquis}(./vlrAquis) x 0,1%; b)
                        {indAquis}(./indAquis) = [4, 5, 6]: 0 (zero).
                    :ivar vr_senar_desc: Valor da contribuição destinada
                        ao SENAR, incidente sobre a aquisição de
                        produção rural de produtor rural pessoa
                        física/segurado especial. Origem: campo
                        {vrSenarDesc} de S-1250.
                    :ivar vr_senar_calc: Valor calculado da contribuição
                        devida pelo produtor rural ao SENAR, conforme
                        segue: a) {indAquis}(./indAquis) = [1, 2, 4, 5]:
                        {vlrAquis}(./vlrAquis) x 0,2%; b)
                        {indAquis}(./indAquis) = [3, 6]: 0 (zero). OBS.:
                        No período de 04/2020 a 06/2020, a alíquota deve
                        ser 0,1%.
                    """
                    ind_aquis: Optional[BasesAquisIndAquis] = field(
                        default=None,
                        metadata={
                            "name": "indAquis",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    vlr_aquis: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vlrAquis",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_cpdesc_pr: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrCPDescPR",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_cpnret: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrCPNRet",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_rat_nret: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrRatNRet",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_senar_nret: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrSenarNRet",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_cpcalc_pr: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrCPCalcPR",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_rat_desc_pr: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrRatDescPR",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_rat_calc_pr: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrRatCalcPR",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_senar_desc: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrSenarDesc",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_senar_calc: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrSenarCalc",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )

                @dataclass
                class BasesComerc:
                    """

                    "

                    :ivar ind_comerc: Indicativo de comercialização.
                        Origem: campo
                        {indComerc}(1260_infoComProd_ideEstabel_tpComerc_indComerc)
                        de S-1260.
                    :ivar vr_bc_com_pr: Valor da base de cálculo da
                        comercialização da produção rural do produtor
                        rural PF/segurado especial a outra PF no varejo
                        ou a outro produtor rural PF/segurado especial
                        ou no mercado externo, conforme
                        {indComerc}(./indComerc). Origem: campo
                        {vrTotCom}(1260_infoComProd_ideEstabel_tpComerc_vrTotCom)
                        de S-1260.
                    :ivar vr_cpsusp: Valor da contribuição
                        previdenciária com exigibilidade suspensa.
                        Origem: campo
                        {vrCPSusp}(1260_infoComProd_ideEstabel_tpComerc_infoProcJud_vrCPSusp)
                        de S-1260.
                    :ivar vr_rat_susp: Valor da contribuição para GILRAT
                        com exigibilidade suspensa. Origem: campo
                        {vrRatSusp}(1260_infoComProd_ideEstabel_tpComerc_infoProcJud_vrRatSusp)
                        de S-1260.
                    :ivar vr_senar_susp: Valor da contribuição para o
                        SENAR com exigibilidade suspensa. Origem: campo
                        {vrSenarSusp}(1260_infoComProd_ideEstabel_tpComerc_infoProcJud_vrSenarSusp)
                        de S-1260.
                    """
                    ind_comerc: Optional[TsIndComerc] = field(
                        default=None,
                        metadata={
                            "name": "indComerc",
                            "type": "Element",
                            "required": True,
                        }
                    )
                    vr_bc_com_pr: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrBcComPR",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_cpsusp: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrCPSusp",
                            "type": "Element",
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_rat_susp: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrRatSusp",
                            "type": "Element",
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_senar_susp: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrSenarSusp",
                            "type": "Element",
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )

                @dataclass
                class InfoCrestab:
                    """

                    "

                    :ivar tp_cr:
                    :ivar vr_cr: Valor correspondente ao CR apurado.
                        Validação: Deve ser apurado de acordo com a
                        legislação em vigor na competência. Deve ser
                        maior que 0 (zero).
                    :ivar vr_susp_cr: Valor suspenso correspondente ao
                        CR apurado. Validação: Deve ser apurado de
                        acordo com as informações de processos judiciais
                        e administrativos.
                    """
                    tp_cr: Optional[str] = field(
                        default=None,
                        metadata={
                            "name": "tpCR",
                            "type": "Element",
                            "required": True,
                            "pattern": r"\d{6}",
                        }
                    )
                    vr_cr: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrCR",
                            "type": "Element",
                            "required": True,
                            "min_exclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_susp_cr: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrSuspCR",
                            "type": "Element",
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )

                @dataclass
                class BasesPisPasep:
                    """

                    "

                    :ivar vr_bc_pis_pasep: Preencher com a base da
                        contribuição do PIS/PASEP. Origem: somatório do
                        campo
                        {}(5001_infoPisPasep_ideEstab_infoCategPisPasep_infoBasePisPasep_valorPisPasep)
                        de S-5001, quando
                        {}(5001_infoPisPasep_ideEstab_infoCategPisPasep_infoBasePisPasep_tpValorPisPasep)
                        em S-5001 = [11].
                    :ivar vr_bc_pis_pasep_susp: Preencher com a base da
                        contribuição do PIS/PASEP suspensa. Origem:
                        somatório do campo
                        {}(5001_infoPisPasep_ideEstab_infoCategPisPasep_infoBasePisPasep_valorPisPasep)
                        de S-5001, quando
                        {}(5001_infoPisPasep_ideEstab_infoCategPisPasep_infoBasePisPasep_tpValorPisPasep)
                        em S-5001 = [91].
                    """
                    vr_bc_pis_pasep: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrBcPisPasep",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )
                    vr_bc_pis_pasep_susp: Optional[Decimal] = field(
                        default=None,
                        metadata={
                            "name": "vrBcPisPasepSusp",
                            "type": "Element",
                            "required": True,
                            "min_inclusive": Decimal('0'),
                            "max_inclusive": Decimal('999999999999.99'),
                            "total_digits": 14,
                            "fraction_digits": 2,
                        }
                    )

            @dataclass
            class InfoCrcontrib:
                """

                "

                :ivar tp_cr:
                :ivar vr_cr: Valor correspondente ao CR apurado.
                    Validação: Deve ser apurado de acordo com a
                    legislação em vigor na competência. Deve ser maior
                    que 0 (zero).
                :ivar vr_crsusp: Valor do tributo com exigibilidade
                    suspensa.
                """
                tp_cr: Optional[str] = field(
                    default=None,
                    metadata={
                        "name": "tpCR",
                        "type": "Element",
                        "required": True,
                        "pattern": r"\d{6}",
                    }
                )
                vr_cr: Optional[Decimal] = field(
                    default=None,
                    metadata={
                        "name": "vrCR",
                        "type": "Element",
                        "required": True,
                        "min_exclusive": Decimal('0'),
                        "max_inclusive": Decimal('999999999999.99'),
                        "total_digits": 14,
                        "fraction_digits": 2,
                    }
                )
                vr_crsusp: Optional[Decimal] = field(
                    default=None,
                    metadata={
                        "name": "vrCRSusp",
                        "type": "Element",
                        "min_inclusive": Decimal('0'),
                        "max_inclusive": Decimal('999999999999.99'),
                        "total_digits": 14,
                        "fraction_digits": 2,
                    }
                )