from app.crane.trt35_validation import evaluate_golden
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
