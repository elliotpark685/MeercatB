from dataclasses import dataclass


@dataclass
class QueryAnalysis:
    law_name: str
    work_types: list[str]
    risk_types: list[str]
    action_types: list[str]


class QueryAnalyzer:
    LAW_NAMES = [
        "산업안전보건법",
        "산업안전보건기준에 관한 규칙",
    ]
    WORK_TYPES = ["비계", "굴착", "철골", "해체", "밀폐공간", "전기", "양중", "지게차", "크레인", "보호구"]
    RISK_TYPES = ["추락", "붕괴", "감전", "화재폭발", "질식", "협착", "낙하물", "전도"]
    ACTION_TYPES = ["설치", "점검", "교육", "보호구", "작업중지", "출입금지", "작업계획서"]

    def analyze(self, query: str) -> QueryAnalysis:
        law_name = "unknown"
        for candidate in self.LAW_NAMES:
            if candidate in query:
                law_name = candidate
                break

        work_types = [item for item in self.WORK_TYPES if item in query]
        risk_types = [item for item in self.RISK_TYPES if item in query]
        action_types = [item for item in self.ACTION_TYPES if item in query]
        return QueryAnalysis(
            law_name=law_name,
            work_types=work_types,
            risk_types=risk_types,
            action_types=action_types,
        )

