"""Encrypted storage for the few secrets the app must keep: Garmin login tokens and the notification address.

Nothing secret is stored in plain text. Each value is encrypted (AES-128-CBC with an HMAC, via Fernet) and kept in the database;
the key is kept somewhere else, in a file only this user can read, outside the data folder. So a copy of the database or of a
backup, on its own, gives away no logins.

What this does not protect against: someone who can read this user's files can read the key too. An unattended service has to be
able to unlock its own secrets, so that is a limit of any self-hosted app. Full-disk encryption on the computer is the answer to it.

No password is ever stored here, encrypted or not. Passwords are exchanged once for tokens and then dropped.
"""
import json
import os

from cryptography.fernet import Fernet, InvalidToken

import db

KEY_FILE = os.path.expanduser(os.environ.get("PERIODIZE_KEY_FILE", "~/.config/periodize/vault.key"))
_fernet = None


def _key():
    global _fernet
    if _fernet is None:
        if not os.path.exists(KEY_FILE):
            os.makedirs(os.path.dirname(KEY_FILE), mode=0o700, exist_ok=True)
            fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(Fernet.generate_key())
        os.chmod(KEY_FILE, 0o600)
        with open(KEY_FILE, "rb") as f:
            _fernet = Fernet(f.read().strip())
    return _fernet


def put(name, value):
    """Store a secret (any JSON value). None removes it."""
    box = db.get("vault") or {}
    if value is None:
        box.pop(name, None)
    else:
        box[name] = _key().encrypt(json.dumps(value).encode()).decode()
    db.put("vault", box)


def get(name, default=None):
    token = (db.get("vault") or {}).get(name)
    if not token:
        return default
    try:
        return json.loads(_key().decrypt(token.encode()))
    except InvalidToken:      # the key file was replaced or lost: the secret is unreadable and must be entered again
        return default


def has(name):
    return get(name) is not None


def names():
    return sorted((db.get("vault") or {}).keys())
