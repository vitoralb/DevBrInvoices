from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from xsdata.models.datatype import XmlDate

__NAMESPACE__ = "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00"


class TsCrdia(Enum):
    """Código de Receita - CR relativo ao Imposto de Renda Retido na Fonte sobre rendimentos do trabalho pagos a residente no exterior para fins fiscais."

    :cvar VALUE_047301: IRRF - Residentes no exterior, para fins fiscais
    """
    VALUE_047301 = '047301'
class TsCrmen(Enum):
    """Código de Receita - CR relativo ao Imposto de Renda Retido na Fonte sobre rendimentos do trabalho."

    :cvar VALUE_056107: IRRF mensal, 13° salário e férias sobre trabalho
        assalariado no país ou ausente no exterior a serviço do país,
        exceto se contratado por empregador doméstico ou por segurado
        especial sujeito a recolhimento unificado
    :cvar VALUE_056108: IRRF mensal e férias - Empregado doméstico
    :cvar VALUE_056109: IRRF 13° salário na rescisão de contrato de
        trabalho - Empregado doméstico
    :cvar VALUE_056110: IRRF - Empregado doméstico 13º salário
    :cvar VALUE_056111: IRRF - Empregado/Trabalhador rural - Segurado
        especial
    :cvar VALUE_056112: IRRF - Empregado/Trabalhador rural - Segurado
        especial 13° salário
    :cvar VALUE_056113: IRRF - Empregado/Trabalhador rural - Segurado
        especial 13° salário rescisório
    :cvar VALUE_058806: IRRF sobre rendimento do trabalho sem vínculo
        empregatício
    :cvar VALUE_061001: IRRF sobre rendimentos relativos a prestação de
        serviços de transporte rodoviário internacional de carga, pagos
        a transportador autônomo PF residente no Paraguai
    :cvar VALUE_353301: Proventos de aposentadoria, reserva, reforma ou
        pensão pagos por previdência pública
    :cvar VALUE_356201: IRRF sobre participação dos trabalhadores em
        lucros ou resultados - PLR
    :cvar VALUE_188901: Rendimentos Recebidos Acumuladamente - RRA
    """
    VALUE_056107 = '056107'
    VALUE_056108 = '056108'
    VALUE_056109 = '056109'
    VALUE_056110 = '056110'
    VALUE_056111 = '056111'
    VALUE_056112 = '056112'
    VALUE_056113 = '056113'
    VALUE_058806 = '058806'
    VALUE_061001 = '061001'
    VALUE_353301 = '353301'
    VALUE_356201 = '356201'
    VALUE_188901 = '188901'
class TsIndApurIr(Enum):
    """

    "

    :cvar VALUE_0: Normal (apuração sob a folha de pagamento declarada
        no eSocial)
    :cvar VALUE_1: Situação especial de apuração de IR
    """
    VALUE_0 = 0
    VALUE_1 = 1
class TsIndApuracao(Enum):
    """
    Indicativo de período de apuração.
    "

    :cvar VALUE_1: Mensal
    :cvar VALUE_2: Anual (13° salário)
    """
    VALUE_1 = 1
    VALUE_2 = 2
class TsIndGuia(Enum):
    """
    Indicativo do tipo de guia.
    "

    :cvar VALUE_1: Documento de Arrecadação do eSocial - DAE
    """
    VALUE_1 = 1
class TsIndMv(Enum):
    """
    Indicador de desconto da contribuição previdenciária do trabalhador.
    "

    :cvar VALUE_1: O declarante aplica a(s) alíquota(s) de desconto do
        segurado sobre a remuneração por ele informada (o percentual
        da(s) alíquota(s) será(ão) obtido(s) considerando a remuneração
        total do trabalhador)
    :cvar VALUE_2: O declarante aplica a(s) alíquota(s) de desconto do
        segurado sobre a diferença entre o limite máximo do salário de
        contribuição e a remuneração de outra(s) empresa(s) para as
        quais o trabalhador informou que houve o desconto
    :cvar VALUE_3: O declarante não realiza desconto do segurado, uma
        vez que houve desconto sobre o limite máximo de salário de
        contribuição em outra(s) empresa(s)
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
class TsIndRetif(Enum):
    """
    Informe [1] para arquivo original ou [2] para arquivo de retificação.
    "

    :cvar VALUE_1: Original
    :cvar VALUE_2: Retificação
    """
    VALUE_1 = 1
    VALUE_2 = 2
class TsIndSimples(Enum):
    """Indicador de contribuição substituída.
    Validação: O preenchimento do campo é obrigatório apenas no caso das empresas enquadradas no regime de tributação Simples Nacional, com tributação previdenciária substituída e não substituída em {perApur}(1200_ideEvento_perApur) ({classTrib}(1000_infoEmpregador_inclusao_infoCadastro_classTrib) em S-1000 = [03] em {perApur}(1200_ideEvento_perApur)). Para os demais empregadores, não deve ser informado.

    :cvar VALUE_1: Contribuição substituída integralmente
    :cvar VALUE_2: Contribuição não substituída
    :cvar VALUE_3: Contribuição não substituída concomitante com
        contribuição substituída
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
class TsProcEmi(Enum):
    """
    Processo de emissão do evento.
    "

    :cvar VALUE_1: Aplicativo do empregador
    :cvar VALUE_2: Aplicativo governamental - Simplificado Pessoa Física
    :cvar VALUE_3: Aplicativo governamental - Web Geral
    :cvar VALUE_4: Aplicativo governamental - Simplificado Pessoa
        Jurídica
    :cvar VALUE_22: Aplicativo governamental para dispositivos móveis -
        Empregador Doméstico
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_22 = 22
class TsProcEmi8(Enum):
    """
    Processo de emissão do evento.
    "

    :cvar VALUE_8: Aplicativo governamental para envio de eventos pelo
        Judiciário
    """
    VALUE_8 = 8
class TsProcEmiPf(Enum):
    """
    Processo de emissão do evento.
    "

    :cvar VALUE_1: Aplicativo do empregador
    :cvar VALUE_2: Aplicativo governamental - Simplificado Pessoa Física
    :cvar VALUE_3: Aplicativo governamental - Web Geral
    :cvar VALUE_22: Aplicativo governamental para dispositivos móveis -
        Empregador Doméstico
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_22 = 22
class TsProcEmiPj(Enum):
    """
    Processo de emissão do evento.
    "

    :cvar VALUE_1: Aplicativo do empregador
    :cvar VALUE_3: Aplicativo governamental - Web Geral
    :cvar VALUE_4: Aplicativo governamental - Simplificado Pessoa
        Jurídica
    """
    VALUE_1 = 1
    VALUE_3 = 3
    VALUE_4 = 4
class TsProcEmiPjSemSimplificado(Enum):
    """
    Processo de emissão do evento.
    "

    :cvar VALUE_1: Aplicativo do empregador
    :cvar VALUE_3: Aplicativo governamental - Web Geral
    """
    VALUE_1 = 1
    VALUE_3 = 3
class TsProcEmiSem8(Enum):
    """
    Processo de emissão do evento.
    "

    :cvar VALUE_1: Aplicativo do empregador
    :cvar VALUE_2: Aplicativo governamental - Simplificado Pessoa Física
    :cvar VALUE_3: Aplicativo governamental - Web Geral
    :cvar VALUE_4: Aplicativo governamental - Simplificado Pessoa
        Jurídica
    :cvar VALUE_9: Aplicativo governamental - Integração com a Junta
        Comercial
    :cvar VALUE_22: Aplicativo governamental para dispositivos móveis -
        Empregador Doméstico
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_9 = 9
    VALUE_22 = 22
class TsProcEmiTodos(Enum):
    """
    Processo de emissão do evento.
    "

    :cvar VALUE_1: Aplicativo do empregador
    :cvar VALUE_2: Aplicativo governamental - Simplificado Pessoa Física
    :cvar VALUE_3: Aplicativo governamental - Web Geral
    :cvar VALUE_4: Aplicativo governamental - Simplificado Pessoa
        Jurídica
    :cvar VALUE_8: Aplicativo governamental para envio de eventos pelo
        Judiciário
    :cvar VALUE_9: Aplicativo governamental - Integração com a Junta
        Comercial
    :cvar VALUE_22: Aplicativo governamental para dispositivos móveis -
        Empregador Doméstico
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_8 = 8
    VALUE_9 = 9
    VALUE_22 = 22
