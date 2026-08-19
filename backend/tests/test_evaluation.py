import json
from types import SimpleNamespace

from evaluation.evaluator import _find_rank, validate_scoped_dataset
from evaluation.metrics import summarize
from evaluation.run_evaluation import _serialize_result_row


def test_metrics_calculate_scoped_hit_mrr_and_latency_only():
    result = summarize([
        {"rank": 1, "hit_at_1": True, "hit_at_3": True, "hit_at_5": True, "latency_ms": 100},
        {"rank": 2, "hit_at_1": False, "hit_at_3": True, "hit_at_5": True, "latency_ms": 300},
        {"rank": None, "hit_at_1": False, "hit_at_3": False, "hit_at_5": False, "latency_ms": 200},
    ])

    assert result == {
        "total_queries": 3,
        "hit_at_1": 1 / 3,
        "hit_at_3": 2 / 3,
        "hit_at_5": 2 / 3,
        "mrr": 0.5,
        "average_latency_ms": 200,
    }


def test_rank_match_prefers_article_id_then_law_and_article_number():
    expected = {
        "expected_law": "산업안전보건기준에 관한 규칙",
        "expected_article": "제42조",
        "expected_article_id": 7,
    }
    retrieved = [
        {"article_id": 99, "law_name": "산업안전보건기준에 관한 규칙", "article_no": "제42조"},
        {"article_id": 7, "law_name": "다른 법령", "article_no": "제42조"},
    ]

    assert _find_rank(expected, retrieved) == 2


def test_rank_match_falls_back_to_law_and_article_when_id_is_unavailable():
    expected = {
        "expected_law": "산업안전보건기준에 관한 규칙",
        "expected_article": "제42조",
        "expected_article_id": None,
    }
    retrieved = [{"article_id": 99, "law_name": "산업안전보건기준에 관한 규칙", "article_no": "제42조"}]

    assert _find_rank(expected, retrieved) == 1


class _ValidationResult:
    def __init__(self, row):
        self.row = row

    def one_or_none(self):
        return self.row


class _ValidationDb:
    def __init__(self, rows):
        self.rows = iter(rows)

    def execute(self, _statement):
        return _ValidationResult(next(self.rows))


def test_dataset_validation_reports_missing_id_and_vector():
    dataset = [
        {"id": 1, "expected_article_id": None, "expected_article": "제1조"},
        {"id": 2, "expected_article_id": 2, "expected_article": "제2조"},
    ]
    issues = validate_scoped_dataset(
        _ValidationDb([SimpleNamespace(chunk_count=1, embedding_count=0)]),
        dataset,
        "산업안전보건기준에 관한 규칙",
    )

    assert [(issue.dataset_id, issue.reason) for issue in issues] == [
        (1, "expected_article_id_missing"),
        (2, "embedding_vector_missing"),
    ]


def test_result_serialization_preserves_json_fields_for_csv():
    serialized = _serialize_result_row({
        "id": 1, "query": "질의", "category": "비계", "expected_law": "규칙",
        "expected_article": "제1조", "expected_article_id": 10,
        "expected_keywords": ["비계"], "rank": 1, "hit_at_1": True,
        "hit_at_3": True, "hit_at_5": True, "latency_ms": 12.3,
        "retrieved_articles": [{"article_id": 10}],
    })

    assert json.loads(serialized["expected_keywords"]) == ["비계"]
    assert json.loads(serialized["retrieved_articles"]) == [{"article_id": 10}]
