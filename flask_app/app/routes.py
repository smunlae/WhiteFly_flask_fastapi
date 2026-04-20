from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from .extensions import limiter
from app.security import honeypot_triggered, is_too_fast, prepare_form
from app.tasks import process_submission
from app.validators import ValidationError, validate_names
from app.services.fingerprint_service import verify_fingerprint
from app.services.submission_service import create_sync_submission, list_submissions

bp = Blueprint("web", __name__)


def _base_context():
    return {
        "base_path": current_app.config["BASE_PATH"],
        "fpjs_public_key": current_app.config.get("FPJS_PUBLIC_KEY"),
    }


def _client_ip() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _user_agent() -> str:
    return request.headers.get("User-Agent", "unknown")[:255]


@bp.get("/")
def home():
    return render_template("home.html", **_base_context())


@bp.get("/form-sync")
def form_sync():
    prepare_form("sync")
    return render_template("form_sync.html", errors=[], **_base_context())


@bp.post("/form-sync")
@limiter.limit("10 per minute")
def submit_sync():
    errors: list[str] = []
    fp_request_id = (request.form.get("fp_request_id") or "").strip() or None
    fp_visitor_id = (request.form.get("fp_visitor_id") or "").strip() or None
    if honeypot_triggered(request.form.get("website")):
        errors.append("Submission was rejected.")
    if is_too_fast("sync", current_app.config["MIN_SUBMIT_SECONDS"]):
        errors.append("Submission was too fast. Please try again.")

    try:
        validated = validate_names(
            request.form.get("first_name", ""),
            request.form.get("last_name", ""),
            current_app.config["MAX_NAME_LENGTH"],
        )
    except ValidationError as exc:
        errors.extend(exc.messages)
        validated = None

    verify_result = verify_fingerprint(
        fp_request_id=fp_request_id,
        fp_visitor_id=fp_visitor_id,
        server_api_key=current_app.config.get("FPJS_SERVER_API_KEY"),
        base_url=current_app.config["FPJS_SERVER_API_BASE_URL"],
        timeout_seconds=current_app.config["FPJS_VERIFY_TIMEOUT_SECONDS"],
        fail_open=current_app.config["FPJS_FAIL_OPEN"],
    )
    if verify_result.is_suspect or (
        verify_result.confidence_score is not None
        and verify_result.confidence_score < current_app.config["FPJS_CONFIDENCE_THRESHOLD"]
    ):
        errors.append("Fingerprint verification flagged this submission.")

    if errors or validated is None:
        return render_template("form_sync.html", errors=errors, **_base_context()), 400

    create_sync_submission(
        first_name=validated.first_name,
        last_name=validated.last_name,
        client_ip=_client_ip(),
        user_agent=_user_agent(),
        fingerprint=(request.form.get("fingerprint") or "").strip() or None,
        fp_visitor_id=verify_result.visitor_id,
        fp_request_id=verify_result.request_id,
        fp_confidence_score=verify_result.confidence_score,
        fp_is_suspect=verify_result.is_suspect,
        fp_verification_error=verify_result.verification_error,
    )
    flash("Synchronous submission completed.", "success")
    return redirect(url_for("web.form_sync"))


@bp.get("/form-async")
def form_async():
    prepare_form("async")
    return render_template("form_async.html", errors=[], **_base_context())


@bp.post("/form-async")
@limiter.limit("10 per minute")
def submit_async():
    errors: list[str] = []
    fp_request_id = (request.form.get("fp_request_id") or "").strip() or None
    fp_visitor_id = (request.form.get("fp_visitor_id") or "").strip() or None
    if honeypot_triggered(request.form.get("website")):
        errors.append("Submission was rejected.")
    if is_too_fast("async", current_app.config["MIN_SUBMIT_SECONDS"]):
        errors.append("Submission was too fast. Please try again.")

    try:
        validated = validate_names(
            request.form.get("first_name", ""),
            request.form.get("last_name", ""),
            current_app.config["MAX_NAME_LENGTH"],
        )
    except ValidationError as exc:
        errors.extend(exc.messages)
        validated = None

    verify_result = verify_fingerprint(
        fp_request_id=fp_request_id,
        fp_visitor_id=fp_visitor_id,
        server_api_key=current_app.config.get("FPJS_SERVER_API_KEY"),
        base_url=current_app.config["FPJS_SERVER_API_BASE_URL"],
        timeout_seconds=current_app.config["FPJS_VERIFY_TIMEOUT_SECONDS"],
        fail_open=current_app.config["FPJS_FAIL_OPEN"],
    )
    if verify_result.is_suspect or (
        verify_result.confidence_score is not None
        and verify_result.confidence_score < current_app.config["FPJS_CONFIDENCE_THRESHOLD"]
    ):
        errors.append("Fingerprint verification flagged this submission.")

    if errors or validated is None:
        return render_template("form_async.html", errors=errors, **_base_context()), 400

    payload = {
        "first_name" : validated.first_name,
        "last_name": validated.last_name,
        "client_ip": _client_ip(),
        "user_agent" : _user_agent(),
        "fingerprint" : (request.form.get("fingerprint") or "").strip() or None,
        "fp_visitor_id": verify_result.visitor_id,
        "fp_request_id": verify_result.request_id,
        "fp_confidence_score": verify_result.confidence_score,
        "fp_is_suspect": verify_result.is_suspect,
        "fp_verification_error": verify_result.verification_error,
    }
    process_submission.delay(payload)
    flash("Asynchronous submission queued. Processing will finish in the background.", "success")
    return redirect(url_for("web.form_async"))


@bp.get("/submissions")
def submissions():
    rows = list_submissions()
    return render_template("submissions.html", submissions=rows, **_base_context())