class TsSimNao(Enum):
    """

    "

    :cvar S: Sim
    :cvar N: Não
    """
    S = 'S'
    N = 'N'
class TsTmpParc(Enum):
    """Preencher com o código relativo ao tipo de contrato em tempo parcial.
    Validação: O código [1] só é válido se {codCateg}(../codCateg) = [104]. Os códigos [2, 3] não são válidos se {codCateg}(../codCateg) = [104].

    :cvar VALUE_0: Não é contrato em tempo parcial
    :cvar VALUE_1: Limitado a 25 horas semanais
    :cvar VALUE_2: Limitado a 30 horas semanais
    :cvar VALUE_3: Limitado a 26 horas semanais
    """
    VALUE_0 = 0
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
class TsTpAmb(Enum):
    """
    Identificação do ambiente.
    "

    :cvar VALUE_1: Produção
    :cvar VALUE_2: Produção restrita
    :cvar VALUE_7: Validação (uso interno)
    :cvar VALUE_8: Teste (uso interno)
    :cvar VALUE_9: Desenvolvimento (uso interno)
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_7 = 7
    VALUE_8 = 8
    VALUE_9 = 9
class TsTpDesc(Enum):
    """
    Indicativo do tipo de desconto.
    "

    :cvar VALUE_1: eConsignado
    """
    VALUE_1 = 1
class TsTpInsc1(Enum):
    """
    Preencher com o código correspondente ao tipo de inscrição, conforme Tabela 05.
    "

    :cvar VALUE_1: CNPJ
    """
    VALUE_1 = 1
class TsTpInsc12(Enum):
    """
    Preencher com o código correspondente ao tipo de inscrição, conforme Tabela 05.
    "

    :cvar VALUE_1: CNPJ
    :cvar VALUE_2: CPF
    """
    VALUE_1 = 1
    VALUE_2 = 2
class TsTpInsc134(Enum):
    """
    Preencher com o código correspondente ao tipo de inscrição, conforme Tabela 05.
    "

    :cvar VALUE_1: CNPJ
    :cvar VALUE_3: CAEPF
    :cvar VALUE_4: CNO
    """
    VALUE_1 = 1
    VALUE_3 = 3
    VALUE_4 = 4
class TsTpProc12(Enum):
    """
    Preencher com o código correspondente ao tipo de processo.
    "

    :cvar VALUE_1: Administrativo
    :cvar VALUE_2: Judicial
    """
    VALUE_1 = 1
    VALUE_2 = 2
class TsTpTrib(Enum):
    """
    Abrangência da decisão.
    "

    :cvar VALUE_1: IRRF
    :cvar VALUE_2: Contribuições sociais do trabalhador
    """
    VALUE_1 = 1
    VALUE_2 = 2
class TsUf(Enum):
    AC = 'AC'
    AL = 'AL'
    AP = 'AP'
    AM = 'AM'
    BA = 'BA'
    CE = 'CE'
    DF = 'DF'
    ES = 'ES'
    GO = 'GO'
    MA = 'MA'
    MT = 'MT'
    MS = 'MS'
    MG = 'MG'
    PA = 'PA'
    PB = 'PB'
    PR = 'PR'
    PE = 'PE'
    PI = 'PI'
    RJ = 'RJ'
    RN = 'RN'
    RS = 'RS'
    RO = 'RO'
    RR = 'RR'
    SC = 'SC'
    SP = 'SP'
    SE = 'SE'
    TO = 'TO'
class TsUndSalFixo(Enum):
    """
    Unidade de pagamento da parte fixa da remuneração.
    "

    :cvar VALUE_1: Por hora
    :cvar VALUE_2: Por dia
    :cvar VALUE_3: Por semana
    :cvar VALUE_4: Por quinzena
    :cvar VALUE_5: Por mês
    :cvar VALUE_6: Por tarefa
    :cvar VALUE_7: Não aplicável - Salário exclusivamente variável
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_6 = 6
    VALUE_7 = 7
@dataclass
class TAlvaraJudicial:
    """

    "

    :ivar nr_proc_jud: Preencher com o número do processo judicial.
        Validação: Deve ser um número de processo judicial válido.
    """
    class Meta:
        name = "T_alvaraJudicial"

    nr_proc_jud: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrProcJud",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "length": 20,
        }
    )
class TAprendIndAprend(Enum):
    """
    Indicativo de modalidade de contratação de aprendiz.
    "

    :cvar VALUE_1: Contratação direta: contratação do aprendiz efetivada
        pelo estabelecimento cumpridor da cota de aprendizagem
    :cvar VALUE_2: Contratação indireta: contratação do aprendiz
        efetivada por entidades sem fins lucrativos ou por entidades de
        prática desportiva a serviço do estabelecimento cumpridor da
        cota
    """
    VALUE_1 = 1
    VALUE_2 = 2
@dataclass
class TContato:
    class Meta:
        name = "T_contato"

    fone_princ: Optional[str] = field(
        default=None,
        metadata={
            "name": "fonePrinc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 8,
            "max_length": 13,
            "pattern": r".*[^\s].*",
        }
    )
    email_princ: Optional[str] = field(
        default=None,
        metadata={
            "name": "emailPrinc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 6,
            "max_length": 60,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TEnderecoExterior:
    """Endereço no exterior.

    CONDICAO_GRUPO: O (se não informado o grupo {brasil}(../brasil)); N
    (nos demais casos)
    "

    :ivar pais_resid: Preencher com o código do país. Validação: Deve
        ser um código válido e existente na Tabela 06.
    :ivar dsc_lograd:
    :ivar nr_lograd:
    :ivar complemento:
    :ivar bairro:
    :ivar nm_cid:
    :ivar cod_postal:
    """
    class Meta:
        name = "T_endereco_exterior"

    pais_resid: Optional[str] = field(
        default=None,
        metadata={
            "name": "paisResid",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{3}",
        }
    )
    dsc_lograd: Optional[str] = field(
        default=None,
        metadata={
            "name": "dscLograd",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 100,
            "pattern": r"[^\s]{1}[\S\s]*",
        }
    )
    nr_lograd: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrLograd",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 10,
            "pattern": r".*[^\s].*",
        }
    )
    complemento: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 30,
            "pattern": r".*[^\s].*",
        }
    )
    bairro: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 90,
            "pattern": r".*[^\s].*",
        }
    )
    nm_cid: Optional[str] = field(
        default=None,
        metadata={
            "name": "nmCid",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 2,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        }
    )
    cod_postal: Optional[str] = field(
        default=None,
        metadata={
            "name": "codPostal",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 4,
            "max_length": 12,
            "pattern": r".*[^\s].*",
        }
    )
class THorContratualTpJornada(Enum):
    """
    Tipo de jornada.
    "

    :cvar VALUE_2: Jornada 12 x 36 (12 horas de trabalho seguidas de 36
        horas ininterruptas de descanso)
    :cvar VALUE_3: Jornada com horário diário fixo e folga variável
    :cvar VALUE_4: Jornada com horário diário fixo e folga fixa (no
        domingo)
    :cvar VALUE_5: Jornada com horário diário fixo e folga fixa (exceto
        no domingo)
    :cvar VALUE_6: Jornada com horário diário fixo e folga fixa (em
        outro dia da semana), com folga adicional periódica no domingo
    :cvar VALUE_7: Turno ininterrupto de revezamento
    :cvar VALUE_9: Demais tipos de jornada
    """
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_5 = 5
    VALUE_6 = 6
    VALUE_7 = 7
    VALUE_9 = 9
