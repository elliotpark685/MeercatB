"""안전기준 검색 관련 테스트.

- SafetyStandardSearchService 기본 동작
- source_type 필터 동작
- 기존 5개 법령 검색 API가 깨지지 않는지 회귀 검증
- AdmrulApiClient mock 기반 테스트
"""
from __future__ import annotations

import io
import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

# 모든 ORM 모델을 먼저 import하여 SQLAlchemy mapper가 관계를 완전히 구성하도록 함
import app.models.user  # noqa: F401
import app.models.site  # noqa: F401
import app.models.generated_document  # noqa: F401
import app.models.safety_quiz  # noqa: F401
import app.models.law_search_log  # noqa: F401

from app.models.law_article import LawArticle
from app.models.law_chunk import LawChunk
from app.models.law_document import LawDocument
from app.repositories.law_repository import SAFETY_STANDARD_CATEGORY
from app.schemas.safety_standard import SafetyStandardSearchResponse
from app.services.safety_standard_search_service import SafetyStandardSearchService


# ── 테스트 픽스처 ─────────────────────────────────────────────────────────────


def _make_doc(
    doc_id: int = 1,
    law_name: str = "산업안전보건기준에 관한 규칙",
    source_category: str = "safety_standard",
    source_type: str = "rule",
    provider: str = "law.go.kr",
) -> LawDocument:
    return LawDocument(
        id=doc_id,
        title=law_name,
        law_name=law_name,
        law_type="시행규칙",
        jurisdiction="KR",
        is_active=True,
        source_category=source_category,
        source_type=source_type,
        provider=provider,
    )


def _make_article(
    article_id: int = 10,
    doc_id: int = 1,
    article_no: str = "제42조",
    article_title: str = "작업발판",
    text: str = "이동식비계 작업발판의 폭은 40cm 이상이어야 한다.",
) -> LawArticle:
    return LawArticle(
        id=article_id,
        law_document_id=doc_id,
        article_number=article_no,
        article_no=article_no,
        article_title=article_title,
        article_text=text,
        full_text=text,
        content=text,
        status="effective",
        version_group_key=f"{doc_id}::{article_no}",
    )


def _make_chunk(
    chunk_id: int = 100,
    article_id: int = 10,
    text: str = "이동식비계 작업발판의 폭은 40cm 이상이어야 한다.",
) -> LawChunk:
    return LawChunk(
        id=chunk_id,
        law_article_id=article_id,
        chunk_level="article",
        chunk_no="1",
        chunk_text=text,
        token_count=len(text.split()),
    )


class _StubRepo:
    """SafetyStandardSearchService 의존성 stub."""

    def __init__(
        self,
        chunk_rows: list | None = None,
        article_rows: list | None = None,
    ) -> None:
        self._chunk_rows = chunk_rows or []
        self._article_rows = article_rows or []

    def search_chunks_by_keyword_for_category(self, **kwargs):
        return [(row[0], row[1], row[2], None) for row in self._chunk_rows]

    def list_chunks_for_category(self, **kwargs):
        return [(row[0], row[1], row[2], None) for row in self._chunk_rows]

    def search_by_keyword_for_category(self, **kwargs):
        return self._article_rows


# ── 검색 서비스 테스트 ──────────────────────────────────────────────────────────


def test_safety_search_returns_response():
    """검색 결과가 SafetyStandardSearchResponse 형태로 반환된다."""
    doc = _make_doc()
    article = _make_article()
    chunk = _make_chunk()

    service = SafetyStandardSearchService(db=None)  # type: ignore[arg-type]
    service.repo = _StubRepo(chunk_rows=[(chunk, article, doc)])

    resp = service.search("이동식비계 작업발판", top_k=5)
    assert isinstance(resp, SafetyStandardSearchResponse)
    assert resp.query == "이동식비계 작업발판"
    assert len(resp.results) == 1
    result = resp.results[0]
    assert result.source_type == "rule"
    assert result.source_name == "산업안전보건기준에 관한 규칙"
    assert result.provider == "law.go.kr"
    assert "이동식비계" in result.content


def test_safety_search_empty_when_no_data():
    """DB에 데이터 없으면 빈 결과 반환."""
    service = SafetyStandardSearchService(db=None)  # type: ignore[arg-type]
    service.repo = _StubRepo()

    resp = service.search("가설공사 비계", top_k=5)
    assert resp.results == []


def test_safety_search_source_type_in_result():
    """guideline source_type 문서 결과 포함."""
    doc = _make_doc(
        doc_id=2,
        law_name="가설공사 표준안전 작업지침",
        source_type="moel_standard_safety_guideline",
    )
    article = _make_article(
        article_id=20,
        doc_id=2,
        article_no="제3조",
        article_title="이동식비계",
        text="이동식비계 설치 시 바퀴 잠금장치를 사용하여야 한다.",
    )
    chunk = _make_chunk(chunk_id=200, article_id=20, text=article.article_text or "")

    service = SafetyStandardSearchService(db=None)  # type: ignore[arg-type]
    service.repo = _StubRepo(chunk_rows=[(chunk, article, doc)])

    resp = service.search("이동식비계 잠금장치")
    assert resp.results[0].source_type == "moel_standard_safety_guideline"
    assert "가설공사" in resp.results[0].source_name


