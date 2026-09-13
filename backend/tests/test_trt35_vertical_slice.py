from app.crane.ocr_table_association import GridAxisPoint, OcrTableGrid, OcrToken
from app.crane.trt35_vertical_slice import Trt35TableIdentity, Trt35VerticalSliceParser


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
