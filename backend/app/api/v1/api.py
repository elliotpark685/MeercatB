from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, documents, health, kosha, laws, quizzes, safety_standards

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(laws.router, prefix="/laws", tags=["laws"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(safety_standards.router, prefix="/safety-standards", tags=["safety-standards"])
api_router.include_router(kosha.router, prefix="/kosha", tags=["kosha"])
