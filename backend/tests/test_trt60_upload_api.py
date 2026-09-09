import io
import json
from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from app.api.v1.endpoints import cranes as crane_endpoints
from app.core.config import settings
from app.main import app


def _fixture_pdf() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((40, 80), "[PAGE:1]\nTerex TRT60\nMAIN BOOM LOAD CHART\nCounterweight: 6 t\nOutrigger: 100%\nOutrigger Width: 7 m\nWorking Area: 360 deg\nRadius (m) 12m 18m\n5 12.5 12500kg\n10 8.0 -")
    payload = document.tobytes()
    document.close()
    return payload


def test_trt60_upload_returns_parser_and_mapping_payload():
    response = TestClient(app).post(
        "/api/v1/cranes/trt60/parse",
        files={"file": ("trt60.pdf", io.BytesIO(_fixture_pdf()), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["parser_result"]["parser_verification_status"] == "AUTO_PARSED"
    assert body["persisted"] is False
    assert body["supabase_rows"]["cranes"][0]["model"] == "TRT60"
    assert len(body["supabase_rows"]["load_chart_cells"]) == 4


def test_trt60_review_requires_the_golden_validated_pdf_revision():
    response = TestClient(app).post(
        "/api/v1/cranes/trt60/review",
        data={"review": json.dumps({"chart_source_page": 11, "radius_m": 2.3, "boom_length_m": 10.5, "required_height_m": 20, "payload_t": 10})},
        files={"file": ("trt60.pdf", io.BytesIO(_fixture_pdf()), "application/pdf")},
    )
    assert response.status_code == 422
    assert "Golden-validated reference PDF revision" in response.json()["detail"]


def test_trt60_review_returns_preliminary_result_without_persistence():
    pdf = Path(r"C:\Meerkat\MobileCrane\Terex\trt60_datasheet_metric_en-fr-de-it-es-pt-ru.pdf")
    if not pdf.exists():
        return
    confirmed = {"counterweight_t": 6, "support_mode": "OUTRIGGER", "outrigger_percent": 100, "outrigger_width_m": 7.0, "outrigger_length_m": 7.3, "working_area": "360" + chr(176)}
    response = TestClient(app).post(
        "/api/v1/cranes/trt60/review",
        data={"review": json.dumps({"chart_source_page": 11, "radius_m": 2.3, "boom_length_m": 10.5, "required_height_m": 20, "payload_t": 10, "rigging_t": 0.5, "confirmed_configuration": confirmed})},
        files={"file": (pdf.name, pdf.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_result"]["capacity_status"] == "PASS"
    assert body["review_result"]["geometry_status"] == "NOT_IMPLEMENTED"
    assert body["approval"] == "NOT_GRANTED"
    assert body["persisted"] is False


def test_trt60_upload_rejects_empty_non_pdf_and_oversized_payloads(monkeypatch):
    client = TestClient(app)
    empty = client.post("/api/v1/cranes/trt60/parse", files={"file": ("trt60.pdf", b"", "application/pdf")})
    assert empty.status_code == 400

    wrong_media_type = client.post("/api/v1/cranes/trt60/parse", files={"file": ("trt60.pdf", _fixture_pdf(), "text/plain")})
    assert wrong_media_type.status_code == 415

    wrong_signature = client.post("/api/v1/cranes/trt60/parse", files={"file": ("trt60.pdf", b"not-a-pdf", "application/pdf")})
    assert wrong_signature.status_code == 415

    monkeypatch.setattr(settings, "crane_pdf_max_upload_bytes", 10)
    oversized = client.post("/api/v1/cranes/trt60/parse", files={"file": ("trt60.pdf", _fixture_pdf(), "application/pdf")})
    assert oversized.status_code == 413


def test_trt60_review_returns_422_for_invalid_review_json_and_fields():
    client = TestClient(app)
    invalid_json = client.post("/api/v1/cranes/trt60/review", data={"review": "{"}, files={"file": ("trt60.pdf", _fixture_pdf(), "application/pdf")})
    assert invalid_json.status_code == 422

    invalid_fields = client.post("/api/v1/cranes/trt60/review", data={"review": json.dumps({"chart_source_page": 11})}, files={"file": ("trt60.pdf", _fixture_pdf(), "application/pdf")})
    assert invalid_fields.status_code == 422


def test_trt60_upload_dispatches_parser_through_threadpool(monkeypatch):
    calls = []
    original = crane_endpoints.run_in_threadpool

    async def tracking_threadpool(function, *args, **kwargs):
        calls.append(function.__name__)
        return await original(function, *args, **kwargs)

    monkeypatch.setattr(crane_endpoints, "run_in_threadpool", tracking_threadpool)
    response = TestClient(app).post("/api/v1/cranes/trt60/parse", files={"file": ("trt60.pdf", _fixture_pdf(), "application/pdf")})
    assert response.status_code == 200
    assert calls == ["parse_pdf_bytes"]


def test_trt60_review_openapi_declares_multipart_contract():
    schema = TestClient(app).get("/openapi.json").json()
    operation = schema["paths"]["/api/v1/cranes/trt60/review"]["post"]
    assert "Multipart form" in operation["description"]
    assert "multipart/form-data" in operation["requestBody"]["content"]
