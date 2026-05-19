class DuplicateIsbnError(Exception):
    """Raised when a book's isbn violates the unique constraint.

    The SQL repository translates the database `IntegrityError` into this
    domain-level exception so the application/HTTP layers stay decoupled from
    SQLAlchemy. The router maps it to HTTP 409.
    """
