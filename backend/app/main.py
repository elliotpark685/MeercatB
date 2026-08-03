import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings


logger = logging.getLogger(__name__)

REQUIRED_CORS_ORIGINS = (
    "https://meerkat-safety.com",
    "https://www.meerkat-safety.com",
    "https://meercat-b.vercel.app",
    "http://localhost:5173",
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
    )

    # Keep the production frontend origins available even when CORS_ORIGINS is
    # set in the deployment environment with an incomplete value.
    allowed_origins = list(dict.fromkeys((*settings.cors_origins, *REQUIRED_CORS_ORIGINS)))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
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

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
