from fastapi import Request
from app.config import Settings

settings = Settings()


def template_context(request: Request) -> dict:
    return {
        "request": request,
        "base_path": settings.base_path,
        "fpjs_public_key": settings.fpjs_public_key,
    }
