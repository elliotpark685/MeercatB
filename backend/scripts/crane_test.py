"""Local Streamlit smoke-test UI for the TRT60 Parser and review PoC."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import streamlit as st

from app.crane.engineering_review import ConfirmedConfiguration, EngineeringReviewInput, MainBoomEngineeringReviewService
from app.crane.trt60_parser import TerexTRT60Parser
from app.crane.trt60_reference import REFERENCE_FILE_HASH_SHA256, load_golden_dataset
from app.crane.trt60_schema import CanonicalTRT60Data


st.set_page_config(page_title="Crane Test", page_icon="🏗️", layout="wide")
st.title("Crane Test")
st.caption("TRT60 Parser PoC local smoke test - no database write and no lifting approval")


@st.cache_data(show_spinner="Parsing uploaded PDF...")
def parse_uploaded_pdf(payload: bytes, filename: str) -> tuple[dict, list[str]]:
    parser = TerexTRT60Parser()
    data = parser.parse_pdf_bytes(payload, source_name=filename)
    errors: list[str] = []
    if data.file_hash_sha256 == REFERENCE_FILE_HASH_SHA256:
        errors = parser.verify(data, load_golden_dataset())
    return data.model_dump(mode="json"), errors


uploaded = st.file_uploader("Upload TRT60 PDF", type=["pdf"])
if uploaded is None:
    st.info("Upload the Golden-validated TRT60 reference PDF to test parsing and Main Boom capacity lookup.")
    st.stop()

try:
    dumped_data, verification_errors = parse_uploaded_pdf(uploaded.getvalue(), uploaded.name)
    data = CanonicalTRT60Data.model_validate(dumped_data)
except Exception as exc:  # Streamlit should show parser failures without a traceback page.
    st.error(f"Parser rejected this upload: {exc}")
    st.stop()

is_reference_pdf = data.file_hash_sha256 == REFERENCE_FILE_HASH_SHA256
left, middle, right = st.columns(3)
left.metric("Parser status", data.parser_verification_status.value)
middle.metric("Main Boom charts", len(data.load_charts))
right.metric("Reference PDF", "MATCH" if is_reference_pdf else "NOT MATCHED")
st.json(
    {
        "file_hash_sha256": data.file_hash_sha256,
        "canonical_content_hash": data.canonical_content_hash,
        "parser_profile": data.parser_profile,
        "parser_version": data.parser_version,
        "golden_errors": verification_errors,
        "persistence": "OFF",
    }
)

if not is_reference_pdf:
    st.warning("This PDF is parsed but cannot enter Engineering Review until it has its own Golden Dataset validation.")
    st.stop()
if verification_errors:
    st.error("Golden/Critical validation failed. Engineering Review is blocked.")
    st.stop()

st.success("Golden and Critical validation passed. Select an exact Main Boom chart cell below.")
charts = [chart for chart in data.load_charts if chart.chart_type == "MAIN_BOOM_LOAD_CHART"]
chart_by_page = {chart.source.source_page: chart for chart in charts}
page = st.selectbox("Load chart source page", options=sorted(chart_by_page))
chart = chart_by_page[page]

st.subheader("Parsed configuration")
st.json(chart.header.model_dump(mode="json", exclude={"source"}))
confirmed = st.checkbox("I confirm this configuration matches the actual crane setup")

radius_options = sorted({cell.radius_m for cell in chart.cells if cell.radius_m is not None})
radius = st.selectbox("Working radius (m)", options=radius_options)
boom_options = sorted({cell.boom_length_m for cell in chart.cells if cell.radius_m == radius and cell.boom_length_m is not None})
boom_length = st.selectbox("Main Boom length (m)", options=boom_options)

st.subheader("Work condition")
input_left, input_right = st.columns(2)
with input_left:
    required_height = st.number_input("Required height (m)", min_value=0.1, value=20.0, step=0.1)
    payload = st.number_input("Payload (t)", min_value=0.0, value=10.0, step=0.1)
with input_right:
    rigging_mode = st.radio("Rigging / sling input", options=["Total weight", "Per sling leg"], horizontal=True)
    rigging = None
    sling_leg_count = None
    sling_weight_per_leg = None
    if rigging_mode == "Total weight":
        rigging = st.number_input("Total rigging / sling weight (t)", min_value=0.0, value=0.0, step=0.01)
    else:
        sling_leg_count = st.selectbox("Number of sling legs", options=[1, 2, 3, 4], index=1)
        sling_weight_per_leg = st.number_input("Weight per sling leg (t)", min_value=0.0, value=0.0, step=0.01)
        st.caption(f"Calculated total rigging weight: {sling_leg_count * sling_weight_per_leg:.2f} t")
    hook_block = st.number_input("Hook block (t)", min_value=0.0, value=0.0, step=0.1)
    spreader = st.number_input("Spreader (t)", min_value=0.0, value=0.0, step=0.1)

if st.button("Run Main Boom capacity test", type="primary"):
    header = chart.header
    confirmation = None
    if confirmed:
        confirmation = ConfirmedConfiguration(
            counterweight_t=header.counterweight_t,
            support_mode=header.support_mode,
            outrigger_percent=header.outrigger_percent,
            outrigger_width_m=header.outrigger_width_m,
            outrigger_length_m=header.outrigger_length_m,
            working_area=header.working_area,
        )
    request = EngineeringReviewInput(
        chart_source_page=page,
        radius_m=radius,
        boom_length_m=boom_length,
        required_height_m=required_height,
        payload_t=payload,
        rigging_t=rigging,
        sling_leg_count=sling_leg_count,
        sling_weight_per_leg_t=sling_weight_per_leg,
        hook_block_t=hook_block,
        spreader_t=spreader,
        confirmed_configuration=confirmation,
    )
    result = MainBoomEngineeringReviewService().review(data, request)
    if result.capacity_status.value == "PASS":
        st.success("Capacity test: PASS")
    else:
        st.warning(f"Capacity test: {result.capacity_status.value}")
    st.json(result.model_dump(mode="json"))
    st.info("Geometry remains NOT_IMPLEMENTED. This screen never grants lifting approval.")
