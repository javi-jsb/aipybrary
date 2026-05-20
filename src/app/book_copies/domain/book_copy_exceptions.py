class DuplicateBarcodeError(Exception):
    """Raised when a book copy's barcode violates the unique constraint.

    The SQL repository translates the database `IntegrityError` into this
    domain-level exception so the application/HTTP layers stay decoupled from
    SQLAlchemy. The router maps it to HTTP 409.
    """


class BookCopyBookNotFoundError(Exception):
    """Raised by the application service when `book_id` does not reference an
    existing `Book` at copy-creation time.

    The router maps it to HTTP 422 (semantically the body value is invalid; the
    addressed `/book-copies` collection itself exists).
    """
