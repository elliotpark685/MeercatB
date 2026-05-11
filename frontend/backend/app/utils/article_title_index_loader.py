from dataclasses import dataclass
import re
from pathlib import Path


ARTICLE_LINE_RE = re.compile(r"^\s*(제\d+조(?:의\d+)?)(?:\(([^)]*)\))\s*$")
PART_RE = re.compile(r"^\s*제\d+편\b.*$")
CHAPTER_RE = re.compile(r"^\s*제\d+장\b.*$")
SECTION_RE = re.compile(r"^\s*제\d+절\b.*$")
GWAN_RE = re.compile(r"^\s*제\d+관\b.*$")
SOK_RE = re.compile(r"^\s*제\d+속\b.*$")


@dataclass
class CanonicalArticleIndexItem:
    article_no: str
    article_title: str
    part: str | None
    chapter: str | None
    section: str | None
    gwan: str | None
    sok: str | None
    order: int


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp949")


def load_article_title_index(file_path: str) -> list[CanonicalArticleIndexItem]:
    path = Path(file_path)
    raw = _read_text(path)

    part: str | None = None
    chapter: str | None = None
    section: str | None = None
    gwan: str | None = None
    sok: str | None = None
    order = 0
    items: list[CanonicalArticleIndexItem] = []

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if PART_RE.match(line):
            part = line
            chapter = None
            section = None
            gwan = None
            sok = None
            continue
        if CHAPTER_RE.match(line):
            chapter = line
            section = None
            gwan = None
            sok = None
            continue
        if SECTION_RE.match(line):
            section = line
            gwan = None
            sok = None
            continue
        if GWAN_RE.match(line):
            gwan = line
            sok = None
            continue
        if SOK_RE.match(line):
            sok = line
            continue

        match = ARTICLE_LINE_RE.match(line)
        if not match:
            continue

        order += 1
        items.append(
            CanonicalArticleIndexItem(
                article_no=match.group(1),
                article_title=match.group(2).strip(),
                part=part,
                chapter=chapter,
                section=section,
                gwan=gwan,
                sok=sok,
                order=order,
            )
        )

    return items

