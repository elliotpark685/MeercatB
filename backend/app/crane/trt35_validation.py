"""Independent Human Golden evaluation for the TRT35 page-11 vertical slice.

This module deliberately treats an unresolved cell as distinct from a wrong
answer.  Acceptance is blocked by every critical disagreement, but does not
require OCR to manufacture a value for every source cell.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.crane.trt35_human_golden import HumanGoldenCell
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


class Trt35HumanGoldenMetrics(BaseModel):
    """Metrics used by the frozen-parser acceptance gate."""

    model_config = ConfigDict(extra="forbid")
    total_human_golden_cells: int
    correct_available: int = 0
    wrong_numeric_capacity: int = 0
    false_available: int = 0
    wrong_cell_association: int = 0
    correct_not_available: int = 0
    false_not_available: int = 0
    unresolved: int = 0
    missing_evidence: int = 0
    cross_configuration: int = 0

    @property
    def critical_error_count(self) -> int:
        return (
            self.wrong_numeric_capacity
            + self.false_available
            + self.wrong_cell_association
            + self.false_not_available
            + self.cross_configuration
        )


def evaluate_full_human_golden(
    result: Trt35VerticalSliceResult,
    golden: list[HumanGoldenCell],
) -> Trt35HumanGoldenMetrics:
    """Compare a frozen parser result against independently verified cells.

    Comparison is by explicit row/column coordinate, rather than value or
    nearest-neighbour matching.  Therefore a cell shifted to another radius or
    boom column cannot be credited as correct.
    """
    metrics = Trt35HumanGoldenMetrics(total_human_golden_cells=len(golden))
    parsed_by_coordinate = {(cell.row_index, cell.column_index): cell for cell in result.cells}
    golden_coordinates = {(cell.row_index, cell.column_index) for cell in golden}

    if len(parsed_by_coordinate) != len(result.cells):
        metrics.wrong_cell_association += len(result.cells) - len(parsed_by_coordinate)
    unexpected_coordinates = set(parsed_by_coordinate) - golden_coordinates
    metrics.wrong_cell_association += len(unexpected_coordinates)

    for expected in golden:
        cell = parsed_by_coordinate.get((expected.row_index, expected.column_index))
        if cell is None:
            metrics.wrong_cell_association += 1
            continue
        if (
            cell.source_page != expected.source_page
            or cell.table_segment != expected.configuration
            or cell.radius_m != expected.radius_m
            or cell.boom_length_m != expected.boom_length_m
        ):
            metrics.cross_configuration += 1
            continue
        if cell.cell_bbox is None:
            metrics.missing_evidence += 1
        if cell.cell_status == "UNRESOLVED":
            metrics.unresolved += 1
            continue
        if expected.expected_cell_status == "NOT_AVAILABLE":
            if cell.cell_status == "NOT_AVAILABLE":
                metrics.correct_not_available += 1
            else:
                metrics.false_available += 1
            continue
        if cell.cell_status == "NOT_AVAILABLE":
            metrics.false_not_available += 1
        elif cell.cell_status != "AVAILABLE" or cell.rated_capacity_t != expected.expected_capacity_t:
            metrics.wrong_numeric_capacity += 1
        else:
            metrics.correct_available += 1
    return metrics


def human_golden_acceptance(metrics: Trt35HumanGoldenMetrics, *, golden_errors: list[str]) -> bool:
    """Return true only for a complete Golden with no critical disagreement."""
    return not golden_errors and metrics.critical_error_count == 0


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
