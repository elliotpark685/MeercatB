"""Validate a full independently reviewed Golden and compare frozen OCR output.

The input Golden must be a JSON array of 135 HumanGoldenCell records.  This
script intentionally rejects the AI review-candidate file until a human has
completed every record.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crane.trt35_human_golden import HumanGoldenCell, validate_full_human_golden
from app.crane.trt35_validation import evaluate_full_human_golden, human_golden_acceptance
from app.crane.trt35_vertical_slice import Trt35VerticalSliceResult


def _load_result(payload: object) -> Trt35VerticalSliceResult:
    if not isinstance(payload, dict):
        raise ValueError("frozen capture must be a JSON object")
    if "result" in payload:
        payload = payload["result"]
    return Trt35VerticalSliceResult.model_validate(payload)


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--golden", type=Path, required=True)
    cli.add_argument("--frozen-capture", type=Path, required=True)
    cli.add_argument("--freeze-manifest", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()

    manifest = json.loads(args.freeze_manifest.read_text(encoding="utf-8"))
    golden = [HumanGoldenCell.model_validate(item) for item in json.loads(args.golden.read_text(encoding="utf-8"))]
    capture = json.loads(args.frozen_capture.read_text(encoding="utf-8"))
    # Experiment files can contain named runs; frozen captures must name one.
    if "result" not in capture and "baseline" in capture:
        capture = capture["baseline"]
    result = _load_result(capture)

    golden_errors = validate_full_human_golden(
        golden,
        expected_document_hash=manifest["source_document_hash"],
        expected_cell_count=manifest["result_counts"]["total"],
        expected_configuration=manifest["table_segment"],
    )
    if result.file_hash_sha256 != manifest["source_document_hash"]:
        golden_errors.append("frozen parser source document hash mismatch")
    if result.canonical_content_hash != manifest["canonical_result_hash"]:
        golden_errors.append("frozen parser canonical result hash mismatch")

    metrics = evaluate_full_human_golden(result, golden)
    accepted = human_golden_acceptance(metrics, golden_errors=golden_errors)
    report = {
        "profile": "TEREX_TRT35_OCR_V1",
        "slice": manifest["table_segment"],
        "freeze_status": manifest["freeze_status"],
        "acceptance_status": "HUMAN_GOLDEN_GATE_PASSED" if accepted else "PARSER_VALIDATION_PENDING",
        "golden_validation_errors": golden_errors,
        "metrics": metrics.model_dump(),
        "acceptance_invariants": {
            "false_available_must_be_zero": metrics.false_available == 0,
            "wrong_numeric_capacity_must_be_zero": metrics.wrong_numeric_capacity == 0,
            "wrong_cell_association_must_be_zero": metrics.wrong_cell_association == 0,
            "false_not_available_must_be_zero": metrics.false_not_available == 0,
            "cross_configuration_must_be_zero": metrics.cross_configuration == 0,
            "unresolved_zero_not_required": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