@dataclass
class TIdeBeneficio:
    """Identificação do beneficiário e do benefício.

    CHAVE_GRUPO: {cpfBenef*}, {nrBeneficio*}
    "

    :ivar cpf_benef: Informar o CPF do beneficiário.
    :ivar nr_beneficio: Número do benefício.
    """
    class Meta:
        name = "T_ideBeneficio"

    cpf_benef: Optional[str] = field(
        default=None,
        metadata={
            "name": "cpfBenef",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{11}",
        }
    )
    nr_beneficio: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrBeneficio",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoRetornoMensal:
    """Identificação do evento de retorno.

    Evento de origem: S-1299. CHAVE_GRUPO: {perApur*}
    "

    :ivar per_apur: Informar o mês/ano (formato AAAA-MM) de referência
        das informações.
    """
    class Meta:
        name = "T_ideEvento_retorno_mensal"

    per_apur: Optional[str] = field(
        default=None,
        metadata={
            "name": "perApur",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "length": 7,
            "pattern": r"([2]\d{3}|19[6-9]\d)-(1[0-2]|0[1-9])",
        }
    )
@dataclass
class TIdeTrabSemVinculo:
    """Identificação do TSVE
    DESCRICAO_COMPLETA:Identificação do Trabalhador Sem Vínculo de Emprego/Estatutário - TSVE.
    CHAVE_GRUPO: {cpfTrab*}, {matricula*}, {codCateg*}"

    :ivar cpf_trab:
    :ivar matricula: Matrícula atribuída ao trabalhador pela empresa.
        Validação: Deve corresponder à matrícula informada pelo
        empregador no evento S-2300 do respectivo contrato. Não
        preencher no caso de TSVE sem informação de matrícula no evento
        S-2300.
    :ivar cod_categ: Preencher com o código da categoria do trabalhador.
        Informar somente no caso de TSVE sem informação de matrícula no
        evento S-2300. Validação: Informação obrigatória e exclusiva se
        não houver preenchimento de {matricula}(./matricula). Se
        informado, deve ser um código válido e existente na Tabela 01.
    """
    class Meta:
        name = "T_ideTrabSemVinculo"

    cpf_trab: Optional[str] = field(
        default=None,
        metadata={
            "name": "cpfTrab",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{11}",
        }
    )
    matricula: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 30,
            "pattern": r".*[^\s].*",
        }
    )
    cod_categ: Optional[str] = field(
        default=None,
        metadata={
            "name": "codCateg",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "pattern": r"\d{3}",
        }
    )
@dataclass
class TIdeVinculo:
    """Informações de identificação do trabalhador e do vínculo.

    CHAVE_GRUPO: {cpfTrab*}, {matricula*}
    "

    :ivar cpf_trab:
    :ivar matricula: Matrícula atribuída ao trabalhador pela empresa ou,
        no caso de servidor público, a matrícula constante no Sistema de
        Administração de Recursos Humanos do órgão. Validação: Deve
        corresponder à matrícula informada pelo empregador no evento
        S-2200 do respectivo vínculo trabalhista.
    """
    class Meta:
        name = "T_ideVinculo"

    cpf_trab: Optional[str] = field(
        default=None,
        metadata={
            "name": "cpfTrab",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{11}",
        }
    )
    matricula: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 30,
        }
    )
@dataclass
class TIdeVinculoBaixa:
    """Informações de identificação do trabalhador e do vínculo.

    CHAVE_GRUPO: {cpfTrab*}, {matricula*}
    "

    :ivar cpf_trab:
    :ivar matricula: Matrícula atribuída ao trabalhador pela empresa ou,
        no caso de servidor público, a matrícula constante no Sistema de
        Administração de Recursos Humanos do órgão. Validação: Deve
        corresponder à matrícula informada pelo empregador no evento
        S-2190 ou S-2200 do respectivo vínculo trabalhista.
    """
    class Meta:
        name = "T_ideVinculo_baixa"

    cpf_trab: Optional[str] = field(
        default=None,
        metadata={
            "name": "cpfTrab",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{11}",
        }
    )
    matricula: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 30,
        }
    )
@dataclass
class TIdeVinculoSst:
    """Informações de identificação do trabalhador e do vínculo.

    CHAVE_GRUPO: {cpfTrab*}, {matricula*}, {codCateg*}
    "

    :ivar cpf_trab:
    :ivar matricula: Matrícula atribuída ao trabalhador pela empresa ou,
        no caso de servidor público, a matrícula constante no Sistema de
        Administração de Recursos Humanos do órgão. Validação: Deve
        corresponder à matrícula informada pelo empregador no evento
        S-2190, S-2200 ou S-2300 do respectivo contrato. Não preencher
        no caso de Trabalhador Sem Vínculo de Emprego/Estatutário - TSVE
        sem informação de matrícula no evento S-2300.
    :ivar cod_categ: Preencher com o código da categoria do trabalhador.
        Informar somente no caso de TSVE sem informação de matrícula no
        evento S-2300. Validação: Informação obrigatória e exclusiva se
        não houver preenchimento de {matricula}(./matricula). Se
        informado, deve ser um código válido e existente na Tabela 01.
    """
    class Meta:
        name = "T_ideVinculo_sst"

    cpf_trab: Optional[str] = field(
        default=None,
        metadata={
            "name": "cpfTrab",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{11}",
        }
    )
    matricula: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 30,
        }
    )
    cod_categ: Optional[str] = field(
        default=None,
        metadata={
            "name": "codCateg",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "pattern": r"\d{3}",
        }
    )
class TInfoEstagiarioNatEstagio(Enum):
    """Natureza do estágio ou da prestação de serviço civil voluntário.

    Validação: Se o código de categoria for igual a [906], deve ser
    preenchido com [N].
    "

    :cvar O: Obrigatório
    :cvar N: Não obrigatório
    """
    O = 'O'
    N = 'N'
class TInfoEstagiarioNivEstagio(Enum):
    """Informar o nível do estágio ou da prestação de serviço civil voluntário.

    Validação: Preenchimento obrigatório se o código de categoria for
    igual a [901]. Se o código de categoria for igual a [906], não pode
    ser informado [9].
    "

    :cvar VALUE_1: Fundamental
    :cvar VALUE_2: Médio
    :cvar VALUE_3: Formação profissional
    :cvar VALUE_4: Superior
    :cvar VALUE_8: Especial
    :cvar VALUE_9: Mãe social (Lei 7.644/1987)
    """
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_4 = 4
    VALUE_8 = 8
    VALUE_9 = 9
@dataclass
class TInfoInterm:
    """

    "

    :ivar dia:
    :ivar hrs_trab: Horas trabalhadas no dia pelo empregado com contrato
        de trabalho intermitente, no formato HHMM. Validação:
        Preenchimento obrigatório e exclusivo se
        {}(1000_infoEmpregador_inclusao_infoCadastro_classTrib) em
        S-1000 = [22]. Se preenchida, deve estar no intervalo entre
        [0000] e [2359], criticando inclusive a segunda parte do número,
        que indica os minutos, que deve ser menor ou igual a 59.
    """
    class Meta:
        name = "T_infoInterm"

    dia: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_inclusive": "0",
            "max_inclusive": "31",
            "pattern": r"\d{1,2}",
        }
    )
    hrs_trab: Optional[str] = field(
        default=None,
        metadata={
            "name": "hrsTrab",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 4,
            "pattern": r"(([0-1][0-9]|2[0-3])[0-5][0-9])",
        }
    )
@dataclass
class TInfoIntermProcTrab:
    """

    "

    :ivar dia:
    :ivar hrs_trab: Horas trabalhadas no dia pelo empregado com contrato
        de trabalho intermitente, no formato HHMM. Validação:
        Preenchimento obrigatório e exclusivo se
        {}(1000_infoEmpregador_inclusao_infoCadastro_classTrib) em
        S-1000 = [22] em
        {}(2500_ideTrab_infoContr_ideEstab_infoVlr_idePeriodo_perRef).
        Se preenchida, deve estar no intervalo entre [0000] e [2359],
        criticando inclusive a segunda parte do número, que indica os
        minutos, que deve ser menor ou igual a 59.
    """
    class Meta:
        name = "T_infoIntermProcTrab"

    dia: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_inclusive": "0",
            "max_inclusive": "31",
            "pattern": r"\d{1,2}",
        }
    )
    hrs_trab: Optional[str] = field(
        default=None,
        metadata={
            "name": "hrsTrab",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 4,
            "pattern": r"(([0-1][0-9]|2[0-3])[0-5][0-9])",
        }
    )
