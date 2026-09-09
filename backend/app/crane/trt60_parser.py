"""Deterministic Terex TRT60 text parser (v0.5 PoC).

The parser intentionally accepts a small, explicit text contract. It never
interpolates missing cells and rejects ambiguous configuration/table input.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.crane.trt60_schema import (
    CanonicalTRT60Data,
    CellStatus,
    ConfigurationHeader,
    LoadChart,
    LoadChartCell,
    ParserVerificationStatus,
    SourceEvidence,
)

NUMBER = r"[-+]?\d+(?:[.,]\d+)?"
_NUM_RE = re.compile(NUMBER)


@dataclass(frozen=True)
class TextPage:
    number: int
    text: str


def _number(value: str) -> float:
    return float(value.replace(",", "."))


def _value_with_unit(text: str) -> tuple[float, str]:
    match = _NUM_RE.search(text)
    if not match:
        raise ValueError(f"no numeric value in {text!r}")
    value = _number(match.group())
    unit = text[match.end():].strip().lower()
    return value, unit


def _capacity(value: str) -> tuple[float, float, str]:
    parsed, unit = _value_with_unit(value)
    if "kg" in unit:
        return parsed / 1000, parsed, "kg"
    if unit in {"t", "ton", "tonne", "metric_tonne", ""}:
        return parsed, parsed, "t"
    raise ValueError(f"unsupported capacity unit: {unit}")


class TerexTRT60Parser:
    parser_profile = "TEREX_TRT"
    parser_version = "0.5.0-poc.2"

    def inspect(self, pages: list[TextPage]) -> dict[str, str | list[int]]:
        text = "\n".join(page.text for page in pages)
        if not re.search(r"\bTerex\b", text, re.I) or not re.search(r"\bTRT\s*60\b", text, re.I):
            raise ValueError("document is not identifiable as Terex TRT60")
        chart_pages = [page.number for page in pages if self.classify_page(page) == "MAIN_BOOM_LOAD_CHART"]
        return {"manufacturer": "Terex", "model": "TRT60", "chart_pages": chart_pages}

    @staticmethod
    def classify_page(page: TextPage) -> str:
        text = page.text.lower()
        if "load chart" in text and "jib" in text:
            return "JIB_LOAD_CHART"
        if "load chart" in text and ("radius" in text or "boom" in text):
            return "MAIN_BOOM_LOAD_CHART"
        return "OTHER"

    def parse_text(self, text: str, *, source_name: str = "inline.txt") -> CanonicalTRT60Data:
        pages = self._pages(text)
        self.inspect(pages)
        charts: list[LoadChart] = []
        for page in pages:
            if self.classify_page(page) != "MAIN_BOOM_LOAD_CHART":
                continue
            charts.append(self._parse_chart(page))
        if not charts:
            raise ValueError("no MAIN_BOOM_LOAD_CHART page found")
        source = SourceEvidence(source_page=1, source_text=source_name)
        result = CanonicalTRT60Data(
            parser_version=self.parser_version,
            manufacturer="Terex",
            source_document=source,
            canonical_content_hash="pending",
            load_charts=charts,
            parser_verification_status=ParserVerificationStatus.AUTO_PARSED,
            validation_errors=[],
            content_hash_sha256="pending",
        )
        errors = self.validate(result)
        result.validation_errors = errors
        result.parser_verification_status = ParserVerificationStatus.AUTO_PARSED if not errors else ParserVerificationStatus.REJECTED
        result.canonical_content_hash = self.content_hash(result)
        result.content_hash_sha256 = result.canonical_content_hash
        return result

    def verify(self, data: CanonicalTRT60Data, golden_dataset: list[dict]) -> list[str]:
        """Run the separate critical and golden checks and update verification state."""
        errors = self.validate(data)
        errors.extend(self.validate_critical(data))
        errors.extend(self.validate_golden(data, golden_dataset))
        data.validation_errors = errors
        data.parser_verification_status = ParserVerificationStatus.AUTO_VALIDATED if not errors else ParserVerificationStatus.REJECTED
        data.canonical_content_hash = self.content_hash(data)
        data.content_hash_sha256 = data.canonical_content_hash
        return errors

    @staticmethod
    def validate_golden(data: CanonicalTRT60Data, golden_dataset: list[dict]) -> list[str]:
        errors: list[str] = []
        charts = [chart for chart in data.load_charts if chart.chart_type == "MAIN_BOOM_LOAD_CHART"]
        for index, expected in enumerate(golden_dataset):
            chart = next((chart for chart in charts if chart.source.source_page == expected["chart_source_page"]), None)
            if chart is None:
                errors.append(f"golden[{index}]: chart page mismatch")
                continue
            header = chart.header
            for field in ("counterweight_t", "support_mode", "outrigger_percent", "outrigger_width_m", "outrigger_length_m", "working_area"):
                if field in expected and getattr(header, field) != expected[field]:
                    errors.append(f"golden[{index}]: {field} mismatch")
            cell = next((cell for cell in chart.cells if cell.radius_m == expected["radius_m"] and cell.boom_length_m == expected["boom_length_m"]), None)
            if cell is None:
                errors.append(f"golden[{index}]: radius/boom cell missing")
                continue
            if cell.rated_capacity_t != expected["rated_capacity_t"] or cell.cell_status.value != expected["cell_status"]:
                errors.append(f"golden[{index}]: capacity/status mismatch")
        return errors

    @staticmethod
    def validate_critical(data: CanonicalTRT60Data) -> list[str]:
        errors: list[str] = []
        seen: set[tuple] = set()
        for chart_index, chart in enumerate(data.load_charts):
            for cell_index, cell in enumerate(chart.cells):
                key = (chart.source.source_page, cell.radius_m, cell.boom_length_m, cell.boom_angle_deg)
                if key in seen:
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: cross-chart cell contamination")
                seen.add(key)
                if cell.source.source_page != chart.source.source_page:
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: source page mismatch")
                if cell.source.source_bbox is None:
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: source bbox missing")
                if cell.source_capacity_unit not in {None, "t", "kg", "ton", "tonne", "metric_tonne"}:
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: unsupported capacity unit")
                if cell.source_capacity_unit == "kg" and cell.parsed_source_capacity_value is not None and cell.rated_capacity_t != cell.parsed_source_capacity_value / 1000:
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: kg normalization mismatch")
                if "interpolat" in cell.source_text.lower():
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: synthetic interpolation marker")
                if cell.cell_status == CellStatus.AVAILABLE and not re.fullmatch(r"\d+(?:[,.]\d+)?(?:kg|t)?", cell.source_text):
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: non-numeric available source")
                if cell.cell_status != CellStatus.AVAILABLE and cell.rated_capacity_t is not None:
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: unavailable cell has capacity")
        return errors

    def parse_pdf(self, path: str | Path) -> CanonicalTRT60Data:
        import fitz

        pdf_path = Path(path)
        with fitz.open(pdf_path) as document:
            return self._parse_document(document, pdf_path.name, hashlib.sha256(pdf_path.read_bytes()).hexdigest())

    def parse_pdf_bytes(self, payload: bytes, *, source_name: str) -> CanonicalTRT60Data:
        import fitz

        with fitz.open(stream=payload, filetype="pdf") as document:
            return self._parse_document(document, source_name, hashlib.sha256(payload).hexdigest())

    def _parse_document(self, document, source_name: str, file_hash_sha256: str | None = None) -> CanonicalTRT60Data:
        import fitz

        if not isinstance(document, fitz.Document):
            raise TypeError("document must be a PyMuPDF document")
        pages = [page for page in document if "LOAD CHART" in page.get_text("text").upper() and "MAIN COUNTERWEIGHT:" in page.get_text("text").upper() and "MAIN BOOM" in page.get_text("text").upper()]
        if not pages:
            text = "\n".join(f"[PAGE:{page.number + 1}]\n{page.get_text('text')}" for page in document)
            return self.parse_text(text, source_name=source_name)
        capacity_basis_source, operational_limit_source = self._trt60_capacity_basis_evidence(document)
        charts = []
        for page in pages:
            chart = self._parse_actual_chart_page(page)
            if capacity_basis_source is not None:
                chart.capacity_basis = "NET_OF_HOOK_BLOCK_AND_SLINGS"
                chart.capacity_basis_source = capacity_basis_source
                chart.operational_limit_source = operational_limit_source
            charts.append(chart)
        result = CanonicalTRT60Data(
            parser_version=self.parser_version,
            manufacturer="Terex",
            source_document=SourceEvidence(source_page=1, source_text=source_name),
            file_hash_sha256=file_hash_sha256,
            canonical_content_hash="pending",
            load_charts=charts,
            parser_verification_status=ParserVerificationStatus.AUTO_PARSED,
            validation_errors=[],
            content_hash_sha256="pending",
        )
        errors = self.validate(result)
        result.validation_errors = errors
        result.parser_verification_status = ParserVerificationStatus.AUTO_PARSED if not errors else ParserVerificationStatus.REJECTED
        result.canonical_content_hash = self.content_hash(result)
        result.content_hash_sha256 = result.canonical_content_hash
        return result

    @staticmethod
    def _trt60_capacity_basis_evidence(document) -> tuple[SourceEvidence | None, SourceEvidence | None]:
        """Use only the explicit English TRT60 manufacturer note as capacity evidence."""
        basis_text = "Weight of hook blocks and slings is considered part of the load and must be subtracted from the capacity ratings."
        limit_text = "For actual crane operation refer to the computer charts and the operating manual"
        for page in document:
            text = page.get_text("text")
            if basis_text not in text:
                continue
            basis_boxes = page.search_for(basis_text)
            limit_boxes = page.search_for(limit_text)
            basis = SourceEvidence(source_page=page.number + 1, source_text=basis_text, source_bbox=tuple(float(value) for value in basis_boxes[0]) if basis_boxes else None)
            limit = SourceEvidence(source_page=page.number + 1, source_text=limit_text, source_bbox=tuple(float(value) for value in limit_boxes[0]) if limit_boxes else None) if limit_boxes else None
            return basis, limit
        return None, None

    def _parse_actual_chart_page(self, page) -> LoadChart:
        """Parse the native-text coordinate grid used by the supplied TRT60 datasheet."""
        page_number = page.number + 1
        words = page.get_text("words")
        text = page.get_text("text")
        # Boom-length headers are horizontally arranged around y=268 in this profile.
        boom_words = [word for word in words if 250 <= word[1] <= 280 and re.fullmatch(r"\d+[,.]\d+", word[4])]
        boom_words.sort(key=lambda word: word[0])
        booms = [_number(word[4]) for word in boom_words]
        radius_words = [word for word in words if 284 <= word[1] <= 515 and word[0] < 90 and re.fullmatch(r"\d+[,.]\d+", word[4])]
        radius_words.sort(key=lambda word: word[1])
        radii = [_number(word[4]) for word in radius_words]
        if not booms or not radii:
            raise ValueError(f"page {page_number}: coordinate grid axes not found")
        x_centers = [((word[0] + word[2]) / 2) for word in boom_words]
        y_centers = [((word[1] + word[3]) / 2) for word in radius_words]
        x_gap = min((b - a for a, b in zip(x_centers, x_centers[1:])), default=30.0) / 2
        cells: list[LoadChartCell] = []
        for radius, y in zip(radii, y_centers):
            for boom, x in zip(booms, x_centers):
                candidates = [word for word in words if abs(((word[0] + word[2]) / 2) - x) < x_gap and abs(((word[1] + word[3]) / 2) - y) < 4]
                value_word = next((word for word in candidates if word[4] != "t"), None)
                raw = value_word[4] if value_word else "-"
                status = CellStatus.NOT_AVAILABLE if raw in {"-", "—"} else CellStatus.AVAILABLE
                parsed = capacity_t = None
                unit = "t"
                if status == CellStatus.AVAILABLE:
                    capacity_t = parsed = _number(raw)
                bbox = tuple(float(value) for value in value_word[:4]) if value_word else None
                source = SourceEvidence(source_page=page_number, source_text=raw, source_bbox=bbox)
                cells.append(LoadChartCell(radius_m=radius, boom_length_m=boom, rated_capacity_t=capacity_t, source_radius_text=str(radius).replace(".", ","), parsed_source_radius_value=radius, source_radius_unit="m", source_capacity_text=raw, parsed_source_capacity_value=parsed, source_capacity_unit=unit if parsed is not None else None, cell_status=status, source_text=raw, source=source, confidence=1.0))
        counterweight_match = re.search(r"Main counterweight:\s*(" + NUMBER + r")\s*t", text, re.I)
        support_match = re.search(r"(\d+)\s*%", text)
        width_match = re.search(r"(" + NUMBER + r")\s*m\s*x\s*(" + NUMBER + r")\s*m", text, re.I)
        on_tires = "ON TIRES" in text.upper()
        if not counterweight_match or (not support_match and not on_tires) or (not width_match and not on_tires):
            raise ValueError(f"page {page_number}: actual TRT60 configuration header is incomplete")
        header = ConfigurationHeader(counterweight_t=_number(counterweight_match.group(1)), support_mode="ON_TIRES" if on_tires else "OUTRIGGER", outrigger_percent=float(support_match.group(1)) if support_match else None, outrigger_width_m=_number(width_match.group(1)) if width_match else None, working_area="ON_TIRES" if on_tires else ("360°" if "360°" in text else None), source=SourceEvidence(source_page=page_number, source_text=text))
        header.outrigger_length_m = _number(width_match.group(2)) if width_match else None
        if header.working_area is None:
            raise ValueError(f"page {page_number}: working area is unresolved")
        return LoadChart(header=header, cells=cells, source=SourceEvidence(source_page=page_number, source_text=text))

    def _parse_actual_jib_page(self, page) -> list[LoadChart]:
        """Parse page 17's two side-by-side jib charts and angle columns."""
        page_number = page.number + 1
        words = page.get_text("words")
        text = page.get_text("text")
        radius_words = [word for word in words if 315 <= word[1] <= 500 and word[0] < 90 and re.fullmatch(r"\d+[,.]\d+", word[4])]
        radius_words.sort(key=lambda word: word[1])
        radii = [_number(word[4]) for word in radius_words]
        y_centers = [((word[1] + word[3]) / 2) for word in radius_words]
        angle_words = [word for word in words if 294 <= word[1] <= 306 and re.fullmatch(r"\d+°", word[4])]
        angle_words.sort(key=lambda word: word[0])
        if len(angle_words) != 6 or not radii:
            raise ValueError(f"page {page_number}: jib axes not found")
        jib_pairs = re.findall(r"(" + NUMBER + r")\s*m\s*\+\s*(" + NUMBER + r")\s*m", text, re.I)
        if len(jib_pairs) < 2:
            raise ValueError(f"page {page_number}: jib length combinations not found")
        counterweight = re.search(r"Main counterweight:\s*(" + NUMBER + r")\s*t", text, re.I)
        width = re.search(r"(" + NUMBER + r")\s*m\s*x\s*(" + NUMBER + r")\s*m", text, re.I)
        if not counterweight or not width:
            raise ValueError(f"page {page_number}: jib configuration header is incomplete")
        charts: list[LoadChart] = []
        for group, (main_boom, jib_length) in enumerate(jib_pairs[:2]):
            group_angles = [float(word[4][:-1]) for word in angle_words[group * 3 : group * 3 + 3]]
            x_centers = [((word[0] + word[2]) / 2) for word in angle_words[group * 3 : group * 3 + 3]]
            cells: list[LoadChartCell] = []
            for radius, y in zip(radii, y_centers):
                for angle, x in zip(group_angles, x_centers):
                    candidates = [word for word in words if abs(((word[0] + word[2]) / 2) - x) < 24 and abs(((word[1] + word[3]) / 2) - y) < 4]
                    raw = next((word[4] for word in candidates if word[4] not in {"t", "m"} and not word[4].endswith("°")), "-")
                    available = raw not in {"-", "—"}
                    parsed = _number(raw) if available else None
                    cells.append(LoadChartCell(radius_m=radius, boom_length_m=_number(main_boom), boom_angle_deg=angle, rated_capacity_t=parsed, source_radius_text=str(radius).replace(".", ","), parsed_source_radius_value=radius, source_radius_unit="m", source_capacity_text=raw, parsed_source_capacity_value=parsed, source_capacity_unit="t" if parsed is not None else None, cell_status=CellStatus.AVAILABLE if available else CellStatus.NOT_AVAILABLE, source_text=raw, source=SourceEvidence(source_page=page_number, source_text=raw), confidence=1.0))
            header = ConfigurationHeader(counterweight_t=_number(counterweight.group(1)), support_mode="OUTRIGGER", outrigger_percent=100.0, outrigger_width_m=_number(width.group(1)), working_area="360°", boom_type="FIXED_JIB", main_boom_length_m=_number(main_boom), jib_length_m=_number(jib_length), source=SourceEvidence(source_page=page_number, source_text=text))
            charts.append(LoadChart(chart_type="JIB_LOAD_CHART", header=header, cells=cells, source=SourceEvidence(source_page=page_number, source_text=text)))
        return charts

    @staticmethod
    def _pages(text: str) -> list[TextPage]:
        chunks = re.split(r"\[PAGE:\s*(\d+)\]", text)
        if len(chunks) > 1:
            return [TextPage(int(chunks[i]), chunks[i + 1].strip()) for i in range(1, len(chunks) - 1, 2)]
        return [TextPage(1, text.strip())]

    def _parse_chart(self, page: TextPage) -> LoadChart:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]
        header = self._header(page, lines)
        cells: list[LoadChartCell] = []
        in_table = False
        boom_lengths: list[float] = []
        for line in lines:
            if re.search(r"^radius\b", line, re.I):
                in_table = True
                boom_lengths = [_number(match.group()) for match in _NUM_RE.finditer(line.split(")", 1)[-1])]
                continue
            if not in_table or re.search(r"^(load chart|counterweight|outrigger|working area|terex|trt\s*60)", line, re.I):
                continue
            cells.extend(self._row(page.number, line, boom_lengths))
        if not cells:
            raise ValueError(f"page {page.number}: load chart table is empty or unknown")
        evidence = SourceEvidence(source_page=page.number, source_text=page.text)
        return LoadChart(header=header, cells=cells, source=evidence)

    def _header(self, page: TextPage, lines: list[str]) -> ConfigurationHeader:
        joined = "\n".join(lines)
        def find(pattern: str) -> str | None:
            match = re.search(pattern, joined, re.I)
            return match.group(1).strip() if match else None
        counterweight = find(r"counterweight\s*[:=]\s*(" + NUMBER + r")\s*(?:t|ton)?")
        width = find(r"(?:outrigger\s+width|support\s+width)\s*[:=]\s*(" + NUMBER + r")\s*m")
        percent = find(r"outrigger\s*[:=]\s*(" + NUMBER + r")\s*%")
        area = find(r"working\s+area\s*[:=]\s*([^\n]+)")
        support = "OUTRIGGER" if re.search(r"outrigger", joined, re.I) else None
        if counterweight is None or width is None or area is None or support is None:
            raise ValueError(f"page {page.number}: configuration header is incomplete")
        return ConfigurationHeader(counterweight_t=_number(counterweight), outrigger_width_m=_number(width), outrigger_percent=_number(percent) if percent else None, working_area=area, support_mode=support, source=SourceEvidence(source_page=page.number, source_text=joined))

    @staticmethod
    def _row(page: int, line: str, boom_lengths: list[float]) -> list[LoadChartCell]:
        tokens = line.split()
        if not tokens or not _NUM_RE.fullmatch(tokens[0].rstrip("m")):
            return []
        radius_text = tokens[0]
        radius = _number(radius_text.rstrip("m"))
        cells: list[LoadChartCell] = []
        for index, raw in enumerate(tokens[1:]):
            if index >= len(boom_lengths):
                return []
            boom = boom_lengths[index]
            status = CellStatus.AVAILABLE
            capacity_t = parsed = None
            unit = None
            if raw in {"-", "—", "NA", "N/A"}:
                status = CellStatus.NOT_AVAILABLE
            elif raw in {"X", "PROHIBITED"}:
                status = CellStatus.PROHIBITED
            else:
                try:
                    capacity_t, parsed, unit = _capacity(raw)
                except ValueError:
                    status = CellStatus.PARSE_ERROR
            cells.append(LoadChartCell(radius_m=radius, boom_length_m=boom, rated_capacity_t=capacity_t, source_radius_text=radius_text, parsed_source_radius_value=radius, source_radius_unit="m", source_capacity_text=raw, parsed_source_capacity_value=parsed, source_capacity_unit=unit, cell_status=status, source_text=line, source=SourceEvidence(source_page=page, source_text=line), confidence=1.0 if status != CellStatus.PARSE_ERROR else 0.0))
        return cells

    @staticmethod
    def validate(data: CanonicalTRT60Data) -> list[str]:
        errors: list[str] = []
        for chart_index, chart in enumerate(data.load_charts):
            if chart.header.support_mode is None or chart.header.working_area is None:
                errors.append(f"chart[{chart_index}]: incomplete configuration")
            for cell_index, cell in enumerate(chart.cells):
                if cell.cell_status == CellStatus.AVAILABLE and cell.rated_capacity_t is None:
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: AVAILABLE without capacity")
                if cell.cell_status != CellStatus.AVAILABLE and cell.rated_capacity_t is not None:
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: non-available cell has capacity")
                if cell.source.source_page != chart.source.source_page:
                    errors.append(f"chart[{chart_index}].cell[{cell_index}]: source page mismatch")
        return errors

    @staticmethod
    def content_hash(data: CanonicalTRT60Data) -> str:
        payload = data.model_dump(mode="json", exclude={"content_hash_sha256", "canonical_content_hash"})
        # Verification/audit metadata must not alter the canonical crane-data hash.
        for field in ("source_document", "file_hash_sha256", "parser_verification_status", "validation_errors"):
            payload.pop(field, None)
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(canonical).hexdigest()

    @staticmethod
    def to_deterministic_json(data: CanonicalTRT60Data) -> str:
        return json.dumps(data.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
