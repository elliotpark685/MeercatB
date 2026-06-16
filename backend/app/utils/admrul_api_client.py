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

        # 행정규칙 API 응답 구조: AdmRulSearch.admrul[]
        search_result = payload.get("AdmRulSearch") or payload.get("LawSearch") or {}
        items = search_result.get("admrul") or search_result.get("law") or []
        if isinstance(items, dict):
            items = [items]

        result: list[AdmrulListItem] = []
        for item in items:
            try:
                # 행정규칙일련번호: lawService.do?ID= 에 사용하는 실제 ID
                doc_id = str(
                    item.get("행정규칙일련번호")
                    or item.get("행정규칙ID")
                    or item.get("법령ID")
                    or item.get("ID")
                    or ""
                )
                name = str(
                    item.get("행정규칙명")
                    or item.get("법령명")
                    or item.get("법령명한글")
                    or ""
                )
                result.append(
                    AdmrulListItem(
                        id=doc_id,
                        lid=doc_id,
                        name=name,
                        enforcement_date=str(item.get("시행일자") or ""),
                        revision_date=str(item.get("개정일자") or item.get("최근개정일자") or ""),
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
        """API 응답 JSON → AdmrulDocument 변환.

        법제처 행정규칙 API 실제 응답 구조:
        {
          "AdmRulService": {
            "행정규칙기본정보": { "행정규칙명": "...", "발령일자": "...", ... },
            "조문내용": ["제1장 총칙", "제1조(목적) ...", "제2조(정의) ...", ...],
            ...
          }
        }
        """
        import re as _re

        service = (
            payload.get("AdmRulService")
            or payload.get("법령")
            or payload.get("AdmRul")
            or {}
        )
        if not service:
            for v in payload.values():
                if isinstance(v, dict):
                    service = v
                    break

        if not service:
            logger.warning("admrul document parse: empty service data for id=%s", doc_id)
            return None

        # 기본 메타
        meta = service.get("행정규칙기본정보") or service.get("기본정보") or {}
        name = str(
            meta.get("행정규칙명")
            or meta.get("법령명칭")
            or service.get("행정규칙명")
            or service.get("법령명")
            or ""
        )
        enforcement_date = str(
            meta.get("발령일자") or meta.get("시행일자") or service.get("시행일자") or ""
        )

        doc = AdmrulDocument(id=doc_id, name=name, enforcement_date=enforcement_date)

        # 조문 파싱 — 실제 응답에서 조문내용은 문자열 리스트
        content_list = service.get("조문내용") or []
        if isinstance(content_list, str):
            content_list = [content_list]

        if content_list:
            doc.raw_text = "\n".join(str(s) for s in content_list)
            doc.articles = _parse_admrul_text_list(content_list, name)
        else:
            # 문자열 blob fallback
            text = str(service.get("규정내용") or service.get("본문내용") or "")
            doc.raw_text = text
            if text:
                doc.articles = [AdmrulArticle(article_no="", title=name, content=text)]

        return doc


# ── 조문 텍스트 리스트 파서 ────────────────────────────────────────────────────

import re as _re

_ARTICLE_PATTERN = _re.compile(r"^제\s*(\d+)\s*조\s*(?:\(([^)]+)\))?\s*(.*)", _re.DOTALL)
_CHAPTER_PATTERN = _re.compile(r"^제\s*\d+\s*장")
_SECTION_PATTERN = _re.compile(r"^제\s*\d+\s*절")


def _parse_admrul_text_list(lines: list, doc_name: str) -> list[AdmrulArticle]:
    """행정규칙 조문 텍스트 리스트를 AdmrulArticle 목록으로 변환."""
    articles: list[AdmrulArticle] = []
    current_chapter = ""
    current_section = ""

    for line in lines:
        text = str(line).strip()
        if not text:
            continue

        if _CHAPTER_PATTERN.match(text):
            current_chapter = text
            current_section = ""
            continue

        if _SECTION_PATTERN.match(text):
            current_section = text
            continue

        m = _ARTICLE_PATTERN.match(text)
        if m:
            article_no = f"제{m.group(1)}조"
            title = m.group(2) or ""
            content = (m.group(3) or "").strip()
            full = f"{article_no}({title}) {content}".strip() if title else f"{article_no} {content}".strip()
            articles.append(
                AdmrulArticle(
                    article_no=article_no,
                    title=title,
                    content=full,
                    chapter=current_chapter,
                    section=current_section,
                )
            )
        else:
            # 조문 형식이 아닌 줄은 마지막 article에 덧붙임
            if articles:
                articles[-1].content += "\n" + text
            else:
                articles.append(
                    AdmrulArticle(article_no="", title=doc_name, content=text)
                )

    return articles
