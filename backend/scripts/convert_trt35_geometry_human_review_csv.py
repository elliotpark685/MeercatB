"""Convert the reviewed TRT35 Geometry CSV into the runtime Golden JSON."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.crane.geometry_golden import GeometryGoldenPoint


INPUT = ROOT / "evaluation" / "datasets" / "trt35_geometry_human_review_template_complete.csv"
OUTPUT = ROOT / "evaluation" / "datasets" / "trt35_geometry_golden.json"
SOURCE_HASH = "7048039dfe68b0626f72966c3ce2db635559443cb131652ff89fa834e27e3207"


def _point(row: dict[str, str]) -> GeometryGoldenPoint:
    return GeometryGoldenPoint(
        source_document_hash=row["source_document_hash"],
        source_page=int(row["source_page"]),
        configuration=row["configuration"],
        unit_system=row["unit_system"],
        boom_length_m=float(row["boom_length_m"]),
        working_radius_m=float(row["working_radius_m"]),
        maximum_hook_height_m=float(row["maximum_hook_height_m"]),
        source_bbox=(float(row["source_bbox_x0"]), float(row["source_bbox_y0"]), float(row["source_bbox_x1"]), float(row["source_bbox_y1"])),
        human_verified=row["human_verified"].lower() == "true",
        verified_at=datetime.fromisoformat(row["verified_at"].replace("Z", "+00:00")),
        verification_note=row["verification_note"],
    )


def _dataset(configuration: str, points: list[GeometryGoldenPoint]) -> dict[str, object]:
    first = points[0]
    if configuration.startswith("MAIN_BOOM_"):
        capacity_boom = first.boom_length_m
        height_reference = "HOOK_BLOCK"
    elif configuration.startswith("LATTICE_JIB_8M_"):
        capacity_boom = 30.1
        height_reference = "HOOK_BALL"
    else:
        raise ValueError(f"Unsupported TRT35 Geometry configuration: {configuration}")
    return {
        "configuration": configuration,
        "height_reference": height_reference,
        "capacity_boom_length_m": capacity_boom,
        "geometry_boom_length_m": first.boom_length_m,
        "source_page": first.source_page,
        "points": [
            {
                "boom_length_m": point.boom_length_m,
                "working_radius_m": point.working_radius_m,
                "maximum_hook_height_m": point.maximum_hook_height_m,
                "source": {
                    "source_page": point.source_page,
                    "source_text": point.verification_note or "Human-verified TRT35 range graph point",
                    "source_bbox": point.source_bbox,
                },
            }
            for point in points
        ],
    }


def main() -> None:
    with INPUT.open(newline="", encoding="utf-8") as stream:
        points = [_point(row) for row in csv.DictReader(stream)]
    if not points or any(point.source_document_hash != SOURCE_HASH for point in points):
        raise ValueError("TRT35 Geometry CSV does not match the registered PDF")
    grouped: dict[str, list[GeometryGoldenPoint]] = {}
    for point in points:
        grouped.setdefault(point.configuration, []).append(point)
    payload = {
        "manufacturer": "Terex",
        "model": "TRT35",
        "file_hash_sha256": SOURCE_HASH,
        "parser_profile": "TEREX_TRT35_GEOMETRY_GOLDEN_V1",
        "parser_version": "0.1.0-human-golden",
        "datasets": [_dataset(configuration, values) for configuration, values in sorted(grouped.items())],
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
