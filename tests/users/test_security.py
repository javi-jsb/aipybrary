"""Tests for core/security.py primitives."""

import time

import jwt
import pytest

from app.core.security import (
    decode_token,
    encode_token,
    generate_password,
    hash_password,
    verify_password,
)

_SECRET = "test-secret"
_ALGO = "HS256"


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_hash_differs_from_plaintext() -> None:
    hashed = hash_password("secret")
    assert hashed != "secret"
    assert hashed.startswith("$argon2")


def test_verify_correct_password() -> None:
    hashed = hash_password("correct")
    assert verify_password("correct", hashed) is True


def test_verify_wrong_password() -> None:
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


# ---------------------------------------------------------------------------
# Password generation
# ---------------------------------------------------------------------------


def test_generate_password_is_non_empty() -> None:
    pw = generate_password()
    assert len(pw) > 0


def test_generate_password_produces_different_values() -> None:
    a = generate_password()
    b = generate_password()
    assert a != b


# ---------------------------------------------------------------------------
# JWT encode/decode
# ---------------------------------------------------------------------------


def test_encode_decode_carries_sub_and_role() -> None:
    token = encode_token("user-id-123", "admin", _SECRET, _ALGO, expire_minutes=30)
    payload = decode_token(token, _SECRET, _ALGO)
    assert payload["sub"] == "user-id-123"
    assert payload["role"] == "admin"


def test_expired_token_is_rejected() -> None:
    token = encode_token("uid", "staff", _SECRET, _ALGO, expire_minutes=0)
    time.sleep(1)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token, _SECRET, _ALGO)


def test_tampered_token_is_rejected() -> None:
    token = encode_token("uid", "staff", _SECRET, _ALGO, expire_minutes=30)
    parts = token.split(".")
    tampered = parts[0] + "." + parts[1] + ".invalidsig"
    with pytest.raises(jwt.InvalidSignatureError):
        decode_token(tampered, _SECRET, _ALGO)
