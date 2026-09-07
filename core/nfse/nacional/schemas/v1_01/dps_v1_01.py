from __future__ import annotations

from dataclasses import dataclass

from core.nfse.nacional.schemas.v1_01.tipos_complexos_v1_01 import Tcdps

__NAMESPACE__ = "http://www.sped.fazenda.gov.br/nfse"


@dataclass(kw_only=True)
class Dps(Tcdps):
    """
    Schema XML da Declaração de Prestação de Serviços - DPS.
    """

    class Meta:
        name = "DPS"
        namespace = "http://www.sped.fazenda.gov.br/nfse"