def test_safety_search_source_type_filter():
    """source_types 필터를 넘기면 repo에 전달된다."""
    service = SafetyStandardSearchService(db=None)  # type: ignore[arg-type]
    stub = _StubRepo()
    service.repo = stub

    received_types: list = []

    def _capture_keyword(**kwargs):
        received_types.extend(kwargs.get("source_types") or [])
        return []

    stub.search_chunks_by_keyword_for_category = _capture_keyword  # type: ignore
    stub.list_chunks_for_category = lambda **kw: []  # type: ignore

    service.search("비계", source_types=["rule"])
    assert "rule" in received_types


def test_safety_search_fallback_to_article_search():
    """청크가 없으면 article 레벨 fallback 검색이 실행된다."""
    doc = _make_doc()
    article = _make_article()

    service = SafetyStandardSearchService(db=None)  # type: ignore[arg-type]
    # 청크는 없고 article만 있는 stub
    service.repo = _StubRepo(chunk_rows=[], article_rows=[(article, doc)])

    resp = service.search("작업발판")
    assert len(resp.results) == 1


# ── AdmrulApiClient mock 테스트 ───────────────────────────────────────────────


def _make_urlopen_mock(payload: dict):
    """urlopen context manager mock 헬퍼."""
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    class _FakeResp:
        def read(self):
            return raw

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    return MagicMock(return_value=_FakeResp())


def test_admrul_api_client_search_list_mock():
    """외부 API 미호출, mock으로만 동작 검증."""
    from app.utils.admrul_api_client import AdmrulApiClient

    mock_payload = {
        "LawSearch": {
            "law": [
                {
                    "법령ID": "123456",
                    "법령명": "가설공사 표준안전 작업지침",
                    "시행일자": "20200101",
                }
            ]
        }
    }

    client = AdmrulApiClient(oc="test-oc")
    with patch("app.utils.admrul_api_client.urlopen", _make_urlopen_mock(mock_payload)):
        items = client.search_list("표준안전 작업지침")

    assert len(items) == 1
    assert items[0].name == "가설공사 표준안전 작업지침"
    assert items[0].id == "123456"


def test_admrul_api_client_get_document_mock():
    """본문 조회 mock 테스트."""
    from app.utils.admrul_api_client import AdmrulApiClient

    mock_payload = {
        "법령": {
            "기본정보": {
                "법령명칭": "가설공사 표준안전 작업지침",
                "시행일자": "20200101",
            },
            "조문": {
                "조문단위": {
                    "조문번호": "제1조",
                    "조문제목": "목적",
                    "조문내용": "이 지침은 가설공사 작업자의 안전을 위한 기준을 정한다.",
                }
            },
        }
    }

    client = AdmrulApiClient(oc="test-oc")
    with patch("app.utils.admrul_api_client.urlopen", _make_urlopen_mock(mock_payload)):
        doc = client.get_document("123456")

    assert doc is not None
    assert doc.name == "가설공사 표준안전 작업지침"
    assert len(doc.articles) == 1
    assert doc.articles[0].article_no == "제1조"


def test_admrul_api_client_handles_request_failure():
    """API 호출 실패 시 None/빈 리스트 반환."""
    from app.utils.admrul_api_client import AdmrulApiClient

    client = AdmrulApiClient(oc="test-oc")
    with patch("app.utils.admrul_api_client.urlopen", side_effect=OSError("network error")):
        items = client.search_list("표준안전 작업지침")
        doc = client.get_document("999")

    assert items == []
    assert doc is None


# ── 기존 법령 검색 API 회귀 테스트 ───────────────────────────────────────────────


def test_existing_law_search_not_broken():
    """기존 LawSearchService가 여전히 동작한다 (회귀)."""
    from app.models.law_article import LawArticle
    from app.models.law_document import LawDocument
    from app.services.law_search_service import LawSearchService

    doc = LawDocument(
        id=1,
        title="산업안전보건법",
        law_name="산업안전보건법",
        law_type="법률",
        jurisdiction="KR",
        is_active=True,
    )
    article = LawArticle(
        id=1,
        law_document_id=1,
        article_number="제38조",
        article_no="제38조",
        article_title="안전조치",
        article_text="사업주는 추락 위험이 있는 장소에 안전망을 설치하여야 한다.",
        full_text="사업주는 추락 위험이 있는 장소에 안전망을 설치하여야 한다.",
        status="effective",
        version_group_key="산업안전보건법_제38조",
    )

    class _LawStubRepo:
        def search_by_keyword(self, keyword, top_k=20, law_scope=None):
            return [(article, doc)]

        def get_article_with_document(self, article_id):
            return article, doc

        def create_law_search_log(self, **kwargs):
            pass

        def search_chunks_by_keyword(self, **kwargs):
            return []

        def list_chunks_for_scope(self, **kwargs):
            return []

    service = LawSearchService(db=None)  # type: ignore[arg-type]
    service.repo = _LawStubRepo()  # type: ignore[assignment]

    result = service.search("추락 안전망", top_k=3)
    assert result.citations
    assert result.citations[0].law_name == "산업안전보건법"
