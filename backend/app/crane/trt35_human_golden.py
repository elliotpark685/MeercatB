"""Gate the TRT35 slice on a complete independently reviewed dataset."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HumanGoldenCell(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_document_hash: str = Field(min_length=64, max_length=64)
    source_page: int = Field(ge=1)
    configuration: str
    row_index: int = Field(ge=0)
    column_index: int = Field(ge=0)
    radius_m: float = Field(gt=0)
    boom_length_m: float = Field(gt=0)
    expected_cell_status: str
    expected_capacity_t: float | None = Field(default=None, ge=0)
    source_bbox: tuple[float, float, float, float]
    human_verified: bool = False
    verified_at: datetime | None = None
    verification_note: str | None = None

    @model_validator(mode="after")
    def verify_semantics(self) -> "HumanGoldenCell":
        if self.expected_cell_status not in {"AVAILABLE", "NOT_AVAILABLE"}:
            raise ValueError("human Golden status must be AVAILABLE or NOT_AVAILABLE")
        if (self.expected_cell_status == "AVAILABLE") != (self.expected_capacity_t is not None):
            raise ValueError("available Golden cells require a capacity and unavailable cells must not have one")
        if self.human_verified != (self.verified_at is not None):
            raise ValueError("human verification requires both a flag and timestamp")
        return self


def validate_full_human_golden(cells: list[HumanGoldenCell], *, expected_document_hash: str) -> list[str]:
    errors: list[str] = []
    if len(cells) != 135:
        errors.append(f"expected 135 human Golden cells, found {len(cells)}")
    keys = {(cell.row_index, cell.column_index) for cell in cells}
    if len(keys) != len(cells):
        errors.append("duplicate row/column cell in human Golden")
    if any(not cell.human_verified for cell in cells):
        errors.append("every human Golden cell must be verified")
    if any(cell.source_document_hash != expected_document_hash for cell in cells):
        errors.append("human Golden source document hash mismatch")
    return errors
