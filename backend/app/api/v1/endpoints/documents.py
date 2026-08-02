import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_embedding_service, get_law_search_service, require_premium
from app.core.database import get_db
from app.schemas.document import DocumentGenerateRequest, DocumentGenerateResponse
from app.services.document_generation_service import DocumentGenerationService
from app.services.administrative_rule_search_service import AdministrativeRuleSearchService
from app.services.embedding_service import EmbeddingService
from app.services.law_search_service import LawSearchService
from app.models.user import User

router = APIRouter()


def get_document_generation_service(
    db: Session = Depends(get_db),
    law_search_service: LawSearchService = Depends(get_law_search_service),
    _: EmbeddingService = Depends(get_embedding_service),
) -> DocumentGenerationService:
    return DocumentGenerationService(
        db=db,
        law_search_service=law_search_service,
        administrative_rule_search_service=AdministrativeRuleSearchService(db),
    )


@router.post("/generate", response_model=DocumentGenerateResponse)
def generate_document(
    payload: DocumentGenerateRequest,
    service: DocumentGenerationService = Depends(get_document_generation_service),
    current_user: User = Depends(require_premium),
) -> DocumentGenerateResponse:
    if payload.user_id is not None and payload.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot generate documents for another user")
    try:
        document = service.generate(
            site_id=payload.site_id,
            user_id=current_user.id,
            document_type=payload.document_type,
            workplace_name=payload.workplace_name,
            prompt=payload.prompt,
            work_title=payload.work_title,
            safety_keywords=payload.safety_keywords,
            equipment_tools=payload.equipment_tools,
            law_names=payload.law_names,
            kosha_categories=payload.kosha_categories,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return DocumentGenerateResponse(
        document_id=document.id,
        title=document.title,
        content=document.content,
        citations=json.loads(document.citations_json) if document.citations_json else [],
    )
