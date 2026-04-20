import secrets
import time
from fastapi import Request


def prepare_form(request: Request, form_key: str) -> tuple[str, int]:
    csrf_token = secrets.token_urlsafe(24)
    issued_at = int(time.time())
    request.session[f"{form_key}_csrf"] = csrf_token
    request.session[f"{form_key}_issued_at"] = issued_at
    return csrf_token, issued_at


def validate_security(request: Request, form_key: str, csrf_token: str, honeypot: str, min_submit_seconds: int) -> list[str]:
    errors: list[str] = []
    if (honeypot or "").strip():
        errors.append("Submission was rejected.")

    expected_token = request.session.get(f"{form_key}_csrf")
    if not expected_token or csrf_token != expected_token:
        errors.append("Security token is invalid.")

    issued_at = request.session.get(f"{form_key}_issued_at")
    if not issued_at:
        errors.append("Submission timing is invalid.")
    else:
        elapsed = int(time.time()) - int(issued_at)
        if elapsed < min_submit_seconds:
            errors.append("Submission was too fast. Please try again.")

    return errors
