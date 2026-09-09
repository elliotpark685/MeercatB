import json
from pathlib import Path

from app.crane.trt60_parser import TerexTRT60Parser
from app.crane.trt60_schema import CellStatus, ParserVerificationStatus


FIXTURE = """[PAGE:1]
Terex TRT60 Rough Terrain Crane
General specification
[PAGE:2]
Terex TRT60 MAIN BOOM LOAD CHART
Counterweight: 6.0 t
Outrigger: 100%
Outrigger Width: 7.0 m
Working Area: 360 deg
Radius (m) 12m 18m
5 12.5 12500kg
10 8.0 -
"""


def test_trt60_vertical_slice_normalizes_and_traces_cells():
    data = TerexTRT60Parser().parse_text(FIXTURE, source_name="trt60-golden.txt")
    assert data.parser_verification_status == ParserVerificationStatus.AUTO_PARSED
    chart = data.load_charts[0]
    assert chart.header.counterweight_t == 6.0
    assert chart.header.working_area == "360 deg"
    assert chart.cells[1].rated_capacity_t == 12.5
    assert chart.cells[1].parsed_source_capacity_value == 12500
    assert chart.cells[1].source_capacity_unit == "kg"
    assert chart.cells[3].cell_status == CellStatus.NOT_AVAILABLE
    assert chart.cells[3].rated_capacity_t is None
    assert chart.cells[1].source.source_page == 2
    assert chart.cells[0].boom_length_m == 12.0
    assert chart.cells[1].boom_length_m == 18.0


def test_trt60_output_is_deterministic():
    parser = TerexTRT60Parser()
    first = parser.parse_text(FIXTURE, source_name="trt60-golden.txt")
    second = parser.parse_text(FIXTURE, source_name="trt60-golden.txt")
    assert parser.to_deterministic_json(first) == parser.to_deterministic_json(second)
    assert first.content_hash_sha256 == second.content_hash_sha256


def test_trt60_fails_closed_on_missing_configuration():
    text = FIXTURE.replace("Working Area: 360 deg\n", "")
    try:
        TerexTRT60Parser().parse_text(text)
    except ValueError as error:
        assert "configuration header is incomplete" in str(error)
    else:
        raise AssertionError("incomplete configuration must not be accepted")


def test_actual_trt60_main_boom_pages_are_separate_configurations():
    """The checked-in environment provides the reference PDF at this path."""
    pdf = Path(r"C:\Meerkat\MobileCrane\Terex\trt60_datasheet_metric_en-fr-de-it-es-pt-ru.pdf")
    if not pdf.exists():
        return
    data = TerexTRT60Parser().parse_pdf(pdf)
    assert data.parser_verification_status == ParserVerificationStatus.AUTO_PARSED
    main = [chart for chart in data.load_charts if chart.chart_type == "MAIN_BOOM_LOAD_CHART"]
    assert [chart.source.source_page for chart in main] == [11, 12, 13, 14, 15]
    assert [chart.header.support_mode for chart in main] == ["OUTRIGGER", "OUTRIGGER", "OUTRIGGER", "ON_TIRES", "ON_TIRES"]
    assert [chart.header.outrigger_percent for chart in main[:3]] == [100.0, 50.0, 0.0]
    golden = json.loads((Path(__file__).parents[1] / "evaluation" / "datasets" / "trt60_golden.json").read_text(encoding="utf-8"))
    errors = TerexTRT60Parser().verify(data, golden)
    assert errors == []
    assert data.parser_verification_status == ParserVerificationStatus.AUTO_VALIDATED
    assert all(cell.source.source_bbox is not None for chart in main for cell in chart.cells)


def test_critical_validation_rejects_duplicate_cross_chart_cell():
    data = TerexTRT60Parser().parse_text(FIXTURE)
    duplicated = data.model_copy(deep=True)
    duplicated.load_charts.append(duplicated.load_charts[0])
    errors = TerexTRT60Parser.validate_critical(duplicated)
    assert any("cross-chart cell contamination" in error for error in errors)


def test_actual_trt60_metadata_and_determinism():
    pdf = Path(r"C:\Meerkat\MobileCrane\Terex\trt60_datasheet_metric_en-fr-de-it-es-pt-ru.pdf")
    if not pdf.exists():
        return
    parser = TerexTRT60Parser()
    first = parser.parse_pdf(pdf)
    second = parser.parse_pdf(pdf)
    assert first.file_hash_sha256
    assert first.file_hash_sha256 == second.file_hash_sha256
    assert first.canonical_content_hash == second.canonical_content_hash
    golden = json.loads((Path(__file__).parents[1] / "evaluation" / "datasets" / "trt60_golden.json").read_text(encoding="utf-8"))
    before_verification_hash = first.canonical_content_hash
    assert parser.verify(first, golden) == []
    assert first.canonical_content_hash == before_verification_hash
    main = [chart for chart in first.load_charts if chart.chart_type == "MAIN_BOOM_LOAD_CHART"]
    cells = [cell for chart in main for cell in chart.cells]
    assert len(cells) == 795
    assert sum(cell.source.source_bbox is not None for cell in cells) == len(cells)


def test_critical_validation_rejects_unit_error_and_interpolation():
    data = TerexTRT60Parser().parse_text(FIXTURE)
    mutated = data.model_copy(deep=True)
    cell = mutated.load_charts[0].cells[0]
    cell.source_capacity_unit = "lb"
    cell.source_text = "interpolated"
    errors = TerexTRT60Parser.validate_critical(mutated)
    assert any("unsupported capacity unit" in error for error in errors)
    assert any("synthetic interpolation" in error for error in errors)


def test_golden_checks_reject_configuration_axis_capacity_and_blank_errors():
    pdf = Path(r"C:\Meerkat\MobileCrane\Terex\trt60_datasheet_metric_en-fr-de-it-es-pt-ru.pdf")
    if not pdf.exists():
        return
    parser = TerexTRT60Parser()
    data = parser.parse_pdf(pdf)
    golden_path = Path(__file__).parents[1] / "evaluation" / "datasets" / "trt60_golden.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    for mutation in ("configuration", "axis", "capacity", "blank"):
        bad = json.loads(json.dumps(golden))
        if mutation == "configuration":
            bad[0]["outrigger_percent"] = 50.0
        elif mutation == "axis":
            bad[1]["radius_m"], bad[1]["boom_length_m"] = bad[1]["boom_length_m"], bad[1]["radius_m"]
        elif mutation == "capacity":
            bad[2]["rated_capacity_t"] += 1.0
        else:
            bad[3]["rated_capacity_t"] = 1.0
            bad[3]["cell_status"] = "AVAILABLE"
        assert parser.verify(data.model_copy(deep=True), bad)
