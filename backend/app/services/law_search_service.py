from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.law_article import LawArticle
from app.models.law_document import LawDocument
from app.repositories.law_repository import LawRepository
from app.schemas.law import CitationItem, LawArticleDetailResponse, LawSearchResponse, RawHitItem
from app.services.law_validation_service import LawValidationService
from app.services.query_analyzer import QueryAnalysis, QueryAnalyzer


@dataclass
class ScoredArticle:
    article: LawArticle
    document: LawDocument
    score: float
    matched_reason: list[str]


class LawSearchService:
    def __init__(self, db: Session, law_validation_service: LawValidationService | None = None) -> None:
        self.db = db
        self.repo = LawRepository(db)
        self.query_analyzer = QueryAnalyzer()
        self.law_validation_service = law_validation_service or LawValidationService()

    def search(
        self,
        query: str,
        top_k: int = 5,
        validate_latest: bool = False,
        user_id: int | None = None,
        site_id: int | None = None,
    ) -> LawSearchResponse:
        analysis = self.query_analyzer.analyze(query)
        rows = self.repo.search_by_keyword(keyword=query, top_k=max(top_k * 5, top_k))
        scored = [self._score_article(article, document, analysis) for article, document in rows]
        scored.sort(key=lambda item: item.score, reverse=True)
        top_scored = scored[:top_k]

        citations = [self._to_citation(item) for item in top_scored]
        raw_hits = [RawHitItem(article_id=item.article.id, score=item.score, matched_reason=item.matched_reason) for item in top_scored]
        answer = self._build_answer(citations)
        if validate_latest:
            answer = self.law_validation_service.validate_latest([citation.model_dump() for citation in citations])

        response = LawSearchResponse(
            query=query,
            answer=answer,
            citations=citations,
            raw_hits=raw_hits,
        )
        self._log_search(query=query, user_id=user_id, site_id=site_id, top_k=top_k, result_count=len(top_scored))
        return response

    def _log_search(self, query: str, user_id: int | None, site_id: int | None, top_k: int, result_count: int) -> None:
        if not hasattr(self.repo, "create_law_search_log"):
            return
        self.repo.create_law_search_log(
            query=query,
            user_id=user_id,
            site_id=site_id,
            top_k=top_k,
            result_count=result_count,
        )
        if self.db is not None:
            self.db.commit()

    def get_article_detail(self, article_id: int) -> LawArticleDetailResponse | None:
        row = self.repo.get_article_with_document(article_id)
        if row is None:
            return None
        article, document = row
        return LawArticleDetailResponse(
            article_id=article.id,
            law_document_id=article.law_document_id,
            law_name=document.title,
            article_no=article.article_number,
            article_title=article.title,
            chapter=article.chapter,
            section=article.section,
            full_text=article.full_text,
            status=article.status,
            effective_date=article.effective_date.isoformat() if article.effective_date else None,
            source_page_start=article.source_page_start,
            source_page_end=article.source_page_end,
            law_type=document.law_type,
            law_no=document.law_no,
            document_effective_date=document.effective_date.isoformat() if document.effective_date else None,
            source_file_path=document.source_file_path,
        )

    def _score_article(self, article: LawArticle, document: LawDocument, analysis: QueryAnalysis) -> ScoredArticle:
        score = 1.0
        matched_reason: list[str] = []
        haystack = " ".join(
            [
                document.title or "",
                article.chapter or "",
                article.section or "",
                article.title or "",
                article.full_text or "",
            ]
        )

        if analysis.law_name != "unknown" and analysis.law_name in (document.title or ""):
            score += 1.0
            matched_reason.append(f"law_name:{analysis.law_name}")

        for work_type in analysis.work_types:
            if work_type in haystack:
                score += 0.35
                matched_reason.append(f"work_type:{work_type}")

        for risk_type in analysis.risk_types:
            if risk_type in haystack:
                score += 0.5
                matched_reason.append(f"risk_type:{risk_type}")

        for action_type in analysis.action_types:
            if action_type in haystack:
                score += 0.25
                matched_reason.append(f"action_type:{action_type}")

        if article.status == "effective":
            score += 0.3
            matched_reason.append("status:effective_boost")
        elif article.status == "scheduled":
            score -= 0.2
            matched_reason.append("status:scheduled_penalty")

        return ScoredArticle(
            article=article,
            document=document,
            score=round(score, 4),
            matched_reason=matched_reason,
        )

    @staticmethod
    def _to_citation(item: ScoredArticle) -> CitationItem:
        return CitationItem(
            article_id=item.article.id,
            law_name=item.document.title,
            article_no=item.article.article_number,
            article_title=item.article.title,
            chapter=item.article.chapter,
            section=item.article.section,
            status=item.article.status,
            effective_date=item.article.effective_date.isoformat() if item.article.effective_date else None,
            source_page_start=item.article.source_page_start,
            source_page_end=item.article.source_page_end,
        )

    @staticmethod
    def _build_answer(citations: list[CitationItem]) -> str:
        if not citations:
            return "관련 법령 조문을 찾지 못했습니다. 검색어를 구체화해 주세요."

        first = citations[0]
        return (
            f"주요 근거 조문은 {first.law_name} {first.article_no}"
            f"{f'({first.article_title})' if first.article_title else ''} 입니다. "
            "아래 인용 조문을 확인해 작업 계획에 반영하세요."
        )

