"""?쒓뎅?곗뾽?덉쟾蹂닿굔怨듬떒(KOSHA) ?덉쟾蹂닿굔踰뺣졊 ?ㅻ쭏?멸???OpenAPI ?대씪?댁뼵??

Endpoint: https://apis.data.go.kr/B552468/srch/smartSearch

?ㅼ젣 ?붿껌/?묐떟 援ъ“ (2026-06 DATA_KEY濡??ㅼ젣 ?몄텧 + 怨듬떒 怨듭떇 ?쒖슜媛?대뱶 docx濡??뺤씤??
backend/docs/?쒓뎅?곗뾽?덉쟾蹂닿굔怨듬떒_?덉쟾蹂닿굔踰뺣졊 ?ㅻ쭏?멸????쒖슜媛?대뱶.docx 李멸퀬):
  ?붿껌: serviceKey, pageNo, numOfRows, searchValue(寃?됱뼱), category
  ?묐떟: {"response": {"header": {resultCode, resultMsg},
                       "body": {associated_word(?곌?寃?됱뼱 list), totalCount,
                                "items": {"item": [{category, content, doc_id,
                                                     highlight_content, score, title,
                                                     keyword?, filepath?, ...}, ...]}}}}

二쇱쓽: item???꾨뱶 援ъ꽦??category???곕씪 ?ㅻⅤ??
  - category 4/5/7 (踰뺣졊湲곗?/怨좎떆?덈졊?덇퇋/KOSHA GUIDE): category, content, doc_id,
    highlight_content, score, title 留??덉쓬. keyword/filepath ?꾨뱶 ?먯껜媛 ?녿떎.
  - category 6 (誘몃뵒??: ?꾩뿉 ?뷀빐 keyword(?쇳몴援щ텇 臾몄옄??, filepath(?ㅼ젣 ?먮Ц URL,
    ?? https://kosha.or.kr/aicuration/index.do?mode=detail&medSeq=43740),
    image_path, med_thumb_yn, media_style媛 異붽?濡??⑤떎.
???대씪?댁뼵?몃뒗 keyword/filepath媛 ?덉쑝硫?洹몃?濡??곌퀬, ?놁쑝硫?`highlight_content`??<em class='smart'>...</em> 媛뺤“ 援ш컙?먯꽌 留ㅼ묶 ?⑥뼱瑜?戮묒븘 keywords???泥??좏샇濡??대떎.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)

KOSHA_SEARCH_URL = "https://apis.data.go.kr/B552468/srch/smartSearch"

_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_HIGHLIGHT_PATTERN = re.compile(r"<em[^>]*>(.*?)</em>", re.DOTALL)


def strip_html(text: str | None) -> str:
    """HTML ?쒓렇 ?쒓굅 + 怨듬갚 ?뺢퇋??"""
    if not text:
        return ""
    no_tags = _TAG_PATTERN.sub(" ", str(text))
    return _WHITESPACE_PATTERN.sub(" ", no_tags).strip()


def extract_highlighted_terms(highlight_content: str | None) -> list[str]:
    """highlight_content??<em>...</em> 媛뺤“ 援ш컙?먯꽌 留ㅼ묶 ?⑥뼱瑜?異붿텧 (以묐났 ?쒓굅, ?쒖꽌 ?좎?)."""
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
    """KOSHA OpenAPI ?묐떟??寃??寃곌낵 1嫄?(?먮낯 洹몃?濡? HTML 誘몄젣嫄?."""

    title: str = ""
    content: str = ""
    category: str = ""
    doc_id: str = ""
    keywords: list[str] = field(default_factory=list)
    score: float = 0.0
    url: str = ""


class KoshaApiError(RuntimeError):
    """Raised when the upstream KOSHA API cannot be used."""


class KoshaApiClient:
    """KOSHA ?ㅻ쭏?멸???API ?섑띁. ?ㅽ뙣 ??鍮?由ъ뒪??諛섑솚 (graceful fallback)."""

    DEFAULT_TIMEOUT = 5

    def __init__(self, service_key: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        if not service_key:
            raise ValueError("DATA_KEY (KOSHA service key) is required")
        self.service_key = service_key
        self.timeout = timeout

    def search(
        self, query: str, category: str, page: int, size: int
    ) -> tuple[list[KoshaRawItem], int, list[str]]:
        """寃???ㅽ뻾. 諛섑솚: (寃곌낵 紐⑸줉, ?꾩껜 嫄댁닔, ?곌?寃?됱뼱). ?ㅽ뙣 ??([], 0, [])."""
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
            raise KoshaApiError(f"kosha search request failed: {exc}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise KoshaApiError(f"kosha search JSON parse failed: {exc}") from exc

        response = payload.get("response", payload)
        header = response.get("header") or {}
        result_code = str(header.get("resultCode") or "")
        if result_code and result_code != "00":
            raise KoshaApiError(
                "kosha search returned non-success "
                f"resultCode={result_code} msg={header.get('resultMsg')}"
            )

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
        # filepath: category=6(誘몃뵒?????뚮쭔 ?쒓났?섎뒗 ?ㅼ젣 ?먮Ц URL. 洹???移댄뀒怨좊━???놁쓬.
        url = item.get("filepath") or ""
        # keyword: category=6???뚮쭔 ?쇳몴援щ텇 臾몄옄?대줈 ?쒓났. ?놁쑝硫?highlight_content?먯꽌 ?泥?異붿텧.
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

