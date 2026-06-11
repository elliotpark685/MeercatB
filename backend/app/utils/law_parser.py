from dataclasses import dataclass
from datetime import date
import re

from app.utils.article_title_index_loader import CanonicalArticleIndexItem

PAGE_MARKER_RE = re.compile(r"^\[PAGE:(\d+)\]\s*$")
PART_RE = re.compile(r"^\s*제\d+편.*$")
CHAPTER_RE = re.compile(r"^\s*제\d+장.*$")
SECTION_RE = re.compile(r"^\s*제\d+절.*$")
EFFECTIVE_DATE_RE = re.compile(r"\[?(?:시행일?|矫青老)\s*:?\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?\s*\]")
STRICT_ARTICLE_HEADER_RE = re.compile(r"^\s*((?:제\d+조(?:의\d+)?)|(?:力\d+炼))(?:\(([^)]*)\))?.*$")
REFERENCE_ONLY_RE = re.compile(r"(?:제\d+조(?:의\d+)?(?:제\d+항)?(?:제\d+호)?)|(?:力\d+炼)")


@dataclass
class ParsedLawArticle:
    law_name: str
    article_no: str
    article_title: str | None
    chapter: str | None
    section: str | None
    full_text: str
    effective_date: date | None
    status: str
    source_page_start: int | None
    source_page_end: int | None
    version_group_key: str


def _extract_effective_date(text: str) -> date | None:
    match = EFFECTIVE_DATE_RE.search(text)
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _compute_status(explicit_effective_date: date | None) -> str:
    if explicit_effective_date is None:
        return "effective"
    return "scheduled" if explicit_effective_date > date.today() else "effective"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _build_canonical_map(
    canonical_article_index: list[CanonicalArticleIndexItem],
) -> dict[str, CanonicalArticleIndexItem]:
    out: dict[str, CanonicalArticleIndexItem] = {}
    for item in canonical_article_index:
        out[_normalize(f"{item.article_no}({item.article_title})")] = item
    return out


def _find_scan_start(lines: list[str], law_name: str) -> int:
    hit_positions = [i for i, line in enumerate(lines) if law_name in line]
    if len(hit_positions) >= 2:
        return hit_positions[1]
    return 0


def parse_korean_law_articles(
    text: str,
    law_name: str,
    canonical_article_index: list[CanonicalArticleIndexItem] | None = None,
    default_effective_date: date | None = None,
) -> list[ParsedLawArticle]:
    lines = text.splitlines()
    start_idx = _find_scan_start(lines, law_name=law_name)

    articles: list[ParsedLawArticle] = []
    current_page: int | None = None
    current_part: str | None = None
    current_chapter: str | None = None
    current_section: str | None = None
    current_article: dict | None = None

    canonical_map = _build_canonical_map(canonical_article_index or [])

    def flush_article() -> None:
        nonlocal current_article
        if not current_article:
            return

        body_lines = [line for line in current_article["lines"][1:] if line.strip()]
        if not body_lines:
            current_article = None
            return

        full_text = "\n".join(current_article["lines"]).strip()
        explicit_eff_date = _extract_effective_date(full_text)
        effective_date = explicit_eff_date or default_effective_date
        status = _compute_status(explicit_eff_date)

        articles.append(
            ParsedLawArticle(
                law_name=law_name,
                article_no=current_article["article_no"],
                article_title=current_article["article_title"],
                chapter=current_article["chapter"],
                section=current_article["section"],
                full_text=full_text,
                effective_date=effective_date,
                status=status,
                source_page_start=current_article["source_page_start"],
                source_page_end=current_article["source_page_end"],
                version_group_key=f"{law_name}_{current_article['article_no']}",
            )
        )
        current_article = None

    for raw_line in lines[start_idx:]:
        line = raw_line.strip()
        if not line:
            if current_article is not None:
                current_article["lines"].append("")
            continue

        page_match = PAGE_MARKER_RE.match(line)
        if page_match:
            current_page = int(page_match.group(1))
            continue

        if PART_RE.match(line):
            current_part = line
            current_chapter = None
            current_section = None
            continue
        if CHAPTER_RE.match(line):
            current_chapter = line
            current_section = None
            continue
        if SECTION_RE.match(line):
            current_section = line
            continue

        if REFERENCE_ONLY_RE.search(line) and not STRICT_ARTICLE_HEADER_RE.match(line):
            if current_article is not None:
                current_article["lines"].append(line)
                current_article["source_page_end"] = current_page
            continue

        article_match = STRICT_ARTICLE_HEADER_RE.match(line)
        if article_match:
            article_no = article_match.group(1)
            article_title = article_match.group(2).strip() if article_match.group(2) else None

            if canonical_map:
                title_key = article_title or ""
                key = _normalize(f"{article_no}({title_key})")
                canonical_item = canonical_map.get(key)
                if not canonical_item:
                    if current_article is not None:
                        current_article["lines"].append(line)
                        current_article["source_page_end"] = current_page
                    continue
                article_title = canonical_item.article_title
                chapter = canonical_item.chapter or current_chapter
                section = canonical_item.section or current_section
            else:
                chapter = current_chapter
                section = current_section

            flush_article()
            current_article = {
                "article_no": article_no,
                "article_title": article_title,
                "part": current_part,
                "chapter": chapter,
                "section": section,
                "lines": [line],
                "source_page_start": current_page,
                "source_page_end": current_page,
            }
            continue

        if current_article is not None:
            current_article["lines"].append(line)
            current_article["source_page_end"] = current_page

    flush_article()
    return articles
