"""
security.py
Password hashing utilities using PBKDF2-HMAC-SHA256 with per-user random salts.
No plain-text passwords are ever stored or compared.
"""

import hashlib
import os
import hmac
import secrets
import string

PBKDF2_ITERATIONS = 200_000


def generate_salt():
    return os.urandom(16).hex()


def hash_password(password: str, salt: str) -> str:
    """Derive a secure hash of the password using the given salt."""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    )
    return dk.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    computed = hash_password(password, salt)
    return hmac.compare_digest(computed, expected_hash)


def generate_temp_password(length: int = 10) -> str:
    """
    Generate a random, secure temporary password for auto-created accounts
    (e.g. support staff added by an admin) or password resets.
    Guaranteed to contain at least one lowercase, one uppercase, one digit,
    and one symbol so it passes typical password strength checks.
    """
    lowercase = secrets.choice(string.ascii_lowercase)
    uppercase = secrets.choice(string.ascii_uppercase)
    digit = secrets.choice(string.digits)
    symbol = secrets.choice("!@#$%&*")

    remaining_pool = string.ascii_letters + string.digits + "!@#$%&*"
    remaining = [secrets.choice(remaining_pool) for _ in range(length - 4)]

    chars = list(lowercase + uppercase + digit + symbol) + remaining
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)
