from __future__ import annotations

from dataclasses import dataclass

from core.nfse.nacional.schemas.v1_00.tipos_cnc_v1_00 import Tcnc

__NAMESPACE__ = "http://www.sped.fazenda.gov.br/nfse"


@dataclass(kw_only=True)
class Cnc(Tcnc):
    """
    Schema XML Leiaute do arquivo para upload - CNC.
    """

    class Meta:
        name = "CNC"
        namespace = "http://www.sped.fazenda.gov.br/nfse"
