"""Create a blank Human Golden review CSV for TRT35 page-12 On Tires 360°."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crane.trt35_pipeline import Trt35Page11Pipeline
from app.crane.trt35_vertical_slice import (
    TRT35_PAGE12_UPPER_ON_TIRES_TABLE_BBOX_PDF,
    trt35_page12_upper_on_tires_identity,
)


FIELDNAMES = [
    "source_document_hash",
    "source_page",
    "configuration",
    "row_index",
    "column_index",
    "radius_m",
    "boom_length_m",
    "expected_cell_status",
    "expected_capacity_t",
    "source_bbox_x0",
    "source_bbox_y0",
    "source_bbox_x1",
    "source_bbox_y1",
    "human_verified",
    "verified_at",
    "verification_note",
]


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("pdf", type=Path)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()

    identity = trt35_page12_upper_on_tires_identity()
    result = Trt35Page11Pipeline().parse_page11(
        args.pdf.read_bytes(),
        page_number=identity.source_page,
        table_bbox_pdf=TRT35_PAGE12_UPPER_ON_TIRES_TABLE_BBOX_PDF,
        identity=identity,
        ocr_runner=lambda _: [],
        cell_ocr_runner=lambda _image, _grid: [],
    )
    if result.grid_status != "PASS" or len(result.cells) != 68:
        raise ValueError("page-12 On Tires grid must resolve to exactly 68 cells before review")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for cell in result.cells:
            x0, y0, x1, y1 = cell.cell_bbox
            writer.writerow({
                "source_document_hash": result.file_hash_sha256,
                "source_page": cell.source_page,
                "configuration": cell.table_segment,
                "row_index": cell.row_index,
                "column_index": cell.column_index,
                "radius_m": cell.radius_m,
                "boom_length_m": cell.boom_length_m,
                "expected_cell_status": "",
                "expected_capacity_t": "",
                "source_bbox_x0": x0,
                "source_bbox_y0": y0,
                "source_bbox_x1": x1,
                "source_bbox_y1": y1,
                "human_verified": "false",
                "verified_at": "",
                "verification_note": "Direct independent PDF review required; no parser value supplied.",
            })


if __name__ == "__main__":
    main()
