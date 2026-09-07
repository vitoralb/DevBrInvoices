from __future__ import annotations

from dataclasses import dataclass

from core.nfse.nacional.schemas.v1_01.tipos_eventos_v1_01 import Tcevento

__NAMESPACE__ = "http://www.sped.fazenda.gov.br/nfse"


@dataclass(kw_only=True)
class Evento(Tcevento):
    """
    Schema XML do Pedido de Registro de Eventos.
    """

    class Meta:
        name = "evento"
        namespace = "http://www.sped.fazenda.gov.br/nfse"
