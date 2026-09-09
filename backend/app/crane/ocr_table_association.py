"""Deterministic association of OCR tokens to a pre-validated table grid.

OCR supplies observations, not engineering values.  This module creates a cell
only when one token is unambiguously inside an explicit row/column grid.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, model_validator


NUMBER = re.compile(r"^\d+(?:\.\d+)?$")


class OcrToken(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    confidence: float = Field(ge=0, le=1)
    bbox: tuple[float, float, float, float]

    @model_validator(mode="after")
    def validate_token(self) -> "OcrToken":
        x0, y0, x1, y1 = self.bbox
        if not self.text.strip():
            raise ValueError("OCR token text must not be empty")
        if not (x0 < x1 and y0 < y1):
            raise ValueError("OCR token bbox must have positive area")
        return self

    @property
    def center(self) -> tuple[float, float]:
        x0, y0, x1, y1 = self.bbox
        return ((x0 + x1) / 2, (y0 + y1) / 2)


class GridAxisPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Geometry reconstruction may know the position before OCR/header parsing
    # has established the engineering value. Never invent an axis value.
    value: float | None = Field(default=None, gt=0)
    center: float
    index: int = Field(default=0, ge=0)


class OcrTableGrid(BaseModel):
    """A human-validated table block and its header/row coordinate centres."""

    model_config = ConfigDict(extra="forbid")
    source_page: int = Field(ge=1)
    table_bbox: tuple[float, float, float, float]
    boom_columns: list[GridAxisPoint] = Field(min_length=1)
    radius_rows: list[GridAxisPoint] = Field(min_length=1)
    x_tolerance: float = Field(gt=0)
    y_tolerance: float = Field(gt=0)
    # Optional explicit edges produced by grid reconstruction. When present,
    # ownership is determined by the cell rectangle, not by overlapping
    # centre tolerances.
    column_edges: list[float] | None = None
    row_edges: list[float] | None = None

    @model_validator(mode="after")
    def validate_edges(self) -> "OcrTableGrid":
        bx0, by0, bx1, by1 = self.table_bbox
        if not (bx0 < bx1 and by0 < by1):
            raise ValueError("table_bbox must have positive area")
        if self.column_edges is not None:
            if len(self.column_edges) != len(self.boom_columns) + 1 or any(
                right <= left for left, right in zip(self.column_edges, self.column_edges[1:])
            ):
                raise ValueError("column_edges must contain monotonic boundaries for every column")
            if self.column_edges[0] < bx0 or self.column_edges[-1] > bx1:
                raise ValueError("column_edges must remain inside table_bbox")
        if self.row_edges is not None:
            if len(self.row_edges) != len(self.radius_rows) + 1 or any(
                bottom <= top for top, bottom in zip(self.row_edges, self.row_edges[1:])
            ):
                raise ValueError("row_edges must contain monotonic boundaries for every row")
            if self.row_edges[0] < by0 or self.row_edges[-1] > by1:
                raise ValueError("row_edges must remain inside table_bbox")
        return self


class AssociatedOcrCell(BaseModel):
    model_config = ConfigDict(extra="forbid")
    radius_m: float | None
    boom_length_m: float | None
    status: str
    rated_capacity_t: float | None = None
    source_token: OcrToken | None = None
    reason: str | None = None
    cell_bbox: tuple[float, float, float, float] | None = None


class OcrTableAssociator:
    """Maps exact OCR observations to a grid without interpolation or repair."""

    def associate(self, grid: OcrTableGrid, tokens: list[OcrToken], *, minimum_confidence: float = 0.8, numeric_pattern: re.Pattern[str] = NUMBER) -> list[AssociatedOcrCell]:
        if not 0 <= minimum_confidence <= 1:
            raise ValueError("minimum_confidence must be between 0 and 1")
        cells: list[AssociatedOcrCell] = []
        matches: dict[int, list[tuple[int, int]]] = {}
        for row_index, row in enumerate(grid.radius_rows):
            for column_index, column in enumerate(grid.boom_columns):
                for token_index, token in enumerate(tokens):
                    if self._matches(grid, row_index, column_index, row, column, token):
                        matches.setdefault(token_index, []).append((row_index, column_index))
        for row_index, row in enumerate(grid.radius_rows):
            for column_index, column in enumerate(grid.boom_columns):
                candidates = [
                    token for token_index, token in enumerate(tokens)
                    if self._matches(grid, row_index, column_index, row, column, token)
                    and len(matches.get(token_index, [])) == 1
                ]
                cells.append(self._cell(row.value, column.value, candidates, minimum_confidence, self._bbox(grid, row_index, column_index), numeric_pattern))
        return cells

    @classmethod
    def _matches(cls, grid, row_index, column_index, row, column, token) -> bool:
        if not cls._inside(token, grid.table_bbox):
            return False
        if grid.column_edges is not None and grid.row_edges is not None:
            left, right = grid.column_edges[column_index], grid.column_edges[column_index + 1]
            top, bottom = grid.row_edges[row_index], grid.row_edges[row_index + 1]
            x, y = token.center
            return left <= x < right and top <= y < bottom
        return abs(token.center[0] - column.center) <= grid.x_tolerance and abs(token.center[1] - row.center) <= grid.y_tolerance

    @staticmethod
    def _bbox(grid, row_index: int, column_index: int):
        if grid.column_edges is None or grid.row_edges is None:
            return None
        return (
            grid.column_edges[column_index], grid.row_edges[row_index],
            grid.column_edges[column_index + 1], grid.row_edges[row_index + 1],
        )

    @staticmethod
    def _inside(token: OcrToken, table_bbox: tuple[float, float, float, float]) -> bool:
        x0, y0, x1, y1 = token.bbox
        bx0, by0, bx1, by1 = table_bbox
        return bx0 <= x0 <= x1 <= bx1 and by0 <= y0 <= y1 <= by1

    @staticmethod
    def _cell(radius_m: float, boom_length_m: float, candidates: list[OcrToken], minimum_confidence: float, cell_bbox=None, numeric_pattern: re.Pattern[str] = NUMBER) -> AssociatedOcrCell:
        if len(candidates) != 1:
            return AssociatedOcrCell(
                radius_m=radius_m,
                boom_length_m=boom_length_m,
                status="UNRESOLVED",
                reason="No unique OCR token matches this exact grid cell",
                cell_bbox=cell_bbox,
            )
        token = candidates[0]
        if token.confidence < minimum_confidence:
            return AssociatedOcrCell(
                radius_m=radius_m,
                boom_length_m=boom_length_m,
                status="UNRESOLVED",
                source_token=token,
                reason="OCR confidence is below the configured threshold",
                cell_bbox=cell_bbox,
            )
        if token.text == "-":
            return AssociatedOcrCell(radius_m=radius_m, boom_length_m=boom_length_m, status="NOT_AVAILABLE", source_token=token, cell_bbox=cell_bbox)
        if not numeric_pattern.fullmatch(token.text):
            return AssociatedOcrCell(
                radius_m=radius_m,
                boom_length_m=boom_length_m,
                status="UNRESOLVED",
                source_token=token,
                reason="OCR token is not a numeric capacity or a dash cell",
                cell_bbox=cell_bbox,
            )
        return AssociatedOcrCell(
            radius_m=radius_m,
            boom_length_m=boom_length_m,
            status="AVAILABLE",
            rated_capacity_t=float(token.text),
            source_token=token,
            cell_bbox=cell_bbox,
        )
