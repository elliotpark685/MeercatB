"""KOSHA GUIDE search tests."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.kosha import KoshaCategory, KoshaResultItem
from app.services.kosha_search_service import KoshaSearchService
from app.services.kosha_summary_service import KoshaSummaryService
from app.utils.kosha_api_client import KoshaApiClient, KoshaApiError, extract_highlighted_terms, strip_html

client = TestClient(app)


def _fake_response(
    items: list[dict], associated_word: list[str] | None = None, total: int | None = None
) -> bytes:
    payload = {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL_SERVICE"},
            "body": {
                "associated_word": associated_word or [],
                "totalCount": total if total is not None else len(items),
                "dataType": "JSON",
                "pageNo": 0,
                "numOfRows": len(items),
                "items": {"item": items},
            },
        }
    }
    return json.dumps(payload).encode("utf-8")


def _fake_error_response(result_code: str = "30", msg: str = "SERVICE_KEY_IS_NOT_REGISTERED_ERROR") -> bytes:
    payload = {"response": {"header": {"resultCode": result_code, "resultMsg": msg}, "body": {}}}
    return json.dumps(payload).encode("utf-8")


class _FakeHttpResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_strip_html_removes_tags_and_normalizes_whitespace():
    assert strip_html("<p>사다리  작업</p><br/>주의") == "사다리 작업 주의"
    assert strip_html(None) == ""


def test_extract_highlighted_terms_dedupes_and_preserves_order():
    highlight = "현장 <em class='smart'>사다리</em> 점검, <em class='smart'>사다리</em> 사용"
    assert extract_highlighted_terms(highlight) == ["사다리"]


def test_kosha_api_client_parses_real_response_shape():
    raw = _fake_response(
        items=[
            {
                "category": "7",
                "content": "이동식 사다리 사용 시 안전조치",
                "doc_id": "KOSHA07_사다리_1",
                "highlight_content": "<em class='smart'>사다리</em> 사용 시 안전조치",
                "score": 69.8285,
                "title": "이동식 사다리 안전작업지침",
            }
        ],
        associated_word=["사다리", "고소작업"],
        total=1,
    )
    with patch("app.utils.kosha_api_client.urlopen", return_value=_FakeHttpResponse(raw)):
        cli = KoshaApiClient(service_key="dummy-key")
        items, total, related = cli.search(query="사다리", category="7", page=1, size=10)

    assert total == 1
    assert related == ["사다리", "고소작업"]
    assert len(items) == 1
    assert items[0].title == "이동식 사다리 안전작업지침"
    assert items[0].doc_id == "KOSHA07_사다리_1"
    assert items[0].keywords == ["사다리"]
    assert items[0].score == 69.8285
    assert items[0].url == ""


def test_kosha_api_client_uses_filepath_and_keyword_for_media_category():
    raw = _fake_response(
        items=[
            {
                "category": "6",
                "content": "이동식 사다리 안전작업지침",
                "doc_id": "KOSHA06_43740_1",
                "filepath": "https://kosha.or.kr/aicuration/index.do?mode=detail&medSeq=43740",
                "highlight_content": "<em class='smart'>사다리</em> 안전작업지침",
                "image_path": [],
                "keyword": "사다리, 고소작업대, 높이",
                "med_thumb_yn": "N",
                "media_style": "OPS",
                "score": 825.4923,
                "title": "이동식사다리 안전작업지침",
            }
        ],
    )
    with patch("app.utils.kosha_api_client.urlopen", return_value=_FakeHttpResponse(raw)):
        cli = KoshaApiClient(service_key="dummy-key")
        items, _total, _related = cli.search(query="사다리", category="6", page=1, size=10)

    assert items[0].url == "https://kosha.or.kr/aicuration/index.do?mode=detail&medSeq=43740"
    assert items[0].keywords == ["사다리", "고소작업대", "높이"]


def test_kosha_api_client_raises_on_request_failure():
    with patch("app.utils.kosha_api_client.urlopen", side_effect=TimeoutError("timeout")):
        cli = KoshaApiClient(service_key="dummy-key")
        with pytest.raises(KoshaApiError, match="request failed"):
            cli.search(query="사다리", category="7", page=1, size=10)


def test_kosha_api_client_raises_on_non_success_result_code():
    raw = _fake_error_response()
    with patch("app.utils.kosha_api_client.urlopen", return_value=_FakeHttpResponse(raw)):
        cli = KoshaApiClient(service_key="dummy-key")
        with pytest.raises(KoshaApiError, match="non-success"):
            cli.search(query="사다리", category="7", page=1, size=10)


def test_kosha_search_service_without_api_key_returns_empty_result(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_search_service.settings.kosha_api_key", None)
    service = KoshaSearchService()
    result = service.search(query="사다리", category=KoshaCategory.KOSHA_GUIDE, page=1, size=10)
    assert result.results == []
    assert result.total == 0
    assert result.error is not None


def test_kosha_search_service_strips_html_and_uses_api_related_keywords(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_search_service.settings.kosha_api_key", "dummy-key")
    raw = _fake_response(
        items=[
            {
                "category": "7",
                "content": "<b>사다리</b> 점검 기준",
                "doc_id": "KOSHA07_사다리_2",
                "highlight_content": "<em class='smart'>사다리</em> 점검 기준",
                "score": 80.1,
                "title": "사다리 점검지침",
            }
        ],
        associated_word=["사다리", "점검"],
    )
    with patch("app.utils.kosha_api_client.urlopen", return_value=_FakeHttpResponse(raw)):
        service = KoshaSearchService()
        result = service.search(query="사다리", category=KoshaCategory.KOSHA_GUIDE, page=1, size=10)

    assert result.results[0].content == "사다리 점검 기준"
    assert result.results[0].keywords == ["사다리"]
    assert result.related_keywords == ["사다리", "점검"]


def test_search_endpoint_default_category_is_all(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_search_service.settings.kosha_api_key", None)
    resp = client.get("/api/v1/kosha/search", params={"query": "사다리"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "0"
    assert body["results"] == []


def test_search_endpoint_rejects_invalid_category():
    resp = client.get("/api/v1/kosha/search", params={"query": "사다리", "category": "99"})
    assert resp.status_code == 422


def test_summarize_endpoint_mock_when_no_openai_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_summary_service.settings.openai_api_key", None)
    payload = {
        "query": "사다리",
        "items": [
            {
                "title": "이동식 사다리 안전작업지침",
                "content": "이동식 사다리 사용 시 안전조치",
                "category": "7",
                "keywords": ["사다리"],
                "score": 0.9,
                "url": "",
                "doc_id": "KOSHA07_사다리_1",
            }
        ],
    }
    resp = client.post("/api/v1/kosha/summarize", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "사다리"
    assert body["core_content"]
    assert body["applicable_scope"]


def test_summarize_endpoint_rejects_more_than_three_items():
    items = [
        {"title": f"t{i}", "content": "c", "category": "7", "keywords": [], "score": 0.0, "url": ""}
        for i in range(4)
    ]
    resp = client.post("/api/v1/kosha/summarize", json={"query": "사다리", "items": items})
    assert resp.status_code == 422


def test_kosha_summary_service_uses_openai_response(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_summary_service.settings.openai_api_key", "dummy")
    fake_message = MagicMock()
    fake_message.content = json.dumps(
        {
            "core_content": "핵심",
            "applicable_scope": "적용 대상",
            "field_application": "활용 분야",
            "precautions": "주의",
            "related_regulations": "관련 법령",
        }
    )
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_completion = MagicMock()
    fake_completion.choices = [fake_choice]

    with patch("app.services.kosha_summary_service.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = fake_completion
        mock_openai_cls.return_value = mock_client

        service = KoshaSummaryService()
        result = service.summarize(
            query="사다리",
            items=[
                KoshaResultItem(
                    title="이동식 사다리 안전작업지침",
                    content="내용",
                    category="7",
                    keywords=["사다리"],
                    score=0.9,
                    url="",
                )
            ],
        )

    assert result.core_content == "핵심"
    assert result.related_regulations == "관련 법령"
