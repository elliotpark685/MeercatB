from pathlib import Path
import uuid

from app.services.embedding_service import EmbeddingService
from app.services.law_ingestion_service import LawIngestionService


class _FakeDB:
    def commit(self):
        return None


class _FakeRepo:
    def __init__(self):
        self.article_rows = []
        self.document = type("Doc", (), {"id": 1})()

    def create_law_document(self, **kwargs):
        _ = kwargs
        return self.document

    def create_law_article(self, **kwargs):
        self.article_rows.append(kwargs)
        return type("Article", (), {"id": len(self.article_rows)})()

    def create_law_embedding(self, **kwargs):
        _ = kwargs
        return None


def test_ingestion_uses_document_effective_date_as_default():
    pdf_like = (
        "[PAGE:1]\n"
        "산업안전보건기준에 관한 규칙\n"
        "제1조(목적)\n"
        "이 규칙은 산업재해를 예방하기 위한 기준을 정한다.\n"
    )
    tmp_dir = Path("tests/.tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    txt_path = tmp_dir / f"law_{uuid.uuid4().hex}.txt"
    txt_path.write_text(pdf_like, encoding="utf-8")

    service = LawIngestionService(db=_FakeDB(), embedding_service=EmbeddingService())
    service.repo = _FakeRepo()
    summary = service.ingest_file(
        file_path=str(txt_path),
        law_name="산업안전보건기준에 관한 규칙",
        effective_date="2026-03-02",
    )

    assert summary["effective_count"] == 1
    assert summary["scheduled_count"] == 0
    assert summary["unknown_count"] == 0
    assert service.repo.article_rows[0]["status"] == "effective"
    assert service.repo.article_rows[0]["effective_date"].isoformat() == "2026-03-02"
