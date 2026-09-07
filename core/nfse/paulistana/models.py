# Backward-compatibility bridge - this file was renamed to rps_signer.py
from core.nfse.paulistana.rps_signer import assinar_rps, assinar_rps_v1

__all__ = ["assinar_rps", "assinar_rps_v1"]
