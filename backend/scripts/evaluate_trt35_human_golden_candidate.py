"""Evaluate an unfrozen parser candidate against the full Human Golden."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crane.trt35_human_golden import HumanGoldenCell, validate_full_human_golden
from app.crane.trt35_validation import evaluate_full_human_golden
from app.crane.trt35_vertical_slice import Trt35VerticalSliceResult


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--golden", type=Path, required=True)
    cli.add_argument("--candidate-capture", type=Path, required=True)
    cli.add_argument("--run-name", required=True)
    cli.add_argument("--freeze-manifest", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()

    manifest = json.loads(args.freeze_manifest.read_text(encoding="utf-8"))
    golden = [HumanGoldenCell.model_validate(item) for item in json.loads(args.golden.read_text(encoding="utf-8"))]
    capture = json.loads(args.candidate_capture.read_text(encoding="utf-8"))
    if args.run_name not in capture:
        raise ValueError(f"candidate capture has no run named {args.run_name}")
    result = Trt35VerticalSliceResult.model_validate(capture[args.run_name]["result"])
    golden_errors = validate_full_human_golden(golden, expected_document_hash=manifest["source_document_hash"])
    if result.file_hash_sha256 != manifest["source_document_hash"]:
        golden_errors.append("candidate source document hash mismatch")
    metrics = evaluate_full_human_golden(result, golden)
    critical_errors = metrics.critical_error_count
    report = {
        "candidate_status": "READY_TO_FREEZE_REVIEW" if not golden_errors and critical_errors == 0 else "CANDIDATE_REJECTED",
        "approval_status": "NOT_APPROVED_UNTIL_VERSIONED_FREEZE",
        "golden_validation_errors": golden_errors,
        "metrics": metrics.model_dump(),
        "candidate_result_hash": result.canonical_content_hash,
        "baseline_result_hash": manifest["canonical_result_hash"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
