"""Fail-closed preliminary lift review for a Human Golden-validated TRT35 chart."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.crane.geometry_review import MainBoomReachReviewService, ReachReviewInput, ReachStatus
from app.crane.trt35_geometry_reference import get_trt35_geometry_lookup
from app.crane.trt35_vertical_slice import Trt35VerticalSliceResult


class Trt35CapacityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CONFIGURATION_NOT_CONFIRMED = "CONFIGURATION_NOT_CONFIRMED"
    CELL_NOT_FOUND = "CELL_NOT_FOUND"
    CELL_NOT_AVAILABLE = "CELL_NOT_AVAILABLE"


class Trt35OverallStatus(str, Enum):
    REVIEW_PASS = "REVIEW_PASS"
    CONFIGURATION_NOT_CONFIRMED = "CONFIGURATION_NOT_CONFIRMED"
    CAPACITY_FAIL = "CAPACITY_FAIL"
    CAPACITY_CELL_NOT_FOUND = "CAPACITY_CELL_NOT_FOUND"
    CAPACITY_CELL_NOT_AVAILABLE = "CAPACITY_CELL_NOT_AVAILABLE"
    GEOMETRY_FAIL = "GEOMETRY_FAIL"
    GEOMETRY_POINT_NOT_FOUND = "GEOMETRY_POINT_NOT_FOUND"
    GEOMETRY_REFERENCE_DATASET_REQUIRED = "GEOMETRY_REFERENCE_DATASET_REQUIRED"


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
    geometry_status: ReachStatus = ReachStatus.REFERENCE_DATASET_REQUIRED
    overall_status: Trt35OverallStatus
    overall_reason: str
    rated_capacity_t: float | None = None
    capacity_margin_t: float | None = None
    utilization_percent: float | None = None
    source_page: int | None = None
    source_bbox: tuple[float, float, float, float] | None = None
    maximum_hook_height_m: float | None = None
    height_margin_m: float | None = None
    height_reference: str | None = None
    geometry_source_page: int | None = None
    geometry_source_bbox: tuple[float, float, float, float] | None = None
    reason: str | None = None
    geometry_reason: str = "TRT35 range-graph Human Golden data is required before lifting height can be verified"
    approval: str = "NOT_GRANTED"


class Trt35EngineeringReviewService:
    """Uses only an exact, verified cell. Interpolation is intentionally absent."""

    @staticmethod
    def _result(request: Trt35ReviewInput, **values: object) -> Trt35ReviewResult:
        capacity_status = values["capacity_status"]
        geometry_status = values.get("geometry_status", ReachStatus.REFERENCE_DATASET_REQUIRED)
        overall_status, overall_reason = Trt35EngineeringReviewService._overall_status(
            capacity_status=capacity_status if isinstance(capacity_status, Trt35CapacityStatus) else Trt35CapacityStatus(capacity_status),
            geometry_status=geometry_status if isinstance(geometry_status, ReachStatus) else ReachStatus(geometry_status),
        )
        return Trt35ReviewResult(
            gross_load_t=request.gross_load_t,
            rigging_total_t=request.rigging_total_t,
            required_height_m=request.required_height_m,
            overall_status=overall_status,
            overall_reason=overall_reason,
            **values,
        )

    @staticmethod
    def _overall_status(*, capacity_status: Trt35CapacityStatus, geometry_status: ReachStatus) -> tuple[Trt35OverallStatus, str]:
        if capacity_status == Trt35CapacityStatus.CONFIGURATION_NOT_CONFIRMED:
            return Trt35OverallStatus.CONFIGURATION_NOT_CONFIRMED, "Selected chart configuration must be confirmed before any review result can be used"
        if capacity_status == Trt35CapacityStatus.FAIL:
            return Trt35OverallStatus.CAPACITY_FAIL, "Gross load exceeds the exact rated-capacity chart cell"
        if capacity_status == Trt35CapacityStatus.CELL_NOT_FOUND:
            return Trt35OverallStatus.CAPACITY_CELL_NOT_FOUND, "Exact rated-capacity chart cell was not found; interpolation is disabled"
        if capacity_status == Trt35CapacityStatus.CELL_NOT_AVAILABLE:
            return Trt35OverallStatus.CAPACITY_CELL_NOT_AVAILABLE, "Selected rated-capacity chart cell is not available"
        if geometry_status == ReachStatus.FAIL:
            return Trt35OverallStatus.GEOMETRY_FAIL, "Required hook height exceeds the exact Human Golden range-graph point"
        if geometry_status == ReachStatus.POINT_NOT_FOUND:
            return Trt35OverallStatus.GEOMETRY_POINT_NOT_FOUND, "Exact Human Golden range-graph point was not found; interpolation is disabled"
        if geometry_status == ReachStatus.REFERENCE_DATASET_REQUIRED:
            return Trt35OverallStatus.GEOMETRY_REFERENCE_DATASET_REQUIRED, "Human Golden range-graph evidence is required before height review"
        return Trt35OverallStatus.REVIEW_PASS, "Exact capacity and range-graph checks both passed; operational approval is not granted"

    @staticmethod
    def _geometry_values(chart: Trt35VerticalSliceResult, request: Trt35ReviewInput) -> dict[str, object]:
        if chart.file_hash_sha256 is None:
            return {
                "geometry_status": ReachStatus.REFERENCE_DATASET_REQUIRED,
                "geometry_reason": "TRT35 source document identity is required before height review",
            }
        lookup = get_trt35_geometry_lookup(
            capacity_configuration=chart.table_segment,
            capacity_boom_length_m=request.boom_length_m,
            expected_document_hash=chart.file_hash_sha256,
        )
        if lookup is None:
            return {
                "geometry_status": ReachStatus.REFERENCE_DATASET_REQUIRED,
                "geometry_reason": "No matching Human Golden range graph is registered for the selected chart configuration and boom length",
            }
        reach = MainBoomReachReviewService().review(
            ReachReviewInput(
                boom_length_m=lookup.geometry_boom_length_m,
                working_radius_m=request.radius_m,
                required_hook_height_m=request.required_height_m,
            ),
            lookup.dataset,
        )
        return {
            "geometry_status": reach.status,
            "maximum_hook_height_m": reach.maximum_hook_height_m,
            "height_margin_m": reach.height_margin_m,
            "height_reference": lookup.height_reference,
            "geometry_source_page": reach.source_page,
            "geometry_source_bbox": reach.source_bbox,
            "geometry_reason": reach.reason or "Exact Human Golden range-graph point verified",
        }

    def review(self, chart: Trt35VerticalSliceResult, request: Trt35ReviewInput) -> Trt35ReviewResult:
        if not request.configuration_confirmed:
            return self._result(
                request,
                capacity_status=Trt35CapacityStatus.CONFIGURATION_NOT_CONFIRMED,
                reason="Confirm that the selected chart configuration matches the crane setup before review",
            )
        geometry = self._geometry_values(chart, request)
        cell = next(
            (item for item in chart.cells if item.radius_m == request.radius_m and item.boom_length_m == request.boom_length_m),
            None,
        )
        if cell is None:
            return self._result(
                request,
                capacity_status=Trt35CapacityStatus.CELL_NOT_FOUND,
                reason="Exact chart cell not found; interpolation is disabled",
                **geometry,
            )
        if cell.cell_status != "AVAILABLE" or cell.rated_capacity_t is None:
            return self._result(
                request,
                capacity_status=Trt35CapacityStatus.CELL_NOT_AVAILABLE,
                source_page=cell.source_page,
                source_bbox=cell.cell_bbox,
                reason="The selected chart cell is not available",
                **geometry,
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
            **geometry,
        )
