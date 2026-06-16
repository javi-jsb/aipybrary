import pytest

from app.core.validators import validate_email


def test_valid_email_is_accepted() -> None:
    assert validate_email("ada@example.com") == "ada@example.com"


def test_email_is_stripped_and_lowercased() -> None:
    assert validate_email("  Ada.Lovelace@Example.COM  ") == "ada.lovelace@example.com"


def test_email_without_at_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid email format"):
        validate_email("not-an-email")


def test_email_without_domain_dot_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid email format"):
        validate_email("ada@localhost")


def test_email_with_whitespace_inside_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid email format"):
        validate_email("ada lovelace@example.com")


def test_empty_email_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid email format"):
        validate_email("")
