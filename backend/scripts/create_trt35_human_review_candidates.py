"""Create review candidates from an AI visual draft; never mark them human-verified."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft", type=Path, default=Path("evaluation/datasets/trt35_page11_100_visual_draft.json"))
    parser.add_argument("--bbox-capture", type=Path, default=Path("evaluation/results/trt35_cell_experiment.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    draft = json.loads(args.draft.read_text(encoding="utf-8"))
    capture = json.loads(args.bbox_capture.read_text(encoding="utf-8"))
    parsed_cells = capture["baseline"]["result"]["cells"]
    bboxes = {(cell["radius_m"], cell["boom_length_m"]): cell["cell_bbox"] for cell in parsed_cells}
    if len(bboxes) != 135:
        raise ValueError("frozen capture must provide exactly 135 unique cell bboxes")
    candidates = []
    for row_index, row in enumerate(draft["rows"]):
        radius, values = row[0], row[1:]
        for column_index, (boom, raw) in enumerate(zip(draft["boom_lengths_m"], values)):
            candidates.append({
                "source_document_hash": draft["source_sha256"],
                "source_page": draft["source_page"],
                "configuration": draft["table_segment"],
                "row_index": row_index,
                "column_index": column_index,
                "radius_m": radius,
                "boom_length_m": boom,
                "expected_cell_status": "NOT_AVAILABLE" if raw == "-" else "AVAILABLE",
                "expected_capacity_t": None if raw == "-" else float(raw),
                # Geometry evidence is taken from the frozen source capture;
                # expected values remain independently reviewed candidates.
                "source_bbox": bboxes[(radius, boom)],
                "human_verified": False,
                "verified_at": None,
                "verification_note": "AI visual transcription candidate; requires independent PDF review"
            })
    args.output.write_text(json.dumps(candidates, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
