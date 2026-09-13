from app.crane.ocr_table_association import GridAxisPoint, OcrTableGrid, OcrToken
from app.crane.trt35_vertical_slice import (
    TRT35_PAGE11_LOWER_50_TABLE_BBOX_PDF,
    TRT35_PAGE12_UPPER_ON_TIRES_TABLE_BBOX_PDF,
    TRT35_PAGE12_LOWER_ON_TIRES_TABLE_BBOX_PDF,
    TRT35_PAGE15_LEFT_LATTICE_JIB_0_TABLE_BBOX_PDF,
    TRT35_PAGE15_RIGHT_LATTICE_JIB_20_TABLE_BBOX_PDF,
    Trt35TableIdentity,
    Trt35VerticalSliceParser,
    trt35_page11_lower_50_identity,
    trt35_page12_upper_on_tires_identity,
    trt35_page12_lower_on_tires_identity,
    trt35_page15_left_lattice_jib_0_identity,
    trt35_page15_right_lattice_jib_20_identity,
)


def _grid():
    return OcrTableGrid(
        source_page=11,
        table_bbox=(0, 0, 200, 100),
        boom_columns=[GridAxisPoint(value=9.1, center=50, index=0), GridAxisPoint(value=14.4, center=150, index=1)],
        radius_rows=[GridAxisPoint(value=3.0, center=25, index=0), GridAxisPoint(value=3.5, center=75, index=1)],
        x_tolerance=10,
        y_tolerance=8,
        column_edges=[0, 100, 200],
        row_edges=[0, 50, 100],
    )


def test_trt35_slice_preserves_geometry_first_status_and_evidence():
    identity = Trt35TableIdentity(boom_lengths_m=[9.1, 14.4], radii_m=[3.0, 3.5])
    result = Trt35VerticalSliceParser().parse(
        _grid(),
        [
            OcrToken(text="35.00", confidence=0.99, bbox=(40, 20, 60, 30)),
            OcrToken(text="-", confidence=0.99, bbox=(140, 20, 160, 30)),
        ],
        identity=identity,
    )
    first = result.cells[0]
    second = result.cells[1]
    assert result.grid_status == "PASS"
    assert (first.radius_m, first.boom_length_m, first.cell_status, first.rated_capacity_t) == (3.0, 9.1, "AVAILABLE", 35.0)
    assert second.cell_status == "NOT_AVAILABLE"
    assert first.cell_bbox == (0.0, 0.0, 100.0, 50.0)


def test_trt35_slice_fails_closed_for_missing_grid_edges_and_low_confidence():
    identity = Trt35TableIdentity(boom_lengths_m=[9.1, 14.4], radii_m=[3.0, 3.5])
    result = Trt35VerticalSliceParser().parse(
        _grid().model_copy(update={"column_edges": None, "row_edges": None}),
        [OcrToken(text="35.00", confidence=0.99, bbox=(40, 20, 60, 30))],
        identity=identity,
    )
    assert result.grid_status == "TABLE_STRUCTURE_UNRESOLVED"
    assert "explicit cell edges are required" in result.critical_errors
    assert all(cell.cell_status == "UNRESOLVED" for cell in result.cells)


def test_trt35_slice_rejects_whole_number_when_the_source_decimal_is_lost():
    identity = Trt35TableIdentity(boom_lengths_m=[9.1, 14.4], radii_m=[3.0, 3.5])
    result = Trt35VerticalSliceParser().parse(
        _grid(),
        [OcrToken(text="90", confidence=0.99, bbox=(40, 20, 60, 30))],
        identity=identity,
    )
    assert result.cells[0].cell_status == "UNRESOLVED"


def test_trt35_slice_includes_explicit_parser_version_in_canonical_output():
    identity = Trt35TableIdentity(boom_lengths_m=[9.1, 14.4], radii_m=[3.0, 3.5])
    result = Trt35VerticalSliceParser().parse(
        _grid(),
        [],
        identity=identity,
        parser_version="0.1.1-tight-crop-candidate",
    )
    assert result.parser_version == "0.1.1-tight-crop-candidate"


def test_page11_lower_50_identity_is_independent_from_upper_100_slice():
    identity = trt35_page11_lower_50_identity()
    assert identity.table_segment == "PAGE_11_LOWER_50_OUTRIGGER"
    assert identity.outrigger_percent == 50.0
    assert identity.outrigger_length_m == 3.3
    assert len(identity.radii_m) == 20
    assert TRT35_PAGE11_LOWER_50_TABLE_BBOX_PDF == (80.0, 584.0, 515.0, 781.0)


def test_page12_on_tires_identity_has_no_outrigger_configuration():
    identity = trt35_page12_upper_on_tires_identity()
    assert identity.source_page == 12
    assert identity.table_segment == "PAGE_12_UPPER_ON_TIRES_360_0_KMH"
    assert identity.support_mode == "ON_TIRES"
    assert identity.outrigger_percent is None
    assert len(identity.boom_lengths_m) == 4
    assert len(identity.radii_m) == 17
    assert identity.min_column_center_span_ratio == 0.50
    assert TRT35_PAGE12_UPPER_ON_TIRES_TABLE_BBOX_PDF == (80.0, 224.0, 515.0, 386.0)


def test_page12_lower_on_tires_identity_is_a_separate_travel_mode():
    identity = trt35_page12_lower_on_tires_identity()
    assert identity.table_segment == "PAGE_12_LOWER_ON_TIRES_0_MAX_2_KMH"
    assert identity.support_mode == "ON_TIRES"
    assert identity.working_area == "0 deg"
    assert len(identity.boom_lengths_m) == 3
    assert len(identity.radii_m) == 17
    assert identity.min_column_center_span_ratio == 0.30
    assert TRT35_PAGE12_LOWER_ON_TIRES_TABLE_BBOX_PDF == (80.0, 456.0, 515.0, 618.0)


def test_page15_left_lattice_jib_identity_is_isolated_from_20_degree_table():
    identity = trt35_page15_left_lattice_jib_0_identity()
    assert identity.source_page == 15
    assert identity.table_segment == "PAGE_15_LEFT_LATTICE_JIB_8M_0_DEG"
    assert identity.working_area == "360 deg"
    assert len(identity.boom_lengths_m) == 5
    assert len(identity.radii_m) == 32
    assert identity.radii_m[:5] == [3.0, 3.5, 4.0, 4.5, 5.0]
    assert identity.radii_m[-1] == 32.0
    assert identity.header_x_bounds_pdf == (100.0, 290.0)
    assert TRT35_PAGE15_LEFT_LATTICE_JIB_0_TABLE_BBOX_PDF == (54.0, 280.0, 292.0, 590.0)


def test_page15_right_lattice_jib_identity_is_isolated_from_0_degree_table():
    identity = trt35_page15_right_lattice_jib_20_identity()
    assert identity.source_page == 15
    assert identity.table_segment == "PAGE_15_RIGHT_LATTICE_JIB_8M_20_DEG"
    assert identity.header_x_bounds_pdf == (335.0, 535.0)
    assert identity.radius_geometry_x_bounds_pdf == (300.0, 330.0)
    assert len(identity.boom_lengths_m) == 5
    assert len(identity.radii_m) == 32
    assert TRT35_PAGE15_RIGHT_LATTICE_JIB_20_TABLE_BBOX_PDF == (292.0, 280.0, 541.0, 590.0)
