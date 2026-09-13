"""Runtime boundary for the TRT35 page-11 OCR vertical slice."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from collections.abc import Callable, Mapping

import fitz
import numpy as np

from app.crane.ocr_input import tokens_from_easyocr
from app.crane.opencv_grid import GridReconstructionConfig, TableStructureUnresolved, reconstruct_grid
from app.crane.ocr_table_association import OcrTableGrid, OcrToken
from app.crane.trt35_vertical_slice import Trt35TableIdentity, Trt35VerticalSliceParser, Trt35VerticalSliceResult


OcrRunner = Callable[[np.ndarray], list[Mapping]]
CellOcrRunner = Callable[[np.ndarray, OcrTableGrid], list[OcrToken]]


@dataclass(frozen=True)
class Trt35Page11AxisGeometry:
    """Layout-only evidence; it intentionally carries no radius values."""

    boom_header_centers_pdf: tuple[float, ...]
    radius_row_centers_pdf: tuple[float, ...]


class Trt35Page11Pipeline:
    """Render and parse one explicitly configured page-11 table segment.

    The ROI is supplied in PDF points and converted using the same render
    matrix used for the page. No default ROI is provided because an arbitrary
    rectangle could mix the 100% and 50% configuration blocks.
    """

    def __init__(self, *, render_scale: float = 3.0):
        if render_scale <= 0:
            raise ValueError("render_scale must be positive")
        self.render_scale = render_scale

    def render_page(self, payload: bytes, *, page_number: int = 11) -> tuple[np.ndarray, str]:
        if not payload.startswith(b"%PDF-"):
            raise ValueError("payload is not a PDF")
        if page_number < 1:
            raise ValueError("page_number must be one-based")
        document = fitz.open(stream=payload, filetype="pdf")
        try:
            if page_number > document.page_count:
                raise ValueError(f"PDF has no page {page_number}")
            page = document.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(self.render_scale, self.render_scale), alpha=False)
            image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)
            if pixmap.n == 4:
                image = image[:, :, :3]
            return image.copy(), hashlib.sha256(payload).hexdigest()
        finally:
            document.close()

    def derive_page11_axis_geometry(self, payload: bytes, *, identity: Trt35TableIdentity | None = None) -> Trt35Page11AxisGeometry:
        """Read only stable header positions and row y-coordinates from page 11.

        TRT35 native text may scramble *radius values*, so those words are
        never used as radius semantics. Their y positions are accepted only
        after count/monotonicity validation and are later paired with the
        independently configured, human-reviewed radius axis.
        """
        expected = identity or Trt35TableIdentity()
        document = fitz.open(stream=payload, filetype="pdf")
        try:
            if document.page_count < 11:
                raise ValueError("PDF has no page 11")
            words = document.load_page(10).get_text("words")
        finally:
            document.close()
        header_words = [word for word in words if 195 <= word[1] <= 215 and re.fullmatch(r"\d+\.\d+", word[4])]
        header_words.sort(key=lambda word: word[0])
        header_values = [float(word[4]) for word in header_words]
        if header_values != expected.boom_lengths_m:
            raise ValueError("TRT35 page 11 boom header does not match the expected 100% Outrigger axis")
        boom_centers = tuple((word[0] + word[2]) / 2 for word in header_words)
        # These two margin columns contain the same visual row lattice. The
        # number strings themselves are intentionally ignored.
        row_words = [word for word in words if 40 < word[0] < 90 and 220 < word[1] < 500 and re.fullmatch(r"\d+(?:\.\d+)?", word[4])]
        row_centers = tuple((word[1] + word[3]) / 2 for word in row_words)
        if len(row_centers) != len(expected.radii_m) or any(b <= a for a, b in zip(row_centers, row_centers[1:])):
            raise ValueError("TRT35 page 11 radius-row geometry is unresolved")
        return Trt35Page11AxisGeometry(boom_header_centers_pdf=boom_centers, radius_row_centers_pdf=row_centers)

    def parse_page11(
        self,
        payload: bytes,
        *,
        table_bbox_pdf: tuple[float, float, float, float],
        ocr_runner: OcrRunner,
        identity: Trt35TableIdentity | None = None,
        minimum_confidence: float = 0.85,
        boom_header_centers_pdf: tuple[float, ...] | None = None,
        radius_row_centers_pdf: tuple[float, ...] | None = None,
        cell_ocr_runner: CellOcrRunner | None = None,
        parser_version: str = "0.1.0-slice",
    ) -> Trt35VerticalSliceResult:
        image, file_hash = self.render_page(payload, page_number=11)
        bbox_px = tuple(value * self.render_scale for value in table_bbox_pdf)
        expected = identity or Trt35TableIdentity()
        if boom_header_centers_pdf is None or radius_row_centers_pdf is None:
            geometry = self.derive_page11_axis_geometry(payload, identity=expected)
            boom_header_centers_pdf = boom_header_centers_pdf or geometry.boom_header_centers_pdf
            radius_row_centers_pdf = radius_row_centers_pdf or geometry.radius_row_centers_pdf
        try:
            grid = reconstruct_grid(
                image,
                GridReconstructionConfig(
                    source_page=11,
                    table_bbox=bbox_px,
                    expected_columns=len(expected.boom_lengths_m),
                    expected_rows=len(expected.radii_m),
                    render_scale=self.render_scale,
                    column_centers_px=tuple(value * self.render_scale for value in boom_header_centers_pdf) if boom_header_centers_pdf else None,
                    row_centers_px=tuple(value * self.render_scale for value in radius_row_centers_pdf) if radius_row_centers_pdf else None,
                ),
            )
        except TableStructureUnresolved as exc:
            raise ValueError(f"TRT35 page 11 table structure unresolved: {exc}") from exc
        tokens: list[OcrToken] = cell_ocr_runner(image, grid) if cell_ocr_runner else tokens_from_easyocr(ocr_runner(image))
        return Trt35VerticalSliceParser().parse(
            grid,
            tokens,
            identity=expected,
            file_hash_sha256=file_hash,
            minimum_confidence=minimum_confidence,
            parser_version=parser_version,
        )
