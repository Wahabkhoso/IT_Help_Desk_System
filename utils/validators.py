"""
validators.py
Reusable input validation helpers used across services and UI forms.
"""

import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_REGEX.match(email.strip()))


def is_non_empty(value: str) -> bool:
    return value is not None and len(value.strip()) > 0


def min_length(value: str, length: int) -> bool:
    return value is not None and len(value.strip()) >= length


def is_valid_username(username: str) -> bool:
    return bool(username) and bool(re.match(r"^[A-Za-z0-9_.]{3,30}$", username.strip()))


class ValidationError(Exception):
    """Raised when a form/service-level validation check fails."""
    pass
