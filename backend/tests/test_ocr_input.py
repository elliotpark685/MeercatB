import json

import pytest

from app.crane.ocr_input import tokens_from_easyocr, tokens_from_json
from app.crane.ocr_table_association import OcrToken


def test_ocr_adapter_preserves_text_confidence_and_pdf_bbox():
    tokens = tokens_from_easyocr([{"text": "35.00", "confidence": 0.99, "bbox_pdf": [1, 2, 3, 4]}])
    assert tokens == [OcrToken(text="35.00", confidence=0.99, bbox=(1.0, 2.0, 3.0, 4.0))]


def test_ocr_adapter_does_not_correct_ambiguous_characters():
    token = tokens_from_json(json.dumps([{"text": "35O", "confidence": 0.99, "bbox": [1, 2, 3, 4]}]))[0]
    assert token.text == "35O"


def test_ocr_token_rejects_invalid_bbox():
    with pytest.raises(ValueError):
        OcrToken(text="35.00", confidence=0.99, bbox=(3, 2, 1, 4))
