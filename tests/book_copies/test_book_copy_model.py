import uuid

import pytest
from pydantic import ValidationError

from app.book_copies.domain.book_copy_model import BookCopy, BookCopyCreate, BookCopyUpdate


def test_book_copy_gets_uuid_and_timestamps() -> None:
    copy = BookCopy(book_id=uuid.uuid4(), barcode="ABC-001")
    assert isinstance(copy.id, uuid.UUID)
    assert copy.id.version == 7
    assert copy.created_at is not None
    assert copy.updated_at is not None


def test_book_copy_create_requires_book_id_and_barcode() -> None:
    with pytest.raises(ValidationError):
        BookCopyCreate(barcode="X")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        BookCopyCreate(book_id=uuid.uuid4())  # type: ignore[call-arg]


def test_book_copy_create_barcode_max_length() -> None:
    with pytest.raises(ValidationError):
        BookCopyCreate(book_id=uuid.uuid4(), barcode="x" * 101)


def test_book_copy_create_location_max_length() -> None:
    with pytest.raises(ValidationError):
        BookCopyCreate(book_id=uuid.uuid4(), barcode="ABC", location="x" * 201)


def test_book_copy_update_rejects_book_id() -> None:
    with pytest.raises(ValidationError):
        BookCopyUpdate(book_id=uuid.uuid4())  # type: ignore[call-arg]


def test_book_copy_update_allows_partial_fields() -> None:
    update = BookCopyUpdate(barcode="NEW")
    assert update.barcode == "NEW"
    assert update.location is None
    assert update.notes is None