@dataclass
class TNascimento:
    """
    Grupo de informações do nascimento do trabalhador.
    "

    :ivar dt_nascto: Preencher com a data de nascimento.
    :ivar pais_nascto: Preencher com o código do país de nascimento do
        trabalhador. Validação: Deve ser um código válido e existente na
        Tabela 06.
    :ivar pais_nac:
    """
    class Meta:
        name = "T_nascimento"

    dt_nascto: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "dtNascto",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    pais_nascto: Optional[str] = field(
        default=None,
        metadata={
            "name": "paisNascto",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{3}",
        }
    )
    pais_nac: Optional[str] = field(
        default=None,
        metadata={
            "name": "paisNac",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{3}",
        }
    )
@dataclass
class TNovaValidade:
    """Novo período de validade das informações.

    DESCRICAO_COMPLETA:Informação preenchida exclusivamente em caso de
    alteração do período de validade das informações, apresentando o
    novo período de validade. CONDICAO_GRUPO: OC
    """

    class Meta:
        name = "T_novaValidade"

    ini_valid: Optional[str] = field(
        default=None,
        metadata={
            "name": "iniValid",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "length": 7,
            "pattern": r"([2]\d{3}|19[6-9]\d)-(1[0-2]|0[1-9])",
        }
    )
    fim_valid: Optional[str] = field(
        default=None,
        metadata={
            "name": "fimValid",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 7,
            "pattern": r"([2]\d{3}|19[6-9]\d)-(1[0-2]|0[1-9])",
        }
    )
@dataclass
class TTreiCap:
    class Meta:
        name = "T_treiCap"

    cod_trei_cap: Optional[str] = field(
        default=None,
        metadata={
            "name": "codTreiCap",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{4}",
        }
    )
@dataclass
class TAprend:
    """

    "

    :ivar ind_aprend:
    :ivar cnpj_ent_qual: Informar o número de inscrição no CNPJ da
        entidade qualificadora, no caso de contratação direta.
        Validação: Preenchimento obrigatório e exclusivo se
        {indAprend}(./indAprend) = [1]. Deve ser um CNPJ válido, com 14
        (catorze) algarismos.
    :ivar tp_insc: Preencher com o código correspondente ao tipo de
        inscrição do estabelecimento para o qual a contratação de
        aprendiz foi efetivada, no caso de contratação indireta,
        conforme Tabela 05. Validação: Preenchimento obrigatório e
        exclusivo se {indAprend}(./indAprend) = [2].
    :ivar nr_insc: Informar o número de inscrição do estabelecimento
        para o qual a contratação de aprendiz foi efetivada, no caso de
        contratação indireta, de acordo com o tipo de inscrição indicado
        no campo {aprend/tpInsc}(./tpInsc). Validação: Preenchimento
        obrigatório e exclusivo se {indAprend}(./indAprend) = [2]. Deve
        ser um identificador válido e: a) Se {aprend/tpInsc}(./tpInsc) =
        [1], deve ser informado com 14 (catorze) algarismos. Se o
        empregador for pessoa jurídica, a raiz do CNPJ informado deve
        ser diferente de {ideEmpregador/nrInsc}(/ideEmpregador_nrInsc).
        b) Se {aprend/tpInsc}(./tpInsc) = [2], deve ser diferente do CPF
        do empregado. Se o empregador for pessoa física, também deve ser
        diferente do CPF do empregador.
    :ivar cnpj_prat: Informar o número de inscrição no CNPJ do
        estabelecimento onde estão sendo realizadas as atividades
        práticas, quando ocorrer uma das seguintes situações: a)
        Modalidade alternativa de cumprimento de cota de aprendizagem
        (neste caso, informar o CNPJ da entidade concedente da parte
        prática); b) Realização das atividades práticas na empresa
        contratante do serviço terceirizado; c) Centralização das
        atividades práticas em estabelecimento da própria empresa,
        diverso do estabelecimento responsável pelo cumprimento da cota.
        Validação: Deve ser um CNPJ válido, com 14 (catorze) algarismos.
    """
    class Meta:
        name = "T_aprend"

    ind_aprend: Optional[TAprendIndAprend] = field(
        default=None,
        metadata={
            "name": "indAprend",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    cnpj_ent_qual: Optional[str] = field(
        default=None,
        metadata={
            "name": "cnpjEntQual",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "pattern": r"\d{14}",
        }
    )
    tp_insc: Optional[TsTpInsc12] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "pattern": r"\d{11}|\d{14}",
        }
    )
    cnpj_prat: Optional[str] = field(
        default=None,
        metadata={
            "name": "cnpjPrat",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "pattern": r"\d{14}",
        }
    )
@dataclass
class TDescFolha:
    """Informações de desconto do empréstimo em folha.
    CONDICAO_GRUPO: O (se {}(1010_infoRubrica_inclusao_dadosRubrica_natRubr) em S-1010 = [9253]); N (nos demais casos)

    :ivar tp_desc:
    :ivar inst_financ:
    :ivar nr_doc:
    :ivar observacao: Outras informações do desconto.
    """
    class Meta:
        name = "T_descFolha"

    tp_desc: Optional[TsTpDesc] = field(
        default=None,
        metadata={
            "name": "tpDesc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    inst_financ: Optional[str] = field(
        default=None,
        metadata={
            "name": "instFinanc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{3}",
        }
    )
    nr_doc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrDoc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 2,
            "max_length": 15,
            "pattern": r"[A-Za-z0-9][-_A-Za-z0-9/.//]{0,13}[A-Za-z0-9]",
        }
    )
    observacao: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 255,
            "pattern": r"[^\s]{1}[\S\s]*",
        }
    )
@dataclass
class TDetReemb:
    """

    "

    :ivar tp_insc: Informar o código correspondente ao tipo de inscrição
        do prestador de serviços.
    :ivar nr_insc: Informar o número de inscrição do prestador de
        serviços de assistência médica, de acordo com o tipo de
        inscrição indicado em {tpInsc}(./tpInsc). Validação: Deve ser um
        CNPJ ou CPF válido, de acordo com o tipo de inscrição indicado
        em {tpInsc}(./tpInsc). Não pode ser igual a
        {}(1210_ideBenef_cpfBenef).
    :ivar vlr_reemb: Valor do reembolso relativo ao ano do período
        indicado em {perApur}(1210_ideEvento_perApur). Validação:
        Informação não obrigatória se {vlrReembAnt}(./vlrReembAnt) for
        maior que zero.
    :ivar vlr_reemb_ant: Valor do reembolso relativo a anos anteriores.
        Validação: Informação não obrigatória se {vlrReemb}(./vlrReemb)
        for maior que zero.
    """
    class Meta:
        name = "T_detReemb"

    tp_insc: Optional[TsTpInsc12] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{11}|\d{14}",
        }
    )
    vlr_reemb: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vlrReemb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_exclusive": Decimal('0'),
            "max_inclusive": Decimal('999999999999.99'),
            "total_digits": 14,
            "fraction_digits": 2,
        }
    )
    vlr_reemb_ant: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vlrReembAnt",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_exclusive": Decimal('0'),
            "max_inclusive": Decimal('999999999999.99'),
            "total_digits": 14,
            "fraction_digits": 2,
        }
    )
@dataclass
class TDetReembTot:
    """

    "

    :ivar tp_insc: Informar o código correspondente ao tipo de inscrição
        do prestador de serviços.
    :ivar nr_insc: Informar o número de inscrição do prestador de
        serviços de assistência médica, de acordo com o tipo de
        inscrição indicado em {tpInsc}(./tpInsc).
    :ivar vlr_reemb: Valor do reembolso relativo ao ano do período
        indicado em {perApur}(1210_ideEvento_perApur).
    :ivar vlr_reemb_ant: Valor do reembolso relativo a anos anteriores.
    """
    class Meta:
        name = "T_detReemb_Tot"

    tp_insc: Optional[TsTpInsc12] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{11}|\d{14}",
        }
    )
    vlr_reemb: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vlrReemb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_inclusive": Decimal('0'),
            "max_inclusive": Decimal('999999999999.99'),
            "total_digits": 14,
            "fraction_digits": 2,
        }
    )
    vlr_reemb_ant: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vlrReembAnt",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_inclusive": Decimal('0'),
            "max_inclusive": Decimal('999999999999.99'),
            "total_digits": 14,
            "fraction_digits": 2,
        }
    )
