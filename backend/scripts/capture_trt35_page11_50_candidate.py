"""Capture an unfrozen OCR candidate for TRT35 page-11 50% Outrigger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crane.cell_ocr import TightCropEasyOcrCellRunner
from app.crane.trt35_pipeline import Trt35Page11Pipeline
from app.crane.trt35_vertical_slice import (
    TRT35_PAGE11_LOWER_50_TABLE_BBOX_PDF,
    trt35_page11_lower_50_identity,
)


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("pdf", type=Path)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()

    result = Trt35Page11Pipeline().parse_page11(
        args.pdf.read_bytes(),
        table_bbox_pdf=TRT35_PAGE11_LOWER_50_TABLE_BBOX_PDF,
        identity=trt35_page11_lower_50_identity(),
        ocr_runner=lambda _: [],
        cell_ocr_runner=TightCropEasyOcrCellRunner().read,
        parser_version="0.1.1-tight-crop-candidate",
    )
    if result.grid_status != "PASS" or len(result.cells) != 100:
        raise ValueError("50% Outrigger candidate requires a resolved 100-cell grid")
    capture = {
        "capture_role": "UNFROZEN_CANDIDATE_OUTPUT",
        "runner": "tight-crop",
        "result": result.model_dump(mode="json"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(capture, indent=2), encoding="utf-8")
    print(result.canonical_content_hash)


if __name__ == "__main__":
    main()
