from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = int(os.getenv("MPESA_PASSWORD_HASH_ITERATIONS", "260000"))
PASSWORD_SALT_BYTES = 16

TOKEN_BYTES = 32
TOKEN_HASH_ALGORITHM = "sha256"
ACCESS_TOKEN_TTL_HOURS = int(os.getenv("MPESA_ACCESS_TOKEN_TTL_HOURS", "24"))


def hash_password(password: str) -> str:
    normalized = (password or "").strip()
    if len(normalized) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        TOKEN_HASH_ALGORITHM,
        normalized.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return (
        f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}$"
        f"{salt.hex()}${digest.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations_s, salt_hex, expected_hex = (stored_hash or "").split("$", 3)
        iterations = int(iterations_s)
    except Exception:
        return False

    if scheme != PASSWORD_SCHEME or iterations <= 0:
        return False

    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac(
        TOKEN_HASH_ALGORITHM,
        (password or "").strip().encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(digest, expected)


def issue_access_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def token_expiry(hours: int | None = None) -> datetime:
    ttl = hours if hours is not None else ACCESS_TOKEN_TTL_HOURS
    if ttl <= 0:
        ttl = ACCESS_TOKEN_TTL_HOURS
    return datetime.now(timezone.utc) + timedelta(hours=ttl)
