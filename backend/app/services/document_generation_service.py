import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.generated_document import GeneratedDocument
from app.models.site import Site
from app.services.law_search_service import LawSearchService


class DocumentGenerationService:
    """Generates document drafts grounded in integrated law search results."""

    MODEL_NAME = "gpt-4o-mini"

    def __init__(self, db: Session, law_search_service: LawSearchService) -> None:
        self.db = db
        self.law_search_service = law_search_service
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

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
        search_result = self.law_search_service.search(
            prompt,
            top_k=5,
            validate_latest=False,
            user_id=user_id,
            site_id=site_id,
        )
        references = self._build_references(search_result.results)
        law_context = self._build_law_context(references)
        generation_prompt = self._build_generation_prompt(
            document_type=normalized_type,
            site_name=site.name,
            user_prompt=prompt,
            law_context=law_context,
        )
        generated_text = self._generate_text(
            document_type=normalized_type,
            site_name=site.name,
            user_prompt=prompt,
            law_context=law_context,
            generation_prompt=generation_prompt,
            references=references,
        )

        references_json = json.dumps(references, ensure_ascii=False)
        document = GeneratedDocument(
            site_id=site_id,
            created_by=user_id,
            document_type=normalized_type,
            title=f"{normalized_type.upper()} - {site.name}",
            prompt=prompt,
            content=generated_text,
            citations_json=references_json,
            references_json=references_json,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    @staticmethod
    def _build_references(search_results) -> list[dict]:
        references: list[dict] = []
        for item in search_results:
            references.append(
                {
                    "law_name": item.law_name,
                    "article_no": item.article_no,
                    "article_title": item.article_title,
                    "chunk_text": item.chunk_text,
                    "effective_date": item.effective_date,
                    "source_url": item.source_url,
                    "score": item.score,
                    "article_id": item.article_id,
                    "chunk_id": item.chunk_id,
                }
            )
        return references

    @staticmethod
    def _build_law_context(references: list[dict]) -> str:
        if not references:
            return "제공된 법령 context가 없습니다."
        lines = []
        for index, reference in enumerate(references, start=1):
            title = reference.get("article_title") or ""
            effective_date = reference.get("effective_date") or "unknown"
            lines.append(
                "\n".join(
                    [
                        f"[{index}] {reference['law_name']} {reference['article_no']} {title}",
                        f"시행일: {effective_date}",
                        f"내용: {reference['chunk_text']}",
                    ]
                )
            )
        return "\n\n".join(lines)

    @classmethod
    def _build_generation_prompt(
        cls,
        document_type: str,
        site_name: str,
        user_prompt: str,
        law_context: str,
    ) -> str:
        return (
            "You are a Korean construction safety document assistant.\n"
            f"Model task: generate a {document_type} document for site '{site_name}'.\n\n"
            "Mandatory constraints:\n"
            "- 제공된 법령 context에 없는 법적 의무는 단정하지 말 것.\n"
            "- 불확실한 내용은 추가 검토 필요로 표시할 것.\n"
            "- 문서 마지막에 참고 법령 목록을 표시할 것.\n"
            "- 법령 context의 조문 근거를 우선 사용하고, 일반 안전 권고와 법적 의무를 구분할 것.\n\n"
            f"User request:\n{user_prompt}\n\n"
            f"Law context:\n{law_context}\n"
        )

    def _generate_text(
        self,
        document_type: str,
        site_name: str,
        user_prompt: str,
        law_context: str,
        generation_prompt: str,
        references: list[dict],
    ) -> str:
        if self._client is None:
            return self._mock_response(
                document_type=document_type,
                site_name=site_name,
                user_prompt=user_prompt,
                law_context=law_context,
                references=references,
            )
        try:
            response = self._client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "법령 context 기반으로만 법적 의무를 설명하는 한국어 안전문서 작성 도우미입니다.",
                    },
                    {"role": "user", "content": generation_prompt},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception:
            pass
        return self._mock_response(
            document_type=document_type,
            site_name=site_name,
            user_prompt=user_prompt,
            law_context=law_context,
            references=references,
        )

    @staticmethod
    def _mock_response(
        document_type: str,
        site_name: str,
        user_prompt: str,
        law_context: str,
        references: list[dict],
    ) -> str:
        law_summary = DocumentGenerationService._format_reference_list(references)
        body = DocumentGenerationService._mock_document_body(document_type=document_type, law_summary=law_summary)
        return (
            f"# {document_type.upper()} - {site_name}\n\n"
            f"## 요청사항\n{user_prompt}\n\n"
            "## 법령 Context 기반 검토\n"
            f"{law_context}\n\n"
            f"{body}\n\n"
            "## 참고 법령 목록\n"
            f"{law_summary}"
        )

    @staticmethod
    def _mock_document_body(document_type: str, law_summary: str) -> str:
        common_note = (
            "- 제공된 법령 context에 근거해 작성합니다.\n"
            "- context에 직접 포함되지 않은 법적 의무는 단정하지 않으며, 추가 검토 필요로 표시합니다.\n"
            "- 현장 조건, 공종, 장비, 작업 높이 등 세부 조건은 추가 검토 필요입니다."
        )
        templates = {
            "tbm": (
                "## 작업개요\n- 작업 대상:\n- 작업 시간:\n- 담당자:\n\n"
                "## 주요위험요인\n- 추락\n- 협착\n- 낙하\n\n"
                f"## 안전대책\n{common_note}\n\n"
                f"## 관련법령\n{law_summary}\n\n"
                "## TBM 전달사항\n- 오늘 작업 핵심 위험과 통제 방안을 전원에게 재확인"
            ),
            "risk_assessment": (
                "## 작업공종\n- 공종명:\n- 세부 작업:\n\n"
                "## 위험요인\n- 잠재 위험요인 식별\n\n"
                "## 현재대책\n- 기존 적용중인 통제\n\n"
                f"## 개선대책\n{common_note}\n\n"
                "## 위험도\n- 발생가능성:\n- 중대성:\n- 종합 위험도:\n\n"
                f"## 관련법령\n{law_summary}"
            ),
            "work_plan": (
                "## 작업목적\n- 작업 목적 정의\n\n"
                "## 작업절차\n1. 사전 점검\n2. 작업 수행\n3. 종료 점검\n\n"
                "## 장비/인원\n- 장비:\n- 투입 인원:\n\n"
                "## 위험요소\n- 고위험 포인트\n\n"
                f"## 안전조치\n{common_note}\n\n"
                f"## 관련법령\n{law_summary}"
            ),
            "inspection_checklist": (
                "## 점검항목\n- 가설구조물\n- 전기설비\n- 개인보호구\n\n"
                "## 점검기준\n- 법령 context와 현장 기준 확인\n\n"
                "## 적합/부적합\n- 항목별 판정 기록\n\n"
                "## 조치사항\n- 부적합 항목 개선 조치 및 기한\n\n"
                f"## 관련법령\n{law_summary}"
            ),
        }
        return templates.get(
            document_type,
            f"## Recommended Safety Actions\n{common_note}\n\n## Related Legal References\n{law_summary}",
        )

    @staticmethod
    def _format_reference_list(references: list[dict]) -> str:
        if not references:
            return "- 제공된 참고 법령 없음"
        lines = []
        for reference in references:
            title = f"({reference['article_title']})" if reference.get("article_title") else ""
            effective_date = reference.get("effective_date") or "unknown"
            lines.append(f"- {reference['law_name']} {reference['article_no']}{title}, 시행일: {effective_date}")
        return "\n".join(lines)
