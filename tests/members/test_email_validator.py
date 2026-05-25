import pytest
from pydantic import ValidationError

from app.members.domain.member_model import MemberCreate


def test_valid_email_is_accepted() -> None:
    member = MemberCreate(full_name="A", email="ada@example.com")
    assert member.email == "ada@example.com"


def test_email_is_stripped_and_lowercased() -> None:
    member = MemberCreate(full_name="A", email="  Ada.Lovelace@Example.COM  ")
    assert member.email == "ada.lovelace@example.com"


def test_email_without_at_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MemberCreate(full_name="A", email="not-an-email")


def test_email_without_domain_dot_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MemberCreate(full_name="A", email="ada@localhost")


def test_email_with_whitespace_inside_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MemberCreate(full_name="A", email="ada lovelace@example.com")


def test_empty_email_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MemberCreate(full_name="A", email="")
