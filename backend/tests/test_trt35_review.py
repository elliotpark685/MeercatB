from app.crane.trt35_golden_reference import load_trt35_human_golden_result
from app.crane.trt35_review import Trt35CapacityStatus, Trt35EngineeringReviewService, Trt35ReviewInput
from app.crane.trt35_runtime import TRT35_REFERENCE_FILE_HASH_SHA256


def _chart():
    return load_trt35_human_golden_result(
        "PAGE_11_UPPER_100_OUTRIGGER",
        expected_document_hash=TRT35_REFERENCE_FILE_HASH_SHA256,
        parser_version="test",
    )


def test_review_calculates_exact_cell_capacity_and_total_lifted_load():
    result = Trt35EngineeringReviewService().review(
        _chart(),
        Trt35ReviewInput(
            radius_m=3.0,
            boom_length_m=9.1,
            required_height_m=5.0,
            payload_t=30.0,
            sling_leg_count=2,
            sling_weight_per_leg_t=0.5,
            hook_block_t=1.0,
            spreader_t=1.0,
            configuration_confirmed=True,
        ),
    )
    assert result.gross_load_t == 33.0
    assert result.rated_capacity_t == 35.0
    assert result.capacity_margin_t == 2.0
    assert result.capacity_status == Trt35CapacityStatus.PASS
    assert result.geometry_status == "REFERENCE_DATASET_REQUIRED"


def test_review_refuses_interpolation_and_unconfirmed_configuration():
    service = Trt35EngineeringReviewService()
    unconfirmed = service.review(
        _chart(),
        Trt35ReviewInput(radius_m=3, boom_length_m=9.1, required_height_m=5, payload_t=1),
    )
    assert unconfirmed.capacity_status == Trt35CapacityStatus.CONFIGURATION_NOT_CONFIRMED
    no_cell = service.review(
        _chart(),
        Trt35ReviewInput(radius_m=3.1, boom_length_m=9.1, required_height_m=5, payload_t=1, configuration_confirmed=True),
    )
    assert no_cell.capacity_status == Trt35CapacityStatus.CELL_NOT_FOUND


def test_review_api_returns_exact_capacity_check_without_persistence(monkeypatch):
    monkeypatch.setattr(crane_endpoints, "parse_trt35_reference_pdf", lambda *_args, **_kwargs: _chart())
    response = TestClient(app).post(
        "/api/v1/cranes/trt35/review",
        data={
            "configuration": "PAGE_11_UPPER_100_OUTRIGGER",
            "review": json.dumps({
                "radius_m": 3, "boom_length_m": 9.1, "required_height_m": 5,
                "payload_t": 30, "rigging_t": 1, "hook_block_t": 1, "spreader_t": 1,
                "configuration_confirmed": True,
            }),
        },
        files={"file": ("trt35.pdf", io.BytesIO(b"%PDF-1.7\nplaceholder"), "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["review_result"]["capacity_status"] == "PASS"
    assert response.json()["review_result"]["geometry_status"] == "REFERENCE_DATASET_REQUIRED"
    assert response.json()["persisted"] is False
import io
import json

from fastapi.testclient import TestClient

import app.api.v1.endpoints.cranes as crane_endpoints
from app.main import app
