from __future__ import annotations

from dataclasses import dataclass

from core.nfse.nacional.schemas.v1_00.tipos_eventos_v1_00 import TcpedRegEvt

__NAMESPACE__ = "http://www.sped.fazenda.gov.br/nfse"


@dataclass(kw_only=True)
class PedRegEvento(TcpedRegEvt):
    """
    Schema XML do Pedido de Registro de Eventos.
    """

    class Meta:
        name = "pedRegEvento"
        namespace = "http://www.sped.fazenda.gov.br/nfse"
