import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_response_size(request, call_next):
        response = await call_next(request)
        content_length = response.headers.get("content-length")
        logger.info(
            "api_response path=%s status=%s content_length=%s",
            request.url.path,
            response.status_code,
            content_length or "unknown",
        )
        return response

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
