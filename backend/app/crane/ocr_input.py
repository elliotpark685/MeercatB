"""Deterministic adapters for OCR engine output.

The adapter intentionally performs no character correction. Invalid or
unsupported observations remain representable as tokens and are resolved by
the cell-status policy, never silently rewritten into a number.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping

from app.crane.ocr_table_association import OcrToken


def tokens_from_easyocr(items: Iterable[Mapping]) -> list[OcrToken]:
    """Convert EasyOCR-style `{bbox, text, confidence}` records to tokens."""
    tokens: list[OcrToken] = []
    for item in items:
        bbox = item.get("bbox") or item.get("bbox_pdf")
        if bbox is None or len(bbox) != 4:
            continue
        tokens.append(OcrToken(text=str(item.get("text", "")).strip(), confidence=float(item.get("confidence", 0)), bbox=tuple(float(v) for v in bbox)))
    return tokens


def tokens_from_json(payload: str | bytes) -> list[OcrToken]:
    """Load a previously captured OCR result without changing its values."""
    value = json.loads(payload)
    if not isinstance(value, list):
        raise ValueError("OCR capture must be a JSON list")
    return tokens_from_easyocr(value)
