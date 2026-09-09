import base64
import hashlib
import os
from cryptography.fernet import Fernet
from django.conf import settings


def get_fernet():
    """Returns a Fernet instance. Uses ENCRYPTION_KEY env var if set,
    otherwise falls back to deriving from SECRET_KEY (for backward compatibility)."""
    raw_key = getattr(settings, "ENCRYPTION_KEY", None) or os.environ.get(
        "ENCRYPTION_KEY"
    )
    if raw_key:
        # Normalize: if it's already a valid URL-safe base64 Fernet key (44 chars), use it directly
        if len(raw_key) == 44:
            return Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
        # Otherwise hash it to get 32 bytes
        key = hashlib.sha256(raw_key.encode()).digest()
    else:
        # Backward-compatible: derive from SECRET_KEY
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    encoded_key = base64.urlsafe_b64encode(key)
    return Fernet(encoded_key)


def encrypt_value(value: str) -> str:
    if not value:
        return value
    if value.startswith("gAAAAA"):  # Fernet tokens start with gAAAAA
        return value
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    if not value:
        return value
    if not value.startswith("gAAAAA"):
        return value
    f = get_fernet()
    try:
        return f.decrypt(value.encode()).decode()
    except Exception:
        # If decryption fails for some reason, return the original
        return value