@dataclass
class TEnderecoBrasil:
    """Endereço no Brasil.

    CONDICAO_GRUPO: O (se não informado o grupo
    {exterior}(../exterior)); N (nos demais casos)
    "

    :ivar tp_lograd:
    :ivar dsc_lograd:
    :ivar nr_lograd:
    :ivar complemento:
    :ivar bairro:
    :ivar cep:
    :ivar cod_munic:
    :ivar uf: Preencher com a sigla da Unidade da Federação - UF.
    """
    class Meta:
        name = "T_endereco_brasil"

    tp_lograd: Optional[str] = field(
        default=None,
        metadata={
            "name": "tpLograd",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 4,
        }
    )
    dsc_lograd: Optional[str] = field(
        default=None,
        metadata={
            "name": "dscLograd",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 100,
            "pattern": r"[^\s]{1}[\S\s]*",
        }
    )
    nr_lograd: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrLograd",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 10,
            "pattern": r".*[^\s].*",
        }
    )
    complemento: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 30,
            "pattern": r".*[^\s].*",
        }
    )
    bairro: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 90,
            "pattern": r".*[^\s].*",
        }
    )
    cep: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{8}",
        }
    )
    cod_munic: Optional[str] = field(
        default=None,
        metadata={
            "name": "codMunic",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{7}",
        }
    )
    uf: Optional[TsUf] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
@dataclass
class THorContratual:
    """

    "

    :ivar qtd_hrs_sem:
    :ivar tp_jornada:
    :ivar tmp_parc:
    :ivar hor_noturno: Indicar se a jornada semanal possui horário
        noturno (no todo ou em parte). Validação: Informação obrigatória
        se {codCateg}(../codCateg) for diferente de [111].
    :ivar dsc_jorn: Descrição da jornada semanal contratual, contendo os
        dias da semana e os respectivos horários contratuais (entrada,
        saída e intervalos).
    """
    class Meta:
        name = "T_horContratual"

    qtd_hrs_sem: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "qtdHrsSem",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_exclusive": Decimal('0'),
            "max_inclusive": Decimal('99.99'),
            "total_digits": 4,
            "fraction_digits": 2,
        }
    )
    tp_jornada: Optional[THorContratualTpJornada] = field(
        default=None,
        metadata={
            "name": "tpJornada",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    tmp_parc: Optional[TsTmpParc] = field(
        default=None,
        metadata={
            "name": "tmpParc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    hor_noturno: Optional[TsSimNao] = field(
        default=None,
        metadata={
            "name": "horNoturno",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    dsc_jorn: Optional[str] = field(
        default=None,
        metadata={
            "name": "dscJorn",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 999,
            "pattern": r"[^\s]{1}[\S\s]*",
        }
    )
@dataclass
class TIdeEmpregador:
    """Informações de identificação do empregador.

    CHAVE_GRUPO: {tpInsc*}, {nrInsc*}
    "

    :ivar tp_insc:
    :ivar nr_insc: Informar o número de inscrição do contribuinte de
        acordo com o tipo de inscrição indicado no campo
        {ideEmpregador/tpInsc}(./tpInsc) e conforme informado em S-1000.
    """
    class Meta:
        name = "T_ideEmpregador"

    tp_insc: Optional[TsTpInsc12] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{8}|\d{11}|\d{14}",
        }
    )
@dataclass
class TIdeEmpregadorCnpj:
    """Informações de identificação do empregador.

    CHAVE_GRUPO: {tpInsc*}, {nrInsc*}
    """

    class Meta:
        name = "T_ideEmpregador_cnpj"

    tp_insc: Optional[TsTpInsc1] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{8}|\d{14}",
        }
    )
@dataclass
class TIdeEmpregadorExclusao:
    """Informações de identificação do empregador.

    CHAVE_GRUPO: {tpInsc}, {nrInsc}
    "

    :ivar tp_insc:
    :ivar nr_insc: Informar o número de inscrição do contribuinte de
        acordo com o tipo de inscrição indicado no campo
        {ideEmpregador/tpInsc}(./tpInsc) e conforme informado em S-1000.
    """
    class Meta:
        name = "T_ideEmpregador_exclusao"

    tp_insc: Optional[TsTpInsc12] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{8}|\d{11}|\d{14}",
        }
    )
