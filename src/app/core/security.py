import secrets
import string
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

_password_hash = PasswordHash([Argon2Hasher()])

_PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*"
_PASSWORD_LENGTH = 16


def hash_password(plaintext: str) -> str:
    return _password_hash.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    return _password_hash.verify(plaintext, hashed)


_DUMMY_HASH = _password_hash.hash("dummy-password")


def dummy_verify_password(plaintext: str) -> None:
    """Verify against a throwaway hash to keep login timing constant when the email is unknown.

    Without this, a missing user short-circuits before the (deliberately slow) Argon2
    verification, letting an attacker enumerate valid emails by response time.
    """
    _password_hash.verify(plaintext, _DUMMY_HASH)


def generate_password(length: int = _PASSWORD_LENGTH) -> str:
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))


def encode_token(sub: str, role: str, secret: str, algorithm: str, expire_minutes: int) -> str:
    payload = {
        "sub": sub,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, secret: str, algorithm: str) -> dict:
    return jwt.decode(token, secret, algorithms=[algorithm])
