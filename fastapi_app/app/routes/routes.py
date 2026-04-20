from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_limiter.depends import RateLimiter
from pydantic import ValidationError
from app.config import Settings
from app.dependencies import template_context
from app.schemas import SubmissionInput
from app.security import prepare_form, validate_security
from app.services.submission_service import create_sync_submission, list_submissions
from app.services.fingerprint_service import verify_fingerprint
from app.tasks import process_submission

settings = Settings()
router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", template_context(request))


@router.get("/form-sync")
async def form_sync(request: Request):
    csrf_token, _ = prepare_form(request, "sync")
    context = template_context(request)
    context.update({"errors": [], "csrf_token": csrf_token})
    return templates.TemplateResponse("form_sync.html", context)


@router.post("/form-sync", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def submit_sync(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    website: str = Form(""),
    fingerprint: str = Form(""),
    fp_request_id: str = Form(""),
    fp_visitor_id: str = Form(""),
    csrf_token: str = Form(""),
):
    errors = validate_security(request, "sync", csrf_token, website, settings.min_submit_seconds)

    try:
        payload = SubmissionInput(first_name=first_name, last_name=last_name)
    except ValidationError:
        errors.append("First name and last name are required and must be at most 100 characters.")
        payload = None

    if errors or payload is None:
        token, _ = prepare_form(request, "sync")
        context = template_context(request)
        context.update({"errors": errors, "csrf_token": token})
        return templates.TemplateResponse("form_sync.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "unknown")[:255]
    verify_result = verify_fingerprint(
        fp_request_id=fp_request_id or None,
        fp_visitor_id=fp_visitor_id or None,
        server_api_key=settings.fpjs_server_api_key,
        base_url=settings.fpjs_server_api_base_url,
        timeout_seconds=settings.fpjs_verify_timeout_seconds,
        fail_open=settings.fpjs_fail_open,
    )
    if verify_result.is_suspect or (
        verify_result.confidence_score is not None
        and verify_result.confidence_score < settings.fpjs_confidence_threshold
    ):
        errors.append("Fingerprint verification flagged this submission.")
    if errors:
        token, _ = prepare_form(request, "sync")
        context = template_context(request)
        context.update({"errors": errors, "csrf_token": token})
        return templates.TemplateResponse("form_sync.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    create_sync_submission(
        first_name=payload.first_name,
        last_name=payload.last_name,
        client_ip=client_ip,
        user_agent=user_agent,
        fingerprint=fingerprint.strip() or None,
        fp_visitor_id=verify_result.visitor_id,
        fp_request_id=verify_result.request_id,
        fp_confidence_score=verify_result.confidence_score,
        fp_is_suspect=verify_result.is_suspect,
        fp_verification_error=verify_result.verification_error,
    )
    response = RedirectResponse(url=f"{settings.base_path}/form-sync?status=ok", status_code=status.HTTP_303_SEE_OTHER)
    return response


@router.get("/form-async")
async def form_async(request: Request):
    csrf_token, _ = prepare_form(request, "async")
    context = template_context(request)
    context.update({"errors": [], "csrf_token": csrf_token})
    return templates.TemplateResponse("form_async.html", context)


@router.post("/form-async", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def submit_async(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    website: str = Form(""),
    fingerprint: str = Form(""),
    fp_request_id: str = Form(""),
    fp_visitor_id: str = Form(""),
    csrf_token: str = Form(""),
):
    errors = validate_security(request, "async", csrf_token, website, settings.min_submit_seconds)

    try:
        payload = SubmissionInput(first_name=first_name, last_name=last_name)
    except ValidationError:
        errors.append("First name and last name are required and must be at most 100 characters.")
        payload = None

    if errors or payload is None:
        token, _ = prepare_form(request, "async")
        context = template_context(request)
        context.update({"errors": errors, "csrf_token": token})
        return templates.TemplateResponse("form_async.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "unknown")[:255]
    verify_result = verify_fingerprint(
        fp_request_id=fp_request_id or None,
        fp_visitor_id=fp_visitor_id or None,
        server_api_key=settings.fpjs_server_api_key,
        base_url=settings.fpjs_server_api_base_url,
        timeout_seconds=settings.fpjs_verify_timeout_seconds,
        fail_open=settings.fpjs_fail_open,
    )
    if verify_result.is_suspect or (
        verify_result.confidence_score is not None
        and verify_result.confidence_score < settings.fpjs_confidence_threshold
    ):
        errors.append("Fingerprint verification flagged this submission.")
    if errors:
        token, _ = prepare_form(request, "async")
        context = template_context(request)
        context.update({"errors": errors, "csrf_token": token})
        return templates.TemplateResponse("form_async.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    payload = {
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "fingerprint": fingerprint.strip() or None,
        "fp_visitor_id": verify_result.visitor_id,
        "fp_request_id": verify_result.request_id,
        "fp_confidence_score": verify_result.confidence_score,
        "fp_is_suspect": verify_result.is_suspect,
        "fp_verification_error": verify_result.verification_error,
    }
    process_submission.delay(payload)
    response = RedirectResponse(url=f"{settings.base_path}/form-async?status=queued", status_code=status.HTTP_303_SEE_OTHER)
    return response


@router.get("/submissions")
async def submissions(request: Request):
    context = template_context(request)
    context.update({"submissions": list_submissions()})
    return templates.TemplateResponse("submissions.html", context)
