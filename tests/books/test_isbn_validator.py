import pytest
from pydantic import ValidationError

from app.books.domain.book_model import BookCreate


def test_valid_isbn13_with_hyphens() -> None:
    book = BookCreate(title="T", author="A", isbn="978-0-06-093434-7")
    assert book.isbn == "9780060934347"


def test_valid_isbn10_with_hyphens() -> None:
    book = BookCreate(title="T", author="A", isbn="0-306-40615-2")
    assert book.isbn == "0306406152"


def test_valid_isbn13_no_hyphens() -> None:
    book = BookCreate(title="T", author="A", isbn="9780060934347")
    assert book.isbn == "9780060934347"


def test_valid_isbn10_no_hyphens() -> None:
    book = BookCreate(title="T", author="A", isbn="0306406152")
    assert book.isbn == "0306406152"


def test_invalid_checksum_isbn13() -> None:
    with pytest.raises(ValidationError):
        BookCreate(title="T", author="A", isbn="9780000000000")


def test_invalid_checksum_isbn10() -> None:
    with pytest.raises(ValidationError):
        BookCreate(title="T", author="A", isbn="0306406153")


def test_wrong_length() -> None:
    with pytest.raises(ValidationError):
        BookCreate(title="T", author="A", isbn="12345")


def test_null_isbn_bypasses_validation() -> None:
    book = BookCreate(title="T", author="A", isbn=None)
    assert book.isbn is None


def test_no_isbn_field_bypasses_validation() -> None:
    book = BookCreate(title="T", author="A")
    assert book.isbn is None


def test_isbn10_non_digit_chars() -> None:
    with pytest.raises(ValidationError):
        BookCreate(title="T", author="A", isbn="ABC456789X")


def test_isbn13_non_digit_chars() -> None:
    with pytest.raises(ValidationError):
        BookCreate(title="T", author="A", isbn="97800000000X0")
