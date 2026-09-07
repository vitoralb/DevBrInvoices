from __future__ import annotations

from dataclasses import dataclass

from core.nfse.nacional.schemas.v1_00.tipos_complexos_v1_00 import Tcnfse

__NAMESPACE__ = "http://www.sped.fazenda.gov.br/nfse"


@dataclass(kw_only=True)
class Nfse(Tcnfse):
    """
    Schema XML da Nota Fiscal de Serviços Eletrônica - NFS-e.
    """

    class Meta:
        name = "NFSe"
        namespace = "http://www.sped.fazenda.gov.br/nfse"
