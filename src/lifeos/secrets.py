"""Keychain access. Every token, password, client secret, and feed URL lives here — never in a file."""
from __future__ import annotations

import getpass

import keyring

SERVICE = "lifeos"

# Patterns lifeos doctor scans the repo and vault for, to catch a secret that
# leaked into a file instead of the Keychain.
LEAK_PATTERNS = [
    r"shpat_[a-fA-F0-9]+",
    r"xoxp-[A-Za-z0-9-]+",
    r"xoxb-[A-Za-z0-9-]+",
    r"ya29\.[A-Za-z0-9_-]+",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\d+~[A-Za-z0-9]{20,}",  # Canvas-style access token
]


def set_secret(key: str) -> None:
    """Prompt for a value and store it in Keychain. Never echoes or logs it."""
    value = getpass.getpass(f"Value for '{key}' (hidden, stored in Keychain): ")
    if not value:
        raise ValueError("Empty value; nothing stored.")
    keyring.set_password(SERVICE, key, value)


def get_secret(key: str) -> str | None:
    return keyring.get_password(SERVICE, key)


def has_secret(key: str) -> bool:
    return get_secret(key) is not None
