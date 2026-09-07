from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDate

from core.nfse.paulistana.schemas.tipos_nfe_v02 import TpCpfcnpj
from core.nfse.paulistana.schemas.xmldsig_core_schema_v02 import Signature

__NAMESPACE__ = "http://www.prefeitura.sp.gov.br/nfe"


@dataclass(kw_only=True)
class PedidoConsultaNfePeriodo:
    """
    Schema utilizado para PEDIDO de consulta de NFS-e Emitidas ou Recebidas
    por período.

    Este Schema XML é utilizado pelos Prestadores/Tomadores de serviços
    consultarem NFS-e Emitidas ou Recebidas por eles.

    :ivar cabecalho: Cabeçalho do pedido.
    :ivar signature: Assinatura digital do tomador das NFS-e.
    """

    class Meta:
        name = "PedidoConsultaNFePeriodo"
        namespace = "http://www.prefeitura.sp.gov.br/nfe"

    cabecalho: PedidoConsultaNfePeriodo.Cabecalho = field(
        metadata={
            "name": "Cabecalho",
            "type": "Element",
            "namespace": "",
        }
    )
    signature: Signature = field(
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        }
    )

    @dataclass(kw_only=True)
    class Cabecalho:
        """
        :ivar cpfcnpjremetente: Informe o CPF/CNPJ do Remetente
            autorizado a transmitir a mensagem XML.
        :ivar cpfcnpj: Para consulta de NFS-e Recebidas Informe o CNPJ
            do Tomador. Para consulta de NFS-e Emitidas Informe o CNPJ
            do Prestador.
        :ivar inscricao: Para consulta de NFS-e Recebidas Informe a
            Inscrição Municipal do Tomador. Para consulta de NFS-e
            Emitidas Informe a Inscrição Municipal do Prestador. Neste
            caso o preenchimento deste campo se torna obrigatório.
        :ivar dt_inicio: Informe a data de início do período a ser
            consultado (AAAA-MM-DD).
        :ivar dt_fim: Informe a data final do período trasmitido (AAAA-
            MM-DD).
        :ivar numero_pagina: Informe o número da página que deseja
            consultar.
        :ivar versao: Informe a Versão do Schema XML utilizado.
        """

        cpfcnpjremetente: TpCpfcnpj = field(
            metadata={
                "name": "CPFCNPJRemetente",
                "type": "Element",
                "namespace": "",
            }
        )
        cpfcnpj: TpCpfcnpj = field(
            metadata={
                "name": "CPFCNPJ",
                "type": "Element",
                "namespace": "",
            }
        )
        inscricao: None | str = field(
            default=None,
            metadata={
                "name": "Inscricao",
                "type": "Element",
                "namespace": "",
                "pattern": r"[0-9]{1,12}",
            },
        )
        dt_inicio: XmlDate = field(
            metadata={
                "name": "dtInicio",
                "type": "Element",
                "namespace": "",
            }
        )
        dt_fim: XmlDate = field(
            metadata={
                "name": "dtFim",
                "type": "Element",
                "namespace": "",
            }
        )
        numero_pagina: str = field(
            default="1",
            metadata={
                "name": "NumeroPagina",
                "type": "Element",
                "namespace": "",
                "pattern": r"[0-9]{1,12}",
            },
        )
        versao: str = field(
            metadata={
                "name": "Versao",
                "type": "Attribute",
                "pattern": r"[0-9]{1,3}",
            }
        )
