class DuplicateIsbnError(Exception):
    """Raised when a book's isbn violates the unique constraint.

    The SQL repository translates the database `IntegrityError` into this
    domain-level exception so the application/HTTP layers stay decoupled from
    SQLAlchemy. The router maps it to HTTP 409.
    """


class BookHasCopiesError(Exception):
    """Raised when a `Book` cannot be deleted because at least one `BookCopy`
    still references it via FK.

    The SQL repository catches the `IntegrityError` from the
    `book_copies.book_id` FK (ON DELETE RESTRICT) and translates it to this
    domain exception. The router maps it to HTTP 409.
    """
