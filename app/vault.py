"""Stand-in for the bank's external card vault.

The real vault is a separate service. Here it is an in-memory map so that card
numbers never enter the application database.
"""
import secrets

_vault: dict[str, str] = {}


def tokenize(card_number: str) -> str:
    token = "tok_" + secrets.token_hex(8)
    _vault[token] = card_number
    return token
