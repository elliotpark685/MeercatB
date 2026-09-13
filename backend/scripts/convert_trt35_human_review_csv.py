"""Convert a reviewed TRT35 CSV into strict Human Golden JSON input."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from pydantic import ValidationError

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crane.trt35_human_golden import HumanGoldenCell


def _required(row: dict[str, str], field: str) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise ValueError(f"missing required {field} at CSV row {row.get('row_index', '?')}/{row.get('column_index', '?')}")
    return value


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--csv", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()

    records: list[dict] = []
    with args.csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            status = _required(row, "expected_cell_status")
            capacity = row.get("expected_capacity_t", "").strip()
            records.append({
                "source_document_hash": _required(row, "source_document_hash"),
                "source_page": int(_required(row, "source_page")),
                "configuration": _required(row, "configuration"),
                "row_index": int(_required(row, "row_index")),
                "column_index": int(_required(row, "column_index")),
                "radius_m": float(_required(row, "radius_m")),
                "boom_length_m": float(_required(row, "boom_length_m")),
                "expected_cell_status": status,
                "expected_capacity_t": None if not capacity else float(capacity),
                "source_bbox": [
                    float(_required(row, "source_bbox_x0")),
                    float(_required(row, "source_bbox_y0")),
                    float(_required(row, "source_bbox_x1")),
                    float(_required(row, "source_bbox_y1")),
                ],
                "human_verified": _required(row, "human_verified").lower() == "true",
                "verified_at": row.get("verified_at", "").strip() or None,
                "verification_note": row.get("verification_note", "").strip() or None,
            })
    try:
        golden = [HumanGoldenCell.model_validate(record) for record in records]
    except ValidationError as exc:
        raise ValueError(f"CSV cannot become Human Golden JSON: {exc}") from exc
    if len(golden) != 135:
        raise ValueError(f"review CSV must contain exactly 135 rows, found {len(golden)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([cell.model_dump(mode="json") for cell in golden], indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
