from celery import Celery
from app.config import Config

config = Config()

celery_app = Celery(
    "flask_tasks",
    broker=config.celery_broker_url,
    backend=config.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_default_queue="flask",
)
