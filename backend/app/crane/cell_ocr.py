"""Cell-level OCR adapter for conservative crane-table extraction."""

from __future__ import annotations

import os
from typing import Protocol

# Must precede NumPy/OpenCV/Torch imports on Windows.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import numpy as np
import cv2

from app.crane.ocr_table_association import OcrTableGrid, OcrToken


class EasyOcrReader(Protocol):
    def readtext(self, image: np.ndarray, *, detail: int, paragraph: bool, allowlist: str): ...


class EasyOcrCellRunner:
    """Runs OCR independently for every validated capacity cell.

    Text is returned verbatim. The parser decides whether it is a valid number
    or dash; this adapter never performs character substitutions.
    """

    allowlist = "0123456789.-"

    def __init__(self, reader: EasyOcrReader | None = None, *, margin_px: int = 2):
        self._reader = reader
        self.margin_px = margin_px

    def _get_reader(self) -> EasyOcrReader:
        if self._reader is None:
            # EasyOCR/Torch can otherwise load two OpenMP runtimes on Windows.
            import easyocr

            self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return self._reader

    def read(self, image: np.ndarray, grid: OcrTableGrid) -> list[OcrToken]:
        if grid.column_edges is None or grid.row_edges is None:
            raise ValueError("cell-level OCR requires explicit grid edges")
        reader = self._get_reader()
        tokens: list[OcrToken] = []
        for row in range(len(grid.radius_rows)):
            for column in range(len(grid.boom_columns)):
                left, top = int(grid.column_edges[column]), int(grid.row_edges[row])
                right, bottom = int(grid.column_edges[column + 1]), int(grid.row_edges[row + 1])
                crop_left, crop_top = left + self.margin_px, top + self.margin_px
                crop_right, crop_bottom = right - self.margin_px, bottom - self.margin_px
                if crop_right <= crop_left or crop_bottom <= crop_top:
                    continue
                crop = image[crop_top:crop_bottom, crop_left:crop_right]
                results = reader.readtext(crop, detail=1, paragraph=False, allowlist=self.allowlist)
                for polygon, text, confidence in results:
                    x_values = [point[0] for point in polygon]
                    y_values = [point[1] for point in polygon]
                    normalized = str(text).strip()
                    if not normalized:
                        continue
                    tokens.append(
                        OcrToken(
                            text=normalized,
                            confidence=float(confidence),
                            bbox=(min(x_values) + crop_left, min(y_values) + crop_top, max(x_values) + crop_left, max(y_values) + crop_top),
                        )
                    )
                # Empty OCR is normally UNRESOLVED. It becomes a dash only
                # when a separate visual detector finds one centred stroke.
                if not results:
                    dash_bbox = detect_confirmed_dash(crop)
                    if dash_bbox is not None:
                        dx0, dy0, dx1, dy1 = dash_bbox
                        tokens.append(OcrToken(text="-", confidence=1.0, bbox=(dx0 + crop_left, dy0 + crop_top, dx1 + crop_left, dy1 + crop_top)))
        return tokens


def detect_confirmed_dash(crop: np.ndarray) -> tuple[float, float, float, float] | None:
    """Detect one isolated, central dash glyph; never infer a blank as dash."""
    if crop.size == 0:
        return None
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
    binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)[1]
    count, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    height, width = gray.shape[:2]
    candidates: list[tuple[int, int, int, int]] = []
    foreground_components = 0
    for index in range(1, count):
        x, y, component_width, component_height, area = stats[index]
        # Only a rule touching the crop boundary can be ignored. Other ink,
        # including a decimal point or a digit fragment, makes a dash ambiguous.
        if component_width >= width * .8 and (y == 0 or y + component_height == height):
            continue
        foreground_components += 1
        if not (max(4, round(width * 0.02)) <= component_width <= max(8, round(width * 0.20))):
            continue
        if component_height > max(3, round(height * 0.22)) or area < component_width:
            continue
        center_x = x + component_width / 2
        center_y = y + component_height / 2
        if abs(center_x - width / 2) > width * 0.25 or abs(center_y - height / 2) > height * 0.25:
            continue
        candidates.append((x, y, x + component_width, y + component_height))
    return candidates[0] if len(candidates) == 1 and foreground_components == 1 else None
