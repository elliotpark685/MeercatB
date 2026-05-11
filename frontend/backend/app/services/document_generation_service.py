import json

from sqlalchemy.orm import Session

from app.models.generated_document import GeneratedDocument
from app.models.site import Site
from app.services.law_search_service import LawSearchService


class DocumentGenerationService:
    """Generates document drafts grounded in law search results."""

    def __init__(self, db: Session, law_search_service: LawSearchService) -> None:
        self.db = db
        self.law_search_service = law_search_service

    def generate(
        self,
        site_id: int,
        user_id: int | None,
        document_type: str,
        prompt: str,
    ) -> GeneratedDocument:
        site = self.db.get(Site, site_id)
        if site is None:
            raise ValueError("Site not found")

        normalized_type = document_type.strip().lower()
        search_result = self.law_search_service.search(prompt, top_k=3, validate_latest=False, user_id=user_id, site_id=site_id)
        references = search_result.citations
        citation_payload = [
            {"article_id": item.article_id, "law_name": item.law_name, "article_no": item.article_no}
            for item in references
        ]
        law_summary = "\n".join(
            [
                f"- [{item.law_name} {item.article_no}] "
                f"{item.article_title or ''}".strip()
                for item in references
            ]
        )

        content = self._build_template_content(
            document_type=normalized_type,
            site_name=site.name,
            prompt=prompt,
            law_summary=law_summary or "- No direct article match found.",
        )

        document = GeneratedDocument(
            site_id=site_id,
            created_by=user_id,
            document_type=normalized_type,
            title=f"{normalized_type.upper()} - {site.name}",
            prompt=prompt,
            content=content,
            citations_json=json.dumps(citation_payload, ensure_ascii=False),
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    @staticmethod
    def _build_template_content(document_type: str, site_name: str, prompt: str, law_summary: str) -> str:
        templates: dict[str, str] = {
            "tbm": (
                f"# TBM Draft for {site_name}\n\n"
                f"Prompt: {prompt}\n\n"
                "## 작업개요\n"
                "- 작업 대상:\n- 작업 시간:\n- 담당자:\n\n"
                "## 주요위험요인\n"
                "- 추락\n- 협착\n- 낙하\n\n"
                "## 안전대책\n"
                "- 작업 전 위험성 공유\n- 보호구 착용 확인\n- 작업구역 통제\n\n"
                "## 관련법령\n"
                f"{law_summary}\n\n"
                "## TBM 전달사항\n"
                "- 오늘 작업 핵심 위험과 통제 방안을 전원에게 재확인\n"
            ),
            "risk_assessment": (
                f"# RISK ASSESSMENT Draft for {site_name}\n\n"
                f"Prompt: {prompt}\n\n"
                "## 작업공종\n"
                "- 공종명:\n- 세부 작업:\n\n"
                "## 위험요인\n"
                "- 잠재 위험요인 식별\n\n"
                "## 현재대책\n"
                "- 기존 적용중인 통제\n\n"
                "## 개선대책\n"
                "- 추가 개선 조치\n\n"
                "## 위험도\n"
                "- 발생가능성:\n- 중대성:\n- 종합 위험도:\n\n"
                "## 관련법령\n"
                f"{law_summary}\n"
            ),
            "work_plan": (
                f"# WORK PLAN Draft for {site_name}\n\n"
                f"Prompt: {prompt}\n\n"
                "## 작업목적\n"
                "- 작업 목적 정의\n\n"
                "## 작업절차\n"
                "1. 사전 점검\n2. 작업 수행\n3. 종료 점검\n\n"
                "## 장비/인원\n"
                "- 장비:\n- 투입 인원:\n\n"
                "## 위험요소\n"
                "- 고위험 포인트\n\n"
                "## 안전조치\n"
                "- 위험요소별 통제조치\n\n"
                "## 관련법령\n"
                f"{law_summary}\n"
            ),
            "inspection_checklist": (
                f"# INSPECTION CHECKLIST Draft for {site_name}\n\n"
                f"Prompt: {prompt}\n\n"
                "## 점검항목\n"
                "- 가설구조물\n- 전기설비\n- 개인보호구\n\n"
                "## 점검기준\n"
                "- 법정 기준 및 사내 기준\n\n"
                "## 적합/부적합\n"
                "- 항목별 판정 기록\n\n"
                "## 조치사항\n"
                "- 부적합 항목 개선 조치 및 기한\n\n"
                "## 관련법령\n"
                f"{law_summary}\n"
            ),
        }
        if document_type in templates:
            return templates[document_type]

        return (
            f"# {document_type.upper()} Draft for {site_name}\n\n"
            f"Prompt: {prompt}\n\n"
            "## Recommended Safety Actions\n"
            "1. Conduct pre-task hazard briefing.\n"
            "2. Verify PPE and fall prevention controls.\n"
            "3. Record toolbox meeting attendance.\n\n"
            "## Related Legal References\n"
            f"{law_summary}\n"
        )

