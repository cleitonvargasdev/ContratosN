import base64
import hashlib
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


ENCRYPTED_PREFIX = "enc::"


def _build_fernet(secret_source: str) -> Fernet:
    secret_source = secret_source.encode("utf-8")
    derived_key = base64.urlsafe_b64encode(hashlib.sha256(secret_source).digest())
    return Fernet(derived_key)


def _get_secret_sources() -> list[str]:
    sources: list[str] = []
    for candidate in (settings.secret_encryption_key, settings.jwt_secret_key):
        cleaned = candidate.strip() if isinstance(candidate, str) else None
        if cleaned and cleaned not in sources:
            sources.append(cleaned)
    return sources


def _decrypt_with_secret(cleaned_value: str, secret_source: str) -> str | None:
    token = cleaned_value[len(ENCRYPTED_PREFIX):]
    try:
        return _build_fernet(secret_source).decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None


def is_encrypted_secret(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(ENCRYPTED_PREFIX)


def encrypt_secret(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if is_encrypted_secret(cleaned):
        return cleaned
    token = _build_fernet(_get_secret_sources()[0]).encrypt(cleaned.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_secret(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if not is_encrypted_secret(cleaned):
        return cleaned
    for secret_source in _get_secret_sources():
        decrypted = _decrypt_with_secret(cleaned, secret_source)
        if decrypted is not None:
            return decrypted
    return cleaned


def secret_needs_reencryption(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = value.strip()
    if not cleaned:
        return False
    if not is_encrypted_secret(cleaned):
        return True
    secret_sources = _get_secret_sources()
    if not secret_sources:
        return False
    return _decrypt_with_secret(cleaned, secret_sources[0]) is None


def secret_matches(stored_value: str | None, plain_value: str | None) -> bool:
    return decrypt_secret(stored_value) == (plain_value.strip() if isinstance(plain_value, str) else plain_value)