@dataclass
class TIdeEventoEvtTab:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_evtTab"

    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmi] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoEvtTabInicial:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_evtTab_inicial"

    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmiSem8] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoExclusao:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_exclusao"

    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmiTodos] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoExclusaoProcTrab:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_exclusao_proc_trab"

    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmi] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoFolha:
    """Informações de identificação do evento.

    CHAVE_GRUPO: {indApuracao*}, {perApur*}, {indGuia*}
    """

    class Meta:
        name = "T_ideEvento_folha"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    ind_apuracao: Optional[TsIndApuracao] = field(
        default=None,
        metadata={
            "name": "indApuracao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    per_apur: Optional[str] = field(
        default=None,
        metadata={
            "name": "perApur",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 4,
            "max_length": 7,
            "pattern": r"[2]{1}\d{3}-(1[0-2]|0[1-9])|[2]{1}\d{3}",
        }
    )
    ind_guia: Optional[TsIndGuia] = field(
        default=None,
        metadata={
            "name": "indGuia",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmi] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoFolhaMensal:
    """Informações de identificação do evento.

    CHAVE_GRUPO: {perApur*}, {indGuia*}
    """

    class Meta:
        name = "T_ideEvento_folha_mensal"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    per_apur: Optional[str] = field(
        default=None,
        metadata={
            "name": "perApur",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "length": 7,
            "pattern": r"([2]\d{3}|19[6-9]\d)-(1[0-2]|0[1-9])",
        }
    )
    ind_guia: Optional[TsIndGuia] = field(
        default=None,
        metadata={
            "name": "indGuia",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmi] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoFolhaMensalPf:
    """Informações de identificação do evento.

    CHAVE_GRUPO: {perApur*}, {indGuia*}
    """

    class Meta:
        name = "T_ideEvento_folha_mensal_PF"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    per_apur: Optional[str] = field(
        default=None,
        metadata={
            "name": "perApur",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "length": 7,
            "pattern": r"([2]\d{3}|19[6-9]\d)-(1[0-2]|0[1-9])",
        }
    )
    ind_guia: Optional[TsIndGuia] = field(
        default=None,
        metadata={
            "name": "indGuia",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmiPf] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoFolhaOpp:
    """Informações de identificação do evento.

    CHAVE_GRUPO: {indApuracao*}, {perApur*}
    """

    class Meta:
        name = "T_ideEvento_folha_opp"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    ind_apuracao: Optional[TsIndApuracao] = field(
        default=None,
        metadata={
            "name": "indApuracao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    per_apur: Optional[str] = field(
        default=None,
        metadata={
            "name": "perApur",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 4,
            "max_length": 7,
            "pattern": r"[2]{1}\d{3}-(1[0-2]|0[1-9])|[2]{1}\d{3}",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmiPj] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoFolhaSemRetificacao:
    """Informações de identificação do evento.

    CHAVE_GRUPO: {indApuracao*}, {perApur*}, {indGuia*}
    """

    class Meta:
        name = "T_ideEvento_folha_sem_retificacao"

    ind_apuracao: Optional[TsIndApuracao] = field(
        default=None,
        metadata={
            "name": "indApuracao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    per_apur: Optional[str] = field(
        default=None,
        metadata={
            "name": "perApur",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 4,
            "max_length": 7,
            "pattern": r"[2]{1}\d{3}-(1[0-2]|0[1-9])|[2]{1}\d{3}",
        }
    )
    ind_guia: Optional[TsIndGuia] = field(
        default=None,
        metadata={
            "name": "indGuia",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmi] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoRetornoContrib:
    """Identificação do evento de retorno.

    Evento de origem: S-1299. CHAVE_GRUPO: {indApuracao*}, {perApur*}
    "

    :ivar ind_apuracao:
    :ivar per_apur: Informar o mês/ano (formato AAAA-MM) de referência
        das informações, se {indApuracao}(./indApuracao) for igual a
        [1], ou apenas o ano (formato AAAA), se
        {indApuracao}(./indApuracao) for igual a [2].
    """
    class Meta:
        name = "T_ideEvento_retorno_contrib"

    ind_apuracao: Optional[TsIndApuracao] = field(
        default=None,
        metadata={
            "name": "indApuracao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    per_apur: Optional[str] = field(
        default=None,
        metadata={
            "name": "perApur",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 4,
            "max_length": 7,
            "pattern": r"[2]{1}\d{3}-(1[0-2]|0[1-9])|[2]{1}\d{3}",
        }
    )
@dataclass
class TIdeEventoTrab:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_trab"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmi] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoTrabPj:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_trab_PJ"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmiPj] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoTrabPjSemSimplificado:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_trab_PJ_sem_simplificado"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmiPjSemSimplificado] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoTrabAdmissao:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_trab_admissao"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmiSem8] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoTrabIndGuia:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_trab_indGuia"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    ind_guia: Optional[TsIndGuia] = field(
        default=None,
        metadata={
            "name": "indGuia",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmi] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TIdeEventoTrabJud:
    """
    Informações de identificação do evento.
    """

    class Meta:
        name = "T_ideEvento_trab_jud"

    ind_retif: Optional[TsIndRetif] = field(
        default=None,
        metadata={
            "name": "indRetif",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_recibo: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrRecibo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "length": 23,
            "pattern": r"[1]{1}\.\d{1}\.\d{19}",
        }
    )
    tp_amb: Optional[TsTpAmb] = field(
        default=None,
        metadata={
            "name": "tpAmb",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    proc_emi: Optional[TsProcEmi8] = field(
        default=None,
        metadata={
            "name": "procEmi",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    ver_proc: Optional[str] = field(
        default=None,
        metadata={
            "name": "verProc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 20,
            "pattern": r".*[^\s].*",
        }
    )
@dataclass
class TInfoEstagiario:
    """

    "

    :ivar nat_estagio:
    :ivar niv_estagio:
    :ivar area_atuacao: Área de atuação do estagiário ou, no caso de
        prestação de serviço civil voluntário, jornada semanal do
        desempenho de atividades em formato decimal.
    :ivar nr_apol: Número da apólice de seguro.
    :ivar dt_prev_term: Data prevista para o término do estágio ou da
        prestação de serviço civil voluntário. Validação: Deve ser uma
        data posterior à data de início do estágio ou da prestação de
        serviço civil voluntário.
    :ivar inst_ensino: Instituição de ensino ou entidade de
        formação/qualificação.
    :ivar age_integracao: Agente de integração. CONDICAO_GRUPO: OC (se o
        código de categoria for igual a [901]); N (nos demais casos)
    :ivar supervisor_estagio: Supervisor do estágio. CONDICAO_GRUPO: OC
        (se o código de categoria for igual a [901]); N (nos demais
        casos)
    """
    class Meta:
        name = "T_infoEstagiario"

    nat_estagio: Optional[TInfoEstagiarioNatEstagio] = field(
        default=None,
        metadata={
            "name": "natEstagio",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    niv_estagio: Optional[TInfoEstagiarioNivEstagio] = field(
        default=None,
        metadata={
            "name": "nivEstagio",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    area_atuacao: Optional[str] = field(
        default=None,
        metadata={
            "name": "areaAtuacao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 100,
            "pattern": r"[^\s]{1}[\S\s]*",
        }
    )
    nr_apol: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrApol",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 30,
            "pattern": r".*[^\s].*",
        }
    )
    dt_prev_term: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "dtPrevTerm",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    inst_ensino: Optional["TInfoEstagiario.InstEnsino"] = field(
        default=None,
        metadata={
            "name": "instEnsino",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    age_integracao: Optional["TInfoEstagiario.AgeIntegracao"] = field(
        default=None,
        metadata={
            "name": "ageIntegracao",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    supervisor_estagio: Optional["TInfoEstagiario.SupervisorEstagio"] = field(
        default=None,
        metadata={
            "name": "supervisorEstagio",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )

    @dataclass
    class InstEnsino:
        """

        "

        :ivar cnpj_inst_ensino: Preencher com o CNPJ da instituição de
            ensino, no caso de estágio, ou da entidade de
            formação/qualificação, no caso de prestação de serviço civil
            voluntário. Deve ser preenchido apenas se a
            instituição/entidade for brasileira. Validação: Se
            informado, deve ser um CNPJ válido, com 14 (catorze)
            algarismos.
        :ivar nm_razao: Informar a razão social. Validação:
            Preenchimento obrigatório e exclusivo se o campo
            {cnpjInstEnsino}(./cnpjInstEnsino) não estiver preenchido.
        :ivar dsc_lograd: Descrição do logradouro. Validação:
            Preenchimento obrigatório e exclusivo se o campo
            {cnpjInstEnsino}(./cnpjInstEnsino) não estiver preenchido.
        :ivar nr_lograd: Número do logradouro. Se não houver número a
            ser informado, preencher com "S/N". Validação: Preenchimento
            obrigatório e exclusivo se o campo
            {cnpjInstEnsino}(./cnpjInstEnsino) não estiver preenchido.
        :ivar bairro: Nome do bairro/distrito. Validação: Preenchimento
            obrigatório e exclusivo se o campo
            {cnpjInstEnsino}(./cnpjInstEnsino) não estiver preenchido.
        :ivar cep: Código de Endereçamento Postal - CEP. Validação: Não
            informar se o campo {cnpjInstEnsino}(./cnpjInstEnsino)
            estiver preenchido. Se informado, deve ser preenchido apenas
            com números, com 8 (oito) posições.
        :ivar cod_munic: Preencher com o código do município, conforme
            tabela do IBGE. Validação: Não informar se o campo
            {cnpjInstEnsino}(./cnpjInstEnsino) estiver preenchido. Se
            informado, deve ser um código válido e existente na tabela
            do IBGE.
        :ivar uf: Preencher com a sigla da Unidade da Federação - UF.
            Validação: Não informar se o campo
            {cnpjInstEnsino}(./cnpjInstEnsino) estiver preenchido.
        """
        cnpj_inst_ensino: Optional[str] = field(
            default=None,
            metadata={
                "name": "cnpjInstEnsino",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "pattern": r"\d{14}",
            }
        )
        nm_razao: Optional[str] = field(
            default=None,
            metadata={
                "name": "nmRazao",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "min_length": 1,
                "max_length": 100,
                "pattern": r"[^\s]{1}[\S\s]*",
            }
        )
        dsc_lograd: Optional[str] = field(
            default=None,
            metadata={
                "name": "dscLograd",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "min_length": 1,
                "max_length": 100,
                "pattern": r"[^\s]{1}[\S\s]*",
            }
        )
        nr_lograd: Optional[str] = field(
            default=None,
            metadata={
                "name": "nrLograd",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "min_length": 1,
                "max_length": 10,
                "pattern": r".*[^\s].*",
            }
        )
        bairro: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "min_length": 1,
                "max_length": 90,
                "pattern": r".*[^\s].*",
            }
        )
        cep: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "pattern": r"\d{8}",
            }
        )
        cod_munic: Optional[str] = field(
            default=None,
            metadata={
                "name": "codMunic",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "pattern": r"\d{7}",
            }
        )
        uf: Optional[TsUf] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            }
        )

    @dataclass
    class AgeIntegracao:
        """

        "

        :ivar cnpj_agnt_integ: CNPJ do agente de integração. Validação:
            Deve ser um CNPJ válido, com 14 (catorze) algarismos.
        """
        cnpj_agnt_integ: Optional[str] = field(
            default=None,
            metadata={
                "name": "cnpjAgntInteg",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
                "pattern": r"\d{14}",
            }
        )

    @dataclass
    class SupervisorEstagio:
        """

        "

        :ivar cpf_supervisor: CPF do responsável pela supervisão do
            estagiário. Validação: Deve ser um CPF válido.
        """
        cpf_supervisor: Optional[str] = field(
            default=None,
            metadata={
                "name": "cpfSupervisor",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
                "pattern": r"\d{11}",
            }
        )
@dataclass
class TInfoMv:
    """Informação de múltiplos vínculos DESCRICAO_COMPLETA:Grupo preenchido
    exclusivamente em caso de trabalhador que possua outros vínculos/atividades nos
    quais já tenha ocorrido desconto de contribuição previdenciária.

    CONDICAO_GRUPO: OC
    "

    :ivar ind_mv:
    :ivar remun_outr_empr: Remuneração recebida pelo trabalhador em
        outras empresas ou atividades DESCRICAO_COMPLETA:Informações
        relativas ao trabalhador que possui vínculo empregatício com
        outra(s) empresa(s) e/ou que exerce outras atividades como
        contribuinte individual, detalhando as empresas que efetuaram
        (ou efetuarão) desconto da contribuição. CHAVE_GRUPO: {tpInsc},
        {nrInsc}, {codCateg}
    """
    class Meta:
        name = "T_infoMV"

    ind_mv: Optional[TsIndMv] = field(
        default=None,
        metadata={
            "name": "indMV",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    remun_outr_empr: List["TInfoMv.RemunOutrEmpr"] = field(
        default_factory=list,
        metadata={
            "name": "remunOutrEmpr",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_occurs": 1,
            "max_occurs": 999,
        }
    )

    @dataclass
    class RemunOutrEmpr:
        """

        "

        :ivar tp_insc:
        :ivar nr_insc: Informar o número de inscrição do contribuinte de
            acordo com o tipo de inscrição indicado no campo
            {remunOutrEmpr/tpInsc}(./tpInsc). Validação: a) Se
            {remunOutrEmpr/tpInsc}(./tpInsc) = [1], deve ser um CNPJ
            válido, diferente do CNPJ base indicado no evento de
            Informações do Empregador (S-1000) e dos estabelecimentos
            informados através do evento S-1005. b) Se
            {remunOutrEmpr/tpInsc}(./tpInsc) = [2], deve ser um CPF
            válido e diferente do CPF do trabalhador e ainda, caso o
            empregador seja pessoa física, diferente do CPF do
            empregador.
        :ivar cod_categ:
        :ivar vlr_remun_oe:
        """
        tp_insc: Optional[TsTpInsc12] = field(
            default=None,
            metadata={
                "name": "tpInsc",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
            }
        )
        nr_insc: Optional[str] = field(
            default=None,
            metadata={
                "name": "nrInsc",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
                "pattern": r"\d{11}|\d{14}",
            }
        )
        cod_categ: Optional[str] = field(
            default=None,
            metadata={
                "name": "codCateg",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
                "pattern": r"\d{3}",
            }
        )
        vlr_remun_oe: Optional[Decimal] = field(
            default=None,
            metadata={
                "name": "vlrRemunOE",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
                "min_exclusive": Decimal('0'),
                "max_inclusive": Decimal('999999999999.99'),
                "total_digits": 14,
                "fraction_digits": 2,
            }
        )
@dataclass
class TInfoRra:
    """Informações complementares de RRA.
    DESCRICAO_COMPLETA:Informações complementares relativas a Rendimentos Recebidos Acumuladamente - RRA.
    CONDICAO_GRUPO: O (se {indRRA}(../indRRA) = [S]); N (nos demais casos)

    :ivar tp_proc_rra:
    :ivar nr_proc_rra: Informar o número do processo/requerimento
        administrativo/judicial. Validação: Informação obrigatória se
        {tpProcRRA}(./tpProcRRA) = [2] e opcional se
        {tpProcRRA}(./tpProcRRA) = [1]. Deve ser número de processo
        válido e: a) Se {tpProcRRA}(./tpProcRRA) = [1], deve possuir 17
        (dezessete) ou 21 (vinte e um) algarismos; b) Se
        {tpProcRRA}(./tpProcRRA) = [2], deve possuir 20 (vinte)
        algarismos.
    :ivar desc_rra:
    :ivar qtd_meses_rra:
    :ivar desp_proc_jud:
    :ivar ide_adv: Identificação dos advogados. CHAVE_GRUPO: {tpInsc},
        {nrInsc} CONDICAO_GRUPO: OC (se
        {vlrDespAdvogados}(../despProcJud_vlrDespAdvogados) &gt; 0); N
        (nos demais casos)
    """
    class Meta:
        name = "T_infoRRA"

    tp_proc_rra: Optional[TsTpProc12] = field(
        default=None,
        metadata={
            "name": "tpProcRRA",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_proc_rra: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrProcRRA",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "pattern": r"\d{17}|\d{20}|\d{21}",
        }
    )
    desc_rra: Optional[str] = field(
        default=None,
        metadata={
            "name": "descRRA",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        }
    )
    qtd_meses_rra: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "qtdMesesRRA",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_exclusive": Decimal('0'),
            "max_inclusive": Decimal('999.9'),
            "total_digits": 4,
            "fraction_digits": 1,
        }
    )
    desp_proc_jud: Optional["TInfoRra.DespProcJud"] = field(
        default=None,
        metadata={
            "name": "despProcJud",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
        }
    )
    ide_adv: List["TInfoRra.IdeAdv"] = field(
        default_factory=list,
        metadata={
            "name": "ideAdv",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "max_occurs": 99,
        }
    )

    @dataclass
    class DespProcJud:
        """Despesas com processo judicial DESCRICAO_COMPLETA:Detalhamento das despesas
        com processo judicial.

        CONDICAO_GRUPO: OC
        "

        :ivar vlr_desp_custas: Preencher com o valor das despesas com
            custas judiciais. Validação: Deve ser maior ou igual a 0
            (zero).
        :ivar vlr_desp_advogados: Preencher com o valor total das
            despesas com advogado(s). Validação: Se o grupo
            {}(../ideAdv) for preenchido, o valor informado neste campo
            deve ser maior ou igual à soma do(s) campo(s)
            {}(../ideAdv_vlrAdv) do grupo {}(../ideAdv). Deve ser maior
            ou igual a 0 (zero). O não preenchimento do grupo
            {}(../ideAdv) indica que o contribuinte declarante não
            possui as informações detalhadas por advogado.
        """
        vlr_desp_custas: Optional[Decimal] = field(
            default=None,
            metadata={
                "name": "vlrDespCustas",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
                "min_inclusive": Decimal('0'),
                "max_inclusive": Decimal('999999999999.99'),
                "total_digits": 14,
                "fraction_digits": 2,
            }
        )
        vlr_desp_advogados: Optional[Decimal] = field(
            default=None,
            metadata={
                "name": "vlrDespAdvogados",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
                "min_inclusive": Decimal('0'),
                "max_inclusive": Decimal('999999999999.99'),
                "total_digits": 14,
                "fraction_digits": 2,
            }
        )

    @dataclass
    class IdeAdv:
        """

        "

        :ivar tp_insc: Preencher com o código correspondente ao tipo de
            inscrição, conforme Tabela 05.
        :ivar nr_insc: Informar o número de inscrição do advogado.
            Validação: Deve ser um número de inscrição válido, de acordo
            com o tipo de inscrição indicado no campo
            {ideAdv/tpInsc}(./tpInsc), considerando as particularidades
            aplicadas à informação de CNPJ de órgão público em S-1000.
            Se {ideAdv/tpInsc}(./tpInsc) = [1], deve possuir 14
            (catorze) algarismos e, no caso de declarante pessoa
            jurídica, ser diferente do CNPJ base do empregador (exceto
            se {ideEmpregador/nrInsc}(/ideEmpregador_nrInsc) tiver 14
            (catorze) algarismos). Se {ideAdv/tpInsc}(./tpInsc) = [2],
            deve possuir 11 (onze) algarismos e, no caso de declarante
            pessoa física, ser diferente do CPF do empregador.
        :ivar vlr_adv: Valor da despesa com o advogado, se houver.
        """
        tp_insc: Optional[TsTpInsc12] = field(
            default=None,
            metadata={
                "name": "tpInsc",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
            }
        )
        nr_insc: Optional[str] = field(
            default=None,
            metadata={
                "name": "nrInsc",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "required": True,
                "pattern": r"\d{11}|\d{14}",
            }
        )
        vlr_adv: Optional[Decimal] = field(
            default=None,
            metadata={
                "name": "vlrAdv",
                "type": "Element",
                "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
                "min_inclusive": Decimal('0'),
                "max_inclusive": Decimal('999999999999.99'),
                "total_digits": 14,
                "fraction_digits": 2,
            }
        )
@dataclass
class TInfoSimplesS2299:
    """Informação relativa a empresas do Simples
    DESCRICAO_COMPLETA:Informação relativa a empresas enquadradas no regime de tributação Simples Nacional.
    CONDICAO_GRUPO: O (se {classTrib}(1000_infoEmpregador_inclusao_infoCadastro_classTrib) em S-1000 = [03] no mês/ano de {dtDeslig}(2299_infoDeslig_dtDeslig)); N (nos demais casos)

    :ivar ind_simples: Indicador de contribuição substituída.
    """
    class Meta:
        name = "T_infoSimples_S-2299"

    ind_simples: Optional[TsIndSimples] = field(
        default=None,
        metadata={
            "name": "indSimples",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
@dataclass
class TInfoSimplesS2399:
    """Informação relativa a empresas do Simples
    DESCRICAO_COMPLETA:Informação relativa a empresas enquadradas no regime de tributação Simples Nacional.
    CONDICAO_GRUPO: O (se {classTrib}(1000_infoEmpregador_inclusao_infoCadastro_classTrib) em S-1000 = [03]); N (nos demais casos)

    :ivar ind_simples: Indicador de contribuição substituída.
    """
    class Meta:
        name = "T_infoSimples_S-2399"

    ind_simples: Optional[TsIndSimples] = field(
        default=None,
        metadata={
            "name": "indSimples",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
@dataclass
class TItensRemunRpps:
    """
    Itens da remuneração do trabalhador DESCRICAO_COMPLETA:Rubricas que compõem a
    remuneração do trabalhador.
    "

    :ivar cod_rubr: Informar o código atribuído pelo empregador que
        identifica a rubrica em sua folha de pagamento.
    :ivar ide_tab_rubr:
    :ivar qtd_rubr: Informar a quantidade de referência para apuração
        (em horas, cotas, meses, etc.). Validação: Deve ser maior que 0
        (zero).
    :ivar fator_rubr: Informar o fator, percentual, etc. da rubrica,
        quando necessário. Validação: Deve ser maior que 0 (zero).
    :ivar vr_rubr:
    :ivar ind_apur_ir: Indicativo de tipo de apuração de IR.
    """
    class Meta:
        name = "T_itensRemun_rpps"

    cod_rubr: Optional[str] = field(
        default=None,
        metadata={
            "name": "codRubr",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 30,
            "pattern": r".*[^\s].*",
        }
    )
    ide_tab_rubr: Optional[str] = field(
        default=None,
        metadata={
            "name": "ideTabRubr",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_length": 1,
            "max_length": 8,
            "pattern": r".*[^\s].*",
        }
    )
    qtd_rubr: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "qtdRubr",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_exclusive": Decimal('0'),
            "max_inclusive": Decimal('9999999999.99'),
            "total_digits": 12,
            "fraction_digits": 2,
        }
    )
    fator_rubr: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "fatorRubr",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_exclusive": Decimal('0'),
            "max_inclusive": Decimal('999.99'),
            "total_digits": 5,
            "fraction_digits": 2,
        }
    )
    vr_rubr: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vrRubr",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_exclusive": Decimal('0'),
            "max_inclusive": Decimal('999999999999.99'),
            "total_digits": 14,
            "fraction_digits": 2,
        }
    )
    ind_apur_ir: Optional[TsIndApurIr] = field(
        default=None,
        metadata={
            "name": "indApurIR",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
@dataclass
class TLocalTrabGeral:
    """

    "

    :ivar tp_insc:
    :ivar nr_insc: Informar o número de inscrição do contribuinte de
        acordo com o tipo de inscrição indicado no campo
        {localTrabGeral/tpInsc}(./tpInsc). Validação: Deve ser um número
        de inscrição válido e existente na Tabela de Estabelecimentos
        (S-1005), bem como compatível com
        {localTrabGeral/tpInsc}(./tpInsc).
    :ivar desc_comp:
    """
    class Meta:
        name = "T_localTrabGeral"

    tp_insc: Optional[TsTpInsc134] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{12}|\d{14}",
        }
    )
    desc_comp: Optional[str] = field(
        default=None,
        metadata={
            "name": "descComp",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 80,
            "pattern": r"[^\s]{1}[\S\s]*",
        }
    )
@dataclass
class TProcJudTrab:
    """Informações sobre a existência de processos judiciais do trabalhador
    DESCRICAO_COMPLETA:Informações sobre a existência de processos judiciais do
    trabalhador com decisão favorável quanto à não incidência de contribuições
    sociais e/ou Imposto de Renda.

    CHAVE_GRUPO: {tpTrib}, {nrProcJud}, {codSusp} CONDICAO_GRUPO: OC
    """

    class Meta:
        name = "T_procJudTrab"

    tp_trib: Optional[TsTpTrib] = field(
        default=None,
        metadata={
            "name": "tpTrib",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_proc_jud: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrProcJud",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "length": 20,
        }
    )
    cod_susp: Optional[str] = field(
        default=None,
        metadata={
            "name": "codSusp",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{1,14}",
        }
    )
@dataclass
class TRemuneracao:
    """

    "

    :ivar vr_sal_fx:
    :ivar und_sal_fixo:
    :ivar dsc_sal_var: Descrição do salário por tarefa ou variável e
        como este é calculado. Ex.: Comissões pagas no percentual de 10%
        sobre as vendas. Validação: Preenchimento obrigatório se
        {undSalFixo}(./undSalFixo) for igual a [6, 7].
    """
    class Meta:
        name = "T_remuneracao"

    vr_sal_fx: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vrSalFx",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "min_inclusive": Decimal('0'),
            "max_inclusive": Decimal('999999999999.99'),
            "total_digits": 14,
            "fraction_digits": 2,
        }
    )
    und_sal_fixo: Optional[TsUndSalFixo] = field(
        default=None,
        metadata={
            "name": "undSalFixo",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    dsc_sal_var: Optional[str] = field(
        default=None,
        metadata={
            "name": "dscSalVar",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 999,
            "pattern": r"[^\s]{1}[\S\s]*",
        }
    )
@dataclass
class TSucessaoVinc:
    """

    "

    :ivar tp_insc:
    :ivar nr_insc: Informar o número de inscrição do empregador
        anterior, de acordo com o tipo de inscrição indicado no campo
        {sucessaoVinc/tpInsc}(./tpInsc).
    :ivar matric_ant: Matrícula do trabalhador no empregador anterior.
    :ivar dt_adm: Preencher com a data de admissão do trabalhador. No
        caso de transferência do empregado, deve ser preenchida a data
        inicial do vínculo no primeiro empregador (data de início do
        vínculo).
    """
    class Meta:
        name = "T_sucessaoVinc"

    tp_insc: Optional[TsTpInsc12] = field(
        default=None,
        metadata={
            "name": "tpInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )
    nr_insc: Optional[str] = field(
        default=None,
        metadata={
            "name": "nrInsc",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
            "pattern": r"\d{11}|\d{14}",
        }
    )
    matric_ant: Optional[str] = field(
        default=None,
        metadata={
            "name": "matricAnt",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "min_length": 1,
            "max_length": 30,
        }
    )
    dt_adm: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "dtAdm",
            "type": "Element",
            "namespace": "http://www.esocial.gov.br/schema/evt/evtIrrf/v_S_01_03_00",
            "required": True,
        }
    )