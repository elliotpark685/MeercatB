"""Fail-closed, non-persistent runtime boundary for Golden-validated TRT35 charts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.crane.trt35_golden_reference import load_trt35_human_golden_result
from app.crane.trt35_vertical_slice import (
    TRT35_PAGE11_LOWER_50_TABLE_BBOX_PDF,
    TRT35_PAGE11_UPPER_100_TABLE_BBOX_PDF,
    TRT35_PAGE12_LOWER_ON_TIRES_TABLE_BBOX_PDF,
    TRT35_PAGE12_UPPER_ON_TIRES_TABLE_BBOX_PDF,
    TRT35_PAGE15_LEFT_LATTICE_JIB_0_TABLE_BBOX_PDF,
    TRT35_PAGE15_RIGHT_LATTICE_JIB_20_TABLE_BBOX_PDF,
    Trt35TableIdentity,
    Trt35VerticalSliceResult,
    trt35_page11_lower_50_identity,
    trt35_page12_lower_on_tires_identity,
    trt35_page12_upper_on_tires_identity,
    trt35_page15_left_lattice_jib_0_identity,
    trt35_page15_right_lattice_jib_20_identity,
)


TRT35_REFERENCE_FILE_HASH_SHA256 = "7048039dfe68b0626f72966c3ce2db635559443cb131652ff89fa834e27e3207"
TRT35_RUNTIME_VERSION = "0.2.0-human-golden-reference"


class Trt35OnboardingRequiredError(ValueError):
    """Raised when an upload is not the exact Golden-validated TRT35 input."""


@dataclass(frozen=True)
class Trt35ConfigurationDefinition:
    configuration: str
    table_bbox_pdf: tuple[float, float, float, float]
    identity: Trt35TableIdentity


TRT35_CONFIGURATIONS: dict[str, Trt35ConfigurationDefinition] = {
    "PAGE_11_UPPER_100_OUTRIGGER": Trt35ConfigurationDefinition(
        configuration="PAGE_11_UPPER_100_OUTRIGGER",
        table_bbox_pdf=TRT35_PAGE11_UPPER_100_TABLE_BBOX_PDF,
        identity=Trt35TableIdentity(),
    ),
    "PAGE_11_LOWER_50_OUTRIGGER": Trt35ConfigurationDefinition(
        configuration="PAGE_11_LOWER_50_OUTRIGGER",
        table_bbox_pdf=TRT35_PAGE11_LOWER_50_TABLE_BBOX_PDF,
        identity=trt35_page11_lower_50_identity(),
    ),
    "PAGE_12_UPPER_ON_TIRES_360_0_KMH": Trt35ConfigurationDefinition(
        configuration="PAGE_12_UPPER_ON_TIRES_360_0_KMH",
        table_bbox_pdf=TRT35_PAGE12_UPPER_ON_TIRES_TABLE_BBOX_PDF,
        identity=trt35_page12_upper_on_tires_identity(),
    ),
    "PAGE_12_LOWER_ON_TIRES_0_MAX_2_KMH": Trt35ConfigurationDefinition(
        configuration="PAGE_12_LOWER_ON_TIRES_0_MAX_2_KMH",
        table_bbox_pdf=TRT35_PAGE12_LOWER_ON_TIRES_TABLE_BBOX_PDF,
        identity=trt35_page12_lower_on_tires_identity(),
    ),
    "PAGE_15_LEFT_LATTICE_JIB_8M_0_DEG": Trt35ConfigurationDefinition(
        configuration="PAGE_15_LEFT_LATTICE_JIB_8M_0_DEG",
        table_bbox_pdf=TRT35_PAGE15_LEFT_LATTICE_JIB_0_TABLE_BBOX_PDF,
        identity=trt35_page15_left_lattice_jib_0_identity(),
    ),
    "PAGE_15_RIGHT_LATTICE_JIB_8M_20_DEG": Trt35ConfigurationDefinition(
        configuration="PAGE_15_RIGHT_LATTICE_JIB_8M_20_DEG",
        table_bbox_pdf=TRT35_PAGE15_RIGHT_LATTICE_JIB_20_TABLE_BBOX_PDF,
        identity=trt35_page15_right_lattice_jib_20_identity(),
    ),
}


def parse_trt35_reference_pdf(payload: bytes, *, configuration: str) -> Trt35VerticalSliceResult:
    """Return reviewed cells for exactly one approved PDF revision/configuration."""
    definition = TRT35_CONFIGURATIONS.get(configuration)
    if definition is None:
        raise Trt35OnboardingRequiredError("TRT35 configuration is not Golden-validated; onboarding required")
    if hashlib.sha256(payload).hexdigest() != TRT35_REFERENCE_FILE_HASH_SHA256:
        raise Trt35OnboardingRequiredError("TRT35 PDF revision is not Golden-validated; onboarding required")

    # The exact document and every returned cell are Human Golden-verified.
    # Do not rerun OCR here: a less certain OCR observation must not replace a
    # verified manufacturer-table value during a safety review.
    return load_trt35_human_golden_result(
        configuration,
        expected_document_hash=TRT35_REFERENCE_FILE_HASH_SHA256,
        parser_version=TRT35_RUNTIME_VERSION,
    )
