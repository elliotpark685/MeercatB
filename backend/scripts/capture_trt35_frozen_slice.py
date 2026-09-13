"""Reproduce and capture exactly the TRT35 parser state named by a freeze manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crane.cell_ocr import EasyOcrCellRunner, TightCropEasyOcrCellRunner
from app.crane.trt35_pipeline import Trt35Page11Pipeline
from app.crane.trt35_vertical_slice import (
    TRT35_PAGE11_LOWER_50_TABLE_BBOX_PDF,
    TRT35_PAGE12_LOWER_ON_TIRES_TABLE_BBOX_PDF,
    TRT35_PAGE15_LEFT_LATTICE_JIB_0_TABLE_BBOX_PDF,
    TRT35_PAGE15_RIGHT_LATTICE_JIB_20_TABLE_BBOX_PDF,
    trt35_page11_lower_50_identity,
    trt35_page12_lower_on_tires_identity,
    trt35_page15_left_lattice_jib_0_identity,
    trt35_page15_right_lattice_jib_20_identity,
)


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("pdf", type=Path)
    cli.add_argument("--freeze-manifest", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--runner", choices=("baseline", "tight-crop"), default="baseline")
    cli.add_argument(
        "--configuration",
        choices=(
            "upper-100", "lower-50", "page12-on-tires-2kmh", "page15-lattice-jib-0",
            "page15-lattice-jib-20",
        ),
        default="upper-100",
    )
    args = cli.parse_args()

    manifest = json.loads(args.freeze_manifest.read_text(encoding="utf-8"))
    runner = EasyOcrCellRunner() if args.runner == "baseline" else TightCropEasyOcrCellRunner()
    configuration_identities = {
        "lower-50": (trt35_page11_lower_50_identity(), TRT35_PAGE11_LOWER_50_TABLE_BBOX_PDF),
        "page12-on-tires-2kmh": (
            trt35_page12_lower_on_tires_identity(),
            TRT35_PAGE12_LOWER_ON_TIRES_TABLE_BBOX_PDF,
        ),
        "page15-lattice-jib-0": (
            trt35_page15_left_lattice_jib_0_identity(),
            TRT35_PAGE15_LEFT_LATTICE_JIB_0_TABLE_BBOX_PDF,
        ),
        "page15-lattice-jib-20": (
            trt35_page15_right_lattice_jib_20_identity(),
            TRT35_PAGE15_RIGHT_LATTICE_JIB_20_TABLE_BBOX_PDF,
        ),
    }
    identity, table_bbox_pdf = configuration_identities.get(
        args.configuration,
        (None, tuple(manifest["table_roi_pdf"])),
    )
    if identity is not None and manifest["table_segment"] != identity.table_segment:
        raise ValueError("freeze manifest does not match requested configuration")
    result = Trt35Page11Pipeline(render_scale=manifest["render_scale"]).parse_page11(
        args.pdf.read_bytes(),
        page_number=manifest["source_page"],
        table_bbox_pdf=table_bbox_pdf,
        ocr_runner=lambda _: [],
        minimum_confidence=manifest["confidence_threshold"],
        cell_ocr_runner=runner.read,
        parser_version=manifest["parser_version"],
        identity=identity,
    )
    if result.file_hash_sha256 != manifest["source_document_hash"]:
        raise ValueError("source document hash differs from freeze manifest")
    if result.canonical_content_hash != manifest["canonical_result_hash"]:
        raise ValueError("parser output differs from freeze manifest; do not replace the freeze")

    capture = {
        "capture_role": "FROZEN_PARSER_OUTPUT",
        "runner": args.runner,
        "configuration": args.configuration,
        "freeze_manifest": str(args.freeze_manifest),
        "result": result.model_dump(mode="json"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(capture, indent=2), encoding="utf-8")
    print(result.canonical_content_hash)


if __name__ == "__main__":
    main()
