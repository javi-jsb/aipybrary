from sqlalchemy.exc import IntegrityError


def is_constraint_violated(exc: IntegrityError, constraint_name: str) -> bool:
    return exc.orig is not None and constraint_name in str(exc.orig)
