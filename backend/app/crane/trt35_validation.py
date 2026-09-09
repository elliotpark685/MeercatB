"""Independent Golden evaluation for the TRT35 page-11 vertical slice."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.crane.trt35_vertical_slice import Trt35VerticalSliceResult


class Trt35GoldenMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_golden_cells: int
    correct_available: int = 0
    wrong_available: int = 0
    false_available: int = 0
    wrong_cell_association: int = 0
    correct_not_available: int = 0
    unresolved: int = 0
    missing_evidence: int = 0


def evaluate_golden(result: Trt35VerticalSliceResult, golden: list[dict]) -> Trt35GoldenMetrics:
    metrics = Trt35GoldenMetrics(total_golden_cells=len(golden))
    lookup = {(cell.source_page, cell.table_segment, cell.radius_m, cell.boom_length_m): cell for cell in result.cells}
    for expected in golden:
        key = (expected["source_page"], expected["table_segment"], expected["radius_m"], expected["boom_length_m"])
        cell = lookup.get(key)
        if cell is None:
            metrics.wrong_cell_association += 1
            continue
        if cell.cell_bbox is None or cell.source_page != expected["source_page"]:
            metrics.missing_evidence += 1
        if cell.cell_status == "UNRESOLVED":
            metrics.unresolved += 1
            continue
        if expected["cell_status"] == "NOT_AVAILABLE":
            if cell.cell_status == "NOT_AVAILABLE":
                metrics.correct_not_available += 1
            elif cell.cell_status == "AVAILABLE":
                metrics.false_available += 1
            continue
        if cell.cell_status != "AVAILABLE":
            metrics.wrong_available += 1
        elif cell.rated_capacity_t != expected["rated_capacity_t"]:
            metrics.wrong_available += 1
        else:
            metrics.correct_available += 1
    return metrics
