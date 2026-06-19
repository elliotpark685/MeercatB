"""KOSHA GUIDE 검색결과 AI 요약 서비스.

검색결과 상위 3건을 받아 GPT-4o-mini로 핵심내용/적용대상/현장적용방법/주의사항/관련법령을 생성한다.
검색과 분리된 온디맨드 호출 (프론트 '요약' 버튼) — 검색 응답 시간에 영향 없음.
"""
from __future__ import annotations

import json

from openai import OpenAI

from app.core.config import settings
from app.schemas.kosha import KoshaResultItem, KoshaSummaryResponse

MODEL_NAME = "gpt-4o-mini"

_SYSTEM_PROMPT = (
    "당신은 한국 건설 현장 산업안전보건 전문가입니다. "
    "주어진 KOSHA GUIDE 검색결과만 근거로 답하고, 근거 없는 내용은 추가 검토 필요로 표시하세요. "
    "반드시 JSON으로만 응답하세요."
)

_RESPONSE_KEYS = [
    "core_content",
    "applicable_scope",
    "field_application",
    "precautions",
    "related_regulations",
]


class KoshaSummaryService:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def summarize(self, query: str, items: list[KoshaResultItem]) -> KoshaSummaryResponse:
        if self._client is None:
            return _mock_summary(query, items)

        prompt = _build_prompt(query, items)
        try:
            response = self._client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            data = json.loads(content) if content else {}
            if all(key in data for key in _RESPONSE_KEYS):
                return KoshaSummaryResponse(query=query, **{k: str(data[k]) for k in _RESPONSE_KEYS})
        except Exception:
            pass
        return _mock_summary(query, items)


def _build_prompt(query: str, items: list[KoshaResultItem]) -> str:
    lines = [f"검색어: {query}", "", "검색결과:"]
    for idx, item in enumerate(items, start=1):
        lines.append(f"[{idx}] {item.title} ({item.category})\n{item.content[:1500]}")
    lines.append(
        "\n위 검색결과를 바탕으로 아래 키를 가진 JSON으로 답하세요: "
        + ", ".join(_RESPONSE_KEYS)
        + ". 각 값은 한국어 문장(들)로 작성하세요."
    )
    return "\n\n".join(lines)


def _mock_summary(query: str, items: list[KoshaResultItem]) -> KoshaSummaryResponse:
    if not items:
        empty = "제공된 검색결과가 없어 요약할 수 없습니다. 추가 검토 필요."
        return KoshaSummaryResponse(
            query=query,
            core_content=empty,
            applicable_scope=empty,
            field_application=empty,
            precautions=empty,
            related_regulations=empty,
        )
    titles = ", ".join(item.title for item in items if item.title)
    return KoshaSummaryResponse(
        query=query,
        core_content=f"'{query}' 관련 KOSHA GUIDE {len(items)}건({titles})의 핵심 내용입니다. 추가 검토 필요.",
        applicable_scope="검색결과 본문을 참고해 적용 대상을 확인하세요. 추가 검토 필요.",
        field_application="현장 적용 방법은 검색결과 원문을 확인 후 적용하세요. 추가 검토 필요.",
        precautions="검색결과에 명시된 주의사항 외 현장별 위험요인은 별도 평가가 필요합니다.",
        related_regulations="검색결과 카드의 원문 링크에서 관련 법령을 확인하세요.",
    )
