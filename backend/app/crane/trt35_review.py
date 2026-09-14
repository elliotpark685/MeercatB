"""Fail-closed preliminary lift review for a Human Golden-validated TRT35 chart."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.crane.trt35_vertical_slice import Trt35VerticalSliceResult


class Trt35CapacityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CONFIGURATION_NOT_CONFIRMED = "CONFIGURATION_NOT_CONFIRMED"
    CELL_NOT_FOUND = "CELL_NOT_FOUND"
    CELL_NOT_AVAILABLE = "CELL_NOT_AVAILABLE"


class Trt35GeometryStatus(str, Enum):
    REFERENCE_DATASET_REQUIRED = "REFERENCE_DATASET_REQUIRED"


class Trt35ReviewInput(BaseModel):
    """Inputs required for a capacity check; all masses are metric tonnes."""

    model_config = ConfigDict(extra="forbid")
    radius_m: float = Field(gt=0)
    boom_length_m: float = Field(gt=0)
    required_height_m: float = Field(gt=0)
    payload_t: float = Field(ge=0)
    rigging_t: float | None = Field(default=None, ge=0)
    sling_leg_count: int | None = Field(default=None, ge=1, le=4)
    sling_weight_per_leg_t: float | None = Field(default=None, ge=0)
    hook_block_t: float = Field(default=0, ge=0)
    spreader_t: float = Field(default=0, ge=0)
    configuration_confirmed: bool = False

    @model_validator(mode="after")
    def validate_rigging_input(self) -> "Trt35ReviewInput":
        per_leg_input = self.sling_leg_count is not None or self.sling_weight_per_leg_t is not None
        if per_leg_input and (self.sling_leg_count is None or self.sling_weight_per_leg_t is None):
            raise ValueError("sling_leg_count and sling_weight_per_leg_t must be provided together")
        if per_leg_input and self.rigging_t is not None:
            raise ValueError("Provide either rigging_t or per-leg sling inputs, not both")
        return self

    @property
    def rigging_total_t(self) -> float:
        if self.sling_leg_count is not None and self.sling_weight_per_leg_t is not None:
            return self.sling_leg_count * self.sling_weight_per_leg_t
        return self.rigging_t or 0.0

    @property
    def gross_load_t(self) -> float:
        return self.payload_t + self.rigging_total_t + self.hook_block_t + self.spreader_t


class Trt35ReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gross_load_t: float
    rigging_total_t: float
    required_height_m: float
    capacity_status: Trt35CapacityStatus
    geometry_status: Trt35GeometryStatus = Trt35GeometryStatus.REFERENCE_DATASET_REQUIRED
    rated_capacity_t: float | None = None
    capacity_margin_t: float | None = None
    utilization_percent: float | None = None
    source_page: int | None = None
    source_bbox: tuple[float, float, float, float] | None = None
    reason: str | None = None
    geometry_reason: str = "TRT35 range-graph Human Golden data is required before lifting height can be verified"
    approval: str = "NOT_GRANTED"


class Trt35EngineeringReviewService:
    """Uses only an exact, verified cell. Interpolation is intentionally absent."""

    @staticmethod
    def _result(request: Trt35ReviewInput, **values: object) -> Trt35ReviewResult:
        return Trt35ReviewResult(
            gross_load_t=request.gross_load_t,
            rigging_total_t=request.rigging_total_t,
            required_height_m=request.required_height_m,
            **values,
        )

    def review(self, chart: Trt35VerticalSliceResult, request: Trt35ReviewInput) -> Trt35ReviewResult:
        if not request.configuration_confirmed:
            return self._result(
                request,
                capacity_status=Trt35CapacityStatus.CONFIGURATION_NOT_CONFIRMED,
                reason="Confirm that the selected chart configuration matches the crane setup before review",
            )
        cell = next(
            (item for item in chart.cells if item.radius_m == request.radius_m and item.boom_length_m == request.boom_length_m),
            None,
        )
        if cell is None:
            return self._result(
                request,
                capacity_status=Trt35CapacityStatus.CELL_NOT_FOUND,
                reason="Exact chart cell not found; interpolation is disabled",
            )
        if cell.cell_status != "AVAILABLE" or cell.rated_capacity_t is None:
            return self._result(
                request,
                capacity_status=Trt35CapacityStatus.CELL_NOT_AVAILABLE,
                source_page=cell.source_page,
                source_bbox=cell.cell_bbox,
                reason="The selected chart cell is not available",
            )
        margin = cell.rated_capacity_t - request.gross_load_t
        utilization = request.gross_load_t / cell.rated_capacity_t * 100
        return self._result(
            request,
            capacity_status=Trt35CapacityStatus.PASS if margin >= 0 else Trt35CapacityStatus.FAIL,
            rated_capacity_t=cell.rated_capacity_t,
            capacity_margin_t=margin,
            utilization_percent=utilization,
            source_page=cell.source_page,
            source_bbox=cell.cell_bbox,
        )
