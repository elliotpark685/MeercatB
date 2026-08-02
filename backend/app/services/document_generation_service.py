import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.generated_document import GeneratedDocument
from app.models.law_search_log import LawSearchLog  # noqa: F401 - mapper registration
from app.models.site import Site
from app.models.safety_quiz import SafetyQuiz  # noqa: F401 - mapper registration
from app.models.user import User  # noqa: F401 - ensures SQLAlchemy mapper registration
from app.schemas.kosha import KoshaCategory
from app.services.administrative_rule_search_service import AdministrativeRuleSearchService
from app.services.kosha_search_service import KoshaSearchService
from app.services.law_search_service import LawSearchService


class DocumentGenerationService:
    """Generates document drafts grounded in law, administrative-rule, and KOSHA context."""

    MODEL_NAME = "gpt-4o-mini"

    def __init__(
        self,
        db: Session,
        law_search_service: LawSearchService,
        kosha_search_service: KoshaSearchService | None = None,
        administrative_rule_search_service: AdministrativeRuleSearchService | None = None,
    ) -> None:
        self.db = db
        self.law_search_service = law_search_service
        self.kosha_search_service = kosha_search_service or KoshaSearchService()
        self.administrative_rule_search_service = (
            administrative_rule_search_service or AdministrativeRuleSearchService(db)
        )
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def generate(
        self,
        site_id: int,
        user_id: int | None,
        document_type: str,
        workplace_name: str,
        prompt: str,
        work_title: str | None = None,
        safety_keywords: list[str] | None = None,
        equipment_tools: list[str] | None = None,
        law_names: list[str] | None = None,
        kosha_categories: list[str] | None = None,
    ) -> GeneratedDocument:
        site = self.db.get(Site, site_id)
        if site is None:
            raise ValueError("Site not found")

        normalized_type = document_type.strip().lower()
        normalized_work_title = (work_title or prompt or site.name).strip() or site.name
        normalized_workplace_name = workplace_name.strip()
        normalized_keywords = self._normalize_terms(safety_keywords)
        normalized_equipment_tools = self._normalize_terms(equipment_tools)
        normalized_law_names = self._normalize_terms(law_names)
        normalized_kosha_categories = self._normalize_terms(kosha_categories)
        search_query = self._build_search_query(
            normalized_workplace_name, normalized_work_title, normalized_keywords, normalized_equipment_tools, prompt
        )

        search_bundle = self._search_for_generation(
            prompt=search_query,
            user_id=user_id,
            site_id=site_id,
            law_names=normalized_law_names or None,
        )
        references = self._build_references(self._extract_reference_items(search_bundle), reference_type="법령")
        administrative_rule_query = " ".join(normalized_keywords)
        if administrative_rule_query:
            administrative_rule_bundle = self.administrative_rule_search_service.search(
                query=administrative_rule_query,
                top_k=3,
                user_id=user_id,
                site_id=site_id,
            )
            references.extend(
                self._build_references(
                    self._extract_reference_items(administrative_rule_bundle),
                    reference_type="행정규칙",
                )
            )
        law_context = self._build_law_context(references)
        kosha_context = self._build_kosha_context(
            query=search_query,
            categories=normalized_kosha_categories,
            work_title=normalized_work_title,
            safety_keywords=normalized_keywords,
        )
        generation_prompt = self._build_generation_prompt(
            document_type=normalized_type,
            workplace_name=normalized_workplace_name,
            work_title=normalized_work_title,
            safety_keywords=normalized_keywords,
            equipment_tools=normalized_equipment_tools,
            user_prompt=prompt,
            law_context=law_context,
            kosha_context=kosha_context,
            selected_laws=normalized_law_names,
            selected_kosha_categories=normalized_kosha_categories,
        )
        generated_text = self._generate_text(
            document_type=normalized_type,
            workplace_name=normalized_workplace_name,
            work_title=normalized_work_title,
            safety_keywords=normalized_keywords,
            equipment_tools=normalized_equipment_tools,
            user_prompt=prompt,
            law_context=law_context,
            kosha_context=kosha_context,
            generation_prompt=generation_prompt,
            references=references,
        )

        references_json = json.dumps(references, ensure_ascii=False)
        document = GeneratedDocument(
            site_id=site_id,
            created_by=user_id,
            document_type=normalized_type,
            title=f"{normalized_work_title} - {normalized_type.upper()}",
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
    def _build_references(search_results, reference_type: str = "법령") -> list[dict]:
        references: list[dict] = []
        for item in search_results:
            article_obj = getattr(item, "article", None)
            document_obj = getattr(item, "document", None)
            full_text = getattr(item, "content_preview", None) or getattr(item, "chunk_text", None) or getattr(
                item, "content", None
            )
            if article_obj is not None:
                full_text = item.chunk.chunk_text if getattr(item, "chunk", None) is not None else (
                    article_obj.article_text or article_obj.full_text or article_obj.content or full_text or ""
                )
            references.append(
                {
                    "law_name": getattr(item, "law_name", None)
                    or getattr(item, "source_name", None)
                    or getattr(document_obj, "law_name", None)
                    or getattr(document_obj, "title", None)
                    or getattr(article_obj, "law_name", None),
                    "article_no": getattr(item, "article_no", None)
                    or getattr(article_obj, "article_no", None)
                    or getattr(article_obj, "article_number", None),
                    "article_title": getattr(item, "title", None)
                    or getattr(item, "article_title", None)
                    or getattr(article_obj, "article_title", None)
                    or getattr(article_obj, "title", None),
                    "chunk_text": full_text or "",
                    "effective_date": (
                        DocumentGenerationService._date_to_string(getattr(item, "effective_date", None))
                        or DocumentGenerationService._date_to_string(getattr(article_obj, "effective_date", None))
                    ),
                    "source_url": getattr(document_obj, "source_url", None) or getattr(item, "source_url", None),
                    "score": getattr(item, "score", 0.0),
                    "article_id": getattr(item, "article_id", None) or getattr(article_obj, "id", None),
                    "chunk_id": getattr(getattr(item, "chunk", None), "id", None),
                    "reference_type": reference_type,
                }
            )
        return references

    @staticmethod
    def _extract_reference_items(search_result: object) -> list[object]:
        if hasattr(search_result, "candidates") and getattr(search_result, "candidates") is not None:
            return list(getattr(search_result, "candidates"))
        if hasattr(search_result, "results") and getattr(search_result, "results") is not None:
            return list(getattr(search_result, "results"))
        return []

    @staticmethod
    def _date_to_string(value) -> str | None:
        return value.isoformat() if hasattr(value, "isoformat") else value

    def _search_for_generation(self, prompt: str, user_id: int | None, site_id: int, law_names: list[str] | None = None) -> object:
        if hasattr(self.law_search_service, "search_for_generation"):
            return self.law_search_service.search_for_generation(
                query=prompt,
                top_k=5,
                validate_latest=False,
                user_id=user_id,
                site_id=site_id,
                law_names=law_names,
            )
        return self.law_search_service.search(
            prompt,
            top_k=5,
            validate_latest=False,
            user_id=user_id,
            site_id=site_id,
            law_names=law_names,
        )

    @staticmethod
    def _normalize_terms(values: list[str] | None) -> list[str]:
        if not values:
            return []
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = " ".join(str(value).split()).strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            normalized.append(cleaned)
        return normalized

    @staticmethod
    def _build_search_query(
        workplace_name: str, work_title: str, safety_keywords: list[str], equipment_tools: list[str], prompt: str
    ) -> str:
        parts = [workplace_name, work_title, *safety_keywords, *equipment_tools, prompt]
        return " ".join(part.strip() for part in parts if part and part.strip())

    @staticmethod
    def _build_law_context(references: list[dict]) -> str:
        if not references:
            return "법령 context가 없습니다."

        lines: list[str] = []
        for index, reference in enumerate(references, start=1):
            title = reference.get("article_title") or ""
            effective_date = reference.get("effective_date") or "unknown"
            lines.append(
                "\n".join(
                    [
                        f"[{index}] [{reference.get('reference_type', '법령')}] {reference['law_name']} {reference['article_no']} {title}",
                        f"시행일: {effective_date}",
                        f"내용: {reference['chunk_text']}",
                    ]
                )
            )
        return "\n\n".join(lines)

    def _build_kosha_context(
        self,
        query: str,
        categories: list[str],
        work_title: str,
        safety_keywords: list[str],
    ) -> str:
        valid_categories: list[KoshaCategory] = []
        for category in categories:
            try:
                valid_categories.append(KoshaCategory(category))
            except ValueError:
                continue

        if not valid_categories:
            return "KOSHA Guide context가 없습니다."

        lookup_query = " ".join([work_title, *safety_keywords]).strip() or query
        sections: list[str] = []
        for category in valid_categories:
            result = self.kosha_search_service.search(
                query=lookup_query,
                category=category,
                page=1,
                size=3,
            )
            if not result.results:
                continue

            lines = [f"[{category.value}] {result.query}"]
            for index, item in enumerate(result.results, start=1):
                preview = " ".join(item.content.split())
                if len(preview) > 240:
                    preview = f"{preview[:240].rstrip()}..."
                lines.append(
                    f"{index}. {item.title} | {preview} | score={item.score:.3f} | category={item.category}"
                )
            sections.append("\n".join(lines))

        if not sections:
            return "KOSHA Guide context가 없습니다."

        return "\n\n".join(sections)

    @classmethod
    def _build_generation_prompt(
        cls,
        document_type: str,
        workplace_name: str,
        work_title: str,
        safety_keywords: list[str],
        equipment_tools: list[str],
        user_prompt: str,
        law_context: str,
        kosha_context: str,
        selected_laws: list[str],
        selected_kosha_categories: list[str],
    ) -> str:
        return (
            "You are a Korean construction safety document assistant.\n"
            f"Workplace: {workplace_name}\n"
            f"Document type: {document_type}\n"
            f"Work title: {work_title}\n"
            f"Safety keywords: {', '.join(safety_keywords) if safety_keywords else 'none'}\n"
            f"Equipment and tools: {', '.join(equipment_tools) if equipment_tools else 'none'}\n"
            f"Selected laws: {', '.join(selected_laws) if selected_laws else 'none'}\n"
            f"Selected KOSHA categories: {', '.join(selected_kosha_categories) if selected_kosha_categories else 'none'}\n\n"
            "Mandatory constraints:\n"
            "- Use the supplied law context when applicable.\n"
            "- Treat administrative-rule context as an enforcement or inspection procedure; distinguish it from statutes.\n"
            "- Do not invent ungrounded legal claims.\n"
            "- Use the KOSHA context as supporting guidance only.\n"
            "- Keep the output specific to the workplace, work title, safety keywords, and equipment/tools.\n\n"
            f"User request:\n{user_prompt}\n\n"
            f"Law context:\n{law_context}\n\n"
            f"KOSHA context:\n{kosha_context}\n"
        )

    def _generate_text(
        self,
        document_type: str,
        workplace_name: str,
        work_title: str,
        safety_keywords: list[str],
        equipment_tools: list[str],
        user_prompt: str,
        law_context: str,
        kosha_context: str,
        generation_prompt: str,
        references: list[dict],
    ) -> str:
        if self._client is None:
            return self._mock_response(
                document_type=document_type,
                workplace_name=workplace_name,
                work_title=work_title,
                safety_keywords=safety_keywords,
                equipment_tools=equipment_tools,
                user_prompt=user_prompt,
                law_context=law_context,
                kosha_context=kosha_context,
                references=references,
            )

        try:
            response = self._client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You draft Korean construction safety documents grounded in supplied law and guide context.",
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
            workplace_name=workplace_name,
            work_title=work_title,
            safety_keywords=safety_keywords,
            equipment_tools=equipment_tools,
            user_prompt=user_prompt,
            law_context=law_context,
            kosha_context=kosha_context,
            references=references,
        )

    @staticmethod
    def _mock_response(
        document_type: str,
        workplace_name: str,
        work_title: str,
        safety_keywords: list[str],
        equipment_tools: list[str],
        user_prompt: str,
        law_context: str,
        kosha_context: str,
        references: list[dict],
    ) -> str:
        law_summary = DocumentGenerationService._format_reference_list(references)
        body = DocumentGenerationService._mock_document_body(document_type=document_type, law_summary=law_summary)
        keyword_text = ", ".join(safety_keywords) if safety_keywords else "-"
        equipment_tools_text = ", ".join(equipment_tools) if equipment_tools else "-"
        return (
            f"# {work_title} - {document_type.upper()}\n\n"
            f"작업장소: {workplace_name}\n\n"
            f"## 작업명\n{work_title}\n\n"
            f"## 안전 키워드\n{keyword_text}\n\n"
            f"## 사용 장비 및 도구\n{equipment_tools_text}\n\n"
            f"## 작업 설명\n{user_prompt}\n\n"
            "## 법령 Context 기반 검토\n"
            f"{law_context}\n\n"
            "## KOSHA Guide Context\n"
            f"{kosha_context}\n\n"
            f"{body}\n\n"
            "## 참고 법령 목록\n"
            f"{law_summary}"
        )

    @staticmethod
    def _mock_document_body(document_type: str, law_summary: str) -> str:
        common_note = (
            "- 현장 조건과 장비 상태를 작업 전에 다시 확인합니다.\n"
            "- 법령 context에 직접 포함되지 않은 내용은 추가 확인이 필요합니다.\n"
            "- 작업 높이, 협착, 추락, 낙하 위험은 별도 점검합니다."
        )
        templates = {
            "tbm": (
                "## 작업개요\n- 작업 목적\n- 작업 시간\n- 참여 인원\n\n"
                "## 주요위험요인\n- 추락\n- 협착\n- 낙하\n\n"
                f"## 안전대책\n{common_note}\n\n"
                f"## 관련법령\n{law_summary}\n\n"
                "## TBM 전달사항\n- 오늘 작업 위험 공유\n- 보호구 및 작업 전 점검\n- 작업 전 안전 확인"
            ),
            "risk_assessment": (
                "## 작업공종\n- 공정명\n- 주요 작업\n\n"
                "## 위험요인\n- 잠재 위험요인 정리\n\n"
                "## 현재대책\n- 기존 적용 중인 통제\n\n"
                f"## 개선대책\n{common_note}\n\n"
                "## 위험도\n- 발생가능성\n- 중대성\n- 종합 위험도\n\n"
                f"## 관련법령\n{law_summary}"
            ),
            "work_plan": (
                "## 작업목적\n- 작업 목적 정의\n\n"
                "## 작업절차\n1. 사전 준비\n2. 작업 수행\n3. 마무리 점검\n\n"
                "## 장비/인원\n- 인원\n- 장비\n\n"
                "## 위험요소\n- 고소 작업 여부\n\n"
                f"## 안전조치\n{common_note}\n\n"
                f"## 관련법령\n{law_summary}"
            ),
            "inspection_checklist": (
                "## 점검항목\n- 구조물 상태\n- 작업 장비\n- 개인보호구\n\n"
                "## 점검기준\n- 법령 context 기준 반영\n\n"
                "## 적합/부적합\n- 항목별 판정 기록\n\n"
                "## 조치사항\n- 부적합 항목 개선 조치 및 확인\n\n"
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
            return "- 참고 법령 없음"

        lines: list[str] = []
        for reference in references:
            title = f"({reference['article_title']})" if reference.get("article_title") else ""
            effective_date = reference.get("effective_date") or "unknown"
            reference_type = reference.get("reference_type", "법령")
            lines.append(f"- [{reference_type}] {reference['law_name']} {reference['article_no']}{title}, 시행일 {effective_date}")
        return "\n".join(lines)
