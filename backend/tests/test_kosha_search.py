"""KOSHA GUIDE 寃???붿빟 愿???뚯뒪??

mock ?묐떟? 2026-06 ?ㅼ젣 DATA_KEY濡??몄텧???뺤씤???ㅼ젣 ?묐떟 援ъ“瑜?洹몃?濡?諛섏쁺?쒕떎
(response.header/response.body, searchValue ?뚮씪誘명꽣, items.item, associated_word,
keyword ?놁쓬쨌url ?놁쓬쨌highlight_content??<em> 媛뺤“ 援ш컙). admrul API ?뚯쿂??媛?뺣쭔?쇰줈
mock??吏쒕㈃ ?ㅼ젣 援ъ“? ?щ씪吏????덈떎???먯쓣 WORKGUIDE.md 7踰???ぉ?먯꽌 ?대? 寃れ뿀??
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.kosha import KoshaCategory, KoshaResultItem
from app.services.kosha_search_service import KoshaSearchService
from app.services.kosha_summary_service import KoshaSummaryService
from app.utils.kosha_api_client import KoshaApiClient, extract_highlighted_terms, strip_html

client = TestClient(app)


def _fake_response(items: list[dict], associated_word: list[str] | None = None, total: int | None = None) -> bytes:
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
    assert strip_html("<p>異붾씫  諛⑹?</p><br/>二쇱쓽") == "異붾씫 諛⑹? 二쇱쓽"
    assert strip_html(None) == ""


def test_extract_highlighted_terms_dedupes_and_preserves_order():
    highlight = "李⑤웾?먯꽌??<em class='smart'>?⑥뼱吏?/em> ?ш퀬 諛⑹?, <em class='smart'>?⑥뼱吏?/em> ?꾪뿕援ъ뿭"
    assert extract_highlighted_terms(highlight) == ["?⑥뼱吏?]


def test_kosha_api_client_parses_real_response_shape():
    raw = _fake_response(
        items=[
            {
                "category": "7",
                "content": "?묒뾽諛쒗뙋? 寃ш퀬?섍쾶 ?ㅼ튂?쒕떎.",
                "doc_id": "KOSHA07_異붾씫?ы빐諛⑹? ?쒖??덉쟾?묒뾽吏移?1",
                "highlight_content": "<em class='smart'>異붾씫</em> 諛⑹?瑜??꾪빐 ?묒뾽諛쒗뙋??寃ш퀬?섍쾶 ?ㅼ튂?쒕떎.",
                "score": 69.8285,
                "title": "異붾씫?ы빐諛⑹? ?쒖??덉쟾?묒뾽吏移?,
            }
        ],
        associated_word=["?곗뾽?덉쟾蹂닿굔", "?덉쟾蹂닿굔怨듬떒"],
        total=1,
    )
    with patch("app.utils.kosha_api_client.urlopen", return_value=_FakeHttpResponse(raw)):
        cli = KoshaApiClient(service_key="dummy-key")
        items, total, related = cli.search(query="異붾씫", category="7", page=1, size=10)

    assert total == 1
    assert related == ["?곗뾽?덉쟾蹂닿굔", "?덉쟾蹂닿굔怨듬떒"]
    assert len(items) == 1
    assert items[0].title == "異붾씫?ы빐諛⑹? ?쒖??덉쟾?묒뾽吏移?
    assert items[0].doc_id == "KOSHA07_異붾씫?ы빐諛⑹? ?쒖??덉쟾?묒뾽吏移?1"
    assert items[0].keywords == ["異붾씫"]
    assert items[0].score == 69.8285
    assert items[0].url == ""


def test_kosha_api_client_uses_filepath_and_keyword_for_media_category():
    raw = _fake_response(
        items=[
            {
                "category": "6",
                "content": "?대룞?앹궗?ㅻ━ ?덉쟾?묒뾽吏移?以?섏궗??,
                "doc_id": "KOSHA06_43740_1",
                "filepath": "https://kosha.or.kr/aicuration/index.do?mode=detail&medSeq=43740",
                "highlight_content": "<em class='smart'>?대룞??/em><em class='smart'>?щ떎由?/em> ?덉쟾?묒뾽吏移?以?섏궗??,
                "image_path": [],
                "keyword": "?щ떎由? 寃쎌옉?? 怨좎냼?묒뾽?, ?믪씠",
                "med_thumb_yn": "N",
                "media_style": "OPS",
                "score": 825.4923,
                "title": "?대룞?앹궗?ㅻ━ ?덉쟾?묒뾽吏移?,
            }
        ],
    )
    with patch("app.utils.kosha_api_client.urlopen", return_value=_FakeHttpResponse(raw)):
        cli = KoshaApiClient(service_key="dummy-key")
        items, _total, _related = cli.search(query="?щ떎由?, category="6", page=1, size=10)

    assert items[0].url == "https://kosha.or.kr/aicuration/index.do?mode=detail&medSeq=43740"
    assert items[0].keywords == ["?щ떎由?, "寃쎌옉??, "怨좎냼?묒뾽?", "?믪씠"]


def test_kosha_api_client_graceful_fallback_on_request_failure():
    with patch("app.utils.kosha_api_client.urlopen", side_effect=TimeoutError("timeout")):
        cli = KoshaApiClient(service_key="dummy-key")
        items, total, related = cli.search(query="異붾씫", category="7", page=1, size=10)
    assert items == []
    assert total == 0
    assert related == []


def test_kosha_api_client_graceful_fallback_on_non_success_result_code():
    raw = _fake_error_response()
    with patch("app.utils.kosha_api_client.urlopen", return_value=_FakeHttpResponse(raw)):
        cli = KoshaApiClient(service_key="dummy-key")
        items, total, related = cli.search(query="異붾씫", category="7", page=1, size=10)
    assert items == []
    assert total == 0


def test_kosha_search_service_without_api_key_returns_empty_result(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_search_service.settings.kosha_api_key", None)
    service = KoshaSearchService()
    result = service.search(query="異붾씫", category=KoshaCategory.KOSHA_GUIDE, page=1, size=10)
    assert result.results == []
    assert result.total == 0


def test_kosha_search_service_strips_html_and_uses_api_related_keywords(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_search_service.settings.kosha_api_key", "dummy-key")
    raw = _fake_response(
        items=[
            {
                "category": "7",
                "content": "<b>?몄뼇?섏쨷</b> 珥덇낵 湲덉?",
                "doc_id": "KOSHA07_??뚰겕?덉씤 ?덉쟾湲곗?_1",
                "highlight_content": "<em class='smart'>?щ젅??/em> ?몄뼇?섏쨷 珥덇낵 湲덉?",
                "score": 80.1,
                "title": "??뚰겕?덉씤 ?덉쟾湲곗?",
            }
        ],
        associated_word=["?몄뼇?섏쨷", "??뚰겕?덉씤"],
    )
    with patch("app.utils.kosha_api_client.urlopen", return_value=_FakeHttpResponse(raw)):
        service = KoshaSearchService()
        result = service.search(query="?щ젅??, category=KoshaCategory.KOSHA_GUIDE, page=1, size=10)

    assert result.results[0].content == "?몄뼇?섏쨷 珥덇낵 湲덉?"
    assert result.results[0].keywords == ["?щ젅??]
    assert result.related_keywords == ["?몄뼇?섏쨷", "??뚰겕?덉씤"]


def test_search_endpoint_default_category_is_all(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_search_service.settings.kosha_api_key", None)
    resp = client.get("/api/v1/kosha/search", params={"query": "異붾씫"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "0"
    assert body["results"] == []


def test_search_endpoint_rejects_invalid_category():
    resp = client.get("/api/v1/kosha/search", params={"query": "異붾씫", "category": "99"})
    assert resp.status_code == 422


def test_summarize_endpoint_mock_when_no_openai_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_summary_service.settings.openai_api_key", None)
    payload = {
        "query": "異붾씫",
        "items": [
            {
                "title": "異붾씫?ы빐諛⑹? 吏移?,
                "content": "?묒뾽諛쒗뙋 ?ㅼ튂 湲곗?",
                "category": "7",
                "keywords": ["異붾씫"],
                "score": 0.9,
                "url": "",
                "doc_id": "KOSHA07_異붾씫?ы빐諛⑹? 吏移?1",
            }
        ],
    }
    resp = client.post("/api/v1/kosha/summarize", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "異붾씫"
    assert body["core_content"]
    assert body["applicable_scope"]


def test_summarize_endpoint_rejects_more_than_three_items():
    items = [
        {"title": f"t{i}", "content": "c", "category": "7", "keywords": [], "score": 0.0, "url": ""}
        for i in range(4)
    ]
    resp = client.post("/api/v1/kosha/summarize", json={"query": "異붾씫", "items": items})
    assert resp.status_code == 422


def test_kosha_summary_service_uses_openai_response(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.kosha_summary_service.settings.openai_api_key", "dummy")
    fake_message = MagicMock()
    fake_message.content = json.dumps(
        {
            "core_content": "?듭떖",
            "applicable_scope": "???,
            "field_application": "?꾩옣 ?곸슜",
            "precautions": "二쇱쓽",
            "related_regulations": "愿??踰뺣졊",
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
            query="異붾씫",
            items=[
                KoshaResultItem(
                    title="異붾씫?ы빐諛⑹?", content="?댁슜", category="7", keywords=["異붾씫"], score=0.9, url=""
                )
            ],
        )

    assert result.core_content == "?듭떖"
    assert result.related_regulations == "愿??踰뺣졊"

