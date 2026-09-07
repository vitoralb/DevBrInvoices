from typing import Optional, Union

from core.models import CompanySettings, Invoice, NotaFiscal
from .base import NFSeProvider


def get_provider(
    invoice_or_nf: Optional[Union[Invoice, NotaFiscal]] = None,
    provider_type: Optional[str] = None,
) -> NFSeProvider:
    """Returns the appropriate NFSeProvider instance.

    If an invoice or NotaFiscal is provided, determines provider by checking:
    - If it has verification_code -> Paulistana.
    - If it has chave_acesso_nacional -> Sefin Nacional.
    Otherwise, defaults to the company's currently configured nfse_provider.
    """
    selected_type = provider_type

    if not selected_type and invoice_or_nf is not None:
        if isinstance(invoice_or_nf, NotaFiscal):
            selected_type = invoice_or_nf.provider_type
        elif isinstance(invoice_or_nf, Invoice):
            selected_type = invoice_or_nf.nfse_provider_type

    if not selected_type:
        company = CompanySettings.objects.first()
        selected_type = company.nfse_provider if company else "PAULISTANA"

    if selected_type == "NACIONAL":
        from .nacional.provider import NacionalProvider

        return NacionalProvider()
    else:
        from .paulistana.provider import PaulistanaProvider

        return PaulistanaProvider()
