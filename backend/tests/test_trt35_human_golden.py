from app.crane.trt35_human_golden import HumanGoldenCell, validate_full_human_golden


def _cell(**changes):
    value = {
        "source_document_hash": "a" * 64,
        "source_page": 11,
        "configuration": "PAGE_11_UPPER_100_OUTRIGGER",
        "row_index": 0,
        "column_index": 0,
        "radius_m": 3.0,
        "boom_length_m": 9.1,
        "expected_cell_status": "AVAILABLE",
        "expected_capacity_t": 35.0,
        "source_bbox": (1, 1, 2, 2),
        "human_verified": True,
        "verified_at": "2026-09-09T00:00:00Z",
    }
    value.update(changes)
    return HumanGoldenCell(**value)


def test_full_human_golden_requires_every_cell_and_independent_verification():
    errors = validate_full_human_golden([_cell()], expected_document_hash="a" * 64)
    assert any("135" in error for error in errors)

    errors = validate_full_human_golden([_cell(human_verified=False, verified_at=None) for _ in range(135)], expected_document_hash="a" * 64)
    assert any("verified" in error for error in errors)
