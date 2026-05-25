class DuplicateEmailError(Exception):
    """Raised when a user's email violates the unique constraint.

    The SQL repository translates the IntegrityError; the router maps it to 409.
    """


class InvalidCredentialsError(Exception):
    """Raised when email is unknown or the password does not match."""


class InactiveUserError(Exception):
    """Raised when a user's is_active is False."""
