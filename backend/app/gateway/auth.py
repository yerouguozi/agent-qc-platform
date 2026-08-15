import hashlib
import os
import secrets

_ITERATIONS = 120_000


def hash_key(key: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", key.encode(), salt, _ITERATIONS)
    return f"pbkdf2${salt.hex()}${dk.hex()}"


def verify_key(key: str, stored: str) -> bool:
    try:
        _algo, salt_hex, dk_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", key.encode(), salt, _ITERATIONS)
        return secrets.compare_digest(dk.hex(), dk_hex)
    except (ValueError, TypeError):
        return False


def generate_api_key() -> str:
    return "qc_" + secrets.token_urlsafe(24)