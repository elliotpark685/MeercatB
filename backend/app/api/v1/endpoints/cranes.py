from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_db
from app.crane.supabase_mapping import TRT60SupabaseMapper
from app.crane.trt60_parser import TerexTRT60Parser
from app.crane.trt60_reference import REFERENCE_FILE_HASH_SHA256, load_golden_dataset
from app.crane.engineering_review import EngineeringReviewInput, MainBoomEngineeringReviewService
from app.crane.postgres_repository import PostgresTRT60Repository
from app.core.config import settings

router = APIRouter()
PDF_MEDIA_TYPES = {"application/pdf", "application/x-pdf"}
UPLOAD_READ_CHUNK_BYTES = 1024 * 1024


async def _read_pdf_upload(file: UploadFile) -> bytes:
    """Read a bounded PDF upload and reject mismatched form metadata/content."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF filename is required")
    if file.content_type not in PDF_MEDIA_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="PDF content type is required")

    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(UPLOAD_READ_CHUNK_BYTES):
        total += len(chunk)
        if total > settings.crane_pdf_max_upload_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="PDF upload exceeds the configured size limit")
        chunks.append(chunk)
    payload = b"".join(chunks)
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded PDF is empty")
    if not payload.startswith(b"%PDF-"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Upload content is not a PDF")
    return payload


def _parse_reference_trt60(payload: bytes, source_name: str):
    parser = TerexTRT60Parser()
    data = parser.parse_pdf_bytes(payload, source_name=source_name)
    if data.file_hash_sha256 != REFERENCE_FILE_HASH_SHA256:
        raise ValueError("TRT60 Engineering Review supports only the Golden-validated reference PDF revision")
    errors = parser.verify(data, load_golden_dataset())
    if errors:
        raise ValueError("TRT60 Golden/Critical validation failed: " + "; ".join(errors))
    return data


@router.post("/trt60/parse")
async def parse_trt60_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        payload = await _read_pdf_upload(file)
        data = await run_in_threadpool(TerexTRT60Parser().parse_pdf_bytes, payload, source_name=file.filename)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    response = {"parser_result": data.model_dump(mode="json"), "supabase_rows": TRT60SupabaseMapper.to_rows(data), "persisted": False}
    if settings.persist_crane_parser_results and settings.database_url:
        response["persistence"] = PostgresTRT60Repository(db).save(data, original_filename=file.filename)
        response["persisted"] = True
    return response


@router.post(
    "/trt60/review",
    description="Multipart form: `file` is a PDF and `review` is a JSON-encoded EngineeringReviewInput.",
)
async def review_trt60_pdf(file: UploadFile = File(...), review: str = Form(...)):
    """Run the Main Boom preliminary review without persistence or approval."""
    try:
        request = EngineeringReviewInput.model_validate_json(review)
        payload = await _read_pdf_upload(file)
        data = await run_in_threadpool(_parse_reference_trt60, payload, file.filename)
        result = MainBoomEngineeringReviewService().review(data, request)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return {
        "review_result": result.model_dump(mode="json"),
        "parser_metadata": {
            "file_hash_sha256": data.file_hash_sha256,
            "parser_profile": data.parser_profile,
            "parser_version": data.parser_version,
            "canonical_content_hash": data.canonical_content_hash,
            "parser_verification_status": data.parser_verification_status,
        },
        "persisted": False,
        "approval": "NOT_GRANTED",
    }
