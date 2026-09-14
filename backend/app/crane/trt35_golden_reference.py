"""Deterministic runtime lookup for fully human-verified TRT35 charts.

These records are the approved value source for the one exact PDF revision
registered by the TRT35 runtime.  OCR captures remain onboarding evidence; an
OCR observation must never override a verified cell at review time.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.crane.trt35_human_golden import HumanGoldenCell, validate_full_human_golden
from app.crane.trt35_vertical_slice import Trt35CellResult, Trt35VerticalSliceParser, Trt35VerticalSliceResult


TRT35_HUMAN_GOLDEN_FILES: dict[str, str] = {
    "PAGE_11_UPPER_100_OUTRIGGER": "trt35_page11_100_full_human_golden.json",
    "PAGE_11_LOWER_50_OUTRIGGER": "trt35_page11_50_full_human_golden.json",
    "PAGE_12_UPPER_ON_TIRES_360_0_KMH": "trt35_page12_on_tires_360_0kmh_full_human_golden.json",
    "PAGE_12_LOWER_ON_TIRES_0_MAX_2_KMH": "trt35_page12_on_tires_2kmh_full_human_golden.json",
    "PAGE_15_LEFT_LATTICE_JIB_8M_0_DEG": "trt35_page15_lattice_jib_0_full_human_golden.json",
    "PAGE_15_RIGHT_LATTICE_JIB_8M_20_DEG": "trt35_page15_lattice_jib_20_full_human_golden.json",
}

_DATASETS = Path(__file__).parents[2] / "evaluation" / "datasets"


@lru_cache(maxsize=len(TRT35_HUMAN_GOLDEN_FILES))
def load_trt35_human_golden_result(
    configuration: str,
    *,
    expected_document_hash: str,
    parser_version: str,
) -> Trt35VerticalSliceResult:
    """Return an immutable-equivalent result composed only of reviewed cells."""
    filename = TRT35_HUMAN_GOLDEN_FILES.get(configuration)
    if filename is None:
        raise ValueError("TRT35 configuration has no Human Golden reference")

    values = json.loads((_DATASETS / filename).read_text(encoding="utf-8"))
    golden = [HumanGoldenCell.model_validate(value) for value in values]
    errors = validate_full_human_golden(
        golden,
        expected_document_hash=expected_document_hash,
        expected_cell_count=len(golden),
        expected_configuration=configuration,
    )
    if errors:
        raise ValueError("TRT35 Human Golden reference is invalid: " + "; ".join(errors))

    cells = [
        Trt35CellResult(
            source_page=cell.source_page,
            table_segment=cell.configuration,
            row_index=cell.row_index,
            column_index=cell.column_index,
            radius_m=cell.radius_m,
            boom_length_m=cell.boom_length_m,
            cell_bbox=cell.source_bbox,
            source_text=(f"{cell.expected_capacity_t:.2f}" if cell.expected_capacity_t is not None else "-"),
            confidence=1.0,
            rated_capacity_t=cell.expected_capacity_t,
            cell_status=cell.expected_cell_status,
            reason=None,
        )
        for cell in sorted(golden, key=lambda value: (value.row_index, value.column_index))
    ]
    result = Trt35VerticalSliceResult(
        parser_version=parser_version,
        file_hash_sha256=expected_document_hash,
        source_page=golden[0].source_page,
        table_segment=configuration,
        grid_status="PASS",
        cells=cells,
        critical_errors=[],
        canonical_content_hash="pending",
    )
    result.canonical_content_hash = Trt35VerticalSliceParser.content_hash(result)
    return result
