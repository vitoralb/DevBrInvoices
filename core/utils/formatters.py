import re
from decimal import Decimal


def format_cnpj(value: str | None) -> str:
    """Formats a 14-digit CNPJ into XX.XXX.XXX/XXXX-XX."""
    if not value:
        return ""
    v = re.sub(r"[^0-9a-zA-Z]", "", str(value))
    if len(v) == 14:
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
    return str(value)


def format_cep(value: str | None) -> str:
    """Formats an 8-digit CEP into XXXXX-XXX."""
    if not value:
        return ""
    v = re.sub(r"[^0-9a-zA-Z]", "", str(value))
    if len(v) == 8:
        return f"{v[:5]}-{v[5:]}"
    return str(value)


def format_money_pt_br(value: float | Decimal | int | None) -> str:
    """Formats a numeric value into Brazilian currency format (1.234,56)."""
    if value is None:
        return "0,00"
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

