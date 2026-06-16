import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(v: str) -> str:
    normalized = v.strip().lower()
    if not _EMAIL_RE.match(normalized):
        raise ValueError("Invalid email format")
    return normalized
