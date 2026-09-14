"""Human Golden schema and validation for manufacturer range-graph points."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GeometryGoldenPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_document_hash: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    source_page: int = Field(ge=1)
    configuration: str = Field(min_length=1)
    unit_system: str
    boom_length_m: float = Field(gt=0)
    working_radius_m: float = Field(gt=0)
    maximum_hook_height_m: float = Field(gt=0)
    source_bbox: tuple[float, float, float, float]
    human_verified: bool = False
    verified_at: datetime | None = None
    verification_note: str | None = None

    @model_validator(mode="after")
    def validate_verification(self) -> "GeometryGoldenPoint":
        if self.unit_system != "METRIC":
            raise ValueError("Geometry Golden currently requires METRIC units")
        if self.human_verified != (self.verified_at is not None):
            raise ValueError("human verification requires both a flag and timestamp")
        x0, y0, x1, y1 = self.source_bbox
        if x1 <= x0 or y1 <= y0:
            raise ValueError("source_bbox must have positive area")
        return self


def validate_geometry_golden(
    points: list[GeometryGoldenPoint],
    *,
    expected_document_hash: str,
    expected_page: int,
    expected_configuration: str,
) -> list[str]:
    errors: list[str] = []
    if not points:
        errors.append("geometry Golden must contain at least one point")
    if any(not point.human_verified for point in points):
        errors.append("every geometry Golden point must be verified")
    if any(point.source_document_hash.lower() != expected_document_hash.lower() for point in points):
        errors.append("geometry Golden source document hash mismatch")
    if any(point.source_page != expected_page for point in points):
        errors.append("geometry Golden source page mismatch")
    if any(point.configuration != expected_configuration for point in points):
        errors.append("geometry Golden configuration mismatch")
    coordinates = {(point.boom_length_m, point.working_radius_m) for point in points}
    if len(coordinates) != len(points):
        errors.append("duplicate boom/radius geometry point")
    return errors
