"""Fail-closed OpenCV reconstruction for a single crane table ROI.

This module reconstructs geometry only. It never reads capacity values and it
never fills missing cells. OCR is intentionally a separate concern.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.crane.ocr_table_association import GridAxisPoint, OcrTableGrid


class TableStructureUnresolved(ValueError):
    """Raised when the image cannot support a trustworthy rectangular grid."""


@dataclass(frozen=True)
class GridReconstructionConfig:
    source_page: int
    table_bbox: tuple[float, float, float, float]
    expected_columns: int
    expected_rows: int
    render_scale: float = 1.0
    min_line_length_ratio: float = 0.65
    merge_tolerance_px: int = 4
    # Some manufacturer tables have no internal vertical rules. In that case
    # validated boom-header centres are the column geometry source.
    column_centers_px: tuple[float, ...] | None = None
    row_centers_px: tuple[float, ...] | None = None


def reconstruct_grid(image: np.ndarray, config: GridReconstructionConfig) -> OcrTableGrid:
    """Detect a rectangular table and return explicit cell ownership edges.

    `image` must be a grayscale or BGR rendered page. The returned coordinates
    are in the same pixel coordinate system as the image. Model-specific axis
    values are deliberately supplied by the caller after independent header
    validation.
    """
    if image is None or image.size == 0:
        raise TableStructureUnresolved("empty rendered page")
    if config.expected_columns < 1 or config.expected_rows < 1:
        raise TableStructureUnresolved("invalid expected grid dimensions")
    x0, y0, x1, y1 = config.table_bbox
    if not (0 <= x0 < x1 <= image.shape[1] and 0 <= y0 < y1 <= image.shape[0]):
        raise TableStructureUnresolved("table ROI is outside the rendered page")

    crop = image[int(y0):int(y1), int(x0):int(x1)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
    binary = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)[1]
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(8, crop.shape[1] // 20), 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(8, crop.shape[0] // 30)))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
    xs = _cluster_lines(_line_positions(vertical, axis=0, minimum=crop.shape[0] * config.min_line_length_ratio), config.merge_tolerance_px)
    ys = _cluster_lines(_line_positions(horizontal, axis=1, minimum=crop.shape[1] * config.min_line_length_ratio), config.merge_tolerance_px)
    if config.column_centers_px is not None:
        centers = [float(center - x0) for center in config.column_centers_px]
        if len(centers) != config.expected_columns or any(b <= a for a, b in zip(centers, centers[1:])):
            raise TableStructureUnresolved("boom header centres are not monotonic or have the wrong count")
        if not all(0 < center < x1 - x0 for center in centers):
            raise TableStructureUnresolved("boom header centre is outside table ROI")
        if (centers[-1] - centers[0]) / (x1 - x0) < 0.60:
            raise TableStructureUnresolved("boom header centres do not span enough of the table ROI")
        xs = [0.0] + [(left + right) / 2 for left, right in zip(centers, centers[1:])] + [float(x1 - x0)]
    if config.row_centers_px is not None:
        centers = [float(center - y0) for center in config.row_centers_px]
        if len(centers) != config.expected_rows or any(b <= a for a, b in zip(centers, centers[1:])):
            raise TableStructureUnresolved("radius row centres are not monotonic or have the wrong count")
        if not all(0 < center < y1 - y0 for center in centers):
            raise TableStructureUnresolved("radius row centre is outside table ROI")
        if (centers[-1] - centers[0]) / (y1 - y0) < 0.80:
            raise TableStructureUnresolved("radius row centres do not span enough of the table ROI")
        ys = [0.0] + [(top + bottom) / 2 for top, bottom in zip(centers, centers[1:])] + [float(y1 - y0)]
    if len(xs) != config.expected_columns + 1 or len(ys) != config.expected_rows + 1:
        raise TableStructureUnresolved(f"expected {config.expected_columns + 1}x{config.expected_rows + 1} grid lines, found {len(xs)}x{len(ys)}")
    xs = [x + x0 for x in xs]
    ys = [y + y0 for y in ys]
    if any(b <= a for a, b in zip(xs, xs[1:])) or any(b <= a for a, b in zip(ys, ys[1:])):
        raise TableStructureUnresolved("grid lines are not monotonic")
    if min(np.diff(xs)) < 2 or min(np.diff(ys)) < 2:
        raise TableStructureUnresolved("grid contains a zero-width or zero-height cell")
    return OcrTableGrid(
        source_page=config.source_page,
        table_bbox=config.table_bbox,
        boom_columns=[GridAxisPoint(index=i, center=(xs[i] + xs[i + 1]) / 2) for i in range(config.expected_columns)],
        radius_rows=[GridAxisPoint(index=i, center=(ys[i] + ys[i + 1]) / 2) for i in range(config.expected_rows)],
        x_tolerance=max(1.0, min(np.diff(xs)) / 2),
        y_tolerance=max(1.0, min(np.diff(ys)) / 2),
        column_edges=xs,
        row_edges=ys,
    )


def _line_positions(mask: np.ndarray, *, axis: int, minimum: float) -> list[int]:
    projection = (mask > 0).sum(axis=axis)
    return [int(index) for index, value in enumerate(projection) if value >= minimum]


def _cluster_lines(values: list[int], tolerance: int) -> list[int]:
    if not values:
        return []
    clusters: list[list[int]] = [[values[0]]]
    for value in values[1:]:
        if value - clusters[-1][-1] <= tolerance:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    return [round(sum(cluster) / len(cluster)) for cluster in clusters]
