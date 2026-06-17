class DuplicateEmailError(Exception):
    """Raised when a member's email violates the unique constraint.

    The SQL repository translates the database `IntegrityError` into this
    domain-level exception so the application/HTTP layers stay decoupled from
    SQLAlchemy. The router maps it to HTTP 409.
    """


class MemberHasLoansError(Exception):
    """Raised when a `Member` cannot be deleted because at least one `Loan`
    still references it via FK.

    The SQL repository catches the `IntegrityError` from the `loans.member_id`
    FK (ON DELETE RESTRICT) and translates it to this domain exception. The
    router maps it to HTTP 409.
    """
