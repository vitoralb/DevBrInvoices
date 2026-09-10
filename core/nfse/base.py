from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
import datetime
from decimal import Decimal
from core.models import Invoice, NotaFiscal


@dataclass
class EmitResult:
    sucesso: bool
    xml_enviado: str = ""
    xml_retorno: str = ""
    codigo_verificacao: str = ""
    numero_nf: str = ""
    chave_acesso_nacional: str = ""
    erros: List[str] = field(default_factory=list)

    # Novas propriedades solicitadas
    data_hora_autorizacao: Optional[datetime.datetime] = None
    codigo_tributacao_nacional: str = ""
    codigo_nbs: str = ""
    aliquota_iss: Optional[Decimal] = None
    valor_iss: Optional[Decimal] = None
    codigo_servico_municipio: str = ""


@dataclass
class CancelResult:
    sucesso: bool
    xml_enviado: str = ""
    xml_retorno: str = ""
    erros: List[str] = field(default_factory=list)
    cancelation_date: Optional[datetime.datetime] = None


class NFSeProviderError(Exception):
    """Exception raised when a provider communication or business logic error occurs."""

    def __init__(
        self,
        message: str,
        raw_response: Optional[str] = None,
        status_code: Optional[int] = None,
        raw_request: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.raw_response = raw_response
        self.status_code = status_code
        self.raw_request = raw_request


class NFSeProvider(ABC):
    @abstractmethod
    def emitir_nfse(self, invoice: Invoice) -> EmitResult:
        """Emits a new NFS-e for the given invoice."""
        pass

    @abstractmethod
    def consultar_nfse(self, invoice: Invoice) -> Optional[EmitResult]:
        """Checks if the NFS-e for the given invoice was already emitted by the tax authority."""
        pass

    @abstractmethod
    def cancelar_nfse(self, invoice: Invoice) -> CancelResult:
        """Cancels an existing NFS-e."""
        pass

    @abstractmethod
    def baixar_pdf(self, invoice: Invoice) -> Optional[bytes]:
        """Downloads the PDF representation of the NFS-e."""
        pass

    @abstractmethod
    def buscar_nfse_por_numero(self, numero: str | int) -> Optional[dict]:
        """Fetches a specific NFS-e by its number."""
        pass

    @abstractmethod
    def buscar_nfse_por_chave(self, chave_acesso: str) -> Optional[dict]:
        """Fetches a specific NFS-e by its national key or verification code."""
        pass
