"""Engineering Review PoC boundary for validated Main Boom data.

This module deliberately does not infer required height, interpolate chart
cells, or bypass an UNKNOWN manufacturer capacity basis.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.crane.trt60_schema import CanonicalTRT60Data, CellStatus, ParserVerificationStatus


class CapacityStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED_CAPACITY_BASIS_UNKNOWN = "BLOCKED_CAPACITY_BASIS_UNKNOWN"
    CELL_NOT_AVAILABLE = "CELL_NOT_AVAILABLE"
    CONFIGURATION_NOT_FOUND = "CONFIGURATION_NOT_FOUND"
    CELL_NOT_FOUND = "CELL_NOT_FOUND"


class ConfigurationStatus(str, Enum):
    NOT_CONFIRMED = "NOT_CONFIRMED"
    CONFIRMED = "CONFIRMED"
    MISMATCH = "MISMATCH"


class GeometryStatus(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class ConfirmedConfiguration(BaseModel):
    """User-entered configuration fields, deliberately excluding parser evidence."""

    model_config = ConfigDict(extra="forbid")
    counterweight_t: float | None = Field(default=None, ge=0)
    support_mode: str | None = None
    outrigger_percent: float | None = Field(default=None, ge=0, le=100)
    outrigger_width_m: float | None = Field(default=None, ge=0)
    outrigger_length_m: float | None = Field(default=None, ge=0)
    working_area: str | None = None


class EngineeringReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chart_source_page: int = Field(ge=1)
    radius_m: float = Field(gt=0)
    boom_length_m: float = Field(gt=0)
    required_height_m: float = Field(gt=0)
    payload_t: float = Field(ge=0)
    rigging_t: float = Field(default=0, ge=0)
    hook_block_t: float = Field(default=0, ge=0)
    spreader_t: float = Field(default=0, ge=0)
    confirmed_configuration: ConfirmedConfiguration | None = None

    @property
    def gross_load_t(self) -> float:
        return self.payload_t + self.rigging_t + self.hook_block_t + self.spreader_t


class EngineeringReviewResult(BaseModel):
    gross_load_t: float
    required_height_m: float
    geometry_status: GeometryStatus = GeometryStatus.NOT_IMPLEMENTED
    configuration_status: ConfigurationStatus
    capacity_status: CapacityStatus
    rated_capacity_t: float | None = None
    utilization_percent: float | None = None
    source_page: int | None = None
    capacity_basis: str | None = None
    capacity_basis_source_page: int | None = None
    capacity_basis_source_bbox: tuple[float, float, float, float] | None = None
    operational_limit: str | None = None
    reason: str | None = None


class MainBoomEngineeringReviewService:
    def review(self, data: CanonicalTRT60Data, request: EngineeringReviewInput) -> EngineeringReviewResult:
        if data.parser_verification_status != ParserVerificationStatus.AUTO_VALIDATED:
            raise ValueError("Engineering Review requires AUTO_VALIDATED parser output")
        chart = next((item for item in data.load_charts if item.chart_type == "MAIN_BOOM_LOAD_CHART" and item.source.source_page == request.chart_source_page), None)
        if chart is None:
            return EngineeringReviewResult(gross_load_t=request.gross_load_t, required_height_m=request.required_height_m, configuration_status=ConfigurationStatus.MISMATCH, capacity_status=CapacityStatus.CONFIGURATION_NOT_FOUND, reason="Selected Main Boom configuration was not found")
        if request.confirmed_configuration is None:
            return EngineeringReviewResult(gross_load_t=request.gross_load_t, required_height_m=request.required_height_m, configuration_status=ConfigurationStatus.NOT_CONFIRMED, capacity_status=CapacityStatus.CONFIGURATION_NOT_FOUND, source_page=chart.source.source_page, reason="User configuration confirmation is required before review")
        expected_configuration = ConfirmedConfiguration(
            counterweight_t=chart.header.counterweight_t,
            support_mode=chart.header.support_mode,
            outrigger_percent=chart.header.outrigger_percent,
            outrigger_width_m=chart.header.outrigger_width_m,
            outrigger_length_m=chart.header.outrigger_length_m,
            working_area=chart.header.working_area,
        )
        if request.confirmed_configuration != expected_configuration:
            return EngineeringReviewResult(gross_load_t=request.gross_load_t, required_height_m=request.required_height_m, configuration_status=ConfigurationStatus.MISMATCH, capacity_status=CapacityStatus.CONFIGURATION_NOT_FOUND, source_page=chart.source.source_page, reason="Confirmed configuration does not match the selected chart")
        cell = next((item for item in chart.cells if item.radius_m == request.radius_m and item.boom_length_m == request.boom_length_m), None)
        if cell is None:
            return EngineeringReviewResult(gross_load_t=request.gross_load_t, required_height_m=request.required_height_m, configuration_status=ConfigurationStatus.CONFIRMED, capacity_status=CapacityStatus.CELL_NOT_FOUND, source_page=chart.source.source_page, reason="Exact chart cell not found; interpolation is disabled")
        if cell.cell_status != CellStatus.AVAILABLE or cell.rated_capacity_t is None:
            return EngineeringReviewResult(gross_load_t=request.gross_load_t, required_height_m=request.required_height_m, configuration_status=ConfigurationStatus.CONFIRMED, capacity_status=CapacityStatus.CELL_NOT_AVAILABLE, source_page=cell.source.source_page, reason="Selected chart cell is not available")
        if chart.capacity_basis == "UNKNOWN":
            return EngineeringReviewResult(gross_load_t=request.gross_load_t, required_height_m=request.required_height_m, configuration_status=ConfigurationStatus.CONFIRMED, capacity_status=CapacityStatus.BLOCKED_CAPACITY_BASIS_UNKNOWN, rated_capacity_t=cell.rated_capacity_t, source_page=cell.source.source_page, reason="Manufacturer capacity basis is unresolved")
        utilization = request.gross_load_t / cell.rated_capacity_t * 100
        basis_source = chart.capacity_basis_source
        limit = chart.operational_limit_source
        return EngineeringReviewResult(
            gross_load_t=request.gross_load_t,
            required_height_m=request.required_height_m,
            configuration_status=ConfigurationStatus.CONFIRMED,
            capacity_status=CapacityStatus.PASS if request.gross_load_t <= cell.rated_capacity_t else CapacityStatus.FAIL,
            rated_capacity_t=cell.rated_capacity_t,
            utilization_percent=utilization,
            source_page=cell.source.source_page,
            capacity_basis=chart.capacity_basis,
            capacity_basis_source_page=basis_source.source_page if basis_source else None,
            capacity_basis_source_bbox=basis_source.source_bbox if basis_source else None,
            operational_limit=limit.source_text if limit else None,
        )
