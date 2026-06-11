import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_embedding_service, get_law_search_service
from app.core.database import get_db
from app.schemas.document import DocumentGenerateRequest, DocumentGenerateResponse
from app.services.document_generation_service import DocumentGenerationService
from app.services.embedding_service import EmbeddingService
from app.services.law_search_service import LawSearchService

router = APIRouter()


def get_document_generation_service(
    db: Session = Depends(get_db),
    law_search_service: LawSearchService = Depends(get_law_search_service),
    _: EmbeddingService = Depends(get_embedding_service),
) -> DocumentGenerationService:
    return DocumentGenerationService(db=db, law_search_service=law_search_service)


@router.post("/generate", response_model=DocumentGenerateResponse)
def generate_document(
    payload: DocumentGenerateRequest,
    service: DocumentGenerationService = Depends(get_document_generation_service),
) -> DocumentGenerateResponse:
    try:
        document = service.generate(
            site_id=payload.site_id,
            user_id=payload.user_id,
            document_type=payload.document_type,
            prompt=payload.prompt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return DocumentGenerateResponse(
        document_id=document.id,
        title=document.title,
        content=document.content,
        citations=json.loads(document.citations_json) if document.citations_json else [],
        generated_text=document.content,
        references=json.loads(document.references_json or document.citations_json) if (document.references_json or document.citations_json) else [],
    )
