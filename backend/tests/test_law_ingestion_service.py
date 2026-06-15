from pathlib import Path
import uuid

from ingestion.ingest_laws import TargetLaw, ingest_target_law, law_api_payload_to_source_document
from app.services.embedding_service import EmbeddingService
from app.services.law_ingestion_service import LawIngestionService, LawSourceArticle, LawSourceDocument


class _FakeDB:
    def __init__(self):
        self.commit_count = 0

    def commit(self):
        self.commit_count += 1
        return None


class _FakeRepo:
    def __init__(self):
        self.document_rows = []
        self.article_rows = []
        self.chunk_rows = []
        self.embedding_rows = []
        self.existing_by_hash = {}

    def create_law_document(self, **kwargs):
        self.document_rows.append(kwargs)
        document = type("Doc", (), {"id": len(self.document_rows), **kwargs})()
        if kwargs.get("version_hash"):
            self.existing_by_hash[kwargs["version_hash"]] = document
        return document

    def create_law_article(self, **kwargs):
        self.article_rows.append(kwargs)
        return type("Article", (), {"id": len(self.article_rows)})()

    def create_law_chunk(self, **kwargs):
        self.chunk_rows.append(kwargs)
        return type("Chunk", (), {"id": len(self.chunk_rows)})()

    def create_law_embedding(self, **kwargs):
        self.embedding_rows.append(kwargs)
        return None

    def get_law_document_by_version_hash(self, version_hash: str):
        return self.existing_by_hash.get(version_hash)

    def deactivate_other_documents(self, law_name: str, keep_document_id: int):
        pass


def test_ingestion_uses_document_effective_date_as_default():
    law_name = "산업안전보건기준에 관한 규칙"
    pdf_like = (
        "[PAGE:1]\n"
        f"{law_name}\n"
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
        law_name=law_name,
        effective_date="2026-03-02",
    )

    assert summary["effective_count"] == 1
    assert summary["scheduled_count"] == 0
    assert summary["unknown_count"] == 0
    assert service.repo.article_rows[0]["status"] == "effective"
    assert service.repo.article_rows[0]["effective_date"].isoformat() == "2026-03-02"
    assert service.repo.document_rows[0]["law_name"] == law_name
    assert service.repo.chunk_rows


def test_ingestion_skips_duplicate_version_hash():
    service = LawIngestionService(db=_FakeDB(), embedding_service=EmbeddingService())
    service.repo = _FakeRepo()
    source = LawSourceDocument(
        law_name="중대재해 처벌 등에 관한 법률",
        law_short_name="중대재해처벌법",
        effective_date="2024-01-27",
        amendment_date="2023-12-26",
        articles=[
            LawSourceArticle(
                article_no="제4조",
                article_title="사업주와 경영책임자등의 안전 및 보건 확보의무",
                article_text="안전보건관리체계를 구축하고 이행하여야 한다.",
            )
        ],
    )

    first = service.ingest_source_document(source)
    second = service.ingest_source_document(source)

    assert first["status"] == "ingested"
    assert second["status"] == "skipped_duplicate"
    assert len(service.repo.document_rows) == 1
    assert len(service.repo.article_rows) == 1


def test_law_api_payload_to_source_document_extracts_metadata_and_articles():
    payload = {
        "법령": {
            "기본정보": {
                "법령명_한글": "건설기술 진흥법",
                "법종구분": {"content": "법률"},
                "공포번호": "12345",
                "시행일자": "20240101",
                "공포일자": "20231212",
            },
            "조문": {
                "조문단위": [
                    {
                        "조문번호": "62",
                        "조문여부": "조문",
                        "조문제목": "건설공사의 안전관리",
                        "조문내용": "제62조(건설공사의 안전관리) 건설공사의 참여자는 안전관리계획을 수립하여야 한다.",
                    }
                ]
            },
        }
    }

    source = law_api_payload_to_source_document(
        payload=payload,
        target=TargetLaw("건설기술 진흥법", "건설기술진흥법"),
        source_url="https://example.test",
    )

    assert source.law_name == "건설기술 진흥법"
    assert source.law_short_name == "건설기술진흥법"
    assert source.law_type == "법률"
    assert source.law_no == "12345"
    assert source.effective_date == "20240101"
    assert source.amendment_date == "20231212"
    assert source.articles is None
    assert "제62조(건설공사의 안전관리)" in source.raw_text
    assert "건설공사의 참여자는 안전관리계획을 수립하여야 한다." in source.raw_text


def test_target_law_ingestion_continues_with_local_fallback_on_api_error():
    tmp_dir = Path("tests/.tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    fallback_file = tmp_dir / f"건설산업기본법_{uuid.uuid4().hex}.txt"
    fallback_file.write_text(
        "건설산업기본법\n"
        "건설산업기본법\n"
        "제1조(목적)\n"
        "이 법은 건설산업의 기본 사항을 정한다.\n",
        encoding="utf-8",
    )

    class _FailingApiClient:
        def fetch_law(self, target):
            raise RuntimeError(f"api failed for {target.law_name}")

    service = LawIngestionService(db=_FakeDB(), embedding_service=EmbeddingService())
    service.repo = _FakeRepo()
    result = ingest_target_law(
        service=service,
        target=TargetLaw("건설산업기본법", "건산법"),
        api_client=_FailingApiClient(),
        fallback_dir=str(tmp_dir),
        prefer_local=False,
    )

    assert result["status"] == "ingested"
    assert result["law_name"] == "건설산업기본법"
    assert "fallback_reason" in result
    assert service.repo.article_rows[0]["article_no"] == "제1조"
