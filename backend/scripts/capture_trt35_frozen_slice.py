"""Reproduce and capture exactly the TRT35 parser state named by a freeze manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.crane.cell_ocr import EasyOcrCellRunner
from app.crane.trt35_pipeline import Trt35Page11Pipeline


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("pdf", type=Path)
    cli.add_argument("--freeze-manifest", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()

    manifest = json.loads(args.freeze_manifest.read_text(encoding="utf-8"))
    result = Trt35Page11Pipeline(render_scale=manifest["render_scale"]).parse_page11(
        args.pdf.read_bytes(),
        table_bbox_pdf=tuple(manifest["table_roi_pdf"]),
        ocr_runner=lambda _: [],
        minimum_confidence=manifest["confidence_threshold"],
        cell_ocr_runner=EasyOcrCellRunner().read,
    )
    if result.file_hash_sha256 != manifest["source_document_hash"]:
        raise ValueError("source document hash differs from freeze manifest")
    if result.canonical_content_hash != manifest["canonical_result_hash"]:
        raise ValueError("parser output differs from freeze manifest; do not replace the freeze")

    capture = {
        "capture_role": "FROZEN_PARSER_OUTPUT",
        "freeze_manifest": str(args.freeze_manifest),
        "result": result.model_dump(mode="json"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(capture, indent=2), encoding="utf-8")
    print(result.canonical_content_hash)


if __name__ == "__main__":
    main()
