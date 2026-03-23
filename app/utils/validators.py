import re


def is_valid_phone(value: str) -> bool:
    return bool(re.fullmatch(r"\d{10,15}", value))

