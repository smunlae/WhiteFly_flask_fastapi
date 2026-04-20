import time
import secrets
from flask import session


def prepare_form(form_key: str) -> int:
    issued_at = int(time.time())
    session[f"{form_key}_issued_at"] = issued_at
    session[f"{form_key}_nonce"] = secrets.token_urlsafe(16)
    return issued_at


def is_too_fast(form_key: str, min_submit_seconds: int) -> bool:
    issued_at = session.get(f"{form_key}_issued_at")
    if not issued_at:
        return True
    elapsed = int(time.time()) - int(issued_at)
    return elapsed < min_submit_seconds


def honeypot_triggered(honeypot_value: str | None) -> bool:
    return bool((honeypot_value or "").strip())
