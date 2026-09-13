from app.crane.trt35_human_golden import HumanGoldenCell
from app.crane.trt35_validation import evaluate_full_human_golden, evaluate_golden, human_golden_acceptance
from app.crane.trt35_vertical_slice import Trt35CellResult, Trt35VerticalSliceResult


def _result(status="AVAILABLE", capacity=35.0):
    return Trt35VerticalSliceResult(
        source_page=11,
        table_segment="PAGE_11_UPPER_100_OUTRIGGER",
        grid_status="PASS",
        canonical_content_hash="x",
        cells=[Trt35CellResult(source_page=11, table_segment="PAGE_11_UPPER_100_OUTRIGGER", row_index=0, column_index=0, radius_m=3, boom_length_m=9.1, cell_bbox=(1, 1, 2, 2), cell_status=status, rated_capacity_t=capacity)],
    )


def test_golden_metrics_separate_wrong_value_false_available_and_unresolved():
    available = {"source_page": 11, "table_segment": "PAGE_11_UPPER_100_OUTRIGGER", "radius_m": 3, "boom_length_m": 9.1, "rated_capacity_t": 35, "cell_status": "AVAILABLE"}
    not_available = {**available, "rated_capacity_t": None, "cell_status": "NOT_AVAILABLE"}
    assert evaluate_golden(_result(capacity=34), [available]).wrong_available == 1
    assert evaluate_golden(_result(status="AVAILABLE"), [not_available]).false_available == 1
    assert evaluate_golden(_result(status="UNRESOLVED", capacity=None), [available]).unresolved == 1


def _human_cell(**changes):
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


def test_full_human_metrics_keep_each_critical_failure_distinct():
    golden = [_human_cell()]
    assert evaluate_full_human_golden(_result(capacity=34), golden).wrong_numeric_capacity == 1
    assert evaluate_full_human_golden(_result(status="NOT_AVAILABLE", capacity=None), golden).false_not_available == 1
    assert evaluate_full_human_golden(_result(status="UNRESOLVED", capacity=None), golden).unresolved == 1

    not_available = [_human_cell(expected_cell_status="NOT_AVAILABLE", expected_capacity_t=None)]
    assert evaluate_full_human_golden(_result(), not_available).false_available == 1

    shifted = _result()
    shifted.cells[0].column_index = 1
    assert evaluate_full_human_golden(shifted, golden).wrong_cell_association == 2

    wrong_configuration = _result()
    wrong_configuration.cells[0].table_segment = "PAGE_11_LOWER_50_OUTRIGGER"
    metrics = evaluate_full_human_golden(wrong_configuration, golden)
    assert metrics.cross_configuration == 1
    assert not human_golden_acceptance(metrics, golden_errors=[])
