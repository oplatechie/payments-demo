"""Helpers for tests."""
import re


def is_luhn_pan(value) -> bool:
    """True if value is a 13-19 digit string that passes the Luhn check (looks like a card number)."""
    s = str(value) if value is not None else ""
    if not re.fullmatch(r"\d{13,19}", s):
        return False
    total = 0
    for i, ch in enumerate(reversed(s)):
        d = int(ch)
        if i % 2 == 1:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def find_pans(text: str) -> list[str]:
    """All Luhn-valid 13-19 digit runs inside a text."""
    return [m for m in re.findall(r"\d{13,19}", text or "") if is_luhn_pan(m)]


def extract_code(email: dict) -> str:
    """The 6-digit code from a login email."""
    match = re.search(r"\b(\d{6})\b", email["body"])
    assert match, f"no code in email: {email['body']!r}"
    return match.group(1)
