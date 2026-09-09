import json
from pathlib import Path

from app.crane.engineering_review import CapacityStatus, ConfigurationStatus, ConfirmedConfiguration, EngineeringReviewInput, MainBoomEngineeringReviewService
from app.crane.trt60_parser import TerexTRT60Parser


def _validated_reference_data():
    pdf = Path(r"C:\Meerkat\MobileCrane\Terex\trt60_datasheet_metric_en-fr-de-it-es-pt-ru.pdf")
    if not pdf.exists():
        return None
    parser = TerexTRT60Parser()
    data = parser.parse_pdf(pdf)
    golden = json.loads((Path(__file__).parents[1] / "evaluation" / "datasets" / "trt60_golden.json").read_text(encoding="utf-8"))
    assert parser.verify(data, golden) == []
    return data


def _confirmed(chart):
    return ConfirmedConfiguration(counterweight_t=chart.header.counterweight_t, support_mode=chart.header.support_mode, outrigger_percent=chart.header.outrigger_percent, outrigger_width_m=chart.header.outrigger_width_m, outrigger_length_m=chart.header.outrigger_length_m, working_area=chart.header.working_area)


def test_review_uses_explicit_manufacturer_capacity_basis_with_traceability():
    data = _validated_reference_data()
    if data is None:
        return
    result = MainBoomEngineeringReviewService().review(data, EngineeringReviewInput(chart_source_page=11, radius_m=2.3, boom_length_m=10.5, required_height_m=20, payload_t=10, rigging_t=0.5, confirmed_configuration=_confirmed(data.load_charts[0])))
    assert result.gross_load_t == 10.5
    assert result.required_height_m == 20
    assert result.capacity_status == CapacityStatus.PASS
    assert result.configuration_status == ConfigurationStatus.CONFIRMED
    assert result.capacity_basis == "NET_OF_HOOK_BLOCK_AND_SLINGS"
    assert result.capacity_basis_source_page == 24
    assert result.capacity_basis_source_bbox is not None
    assert result.operational_limit is not None


def test_review_blocks_unknown_capacity_basis_without_inference():
    data = _validated_reference_data()
    if data is None:
        return
    data.load_charts[0].capacity_basis = "UNKNOWN"
    result = MainBoomEngineeringReviewService().review(data, EngineeringReviewInput(chart_source_page=11, radius_m=2.3, boom_length_m=10.5, required_height_m=20, payload_t=10, confirmed_configuration=_confirmed(data.load_charts[0])))
    assert result.capacity_status == CapacityStatus.BLOCKED_CAPACITY_BASIS_UNKNOWN


def test_review_uses_exact_cell_and_never_interpolates():
    data = _validated_reference_data()
    if data is None:
        return
    result = MainBoomEngineeringReviewService().review(data, EngineeringReviewInput(chart_source_page=11, radius_m=2.4, boom_length_m=10.5, required_height_m=20, payload_t=10, confirmed_configuration=_confirmed(data.load_charts[0])))
    assert result.capacity_status == CapacityStatus.CELL_NOT_FOUND


def test_review_requires_user_configuration_confirmation():
    data = _validated_reference_data()
    if data is None:
        return
    result = MainBoomEngineeringReviewService().review(data, EngineeringReviewInput(chart_source_page=11, radius_m=2.3, boom_length_m=10.5, required_height_m=20, payload_t=10))
    assert result.configuration_status == ConfigurationStatus.NOT_CONFIRMED


def test_review_rejects_mismatched_user_configuration():
    data = _validated_reference_data()
    if data is None:
        return
    other = _confirmed(data.load_charts[1])
    result = MainBoomEngineeringReviewService().review(data, EngineeringReviewInput(chart_source_page=11, radius_m=2.3, boom_length_m=10.5, required_height_m=20, payload_t=10, confirmed_configuration=other))
    assert result.configuration_status == ConfigurationStatus.MISMATCH


def test_review_counts_hook_block_and_sling_once_against_rated_capacity():
    data = _validated_reference_data()
    if data is None:
        return
    result = MainBoomEngineeringReviewService().review(
        data,
        EngineeringReviewInput(
            chart_source_page=11,
            radius_m=2.3,
            boom_length_m=10.5,
            required_height_m=20,
            payload_t=59,
            hook_block_t=1,
            rigging_t=0.1,
            confirmed_configuration=_confirmed(data.load_charts[0]),
        ),
    )
    assert result.gross_load_t == 60.1
    assert result.capacity_status == CapacityStatus.FAIL
