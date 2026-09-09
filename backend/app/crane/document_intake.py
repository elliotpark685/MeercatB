"""Safe common intake for crane-equipment PDF documents.

Intake identifies a document against explicitly registered parser profiles.  It
does not send an unknown PDF through a model-specific parser and it does not
persist anything.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

import fitz
from pydantic import BaseModel, ConfigDict, Field

from app.crane.trt60_schema import SourceEvidence


class DocumentSupportStatus(str):
    SUPPORTED_PROFILE = "SUPPORTED_PROFILE"
    ONBOARDING_REQUIRED = "ONBOARDING_REQUIRED"


class EquipmentDocumentIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manufacturer: str
    model: str
    equipment_type: str
    parser_profile: str
    parser_version: str
    source: SourceEvidence


class EquipmentDocumentIntakeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original_filename: str
    file_hash_sha256: str
    page_count: int = Field(ge=1)
    support_status: str
    identity: EquipmentDocumentIdentity | None = None
    reason: str | None = None
    persisted: bool = False


@dataclass(frozen=True)
class RegisteredParserProfile:
    manufacturer: str
    model: str
    equipment_type: str
    parser_profile: str
    parser_version: str
    manufacturer_pattern: re.Pattern[str]
    model_pattern: re.Pattern[str]

    def matches(self, text: str) -> bool:
        return bool(self.manufacturer_pattern.search(text) and self.model_pattern.search(text))


REGISTERED_PARSER_PROFILES: tuple[RegisteredParserProfile, ...] = (
    RegisteredParserProfile(
        manufacturer="Terex",
        model="TRT60",
        equipment_type="rough_terrain_crane",
        parser_profile="TEREX_TRT",
        parser_version="0.5.0-poc.2",
        manufacturer_pattern=re.compile(r"\bterex\b", re.IGNORECASE),
        model_pattern=re.compile(r"\btrt\s*60\b", re.IGNORECASE),
    ),
)


class EquipmentDocumentIntakeService:
    """Classify supported PDFs before choosing any equipment-specific parser."""

    def inspect_pdf_bytes(self, payload: bytes, *, source_name: str) -> EquipmentDocumentIntakeResult:
        if not payload.startswith(b"%PDF-"):
            raise ValueError("Upload content is not a PDF")
        try:
            document = fitz.open(stream=payload, filetype="pdf")
        except (fitz.FileDataError, RuntimeError, ValueError) as exc:
            raise ValueError("PDF could not be opened for document intake") from exc
        try:
            pages = list(document)
            if not pages:
                raise ValueError("PDF has no pages")
            page_text = [(number, page.get_text("text")) for number, page in enumerate(pages, start=1)]
            combined_text = "\n".join(text for _, text in page_text)
            result_base = {
                "original_filename": source_name,
                "file_hash_sha256": hashlib.sha256(payload).hexdigest(),
                "page_count": len(pages),
            }
            profile = next((item for item in REGISTERED_PARSER_PROFILES if item.matches(combined_text)), None)
            if profile is None:
                return EquipmentDocumentIntakeResult(
                    support_status=DocumentSupportStatus.ONBOARDING_REQUIRED,
                    reason="No registered parser profile matches this PDF; do not run a model-specific parser",
                    **result_base,
                )
            model_page_number, model_text = next((item for item in page_text if profile.model_pattern.search(item[1])), page_text[0])
            model_bbox = next(iter(pages[model_page_number - 1].search_for(profile.model_pattern.search(model_text).group(0))), None)
            source = SourceEvidence(
                source_page=model_page_number,
                source_text=profile.model_pattern.search(model_text).group(0),
                source_bbox=tuple(model_bbox) if model_bbox else None,
            )
            return EquipmentDocumentIntakeResult(
                support_status=DocumentSupportStatus.SUPPORTED_PROFILE,
                identity=EquipmentDocumentIdentity(
                    manufacturer=profile.manufacturer,
                    model=profile.model,
                    equipment_type=profile.equipment_type,
                    parser_profile=profile.parser_profile,
                    parser_version=profile.parser_version,
                    source=source,
                ),
                **result_base,
            )
        finally:
            document.close()
