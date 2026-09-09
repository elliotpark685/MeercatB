import io

import fitz
from fastapi.testclient import TestClient

from app.crane.document_intake import DocumentSupportStatus, EquipmentDocumentIntakeService
from app.main import app


def _pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((40, 80), text)
    payload = document.tobytes()
    document.close()
    return payload


def test_intake_selects_only_the_registered_trt60_profile():
    result = EquipmentDocumentIntakeService().inspect_pdf_bytes(
        _pdf("Terex TRT 60\nRough terrain crane"), source_name="trt60.pdf"
    )
    assert result.support_status == DocumentSupportStatus.SUPPORTED_PROFILE
    assert result.identity is not None
    assert result.identity.model == "TRT60"
    assert result.identity.parser_profile == "TEREX_TRT"
    assert result.identity.source.source_page == 1
    assert result.persisted is False


def test_intake_never_routes_unknown_equipment_to_trt60_parser():
    result = EquipmentDocumentIntakeService().inspect_pdf_bytes(
        _pdf("Example Manufacturer ZX 500\nLoad chart"), source_name="unknown.pdf"
    )
    assert result.support_status == DocumentSupportStatus.ONBOARDING_REQUIRED
    assert result.identity is None
    assert "do not run" in result.reason


def test_intake_keeps_an_unonboarded_trt_model_out_of_the_trt60_profile():
    result = EquipmentDocumentIntakeService().inspect_pdf_bytes(
        _pdf("Terex TRT 35\nRough terrain crane"), source_name="trt35.pdf"
    )
    assert result.support_status == DocumentSupportStatus.ONBOARDING_REQUIRED
    assert result.identity is None


def test_common_inspection_api_returns_onboarding_status_without_persistence():
    response = TestClient(app).post(
        "/api/v1/cranes/inspect",
        files={"file": ("unknown.pdf", io.BytesIO(_pdf("Unknown Crane Model")), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document"]["support_status"] == DocumentSupportStatus.ONBOARDING_REQUIRED
    assert body["persisted"] is False
