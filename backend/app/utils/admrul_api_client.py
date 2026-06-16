"""법제처 행정규칙 Open API 클라이언트.

목록 조회: lawSearch.do?target=admrul
본문 조회: lawService.do?target=admrul&ID={id}
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)

ADMRUL_SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
ADMRUL_SERVICE_URL = "https://www.law.go.kr/DRF/lawService.do"


@dataclass
class AdmrulListItem:
    """행정규칙 목록 항목."""
    id: str
    lid: str
    name: str
    enforcement_date: str = ""
    revision_date: str = ""
    ministry: str = ""


@dataclass
class AdmrulArticle:
    """행정규칙 조문."""
    article_no: str
    title: str
    content: str
    chapter: str = ""
    section: str = ""


@dataclass
class AdmrulDocument:
    """행정규칙 문서 전체."""
    id: str
    name: str
    enforcement_date: str = ""
    raw_text: str = ""
    articles: list[AdmrulArticle] = field(default_factory=list)


class AdmrulApiClient:
    """법제처 행정규칙 API 래퍼."""

    def __init__(self, oc: str, timeout: int = 30) -> None:
        if not oc:
            raise ValueError("LAW_API_OC key is required for admrul API")
        self.oc = oc
        self.timeout = timeout

    # ── 목록 조회 ────────────────────────────────────────────────────────────

    def search_list(self, query: str, page: int = 1, display: int = 20) -> list[AdmrulListItem]:
        """행정규칙 목록 검색."""
        params = {
            "OC": self.oc,
            "target": "admrul",
            "query": query,
            "search": "1",
            "type": "JSON",
            "page": page,
            "display": display,
        }
        url = f"{ADMRUL_SEARCH_URL}?{urlencode(params)}"
        logger.debug("admrul search: %s", url)

        try:
            with urlopen(url, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except Exception as exc:
            logger.warning("admrul search request failed: %s", exc)
            return []

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("admrul search JSON parse failed: %s", exc)
            return []

        search_result = payload.get("LawSearch") or {}
        items = search_result.get("law") or []
        if isinstance(items, dict):
            items = [items]

        result: list[AdmrulListItem] = []
        for item in items:
            try:
                result.append(
                    AdmrulListItem(
                        id=str(item.get("법령ID") or item.get("ID") or ""),
                        lid=str(item.get("법령ID") or item.get("LID") or item.get("ID") or ""),
                        name=str(item.get("법령명") or item.get("법령명한글") or ""),
                        enforcement_date=str(item.get("시행일자") or ""),
                        revision_date=str(item.get("최근개정일자") or ""),
                        ministry=str(item.get("소관부처명") or ""),
                    )
                )
            except Exception as exc:
                logger.debug("admrul list item parse error: %s item=%s", exc, item)

        return result

    def search_all(self, query: str, max_pages: int = 5, display: int = 20) -> list[AdmrulListItem]:
        """여러 페이지 순회하며 목록 수집."""
        all_items: list[AdmrulListItem] = []
        for page in range(1, max_pages + 1):
            items = self.search_list(query=query, page=page, display=display)
            if not items:
                break
            all_items.extend(items)
            if len(items) < display:
                break
        return all_items

    # ── 본문 조회 ────────────────────────────────────────────────────────────

    def get_document(self, doc_id: str) -> AdmrulDocument | None:
        """행정규칙 본문 조회 (ID 사용)."""
        params = {
            "OC": self.oc,
            "target": "admrul",
            "ID": doc_id,
            "type": "JSON",
        }
        url = f"{ADMRUL_SERVICE_URL}?{urlencode(params)}"
        logger.debug("admrul service: %s", url)

        try:
            with urlopen(url, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except Exception as exc:
            logger.warning("admrul service request failed id=%s: %s", doc_id, exc)
            return None

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("admrul service JSON parse failed id=%s: %s", doc_id, exc)
            return None

        return self._parse_document(doc_id, payload)

    # ── 파싱 ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_document(doc_id: str, payload: dict) -> AdmrulDocument | None:
        """API 응답 JSON → AdmrulDocument 변환."""
        law_data = payload.get("법령") or payload.get("AdmRul") or {}
        if not law_data:
            # 다른 최상위 키 시도
            for key in payload:
                if isinstance(payload[key], dict):
                    law_data = payload[key]
                    break

        if not law_data:
            logger.warning("admrul document parse: empty law_data for id=%s", doc_id)
            return None

        # 기본 메타
        name = str(
            law_data.get("기본정보", {}).get("법령명칭")
            or law_data.get("법령명")
            or law_data.get("법령명한글")
            or ""
        )
        enforcement_date = str(
            law_data.get("기본정보", {}).get("시행일자")
            or law_data.get("시행일자")
            or ""
        )

        doc = AdmrulDocument(id=doc_id, name=name, enforcement_date=enforcement_date)

        # 조문 파싱
        body = law_data.get("조문") or law_data.get("규정내용") or law_data.get("본문") or {}
        articles_raw = body.get("조문단위") if isinstance(body, dict) else None
        if isinstance(articles_raw, dict):
            articles_raw = [articles_raw]

        raw_texts: list[str] = []

        if articles_raw:
            for item in articles_raw:
                article_no = str(item.get("조문번호") or item.get("조번호") or "")
                title = str(item.get("조문제목") or item.get("제목") or "")
                content_raw = item.get("조문내용") or item.get("내용") or ""
                if isinstance(content_raw, list):
                    content = "\n".join(str(c) for c in content_raw)
                else:
                    content = str(content_raw)

                chapter = str(item.get("편번호") or item.get("장번호") or "")
                section = str(item.get("절번호") or "")
                raw_texts.append(f"{article_no} {title}\n{content}".strip())
                doc.articles.append(
                    AdmrulArticle(
                        article_no=article_no,
                        title=title,
                        content=content,
                        chapter=chapter,
                        section=section,
                    )
                )
        else:
            # 조문 구조가 없으면 전체 텍스트를 하나의 청크로
            text = (
                law_data.get("규정내용")
                or law_data.get("본문내용")
                or law_data.get("내용")
                or ""
            )
            if isinstance(text, list):
                text = "\n".join(str(t) for t in text)
            text = str(text)
            raw_texts.append(text)
            if text:
                doc.articles.append(
                    AdmrulArticle(article_no="", title=name, content=text)
                )

        doc.raw_text = "\n\n".join(raw_texts)
        return doc
