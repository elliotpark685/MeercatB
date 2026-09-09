"""TRT35 page 11 / 100% Outrigger vertical slice.

The slice consumes an independently reconstructed grid and OCR observations.
It does not perform interpolation, numeric repair, or cross-configuration
fallback. It is intentionally not registered as a production parser profile
until its Golden Dataset and source-revision checks are accepted.
"""

from __future__ import annotations

import hashlib
import json
import re

from pydantic import BaseModel, ConfigDict, Field

from app.crane.ocr_table_association import OcrTableAssociator, OcrTableGrid, OcrToken


TRT35_PROFILE = "TEREX_TRT35_OCR_V1"
# The supplied TRT35 page-11 capacity cells are printed with two decimal
# places. Requiring that source form prevents a lost decimal point (1.90 ->
# 90) from becoming an engineering value. This is a profile-specific safety
# rule, not a numeric correction.
CAPACITY = re.compile(r"^\d+\.\d{2}$")


class Trt35TableIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_page: int = Field(default=11, ge=1)
    table_segment: str = "PAGE_11_UPPER_100_OUTRIGGER"
    counterweight_t: float = Field(default=4.2, gt=0)
    outrigger_percent: float = Field(default=100, gt=0, le=100)
    outrigger_width_m: float = Field(default=5.9, gt=0)
    outrigger_length_m: float = Field(default=5.8, gt=0)
    working_area: str = "360 deg"
    boom_lengths_m: list[float] = Field(default=[9.1, 14.4, 19.6, 24.9, 30.1], min_length=1)
    radii_m: list[float] = Field(default_factory=lambda: [3.0, 3.5, 4.0, 4.5] + [float(i) for i in range(5, 28)])


class Trt35CellResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_page: int
    table_segment: str
    row_index: int
    column_index: int
    radius_m: float
    boom_length_m: float
    cell_bbox: tuple[float, float, float, float]
    source_text: str | None = None
    confidence: float | None = None
    rated_capacity_t: float | None = None
    cell_status: str
    reason: str | None = None


class Trt35VerticalSliceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    parser_profile: str = TRT35_PROFILE
    parser_version: str = "0.1.0-slice"
    file_hash_sha256: str | None = None
    source_page: int
    table_segment: str
    grid_status: str
    cells: list[Trt35CellResult]
    critical_errors: list[str] = Field(default_factory=list)
    canonical_content_hash: str

    @property
    def false_available_count(self) -> int:
        return sum(cell.cell_status == "AVAILABLE" and cell.rated_capacity_t is None for cell in self.cells)


class Trt35VerticalSliceParser:
    """Builds a strict result from geometry and cell OCR observations."""

    def parse(
        self,
        grid: OcrTableGrid,
        tokens: list[OcrToken],
        *,
        identity: Trt35TableIdentity | None = None,
        file_hash_sha256: str | None = None,
        minimum_confidence: float = 0.85,
    ) -> Trt35VerticalSliceResult:
        identity = identity or Trt35TableIdentity()
        errors = self._validate_identity(grid, identity)
        # A structurally unresolved grid must not fall back to centre-based
        # association. That fallback could manufacture a valid-looking cell
        # from an incorrect table geometry.
        associations = OcrTableAssociator().associate(
            grid,
            tokens if not errors else [],
            minimum_confidence=minimum_confidence,
            numeric_pattern=CAPACITY,
        )
        cells: list[Trt35CellResult] = []
        for index, associated in enumerate(associations):
            row_index, column_index = divmod(index, len(grid.boom_columns))
            radius = identity.radii_m[row_index] if row_index < len(identity.radii_m) else associated.radius_m
            boom = identity.boom_lengths_m[column_index] if column_index < len(identity.boom_lengths_m) else associated.boom_length_m
            token = associated.source_token
            cell = Trt35CellResult(
                source_page=grid.source_page,
                table_segment=identity.table_segment,
                row_index=row_index,
                column_index=column_index,
                radius_m=radius,
                boom_length_m=boom,
                cell_bbox=associated.cell_bbox or grid.table_bbox,
                source_text=token.text if token else None,
                confidence=token.confidence if token else None,
                rated_capacity_t=associated.rated_capacity_t,
                cell_status=associated.status,
                reason=associated.reason,
            )
            cells.append(cell)
        result = Trt35VerticalSliceResult(
            source_page=identity.source_page,
            table_segment=identity.table_segment,
            grid_status="PASS" if not errors else "TABLE_STRUCTURE_UNRESOLVED",
            cells=cells,
            critical_errors=errors,
            file_hash_sha256=file_hash_sha256,
            canonical_content_hash="pending",
        )
        result.canonical_content_hash = self.content_hash(result)
        return result

    @staticmethod
    def _validate_identity(grid: OcrTableGrid, identity: Trt35TableIdentity) -> list[str]:
        errors: list[str] = []
        if grid.source_page != identity.source_page:
            errors.append("source page mismatch")
        if len(grid.boom_columns) != len(identity.boom_lengths_m):
            errors.append("boom column count mismatch")
        if len(grid.radius_rows) != len(identity.radii_m):
            errors.append("radius row count mismatch")
        if grid.column_edges is None or grid.row_edges is None:
            errors.append("explicit cell edges are required")
        return errors

    @staticmethod
    def content_hash(result: Trt35VerticalSliceResult) -> str:
        payload = result.model_dump(mode="json", exclude={"canonical_content_hash", "file_hash_sha256", "critical_errors", "grid_status"})
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
