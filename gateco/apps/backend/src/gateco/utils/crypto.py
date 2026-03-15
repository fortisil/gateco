"""Fernet-based symmetric encryption for config secrets."""

import os

from cryptography.fernet import Fernet


def _get_key() -> bytes:
    """Return the Fernet key from env, generating a warning if missing."""
    raw = os.getenv("CONFIG_ENCRYPTION_KEY", "")
    if not raw:
        raw = Fernet.generate_key().decode()
    key = raw.encode() if isinstance(raw, str) else raw
    return key


def encrypt_value(plaintext: str, key: bytes | None = None) -> str:
    """Encrypt a plaintext string and return the ciphertext as a string."""
    f = Fernet(key or _get_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str, key: bytes | None = None) -> str:
    """Decrypt a ciphertext string and return the plaintext."""
    f = Fernet(key or _get_key())
    return f.decrypt(ciphertext.encode()).decode()


def encrypt_config_secrets(
    config: dict, secret_fields: list[str], key: bytes | None = None,
) -> dict:
    """Encrypt only the named secret fields in a config dict (in-place copy)."""
    result = dict(config)
    for field in secret_fields:
        if field in result and result[field]:
            result[field] = encrypt_value(str(result[field]), key)
    return result


def decrypt_config_secrets(
    config: dict, secret_fields: list[str], key: bytes | None = None,
) -> dict:
    """Decrypt only the named secret fields in a config dict."""
    result = dict(config)
    for field in secret_fields:
        if field in result and result[field]:
            try:
                result[field] = decrypt_value(str(result[field]), key)
            except Exception:
                pass  # field not encrypted or corrupt
    return result


def mask_config_secrets(config: dict, secret_fields: list[str]) -> dict:
    """Replace secret fields with None for API responses."""
    result = dict(config)
    for field in secret_fields:
        if field in result:
            result[field] = None
    return result
