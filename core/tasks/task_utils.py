import re
import socket
import smtplib
from typing import Optional
import requests

# Deterministic error indicators: will not resolve by retrying without user/code intervention
DETERMINISTIC_STATUS_CODES = {
    400,
    401,
    403,
    404,
    405,
    406,
    409,
    410,
    411,
    412,
    413,
    414,
    415,
    416,
    417,
    422,
}

# Transient status codes: server-side errors, rate-limiting, or timeouts
TRANSIENT_STATUS_CODES = {
    408,
    429,
    500,
    502,
    503,
    504,
    520,
    521,
    522,
    523,
    524,
}

DETERMINISTIC_PATTERNS = [
    r"http\s+4(?!08|29)\d\d",
    r"4\d\d\s+client\s+error",
    r"bad\s+request",
    r"unauthorized|não\s+autorizado",
    r"forbidden|proibido",
    r"not\s+found|não\s+encontrad",
    r"unprocessable\s+entity",
    r"doesnotexist",
    r"validationerror|erro\s+de\s+validação|schema\s+validation",
    r"código\s+de\s+serviço|codigo\s+de\s+servico|ctribmun",
    r"código\s+de\s+tributação|codigo\s+de\s+tributacao",
    r"código\s+nbs|codigo\s+nbs",
    r"certificado\s+inválido|certificado\s+invalido|certificado\s+expirado|certificado\s+revogado",
    r"cnpj\s+do\s+certificado\s+não\s+confere|cnpj\s+inválido|cnpj\s+invalido",
    r"assinatura\s+digital\s+inválida|assinatura\s+invalida",
    r"24\s+horas|não\s+pode\s+ser\s+cancelada|nao\s+pode\s+ser\s+cancelada|prazo.*expirado",
    r"já\s+cancelada|ja\s+cancelada",
    r"companysettings\s+not\s+found",
    r"535\s+authentication\s+failed|bad\s+credentials",
    r"550\s+|553\s+|recipients\s+refused",
]

TRANSIENT_PATTERNS = [
    r"http\s+(408|429|5\d\d)",
    r"5\d\d\s+server\s+error",
    r"service\s+unavailable|temporarily\s+unavailable",
    r"bad\s+gateway|gateway\s+timeout",
    r"internal\s+server\s+error",
    r"fora\s+do\s+ar|prefeitura\s+fora\s+do\s+ar",
    r"indispon[íi]vel|temporariamente\s+indispon[íi]vel|serviço\s+indispon[íi]vel|servidor\s+indispon[íi]vel",
    r"falha\s+na\s+comunica[çc][ãa]o",
    r"not\s+processed\s+yet|waiting\s+for\s+prefeitura",
    r"pdf\s+not\s+ready\s+yet",
    r"lote\s+em\s+processamento|aguardando\s+processamento|em\s+processamento",
    r"timed?\s*out|timeout",
    r"connection\s+(error|reset|refused|dropped)",
    r"failed\s+to\s+establish\s+a\s+new\s+connection",
    r"network\s+is\s+unreachable|remote\s+end\s+closed|broken\s+pipe",
]


def _extract_status_code(exc: Exception) -> Optional[int]:
    status_code = getattr(exc, "status_code", None)
    if status_code is None and hasattr(exc, "response") and exc.response is not None:
        status_code = getattr(exc.response, "status_code", None)
    return status_code


def is_transient_error(e: Exception) -> bool:
    """Classifies whether an exception is transient (server/network side, worth retrying)
    or deterministic (client/validation/business-rule side, should fail immediately).
    """
    if not e:
        return False

    # Check exception chain (cause or context)
    chain = []
    curr = e
    while curr and curr not in chain:
        chain.append(curr)
        curr = getattr(curr, "__cause__", None) or getattr(curr, "__context__", None)

    for exc in chain:
        # Check HTTP status code on exception object
        status_code = _extract_status_code(exc)
        if status_code is not None:
            if status_code in DETERMINISTIC_STATUS_CODES:
                return False
            if status_code in TRANSIENT_STATUS_CODES:
                return True

        # Check standard transient exception classes
        if isinstance(
            exc,
            (
                requests.Timeout,
                requests.ConnectionError,
                socket.timeout,
                TimeoutError,
                ConnectionResetError,
                ConnectionRefusedError,
                BrokenPipeError,
                smtplib.SMTPServerDisconnected,
                smtplib.SMTPConnectError,
            ),
        ):
            return True

        # Check standard deterministic exception classes
        if isinstance(
            exc,
            (
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
                NotImplementedError,
            ),
        ):
            return False

        if isinstance(
            exc,
            (
                smtplib.SMTPAuthenticationError,
                smtplib.SMTPRecipientsRefused,
                smtplib.SMTPSenderRefused,
            ),
        ):
            return False

    # Examine string representations across the chain
    full_err_str = " ".join(str(exc) for exc in chain).lower()

    # If any deterministic pattern matches, fail immediately
    for pattern in DETERMINISTIC_PATTERNS:
        if re.search(pattern, full_err_str, re.IGNORECASE):
            return False

    # If any transient pattern matches, retry
    for pattern in TRANSIENT_PATTERNS:
        if re.search(pattern, full_err_str, re.IGNORECASE):
            return True

    # Safe default: fail immediately if not positively identified as transient
    return False

