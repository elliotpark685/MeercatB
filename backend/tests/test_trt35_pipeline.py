import fitz
import numpy as np
import pytest

from app.crane.trt35_pipeline import Trt35Page11Pipeline


def _pdf(page_count=1):
    document = fitz.open()
    for _ in range(page_count):
        document.new_page(width=200, height=100)
    payload = document.tobytes()
    document.close()
    return payload


def test_render_page_uses_one_based_page_number_and_fixed_scale():
    image, digest = Trt35Page11Pipeline(render_scale=3).render_page(_pdf(page_count=11), page_number=11)
    assert image.shape[:2] == (300, 600)
    assert len(digest) == 64


def test_render_page_rejects_missing_page():
    with pytest.raises(ValueError, match="no page 11"):
        Trt35Page11Pipeline().render_page(_pdf(), page_number=11)


def test_parse_page11_does_not_accept_an_unvalidated_full_page_as_table_roi():
    with pytest.raises(ValueError, match="table structure unresolved"):
        Trt35Page11Pipeline().parse_page11(
            _pdf(page_count=11),
            table_bbox_pdf=(0, 0, 200, 100),
            ocr_runner=lambda image: [],
            boom_header_centers_pdf=(20, 60, 100, 140, 180),
            radius_row_centers_pdf=tuple(float(index + 1) for index in range(27)),
        )


def test_axis_geometry_rejects_missing_or_unexpected_page11_layout():
    with pytest.raises(ValueError, match="boom header"):
        Trt35Page11Pipeline().derive_page11_axis_geometry(_pdf(page_count=11))
