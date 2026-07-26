"""
Password hashing for admin accounts.

Uses hashlib.pbkdf2_hmac (stdlib only — no bcrypt/passlib dependency, so
`pip install -r requirements.txt` stays simple). Stored format:

    pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>

verify_password re-derives the hash with the stored salt/iterations and
compares using a constant-time comparison.
"""
import hashlib
import hmac
import os

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 260_000
_SALT_BYTES = 16


def hash_password(plain_password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGORITHM}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_str, salt_hex, hash_hex = stored_hash.split("$")
        if algorithm != _ALGORITHM:
            return False
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)
