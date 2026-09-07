import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet():
    # Derive a 32-byte key from the SECRET_KEY using SHA-256
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
