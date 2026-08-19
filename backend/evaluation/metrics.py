"""Pure metric calculations for retrieval evaluation."""

from __future__ import annotations

from collections.abc import Iterable


def hit_rate(rows: Iterable[dict], k: int) -> float:
    values = list(rows)
    return _mean(bool(row.get(f"hit_at_{k}")) for row in values)


def mean_reciprocal_rank(rows: Iterable[dict]) -> float:
    values = list(rows)
    return _mean(1 / int(row["rank"]) if row.get("rank") else 0 for row in values)


def average_latency_ms(rows: Iterable[dict]) -> float:
    values = list(rows)
    return _mean(float(row.get("latency_ms", 0)) for row in values)


def summarize(rows: list[dict]) -> dict[str, float | int]:
    return {
        "total_queries": len(rows),
        "hit_at_1": hit_rate(rows, 1),
        "hit_at_3": hit_rate(rows, 3),
        "hit_at_5": hit_rate(rows, 5),
        "mrr": mean_reciprocal_rank(rows),
        "average_latency_ms": average_latency_ms(rows),
    }


def _mean(values: Iterable[float | bool]) -> float:
    items = [float(value) for value in values]
    return sum(items) / len(items) if items else 0.0
