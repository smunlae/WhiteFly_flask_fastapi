import os


class Config:
    secret_key = os.getenv("SECRET_KEY", "vefdvohafviojnka1623561235")
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@postgres:5432/whitefly")
    celery_broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    celery_result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
    limiter_storage_uri = os.getenv("LIMITER_STORAGE_URI", "redis://redis:6379/2")
    min_submit_seconds = int(os.getenv("MIN_SUBMIT_SECONDS", "2"))
    max_name_length = int(os.getenv("MAX_NAME_LENGTH", "100"))
    base_path = os.getenv("BASE_PATH", "/flask")
    fpjs_public_key = os.getenv("FPJS_PUBLIC_KEY")
    fpjs_server_api_key = os.getenv("FPJS_SERVER_API_KEY")
    fpjs_confidence_threshold = float(os.getenv("FPJS_CONFIDENCE_THRESHOLD", 0.5))
    fpjs_server_api_base_url = os.getenv("FPJS_SERVER_API_BASE_URL", "https://api.fpjs.io")
    fpjs_verify_timeout_seconds = float(os.getenv("FPJS_VERIFY_TIMEOUT_SECONDS", "3"))
    fpjs_fail_open = os.getenv("FPJS_FAIL_OPEN", "true").lower() == "true"
