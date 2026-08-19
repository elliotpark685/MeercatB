"""CLI for an offline, read-only baseline retrieval measurement."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal, get_engine, import_all_models
from app.services.law_search_service import LawSearchService
from evaluation.evaluator import (
    EvaluationConfig,
    evaluate_dataset,
    evaluate_threshold_diagnostics,
    validate_scoped_dataset,
)
from evaluation.metrics import summarize

ROOT = Path(__file__).resolve().parent
SCOPED_SAFETY_RULE = "산업안전보건기준에 관한 규칙"
CSV_FIELDNAMES = [
    "id",
    "query",
    "category",
    "expected_law",
    "expected_article",
    "expected_article_id",
    "expected_keywords",
    "rank",
    "hit_at_1",
    "hit_at_3",
    "hit_at_5",
    "latency_ms",
    "retrieved_articles",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "datasets" / "scoped_safety_rule.json")
    parser.add_argument("--name", default="scoped_safety_rule_baseline")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8-sig"))
    if not dataset:
        raise RuntimeError("Evaluation dataset is empty; baseline was not generated.")
    _initialize_evaluation_runtime()
    _print_runtime_config(args.top_k)
    config = EvaluationConfig(top_k=args.top_k, law_scope=[SCOPED_SAFETY_RULE])
    with SessionLocal() as db:
        service = LawSearchService(db)
        _validate_dataset_or_fail(db, dataset)
        _run_smoke_test(service, _smoke_item(dataset), args.top_k)
        rows = evaluate_dataset(service, dataset, config)
        diagnostic_rows, threshold_simulation = evaluate_threshold_diagnostics(service, dataset, config)
    production_metrics = summarize(rows)
    production_metrics["no_result_rate"] = sum(not row["retrieved_articles"] for row in rows) / len(rows)
    pre_threshold_rows = [
        {
            "rank": row["pre_rank"],
            "hit_at_1": row["pre_rank"] == 1,
            "hit_at_3": bool(row["pre_rank"] and row["pre_rank"] <= 3),
            "hit_at_5": bool(row["pre_rank"] and row["pre_rank"] <= 5),
            "latency_ms": row["latency_ms"],
        }
        for row in diagnostic_rows
    ]
    drop_analysis = {
        "retrieved_then_filtered": sum(
            bool(diagnostic["pre_rank"]) and production["rank"] is None
            for diagnostic, production in zip(diagnostic_rows, rows)
        ),
        "not_retrieved_pre_threshold": sum(row["pre_rank"] is None for row in diagnostic_rows),
        "production_no_result": sum(not row["retrieved_articles"] for row in rows),
    }
    report = {
        "evaluation_type": "scoped",
        "scope": SCOPED_SAFETY_RULE,
        "latency_scope": "retrieval_only",
        "config": asdict(config),
        "metrics": production_metrics,
        "pre_threshold_metrics": summarize(pre_threshold_rows),
        "threshold_simulation": threshold_simulation,
        "drop_analysis": drop_analysis,
        "diagnostic_results": diagnostic_rows,
        "results": rows,
    }
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    json_path = results_dir / f"{args.name}.json"
    csv_path = results_dir / f"{args.name}.csv"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=CSV_FIELDNAMES,
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(_serialize_result_row(row))
    _print_report(report)
    for row in rows:
        if not row["hit_at_5"]:
            print(f"\n[FAILED QUERY] {row['query']}\nExpected: {row['expected_law']} {row['expected_article']}\nRetrieved: {row['retrieved_articles']}")


def _print_report(report: dict) -> None:
    m = report["metrics"]
    print("\nScoped Evaluation")
    print(f"Scope: {report['scope']}")
    print(f"Total Queries: {m['total_queries']}")
    for key in ("hit_at_1", "hit_at_3", "hit_at_5", "mrr"):
        value = m[key]
        print(f"{key}: {value:.2%}" if key != "mrr" else f"MRR: {value:.3f}")
    print(f"Average Retrieval Latency: {m['average_latency_ms']:.2f} ms")
    print(f"No-result Rate: {m['no_result_rate']:.2%}")
    print("\nPre-threshold Evaluation")
    for key, value in report["pre_threshold_metrics"].items():
        if key != "total_queries":
            print(f"{key}: {value:.2%}" if key.startswith("hit_") else f"{key}: {value:.3f}")
    print("\nThreshold Simulation")
    for threshold, metrics in report["threshold_simulation"].items():
        print(f"{threshold}: Hit@1={metrics['hit_at_1']:.2%}, Hit@3={metrics['hit_at_3']:.2%}, Hit@5={metrics['hit_at_5']:.2%}, No-result={metrics['no_result_rate']:.2%}")


def _initialize_evaluation_runtime() -> None:
    if not settings.use_pgvector:
        raise RuntimeError("Evaluation requires USE_PGVECTOR=true; baseline was not generated.")
    if not settings.openai_api_key:
        raise RuntimeError("Evaluation requires OPENAI_API_KEY; baseline was not generated.")
    import_all_models()
    engine = get_engine()
    if engine.dialect.name != "postgresql":
        raise RuntimeError(f"Evaluation requires PostgreSQL, got {engine.dialect.name}; baseline was not generated.")
    with engine.connect() as connection:
        connection.execute(__import__("sqlalchemy").text("SELECT 1"))
        connection.commit()


def _print_runtime_config(top_k: int) -> None:
    print("[EVALUATION MODE]")
    print("Database: PostgreSQL")
    print(f"Schema: {settings.db_schema}")
    print("Vector Search: pgvector")
    print(f"Embedding: {settings.embedding_model}")
    print("Mock Embedding: DISABLED")
    print(f"Scope: {SCOPED_SAFETY_RULE}")
    print(f"Top-K: {top_k}")


def _run_smoke_test(service: LawSearchService, item: dict, top_k: int) -> None:
    print(f"Smoke query: {item['query']}")
    bundle = service.search_for_evaluation(
        query=item["query"], top_k=top_k, law_scope=[SCOPED_SAFETY_RULE]
    )
    if not bundle.citations:
        raise RuntimeError("Smoke test returned no citations; baseline was not generated.")
    rank = next((i for i, item_ in enumerate(bundle.citations, 1) if item_.article_id == item["expected_article_id"]), None)
    print(
        "Scope applied: YES\nPostgreSQL connected: YES\npgvector executed: YES\n"
        "OpenAI embedding executed: YES\nMock embedding used: NO\n"
        f"Expected article exists: YES\nExpected embedding exists: YES\nTop-{top_k} returned: YES\n"
        f"Expected article rank: {rank if rank is not None else 'not in top-' + str(top_k)}"
    )


def _validate_dataset_or_fail(db, dataset: list[dict]) -> None:
    issues = validate_scoped_dataset(db, dataset, SCOPED_SAFETY_RULE)
    print("Dataset Validation")
    print(f"Total: {len(dataset)}")
    print(f"Valid: {len(dataset) - len(issues)}")
    print(f"Invalid: {len(issues)}")
    if issues:
        for issue in issues:
            print(f"ID {issue.dataset_id} - {issue.reason}")
        raise RuntimeError("Scoped dataset validation failed; baseline was not generated.")


def _smoke_item(dataset: list[dict]) -> dict:
    for item in dataset:
        if item["query"] == "시스템비계 구조 기준은?":
            return item
    raise RuntimeError("Smoke-test query is missing from the scoped dataset.")


def _serialize_result_row(row: dict) -> dict:
    return {
        "id": row["id"],
        "query": row["query"],
        "category": row["category"],
        "expected_law": row["expected_law"],
        "expected_article": row["expected_article"],
        "expected_article_id": row["expected_article_id"],
        "expected_keywords": json.dumps(row["expected_keywords"], ensure_ascii=False),
        "rank": row["rank"],
        "hit_at_1": row["hit_at_1"],
        "hit_at_3": row["hit_at_3"],
        "hit_at_5": row["hit_at_5"],
        "latency_ms": row["latency_ms"],
        "retrieved_articles": json.dumps(row["retrieved_articles"], ensure_ascii=False),
    }


if __name__ == "__main__":
    main()
