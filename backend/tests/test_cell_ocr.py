import numpy as np

from app.crane.cell_ocr import EasyOcrCellRunner, TightCropRecognitionReader, detect_confirmed_dash
from app.crane.ocr_table_association import GridAxisPoint, OcrTableGrid


class _Reader:
    def readtext(self, image, *, detail, paragraph, allowlist):
        assert allowlist == "0123456789.-"
        return [([[1, 2], [8, 2], [8, 7], [1, 7]], "35.00", 0.99)]


def test_cell_ocr_translates_each_crop_bbox_to_page_coordinates():
    grid = OcrTableGrid(
        source_page=11,
        table_bbox=(0, 0, 100, 50),
        boom_columns=[GridAxisPoint(value=9.1, center=50)],
        radius_rows=[GridAxisPoint(value=3.0, center=25)],
        x_tolerance=10,
        y_tolerance=10,
        column_edges=[10, 90],
        row_edges=[5, 45],
    )
    tokens = EasyOcrCellRunner(_Reader()).read(np.zeros((50, 100, 3), dtype=np.uint8), grid)
    assert tokens[0].text == "35.00"
    assert tokens[0].bbox == (13.0, 9.0, 20.0, 14.0)


def test_dash_detector_requires_one_central_isolated_horizontal_stroke():
    crop = np.full((30, 100), 255, dtype=np.uint8)
    crop[14:16, 45:55] = 0
    assert detect_confirmed_dash(crop) == (45, 14, 55, 16)

    blank = np.full((30, 100), 255, dtype=np.uint8)
    assert detect_confirmed_dash(blank) is None

    border_line = np.full((30, 100), 255, dtype=np.uint8)
    border_line[0:2, 45:55] = 0
    assert detect_confirmed_dash(border_line) is None


def test_dash_detector_rejects_dash_with_other_digit_or_decimal_ink():
    crop = np.full((30, 100), 255, dtype=np.uint8)
    crop[14:16, 45:55] = 0
    crop[10:20, 60:63] = 0
    assert detect_confirmed_dash(crop) is None
    crop[10:20, 60:63] = 255
    crop[20, 60] = 0
    assert detect_confirmed_dash(crop) is None


class _RecognitionReader:
    def recognize(self, image, *, detail, allowlist, paragraph):
        assert image.shape == (21, 21)
        assert allowlist == "0123456789.-"
        return [([], "16.25", 0.99)]


def test_tight_crop_reader_preserves_border_adjacent_glyphs_without_repair():
    image = np.full((20, 20, 3), 255, dtype=np.uint8)
    image[4:9, 1:6] = 0
    reader = TightCropRecognitionReader(_RecognitionReader())
    observed = reader.readtext(image, detail=1, paragraph=False, allowlist="0123456789.-")
    assert observed == [([[1, 4], [6, 4], [6, 9], [1, 9]], "16.25", 0.99)]
