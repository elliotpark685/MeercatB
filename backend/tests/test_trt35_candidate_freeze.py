"""CI gate for the versioned TRT35 page-11 candidate freeze."""

from __future__ import annotations

import json
from pathlib import Path

from app.crane.trt35_human_golden import HumanGoldenCell, validate_full_human_golden
from app.crane.trt35_validation import evaluate_full_human_golden
from app.crane.trt35_vertical_slice import Trt35VerticalSliceResult


ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / "evaluation" / "baselines"
DATASETS = ROOT / "evaluation" / "datasets"


def test_v011_candidate_freeze_matches_full_human_golden() -> None:
    manifest = json.loads((BASELINES / "trt35_page11_100_v011_tight_crop_candidate_freeze.json").read_text(encoding="utf-8"))
    capture = json.loads((BASELINES / "trt35_page11_100_v011_tight_crop_candidate_capture.json").read_text(encoding="utf-8"))
    golden = [
        HumanGoldenCell.model_validate(value)
        for value in json.loads((DATASETS / "trt35_page11_100_full_human_golden.json").read_text(encoding="utf-8"))
    ]

    assert validate_full_human_golden(golden, expected_document_hash=manifest["source_document_hash"]) == []
    assert capture["capture_role"] == "FROZEN_PARSER_OUTPUT"
    assert capture["runner"] == manifest["runner"] == "tight-crop"
    result = Trt35VerticalSliceResult.model_validate(capture["result"])
    assert result.file_hash_sha256 == manifest["source_document_hash"]
    assert result.parser_version == manifest["parser_version"]
    assert result.canonical_content_hash == manifest["canonical_result_hash"]

    metrics = evaluate_full_human_golden(result, golden)
    assert metrics.critical_error_count == 0
    assert metrics.unresolved == manifest["result_counts"]["unresolved"] == 13


def test_page12_on_tires_2kmh_v011_candidate_freeze_matches_full_human_golden() -> None:
    manifest = json.loads(
        (BASELINES / "trt35_page12_on_tires_2kmh_v011_tight_crop_candidate_freeze.json").read_text(encoding="utf-8")
    )
    capture = json.loads(
        (BASELINES / "trt35_page12_on_tires_2kmh_v011_tight_crop_candidate_capture.json").read_text(encoding="utf-8")
    )
    golden = [
        HumanGoldenCell.model_validate(value)
        for value in json.loads(
            (DATASETS / "trt35_page12_on_tires_2kmh_full_human_golden.json").read_text(encoding="utf-8")
        )
    ]

    assert validate_full_human_golden(
        golden,
        expected_document_hash=manifest["source_document_hash"],
        expected_cell_count=51,
        expected_configuration=manifest["table_segment"],
    ) == []
    assert capture["capture_role"] == "FROZEN_PARSER_OUTPUT"
    assert capture["runner"] == manifest["runner"] == "tight-crop"
    result = Trt35VerticalSliceResult.model_validate(capture["result"])
    assert result.file_hash_sha256 == manifest["source_document_hash"]
    assert result.parser_version == manifest["parser_version"]
    assert result.canonical_content_hash == manifest["canonical_result_hash"]

    metrics = evaluate_full_human_golden(result, golden)
    assert metrics.critical_error_count == 0
    assert metrics.unresolved == manifest["result_counts"]["unresolved"] == 18


def test_page15_lattice_jib_0_v011_candidate_freeze_matches_full_human_golden() -> None:
    manifest = json.loads(
        (BASELINES / "trt35_page15_lattice_jib_0_v011_tight_crop_candidate_freeze.json").read_text(encoding="utf-8")
    )
    capture = json.loads(
        (BASELINES / "trt35_page15_lattice_jib_0_v011_tight_crop_candidate_capture.json").read_text(encoding="utf-8")
    )
    golden = [
        HumanGoldenCell.model_validate(value)
        for value in json.loads(
            (DATASETS / "trt35_page15_lattice_jib_0_full_human_golden.json").read_text(encoding="utf-8")
        )
    ]

    assert validate_full_human_golden(
        golden,
        expected_document_hash=manifest["source_document_hash"],
        expected_cell_count=160,
        expected_configuration=manifest["table_segment"],
    ) == []
    assert capture["capture_role"] == "FROZEN_PARSER_OUTPUT"
    assert capture["runner"] == manifest["runner"] == "tight-crop"
    result = Trt35VerticalSliceResult.model_validate(capture["result"])
    assert result.file_hash_sha256 == manifest["source_document_hash"]
    assert result.parser_version == manifest["parser_version"]
    assert result.canonical_content_hash == manifest["canonical_result_hash"]

    metrics = evaluate_full_human_golden(result, golden)
    assert metrics.critical_error_count == 0
    assert metrics.unresolved == manifest["result_counts"]["unresolved"] == 60


def test_page15_lattice_jib_20_v011_candidate_freeze_matches_full_human_golden() -> None:
    manifest = json.loads(
        (BASELINES / "trt35_page15_lattice_jib_20_v011_tight_crop_candidate_freeze.json").read_text(encoding="utf-8")
    )
    capture = json.loads(
        (BASELINES / "trt35_page15_lattice_jib_20_v011_tight_crop_candidate_capture.json").read_text(encoding="utf-8")
    )
    golden = [
        HumanGoldenCell.model_validate(value)
        for value in json.loads(
            (DATASETS / "trt35_page15_lattice_jib_20_full_human_golden.json").read_text(encoding="utf-8")
        )
    ]

    assert validate_full_human_golden(
        golden,
        expected_document_hash=manifest["source_document_hash"],
        expected_cell_count=160,
        expected_configuration=manifest["table_segment"],
    ) == []
    assert capture["capture_role"] == "FROZEN_PARSER_OUTPUT"
    assert capture["runner"] == manifest["runner"] == "tight-crop"
    result = Trt35VerticalSliceResult.model_validate(capture["result"])
    assert result.file_hash_sha256 == manifest["source_document_hash"]
    assert result.parser_version == manifest["parser_version"]
    assert result.canonical_content_hash == manifest["canonical_result_hash"]

    metrics = evaluate_full_human_golden(result, golden)
    assert metrics.critical_error_count == 0
    assert metrics.unresolved == manifest["result_counts"]["unresolved"] == 62
