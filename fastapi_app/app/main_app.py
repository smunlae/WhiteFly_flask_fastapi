import redis.asyncio as redis
import app.db as db
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from app.config import Settings
from app.models import Base
from app.routes.routes import router


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title="WhiteFly FastAPI Service")
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax", https_only=False)

    db.init_db(settings.database_url)
    Base.metadata.create_all(bind=db.engine)
    db.ensure_submission_fp_columns()

    app.include_router(router)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.on_event("startup")
    async def startup():
        redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_client)

    return app
