from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db
# from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
    )

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()



# 추후 프론트엔드와 통신할 때 CORS 설정이 필요할 수 있습니다. 아래는 예시입니다.
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",
#         "https://your-frontend.onrender.com",  # 프론트 배포 URL
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )