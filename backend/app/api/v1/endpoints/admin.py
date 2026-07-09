from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.generated_document import GeneratedDocument
from app.models.law_search_log import LawSearchLog
from app.models.safety_quiz import SafetyQuiz
from app.models.user import User
from app.schemas.admin import (
    AdminDashboardResponse,
    DashboardDocumentItem,
    DashboardLawSearchItem,
    LawSearchLogItem,
    LawSearchLogListResponse,
)

router = APIRouter()


def _apply_date_range(stmt, column, from_date: date | None, to_date: date | None):
    if from_date is not None:
        stmt = stmt.where(column >= from_date)
    if to_date is not None:
        stmt = stmt.where(column < to_date + timedelta(days=1))
    return stmt


@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
    responses={
        401: {"description": "X-User-Id header is missing or invalid user"},
        403: {"description": "Worker role cannot access admin dashboard"},
    },
)
def get_admin_dashboard(
    site_id: int | None = Query(default=None, description="Filter dashboard metrics by site_id"),
    limit: int = Query(default=20, ge=1, le=50, description="Max latest items to return"),
    from_date: date | None = Query(default=None, description="Filter latest items from this date"),
    to_date: date | None = Query(default=None, description="Filter latest items up to this date"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminDashboardResponse:
    doc_count_stmt = select(func.count(GeneratedDocument.id))
    log_count_stmt = select(func.count(LawSearchLog.id))
    quiz_count_stmt = select(func.count(SafetyQuiz.id)).where(
        SafetyQuiz.quiz_date == date.today(),
        SafetyQuiz.is_active.is_(True),
    )

    if site_id is not None:
        doc_count_stmt = doc_count_stmt.where(GeneratedDocument.site_id == site_id)
        log_count_stmt = log_count_stmt.where(LawSearchLog.site_id == site_id)
        quiz_count_stmt = quiz_count_stmt.where(SafetyQuiz.site_id == site_id)

    total_documents = db.scalar(doc_count_stmt) or 0
    total_searches = db.scalar(log_count_stmt) or 0
    today_quiz_count = db.scalar(quiz_count_stmt) or 0

    latest_docs_stmt = select(GeneratedDocument).order_by(GeneratedDocument.created_at.desc()).limit(limit)
    latest_logs_stmt = select(LawSearchLog).order_by(LawSearchLog.created_at.desc()).limit(limit)
    if site_id is not None:
        latest_docs_stmt = latest_docs_stmt.where(GeneratedDocument.site_id == site_id)
        latest_logs_stmt = latest_logs_stmt.where(LawSearchLog.site_id == site_id)
    latest_docs_stmt = _apply_date_range(latest_docs_stmt, GeneratedDocument.created_at, from_date, to_date)
    latest_logs_stmt = _apply_date_range(latest_logs_stmt, LawSearchLog.created_at, from_date, to_date)

    latest_docs = db.scalars(latest_docs_stmt).all()
    latest_logs = db.scalars(latest_logs_stmt).all()

    return AdminDashboardResponse(
        site_id=site_id,
        total_generated_documents=total_documents,
        total_law_searches=total_searches,
        today_quiz_count=today_quiz_count,
        latest_generated_documents=[
            DashboardDocumentItem(
                id=item.id,
                site_id=item.site_id,
                document_type=item.document_type,
                title=item.title,
                created_at=item.created_at,
            )
            for item in latest_docs
        ],
        latest_law_searches=[
            DashboardLawSearchItem(
                id=item.id,
                query=item.query,
                top_k=item.top_k,
                result_count=item.result_count,
                created_at=item.created_at,
            )
            for item in latest_logs
        ],
    )


@router.get("/law-search-logs", response_model=LawSearchLogListResponse)
def list_law_search_logs(
    site_id: int | None = Query(default=None, description="Filter logs by site_id"),
    limit: int = Query(default=20, ge=1, le=50, description="Max logs to return"),
    from_date: date | None = Query(default=None, description="Filter logs from this date"),
    to_date: date | None = Query(default=None, description="Filter logs up to this date"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> LawSearchLogListResponse:
    stmt = select(LawSearchLog)
    count_stmt = select(func.count(LawSearchLog.id))

    if site_id is not None:
        stmt = stmt.where(LawSearchLog.site_id == site_id)
        count_stmt = count_stmt.where(LawSearchLog.site_id == site_id)

    stmt = _apply_date_range(stmt, LawSearchLog.created_at, from_date, to_date)
    count_stmt = _apply_date_range(count_stmt, LawSearchLog.created_at, from_date, to_date)

    items = db.scalars(stmt.order_by(LawSearchLog.created_at.desc()).limit(limit)).all()
    total = db.scalar(count_stmt) or 0

    return LawSearchLogListResponse(
        site_id=site_id,
        limit=limit,
        from_date=from_date.isoformat() if from_date else None,
        to_date=to_date.isoformat() if to_date else None,
        total=total,
        items=[
            LawSearchLogItem(
                id=item.id,
                query=item.query,
                user_id=item.user_id,
                site_id=item.site_id,
                top_k=item.top_k,
                result_count=item.result_count,
                created_at=item.created_at,
            )
            for item in items
        ],
    )
