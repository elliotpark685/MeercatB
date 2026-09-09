"""Evidence-bound Main Boom reach review.

This module intentionally does not derive a hook-height curve from a PDF image.
It evaluates only exact, human-verified range-graph points.  Capacity review,
obstacle clearance, and operational approval remain separate concerns.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.crane.trt60_schema import SourceEvidence


class ReachStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    POINT_NOT_FOUND = "POINT_NOT_FOUND"
    REFERENCE_DATASET_REQUIRED = "REFERENCE_DATASET_REQUIRED"


class RangeGraphPoint(BaseModel):
    """One human-verified point from a manufacturer Main Boom range graph."""

    model_config = ConfigDict(extra="forbid")
    boom_length_m: float = Field(gt=0)
    working_radius_m: float = Field(gt=0)
    maximum_hook_height_m: float = Field(gt=0)
    source: SourceEvidence


class RangeGraphDataset(BaseModel):
    """A revision-bound set of verified points for one crane/range-graph page."""

    model_config = ConfigDict(extra="forbid")
    manufacturer: str
    model: str
    file_hash_sha256: str
    parser_profile: str
    parser_version: str
    points: list[RangeGraphPoint] = Field(min_length=1)


class ReachReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    boom_length_m: float = Field(gt=0)
    working_radius_m: float = Field(gt=0)
    required_hook_height_m: float = Field(gt=0)


class ReachReviewResult(BaseModel):
    status: ReachStatus
    boom_length_m: float
    working_radius_m: float
    required_hook_height_m: float
    maximum_hook_height_m: float | None = None
    height_margin_m: float | None = None
    source_page: int | None = None
    source_bbox: tuple[float, float, float, float] | None = None
    reason: str | None = None
    approval: str = "NOT_GRANTED"


class MainBoomReachReviewService:
    """Performs an exact-match reach check against a verified range-graph dataset."""

    def review(self, request: ReachReviewInput, dataset: RangeGraphDataset | None) -> ReachReviewResult:
        base = {
            "boom_length_m": request.boom_length_m,
            "working_radius_m": request.working_radius_m,
            "required_hook_height_m": request.required_hook_height_m,
        }
        if dataset is None:
            return ReachReviewResult(
                status=ReachStatus.REFERENCE_DATASET_REQUIRED,
                reason="A human-verified manufacturer range-graph dataset is required before reach review",
                **base,
            )
        point = next(
            (
                item
                for item in dataset.points
                if item.boom_length_m == request.boom_length_m and item.working_radius_m == request.working_radius_m
            ),
            None,
        )
        if point is None:
            return ReachReviewResult(
                status=ReachStatus.POINT_NOT_FOUND,
                reason="Exact range-graph point not found; interpolation is disabled",
                **base,
            )
        margin = point.maximum_hook_height_m - request.required_hook_height_m
        return ReachReviewResult(
            status=ReachStatus.PASS if margin >= 0 else ReachStatus.FAIL,
            maximum_hook_height_m=point.maximum_hook_height_m,
            height_margin_m=margin,
            source_page=point.source.source_page,
            source_bbox=point.source.source_bbox,
            **base,
        )
