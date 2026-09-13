"""Evaluate page-12 On Tires / max. 2 km/h against its full Human Golden."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crane.trt35_human_golden import HumanGoldenCell, validate_full_human_golden
from app.crane.trt35_validation import evaluate_full_human_golden
from app.crane.trt35_vertical_slice import Trt35VerticalSliceResult


CONFIGURATION = "PAGE_12_LOWER_ON_TIRES_0_MAX_2_KMH"
EXPECTED_CELLS = 51


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--golden", type=Path, required=True)
    cli.add_argument("--candidate-capture", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()

    golden = [HumanGoldenCell.model_validate(value) for value in json.loads(args.golden.read_text(encoding="utf-8"))]
    result = Trt35VerticalSliceResult.model_validate(json.loads(args.candidate_capture.read_text(encoding="utf-8"))["result"])
    golden_errors = validate_full_human_golden(
        golden,
        expected_document_hash=result.file_hash_sha256 or "",
        expected_cell_count=EXPECTED_CELLS,
        expected_configuration=CONFIGURATION,
    )
    metrics = evaluate_full_human_golden(result, golden)
    report = {
        "candidate_status": "READY_TO_FREEZE_REVIEW" if not golden_errors and metrics.critical_error_count == 0 else "CANDIDATE_REJECTED",
        "approval_status": "NOT_APPROVED_UNTIL_VERSIONED_FREEZE",
        "configuration": CONFIGURATION,
        "golden_validation_errors": golden_errors,
        "metrics": metrics.model_dump(),
        "candidate_result_hash": result.canonical_content_hash,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
