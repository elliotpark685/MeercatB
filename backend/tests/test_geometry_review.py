import pytest

from app.crane.geometry_review import (
    MainBoomReachReviewService,
    RangeGraphDataset,
    RangeGraphPoint,
    ReachReviewInput,
    ReachStatus,
)
from app.crane.trt60_schema import SourceEvidence


def _dataset() -> RangeGraphDataset:
    return RangeGraphDataset(
        manufacturer="Terex",
        model="TRT60",
        file_hash_sha256="test-reference-hash",
        parser_profile="TEREX_TRT",
        parser_version="0.5.0-poc.2",
        points=[
            RangeGraphPoint(
                boom_length_m=33.0,
                working_radius_m=16.0,
                maximum_hook_height_m=31.0,
                source=SourceEvidence(source_page=10, source_text="Human-verified range graph point", source_bbox=(100, 200, 110, 210)),
            )
        ],
    )


def test_reach_review_passes_exact_human_verified_point():
    result = MainBoomReachReviewService().review(
        ReachReviewInput(boom_length_m=33.0, working_radius_m=16.0, required_hook_height_m=30.0),
        _dataset(),
    )
    assert result.status == ReachStatus.PASS
    assert result.height_margin_m == 1.0
    assert result.source_page == 10
    assert result.approval == "NOT_GRANTED"


def test_reach_review_fails_when_required_height_exceeds_verified_height():
    result = MainBoomReachReviewService().review(
        ReachReviewInput(boom_length_m=33.0, working_radius_m=16.0, required_hook_height_m=31.1),
        _dataset(),
    )
    assert result.status == ReachStatus.FAIL
    assert result.height_margin_m == pytest.approx(-0.1)


def test_reach_review_never_interpolates_missing_point():
    result = MainBoomReachReviewService().review(
        ReachReviewInput(boom_length_m=33.0, working_radius_m=16.1, required_hook_height_m=30.0),
        _dataset(),
    )
    assert result.status == ReachStatus.POINT_NOT_FOUND
    assert result.maximum_hook_height_m is None


def test_reach_review_requires_human_verified_source_dataset():
    result = MainBoomReachReviewService().review(
        ReachReviewInput(boom_length_m=33.0, working_radius_m=16.0, required_hook_height_m=30.0),
        None,
    )
    assert result.status == ReachStatus.REFERENCE_DATASET_REQUIRED
