"""
Email-verification codes for self-service account registration.

The account is created immediately, but the registration flow does NOT return
an access token directly: a random 6-digit code is emailed to the address the
person typed, and only entering that code on the next step lets them in.

Codes are held in-process (per server, keyed by lowercased email) with a short
TTL. This is a lightweight, dependency-free store - perfectly fine for the
module's standalone/sandbox deployment, where a persistent verified-flag on the
platform-owned users table is out of scope.
"""
import random
import threading
import time

_TTL_SECONDS = 10 * 60
_MAX_ATTEMPTS = 5

_lock = threading.Lock()
# mailto-lower -> {"code": "000000", "expires_at": epoch, "attempts": int}
_pending: dict[str, dict] = {}


def _now() -> float:
    return time.time()


def _purge_locked() -> None:
    for email in [e for e, v in _pending.items() if v["expires_at"] < _now()]:
        del _pending[email]


def issue_code(email: str) -> str:
    """Generate a fresh 6-digit code for the email (replacing any old one)."""
    code = f"{random.randint(0, 999999):06d}"
    with _lock:
        _purge_locked()
        _pending[email.lower()] = {"code": code, "expires_at": _now() + _TTL_SECONDS, "attempts": 0}
    return code


def get_code(email: str) -> str | None:
    """Return the currently active code for an email (used by tests)."""
    with _lock:
        entry = _pending.get(email.lower())
        if entry is None or entry["expires_at"] < _now():
            return None
        return entry["code"]


def verify_code(email: str, code: str) -> bool:
    """Validate a submitted code. Consumes it on success; limits brute force."""
    normalized = email.lower()
    with _lock:
        entry = _pending.get(normalized)
        if entry is None or entry["expires_at"] < _now():
            return False
        if entry["attempts"] >= _MAX_ATTEMPTS:
            return False
        if entry["code"] != code:
            entry["attempts"] += 1
            return False
        del _pending[normalized]
        return True
