from datetime import datetime, timezone
import csv
from pathlib import Path

import pytest

from app.crane.geometry_golden import GeometryGoldenPoint, validate_geometry_golden


def _point(**changes):
    value = {
        "source_document_hash": "a" * 64,
        "source_page": 10,
        "configuration": "PAGE_10_RANGE_GRAPH",
        "unit_system": "METRIC",
        "boom_length_m": 18,
        "working_radius_m": 8,
        "maximum_hook_height_m": 16.4,
        "source_bbox": (1, 2, 3, 4),
        "human_verified": True,
        "verified_at": datetime.now(timezone.utc),
    }
    value.update(changes)
    return GeometryGoldenPoint(**value)


def test_geometry_golden_requires_metric_and_verified_evidence():
    with pytest.raises(ValueError, match="METRIC"):
        _point(unit_system="IMPERIAL")
    with pytest.raises(ValueError, match="both"):
        _point(human_verified=False, verified_at=datetime.now(timezone.utc))


def test_geometry_golden_rejects_duplicate_points_and_accepts_verified_point():
    point = _point()
    assert validate_geometry_golden(
        [point],
        expected_document_hash="a" * 64,
        expected_page=10,
        expected_configuration="PAGE_10_RANGE_GRAPH",
    ) == []
    assert "duplicate boom/radius geometry point" in validate_geometry_golden(
        [point, _point()],
        expected_document_hash="a" * 64,
        expected_page=10,
        expected_configuration="PAGE_10_RANGE_GRAPH",
    )


def test_completed_trt35_geometry_csv_is_schema_validated():
    path = Path(__file__).parents[1] / "evaluation" / "datasets" / "trt35_geometry_human_review_template_complete.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 43
    points = [
        GeometryGoldenPoint(
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
        for row in rows
    ]
    for configuration, page in {
        "MAIN_BOOM_9.1M": 10,
        "MAIN_BOOM_14.4M": 10,
        "MAIN_BOOM_19.6M": 10,
        "MAIN_BOOM_24.9M": 10,
        "MAIN_BOOM_30.1M": 10,
        "LATTICE_JIB_8M_0DEG": 14,
        "LATTICE_JIB_8M_20DEG": 14,
    }.items():
        subset = [point for point in points if point.configuration == configuration]
        assert validate_geometry_golden(
            subset,
            expected_document_hash="7048039dfe68b0626f72966c3ce2db635559443cb131652ff89fa834e27e3207",
            expected_page=page,
            expected_configuration=configuration,
        ) == []
