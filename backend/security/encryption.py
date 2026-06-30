import os
import base64
import hashlib
from cryptography.fernet import Fernet
from typing import Union

# Retrieve key from environment or use a stable fallback for development/testing
_KEY_STR = os.getenv("ENCRYPTION_SECRET")
if not _KEY_STR:
    # Fixed base64-encoded key for development consistency
    _KEY_STR = "VisooraDefaultSecretEncryptionKeyMustBe32Bytes="

# Ensure we have a valid 32-byte key for Fernet
try:
    # Ensure it is a valid url-safe base64 key
    _key = _KEY_STR.encode("utf-8")
    Fernet(_key)
except Exception:
    # Fallback: derive a valid key using SHA-256
    hasher = hashlib.sha256(_KEY_STR.encode("utf-8"))
    _key = base64.urlsafe_b64encode(hasher.digest())

_fernet = Fernet(_key)

def encrypt_value(value: Union[str, bytes]) -> str:
    """Encrypts a plaintext string or bytes and returns a base64 string."""
    if not value:
        return ""
    if isinstance(value, str):
        data = value.encode("utf-8")
    else:
        data = value
    return _fernet.encrypt(data).decode("utf-8")

def decrypt_value(cipher_text: str) -> str:
    """Decrypts a base64 ciphertext and returns the decrypted plaintext string."""
    if not cipher_text:
        return ""
    try:
        return _fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt credential value: {str(e)}")
