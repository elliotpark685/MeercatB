"""Canonical, serializable schema for the v0.5 TRT60 Parser PoC.

This module deliberately contains parser output only. Engineering review inputs
(required height, radius, payload and approval states) are out of scope.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CellStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    PROHIBITED = "PROHIBITED"
    BLANK = "BLANK"
    PARSE_ERROR = "PARSE_ERROR"


class ParserVerificationStatus(str, Enum):
    AUTO_PARSED = "AUTO_PARSED"
    AUTO_VALIDATED = "AUTO_VALIDATED"
    REJECTED = "REJECTED"


class SourceEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_page: int = Field(ge=1)
    source_text: str
    source_bbox: tuple[float, float, float, float] | None = None


class LoadChartCell(BaseModel):
    model_config = ConfigDict(extra="forbid")
    radius_m: float | None = Field(default=None, ge=0)
    boom_length_m: float | None = Field(default=None, ge=0)
    boom_angle_deg: float | None = None
    rated_capacity_t: float | None = Field(default=None, ge=0)
    source_radius_text: str | None = None
    parsed_source_radius_value: float | None = None
    source_radius_unit: str | None = None
    source_capacity_text: str | None = None
    parsed_source_capacity_value: float | None = None
    source_capacity_unit: str | None = None
    cell_status: CellStatus
    source_text: str
    source: SourceEvidence
    confidence: float = Field(ge=0, le=1)


class ConfigurationHeader(BaseModel):
    model_config = ConfigDict(extra="forbid")
    counterweight_t: float | None = None
    support_mode: str | None = None
    outrigger_percent: float | None = None
    outrigger_width_m: float | None = None
    outrigger_length_m: float | None = None
    working_area: str | None = None
    boom_type: str = "MAIN"
    main_boom_length_m: float | None = None
    jib_length_m: float | None = None
    standard: str | None = None
    source: SourceEvidence


class LoadChart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chart_type: str = "MAIN_BOOM_LOAD_CHART"
    unit_system: str = "METRIC"
    capacity_basis: str = "UNKNOWN"
    capacity_basis_source: SourceEvidence | None = None
    operational_limit_source: SourceEvidence | None = None
    header: ConfigurationHeader
    cells: list[LoadChartCell]
    source: SourceEvidence


class CanonicalTRT60Data(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "trt60-canonical-v0.5"
    parser_profile: str = "TEREX_TRT"
    parser_version: str
    manufacturer: str
    brand: str = "Terex"
    model: str = "TRT60"
    crane_type: str = "rough_terrain"
    nominal_capacity_t: float = 60.0
    source_document: SourceEvidence
    file_hash_sha256: str | None = None
    canonical_content_hash: str
    load_charts: list[LoadChart]
    parser_verification_status: ParserVerificationStatus
    validation_errors: list[str] = []
    content_hash_sha256: str

    def deterministic_payload(self) -> dict[str, Any]:
        value = self.model_dump(mode="json", exclude={"content_hash_sha256"})
        return value
