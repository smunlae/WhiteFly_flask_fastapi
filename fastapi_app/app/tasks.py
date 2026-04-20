from app.celery_app import celery_app
import app.db as db
from app.config import Settings
from app.services.submission_service import insert_submission_from_queue, insert_failed_submission_info

settings = Settings()
db.init_db(settings.database_url)


@celery_app.task(name="fastapi.process_submission")
def process_submission(payload: dict):
    try:
        insert_submission_from_queue(**payload)
    except Exception as exc:
        insert_failed_submission_info(**payload, error_msg=str(exc))
        raise
