import re
from decimal import Decimal


def format_cnpj(value: str | None) -> str:
    """Formats a 14-character CNPJ into XX.XXX.XXX/XXXX-XX."""
    if not value:
        return ""
    v = re.sub(r"[^0-9a-zA-Z]", "", str(value)).upper()
    if len(v) == 14:
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
    return str(value)


def validate_cnpj(cnpj: str | None) -> bool:
    """
    Validates a 14-character CNPJ (supporting both standard numeric and
    alphanumeric CNPJs per Receita Federal IN RFB nº 2.229/2024 and Portaria RFB nº 439/2024).

    Rules:
    - Positions 1 to 12: alphanumeric [0-9A-Z]
    - Positions 13 and 14: numeric [0-9] (the two check digits)
    - Modulo 11 checksum calculation: character value = ord(c) - 48
    """
    if not cnpj:
        return False
    cleaned = re.sub(r"[^0-9a-zA-Z]", "", str(cnpj)).upper()
    if len(cleaned) != 14:
        return False
    if not re.match(r"^[0-9A-Z]{12}[0-9]{2}$", cleaned):
        return False

    def calc_digit(chars: str, weights: list[int]) -> int:
        total = sum((ord(c) - 48) * w for c, w in zip(chars, weights))
        rem = total % 11
        return 0 if rem < 2 else 11 - rem

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    dv1 = calc_digit(cleaned[:12], w1)
    dv2 = calc_digit(cleaned[:12] + str(dv1), w2)

    return f"{dv1}{dv2}" == cleaned[12:14]


def format_cep(value: str | None) -> str:
    """Formats an 8-digit CEP into XXXXX-XXX."""
    if not value:
        return ""
    v = re.sub(r"[^0-9a-zA-Z]", "", str(value))
    if len(v) == 8:
        return f"{v[:5]}-{v[5:]}"
    return str(value)


def format_money_pt_br(value: float | Decimal | int | None, decimals: int = 2) -> str:
    """Formats a numeric value into Brazilian currency format (1.234,56)."""
    if value is None:
        return f"0,{'0' * decimals}"
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")

