import uuid

import pytest
from pydantic import ValidationError

from app.members.domain.member_model import Member, MemberCreate, MemberStatus


def test_member_gets_uuid_and_timestamps() -> None:
    member = Member(full_name="Ada Lovelace", user_id=uuid.uuid4())
    assert isinstance(member.id, uuid.UUID)
    assert member.id.version == 7
    assert member.created_at is not None
    assert member.updated_at is not None


def test_status_defaults_to_active() -> None:
    member = Member(full_name="Grace Hopper", user_id=uuid.uuid4())
    assert member.status is MemberStatus.active


def test_member_create_status_defaults_to_active() -> None:
    data = MemberCreate(full_name="Alan Turing", email="alan@example.com")
    assert data.status is MemberStatus.active


def test_member_create_accepts_explicit_status() -> None:
    data = MemberCreate(full_name="Edsger", email="edsger@example.com", status="suspended")
    assert data.status is MemberStatus.suspended


def test_invalid_status_rejected() -> None:
    with pytest.raises(ValidationError):
        MemberCreate(full_name="Bad", email="bad@example.com", status="banned")
