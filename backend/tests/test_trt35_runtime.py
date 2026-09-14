import hashlib
import io

import fitz
import pytest
from fastapi.testclient import TestClient

import app.api.v1.endpoints.cranes as crane_endpoints
from app.crane.document_intake import DocumentSupportStatus, EquipmentDocumentIntakeService
from app.crane.trt35_runtime import (
    TRT35_CONFIGURATIONS,
    TRT35_REFERENCE_FILE_HASH_SHA256,
    Trt35OnboardingRequiredError,
    parse_trt35_reference_pdf,
)
from app.crane.trt35_golden_reference import load_trt35_human_golden_result
from app.main import app


def _pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((40, 80), text)
    payload = document.tobytes()
    document.close()
    return payload


def test_trt35_runtime_exposes_only_the_six_human_golden_configurations():
    assert set(TRT35_CONFIGURATIONS) == {
        "PAGE_11_UPPER_100_OUTRIGGER",
        "PAGE_11_LOWER_50_OUTRIGGER",
        "PAGE_12_UPPER_ON_TIRES_360_0_KMH",
        "PAGE_12_LOWER_ON_TIRES_0_MAX_2_KMH",
        "PAGE_15_LEFT_LATTICE_JIB_8M_0_DEG",
        "PAGE_15_RIGHT_LATTICE_JIB_8M_20_DEG",
    }


@pytest.mark.parametrize(
    ("configuration", "expected_cell_count"),
    [
        ("PAGE_11_UPPER_100_OUTRIGGER", 135),
        ("PAGE_11_LOWER_50_OUTRIGGER", 100),
        ("PAGE_12_UPPER_ON_TIRES_360_0_KMH", 68),
        ("PAGE_12_LOWER_ON_TIRES_0_MAX_2_KMH", 51),
        ("PAGE_15_LEFT_LATTICE_JIB_8M_0_DEG", 160),
        ("PAGE_15_RIGHT_LATTICE_JIB_8M_20_DEG", 160),
    ],
)
def test_human_golden_runtime_reference_has_no_unresolved_cells(configuration, expected_cell_count):
    result = load_trt35_human_golden_result(
        configuration,
        expected_document_hash=TRT35_REFERENCE_FILE_HASH_SHA256,
        parser_version="test",
    )
    assert result.grid_status == "PASS"
    assert len(result.cells) == expected_cell_count
    assert all(cell.cell_status in {"AVAILABLE", "NOT_AVAILABLE"} for cell in result.cells)
    assert not result.critical_errors


def test_trt35_runtime_rejects_unknown_configuration_before_parsing():
    with pytest.raises(Trt35OnboardingRequiredError, match="configuration"):
        parse_trt35_reference_pdf(b"not a PDF", configuration="UNREGISTERED_TABLE")


def test_trt35_runtime_rejects_different_pdf_revision_before_ocr():
    payload = _pdf("Terex TRT 35")
    assert hashlib.sha256(payload).hexdigest() != TRT35_REFERENCE_FILE_HASH_SHA256
    with pytest.raises(Trt35OnboardingRequiredError, match="revision"):
        parse_trt35_reference_pdf(payload, configuration="PAGE_11_UPPER_100_OUTRIGGER")


def test_intake_requires_onboarding_for_a_trt35_revision_without_golden_hash():
    result = EquipmentDocumentIntakeService().inspect_pdf_bytes(_pdf("Terex TRT 35"), source_name="revised-trt35.pdf")
    assert result.support_status == DocumentSupportStatus.ONBOARDING_REQUIRED
    assert result.identity is None
    assert result.reason == "Registered parser profile exists, but this PDF revision is not Golden-validated"


def test_trt35_parse_api_rejects_unknown_configuration_without_persistence():
    response = TestClient(app).post(
        "/api/v1/cranes/trt35/parse",
        data={"configuration": "UNREGISTERED_TABLE"},
        files={"file": ("trt35.pdf", io.BytesIO(_pdf("Terex TRT 35")), "application/pdf")},
    )
    assert response.status_code == 422
    assert "configuration" in response.json()["detail"]


def test_trt35_parse_api_rejects_unvalidated_revision_without_persistence():
    response = TestClient(app).post(
        "/api/v1/cranes/trt35/parse",
        data={"configuration": "PAGE_11_UPPER_100_OUTRIGGER"},
        files={"file": ("trt35.pdf", io.BytesIO(_pdf("Terex TRT 35")), "application/pdf")},
    )
    assert response.status_code == 422
    assert "revision" in response.json()["detail"]


def test_trt35_parse_api_allows_the_production_frontend_origin_in_preflight_and_errors():
    client = TestClient(app)
    preflight = client.options(
        "/api/v1/cranes/trt35/parse",
        headers={
            "Origin": "https://meerkat-safety.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "https://meerkat-safety.com"

    rejected = client.post(
        "/api/v1/cranes/trt35/parse",
        headers={"Origin": "https://meerkat-safety.com"},
        data={"configuration": "PAGE_11_UPPER_100_OUTRIGGER"},
        files={"file": ("unvalidated.pdf", io.BytesIO(_pdf("Terex TRT 35")), "application/pdf")},
    )
    assert rejected.status_code == 422
    assert rejected.headers["access-control-allow-origin"] == "https://meerkat-safety.com"


def test_trt35_parse_api_returns_cors_compatible_503_when_reference_loading_fails(monkeypatch):
    def raise_reference_loading_failure(*_args, **_kwargs):
        raise OSError("reference assets are unavailable")

    monkeypatch.setattr(crane_endpoints, "parse_trt35_reference_pdf", raise_reference_loading_failure)
    response = TestClient(app).post(
        "/api/v1/cranes/trt35/parse",
        headers={"Origin": "https://meerkat-safety.com"},
        data={"configuration": "PAGE_11_UPPER_100_OUTRIGGER"},
        files={"file": ("trt35.pdf", io.BytesIO(_pdf("Terex TRT 35")), "application/pdf")},
    )
    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == "https://meerkat-safety.com"
    assert response.json()["detail"] == "TRT35 verified reference data is temporarily unavailable; retry later or contact an administrator"
