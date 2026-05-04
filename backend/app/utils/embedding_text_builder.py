from datetime import date

from app.utils.law_parser import ParsedLawArticle


def _date_to_string(value: date | None) -> str:
    return value.isoformat() if value else ""


def build_law_embedding_text(article: ParsedLawArticle) -> str:
    parts = [
        f"law_name: {article.law_name}",
        f"chapter: {article.chapter or ''}",
        f"section: {article.section or ''}",
        f"article_no: {article.article_no}",
        f"article_title: {article.article_title or ''}",
        f"status: {article.status}",
        f"effective_date: {_date_to_string(article.effective_date)}",
        f"full_text: {article.full_text}",
    ]
    return "\n".join(parts).strip()

