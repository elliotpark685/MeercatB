"""한국산업안전보건공단(KOSHA) 안전보건법령 스마트검색 OpenAPI 클라이언트.

Endpoint: http://apis.data.go.kr/B552468/srch/smartSearch

실제 요청/응답 구조 (2026-06 DATA_KEY로 실제 호출 + 공단 공식 활용가이드 docx로 확인됨,
backend/docs/한국산업안전보건공단_안전보건법령 스마트검색 활용가이드.docx 참고):
  요청: serviceKey, pageNo, numOfRows, searchValue(검색어), category
  응답: {"response": {"header": {resultCode, resultMsg},
                       "body": {associated_word(연관검색어 list), totalCount,
                                "items": {"item": [{category, content, doc_id,
                                                     highlight_content, score, title,
                                                     keyword?, filepath?, ...}, ...]}}}}

주의: item의 필드 구성이 category에 따라 다르다.
  - category 4/5/7 (법령기준/고시훈령예규/KOSHA GUIDE): category, content, doc_id,
    highlight_content, score, title 만 있음. keyword/filepath 필드 자체가 없다.
  - category 6 (미디어): 위에 더해 keyword(쉼표구분 문자열), filepath(실제 원문 URL,
    예: https://kosha.or.kr/aicuration/index.do?mode=detail&medSeq=43740),
    image_path, med_thumb_yn, media_style가 추가로 온다.
이 클라이언트는 keyword/filepath가 있으면 그대로 쓰고, 없으면 `highlight_content`의
<em class='smart'>...</em> 강조 구간에서 매칭 단어를 뽑아 keywords의 대체 신호로 쓴다.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)

KOSHA_SEARCH_URL = "http://apis.data.go.kr/B552468/srch/smartSearch"

_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_HIGHLIGHT_PATTERN = re.compile(r"<em[^>]*>(.*?)</em>", re.DOTALL)


def strip_html(text: str | None) -> str:
    """HTML 태그 제거 + 공백 정규화."""
    if not text:
        return ""
    no_tags = _TAG_PATTERN.sub(" ", str(text))
    return _WHITESPACE_PATTERN.sub(" ", no_tags).strip()


def extract_highlighted_terms(highlight_content: str | None) -> list[str]:
    """highlight_content의 <em>...</em> 강조 구간에서 매칭 단어를 추출 (중복 제거, 순서 유지)."""
    if not highlight_content:
        return []
    seen: set[str] = set()
    terms: list[str] = []
    for match in _HIGHLIGHT_PATTERN.findall(highlight_content):
        term = strip_html(match)
        if term and term not in seen:
            seen.add(term)
            terms.append(term)
    return terms


@dataclass
class KoshaRawItem:
    """KOSHA OpenAPI 응답의 검색 결과 1건 (원본 그대로, HTML 미제거)."""

    title: str = ""
    content: str = ""
    category: str = ""
    doc_id: str = ""
    keywords: list[str] = field(default_factory=list)
    score: float = 0.0
    url: str = ""


class KoshaApiClient:
    """KOSHA 스마트검색 API 래퍼. 실패 시 빈 리스트 반환 (graceful fallback)."""

    DEFAULT_TIMEOUT = 5

    def __init__(self, service_key: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        if not service_key:
            raise ValueError("DATA_KEY (KOSHA service key) is required")
        self.service_key = service_key
        self.timeout = timeout

    def search(
        self, query: str, category: str, page: int, size: int
    ) -> tuple[list[KoshaRawItem], int, list[str]]:
        """검색 실행. 반환: (결과 목록, 전체 건수, 연관검색어). 실패 시 ([], 0, [])."""
        params = {
            "serviceKey": self.service_key,
            "searchValue": query,
            "category": category,
            "pageNo": str(page),
            "numOfRows": str(size),
        }
        url = f"{KOSHA_SEARCH_URL}?{urlencode(params)}"
        logger.debug("kosha search: %s", url)

        try:
            with urlopen(url, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except Exception as exc:
            logger.warning("kosha search request failed: %s", exc)
            return [], 0, []

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("kosha search JSON parse failed: %s", exc)
            return [], 0, []

        response = payload.get("response", payload)
        header = response.get("header") or {}
        result_code = str(header.get("resultCode") or "")
        if result_code and result_code != "00":
            logger.warning(
                "kosha search returned non-success resultCode=%s msg=%s",
                result_code,
                header.get("resultMsg"),
            )
            return [], 0, []

        return self._parse_body(response.get("body") or {})

    @staticmethod
    def _parse_body(body: dict) -> tuple[list[KoshaRawItem], int, list[str]]:
        items = body.get("items")
        if isinstance(items, dict):
            items = items.get("item") or []
        if items is None:
            items = []
        if isinstance(items, dict):
            items = [items]

        total = int(body.get("totalCount") or len(items) or 0)

        associated = body.get("associated_word") or []
        if isinstance(associated, str):
            associated = [associated] if associated else []
        related_keywords = [str(w).strip() for w in associated if str(w).strip()]

        results: list[KoshaRawItem] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                results.append(KoshaApiClient._parse_item(item))
            except Exception as exc:
                logger.debug("kosha item parse error: %s item=%s", exc, item)

        return results, total, related_keywords

    @staticmethod
    def _parse_item(item: dict) -> KoshaRawItem:
        title = item.get("title") or ""
        content = item.get("content") or ""
        category = item.get("category") or ""
        doc_id = item.get("doc_id") or ""
        highlight_content = item.get("highlight_content") or ""
        score_raw = item.get("score")
        # filepath: category=6(미디어)일 때만 제공되는 실제 원문 URL. 그 외 카테고리는 없음.
        url = item.get("filepath") or ""
        # keyword: category=6일 때만 쉼표구분 문자열로 제공. 없으면 highlight_content에서 대체 추출.
        keyword_field = item.get("keyword")
        if keyword_field:
            keywords = [k.strip() for k in str(keyword_field).split(",") if k.strip()]
        else:
            keywords = extract_highlighted_terms(highlight_content)

        try:
            score = float(score_raw) if score_raw not in (None, "") else 0.0
        except (TypeError, ValueError):
            score = 0.0

        return KoshaRawItem(
            title=str(title),
            content=str(content),
            category=str(category),
            doc_id=str(doc_id),
            keywords=keywords,
            score=score,
            url=str(url),
        )
