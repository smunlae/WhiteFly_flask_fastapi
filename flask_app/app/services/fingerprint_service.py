import json
import logging
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)


@dataclass
class FingerprintVerificationResult:
    visitor_id: str | None
    request_id: str | None
    confidence_score: float | None
    is_suspect: bool
    verification_error: str | None


def _get_in(source: dict, path: tuple[str, ...]):
    current = source
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_visitor_id(payload: dict) -> str | None:
    if isinstance(payload.get("visitorId"), str):
        return payload["visitorId"]
    value = _get_in(payload, ("products", "identification", "data", "visitorId"))
    return value if isinstance(value, str) else None


def _extract_confidence(payload: dict) -> float | None:
    return _to_float(
        _get_in(payload, ("confidence", "score"))
        or _get_in(payload, ("products", "identification", "data", "confidence", "score"))
    )


def _extract_suspect(payload: dict) -> bool:
    if isinstance(payload.get("suspect"), bool):
        return payload["suspect"]
    value = _get_in(payload, ("products", "suspectScore", "data", "result"))
    if isinstance(value, bool):
        return value
    return False


def verify_fingerprint(
    fp_request_id: str | None,
    fp_visitor_id: str | None,
    server_api_key: str | None,
    base_url: str,
    timeout_seconds: float,
    fail_open: bool,
) -> FingerprintVerificationResult:
    if not fp_request_id:
        return FingerprintVerificationResult(
            visitor_id=fp_visitor_id,
            request_id=None,
            confidence_score=None,
            is_suspect=not fail_open,
            verification_error="missing_request_id",
        )
    if not server_api_key:
        return FingerprintVerificationResult(
            visitor_id=fp_visitor_id,
            request_id=fp_request_id,
            confidence_score=None,
            is_suspect=not fail_open,
            verification_error="missing_server_api_key",
        )

    url = f"{base_url.rstrip('/')}/events/{quote(fp_request_id)}"
    request = Request(url=url, method="GET", headers={"Auth-API-Key": server_api_key})

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        logger.warning("Fingerprint verification HTTP error: %s", exc.code)
        return FingerprintVerificationResult(
            visitor_id=fp_visitor_id,
            request_id=fp_request_id,
            confidence_score=None,
            is_suspect=not fail_open,
            verification_error=f"http_{exc.code}",
        )
    except (URLError, TimeoutError, ValueError) as exc:
        logger.warning("Fingerprint verification transport error: %s", exc)
        return FingerprintVerificationResult(
            visitor_id=fp_visitor_id,
            request_id=fp_request_id,
            confidence_score=None,
            is_suspect=not fail_open,
            verification_error="verification_unavailable",
        )

    api_visitor_id = _extract_visitor_id(payload)
    if fp_visitor_id and api_visitor_id and fp_visitor_id != api_visitor_id:
        return FingerprintVerificationResult(
            visitor_id=api_visitor_id,
            request_id=fp_request_id,
            confidence_score=_extract_confidence(payload),
            is_suspect=True,
            verification_error="visitor_id_mismatch",
        )

    return FingerprintVerificationResult(
        visitor_id=api_visitor_id or fp_visitor_id,
        request_id=fp_request_id,
        confidence_score=_extract_confidence(payload),
        is_suspect=_extract_suspect(payload),
        verification_error=None,
    )
