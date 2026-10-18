from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v1_0_0"


@dataclass
class ESocial:
    """
    Elemento raiz do eSocial.
    "

    :ivar consulta_lote_eventos: Define o(s) parâmetro(s) da consulta do
        resultado de processamento do lote.
    """
    class Meta:
        name = "eSocial"
        namespace = "http://www.esocial.gov.br/schema/lote/eventos/envio/consulta/retornoProcessamento/v1_0_0"

    consulta_lote_eventos: Optional["ESocial.ConsultaLoteEventos"] = field(
        default=None,
        metadata={
            "name": "consultaLoteEventos",
            "type": "Element",
            "required": True,
        }
    )

    @dataclass
    class ConsultaLoteEventos:
        """

        "

        :ivar protocolo_envio: Código de retorno para localização do
            lote. Número sequencial único produzido no instante de
            recepção da mensagem originada no empregador. São válidos os
            seguintes intervalos, expressos na base decimal:
            A.B.NNNNNNNNNNNNNNNNNNN A = Agente de recepção: Serpro=1 ou
            Caixa=2 (1 posição) B = Ambiente de recepção: Produção=1;
            Pré-produção - dados reais=2; Pré-produção - dados
            fictícios=3; Homologação=6; Validação=7; Testes=8;
            Desenvolvimento=9 N = Número sequencial (19 posições)
            Exemplo: SERPRO: 1.1.0000000000000000001 Caixa:
            2.1.0000000000000000001
        """
        protocolo_envio: Optional[str] = field(
            default=None,
            metadata={
                "name": "protocoloEnvio",
                "type": "Element",
                "required": True,
            }
        )