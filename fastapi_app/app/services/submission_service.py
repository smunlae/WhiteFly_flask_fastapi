from sqlalchemy import select
from app.db import get_db_session
from app.models import Submission


def create_sync_submission(
    first_name: str,
    last_name: str,
    client_ip: str,
    user_agent: str,
    fingerprint: str | None,
    fp_visitor_id: str | None,
    fp_request_id: str | None,
    fp_confidence_score: float | None,
    fp_is_suspect: bool,
    fp_verification_error: str | None,
):
    session = get_db_session()
    try:
        submission = Submission(
            first_name=first_name,
            last_name=last_name,
            framework="fastapi",
            source_type="sync",
            status="completed",
            client_ip=client_ip,
            user_agent=user_agent,
            fingerprint=fingerprint,
            honeypot_triggered=False,
            fp_visitor_id=fp_visitor_id,
            fp_request_id=fp_request_id,
            fp_confidence_score=fp_confidence_score,
            fp_is_suspect=fp_is_suspect,
            fp_verification_error=fp_verification_error,
        )
        session.add(submission)
        session.commit()
    finally:
        session.close()


def insert_submission_from_queue(
    first_name: str,
    last_name: str,
    client_ip: str,
    user_agent: str,
    fingerprint: str | None,
    fp_visitor_id: str | None,
    fp_request_id: str | None,
    fp_confidence_score: float | None,
    fp_is_suspect: bool,
    fp_verification_error: str | None,
):
    session = get_db_session()
    try:
        submission = Submission(
            first_name=first_name,
            last_name=last_name,
            framework="fastapi",
            source_type="async",
            status="processed",
            client_ip=client_ip,
            user_agent=user_agent,
            fingerprint=fingerprint,
            honeypot_triggered=False,
            fp_visitor_id=fp_visitor_id,
            fp_request_id=fp_request_id,
            fp_confidence_score=fp_confidence_score,
            fp_is_suspect=fp_is_suspect,
            fp_verification_error=fp_verification_error,
        )
        session.add(submission)
        session.commit()
    finally:
        session.close()


def insert_failed_submission_info(
    first_name: str,
    last_name: str,
    client_ip: str,
    user_agent: str,
    fingerprint: str | None,
    fp_visitor_id: str | None,
    fp_request_id: str | None,
    fp_confidence_score: float | None,
    fp_is_suspect: bool,
    fp_verification_error: str | None,
    error_msg: str,
):
    session = get_db_session()
    try:
        submission = Submission(
            first_name=first_name,
            last_name=last_name,
            framework="fastapi",
            source_type="async",
            status="failed",
            client_ip=client_ip,
            user_agent=user_agent,
            fingerprint=fingerprint,
            honeypot_triggered=False,
            fp_visitor_id=fp_visitor_id,
            fp_request_id=fp_request_id,
            fp_confidence_score=fp_confidence_score,
            fp_is_suspect=fp_is_suspect,
            fp_verification_error=fp_verification_error,
            processing_error=error_msg,
        )
        session.add(submission)
        session.commit()
        return submission.id
    finally:
        session.close()


def list_submissions(limit: int = 100):
    session = get_db_session()
    try:
        stmt = select(Submission).order_by(Submission.created_at.desc()).limit(limit)
        return list(session.scalars(stmt).all())
    finally:
        session.close()
