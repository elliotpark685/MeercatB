"""Revision-bound TRT35 range-graph Golden lookup."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.crane.geometry_review import RangeGraphDataset, RangeGraphPoint
from app.crane.trt60_schema import SourceEvidence


class Trt35GeometryGoldenDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    configuration: str
    height_reference: str
    capacity_boom_length_m: float = Field(gt=0)
    geometry_boom_length_m: float = Field(gt=0)
    source_page: int = Field(ge=1)
    points: list[RangeGraphPoint] = Field(min_length=1)


class Trt35GeometryGoldenReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manufacturer: str
    model: str
    file_hash_sha256: str
    parser_profile: str
    parser_version: str
    datasets: list[Trt35GeometryGoldenDataset] = Field(min_length=1)


@dataclass(frozen=True)
class Trt35GeometryLookup:
    dataset: RangeGraphDataset
    geometry_boom_length_m: float
    height_reference: str


_DATASET_PATH = Path(__file__).parents[2] / "evaluation" / "datasets" / "trt35_geometry_golden.json"
_MAIN_BOOM_CAPACITY_CONFIGURATIONS = {
    "PAGE_11_UPPER_100_OUTRIGGER",
    "PAGE_11_LOWER_50_OUTRIGGER",
    "PAGE_12_UPPER_ON_TIRES_360_0_KMH",
    "PAGE_12_LOWER_ON_TIRES_0_MAX_2_KMH",
}
_JIB_CONFIGURATION_TO_GOLDEN = {
    "PAGE_15_LEFT_LATTICE_JIB_8M_0_DEG": "LATTICE_JIB_8M_0DEG",
    "PAGE_15_RIGHT_LATTICE_JIB_8M_20_DEG": "LATTICE_JIB_8M_20DEG",
}


@lru_cache(maxsize=1)
def load_trt35_geometry_golden_reference() -> Trt35GeometryGoldenReference:
    return Trt35GeometryGoldenReference.model_validate_json(_DATASET_PATH.read_text(encoding="utf-8"))


def get_trt35_geometry_lookup(
    *,
    capacity_configuration: str,
    capacity_boom_length_m: float,
    expected_document_hash: str,
) -> Trt35GeometryLookup | None:
    """Return only the exact, registered range graph for the selected chart."""
    reference = load_trt35_geometry_golden_reference()
    if reference.file_hash_sha256 != expected_document_hash:
        raise ValueError("TRT35 Geometry Golden source document hash mismatch")
    if capacity_configuration in _MAIN_BOOM_CAPACITY_CONFIGURATIONS:
        golden_configuration = f"MAIN_BOOM_{capacity_boom_length_m:.1f}M"
    else:
        golden_configuration = _JIB_CONFIGURATION_TO_GOLDEN.get(capacity_configuration)
    if golden_configuration is None:
        return None
    golden = next((item for item in reference.datasets if item.configuration == golden_configuration), None)
    if golden is None or golden.capacity_boom_length_m != capacity_boom_length_m:
        return None
    dataset = RangeGraphDataset(
        manufacturer=reference.manufacturer,
        model=reference.model,
        file_hash_sha256=reference.file_hash_sha256,
        parser_profile=reference.parser_profile,
        parser_version=reference.parser_version,
        points=golden.points,
    )
    return Trt35GeometryLookup(
        dataset=dataset,
        geometry_boom_length_m=golden.geometry_boom_length_m,
        height_reference=golden.height_reference,
    )
