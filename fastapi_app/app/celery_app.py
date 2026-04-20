from celery import Celery
from app.config import Settings

settings = Settings()

celery_app = Celery(
    "fastapi_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_default_queue="fastapi",
)
