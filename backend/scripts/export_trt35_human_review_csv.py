"""Export Human Golden candidates as a reviewer-editable CSV without approval."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


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
    cli.add_argument("--candidates", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()

    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    if len(candidates) != 135:
        raise ValueError("candidate source must contain exactly 135 cells")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for cell in candidates:
            x0, y0, x1, y1 = cell["source_bbox"]
            writer.writerow({
                **{name: cell[name] for name in FIELDNAMES if name in cell},
                "expected_capacity_t": "" if cell["expected_capacity_t"] is None else cell["expected_capacity_t"],
                "source_bbox_x0": x0,
                "source_bbox_y0": y0,
                "source_bbox_x1": x1,
                "source_bbox_y1": y1,
                "human_verified": "false",
                "verified_at": "",
            })


if __name__ == "__main__":
    main()
