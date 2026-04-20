from app.celery_app import celery_app
import app.db as db
from .config import Config
from app.services.submission_service import insert_failed_submission_info, insert_submission_from_queue

config = Config()
db.init_db(config.database_url)


@celery_app.task(name="flask.process_submission")
def process_submission(payload: dict):
    try:
        insert_submission_from_queue(**payload)
    except Exception as exc:
        insert_failed_submission_info(**payload, error_msg=str(exc))
        raise
