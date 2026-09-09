from app.crane.ocr_table_association import GridAxisPoint, OcrTableAssociator, OcrTableGrid, OcrToken


GRID = OcrTableGrid(
    source_page=11,
    table_bbox=(50, 220, 500, 260),
    boom_columns=[GridAxisPoint(value=9.1, center=150), GridAxisPoint(value=14.4, center=230)],
    radius_rows=[GridAxisPoint(value=3.0, center=230), GridAxisPoint(value=3.5, center=245)],
    x_tolerance=20,
    y_tolerance=6,
)


def test_association_maps_one_high_confidence_token_to_its_exact_cell():
    cells = OcrTableAssociator().associate(GRID, [OcrToken(text="35.00", confidence=0.99, bbox=(140, 226, 160, 234))])
    available = next(cell for cell in cells if cell.radius_m == 3.0 and cell.boom_length_m == 9.1)
    assert available.status == "AVAILABLE"
    assert available.rated_capacity_t == 35.0
    assert available.source_token is not None
    assert available.source_token.bbox == (140, 226, 160, 234)


def test_association_preserves_dash_as_not_available():
    cells = OcrTableAssociator().associate(GRID, [OcrToken(text="-", confidence=0.99, bbox=(220, 241, 230, 249))])
    unavailable = next(cell for cell in cells if cell.radius_m == 3.5 and cell.boom_length_m == 14.4)
    assert unavailable.status == "NOT_AVAILABLE"
    assert unavailable.rated_capacity_t is None


def test_association_rejects_low_confidence_or_ambiguous_tokens():
    low_confidence = OcrTableAssociator().associate(GRID, [OcrToken(text="35.00", confidence=0.2, bbox=(140, 226, 160, 234))])
    assert next(cell for cell in low_confidence if cell.radius_m == 3.0 and cell.boom_length_m == 9.1).status == "UNRESOLVED"

    ambiguous = OcrTableAssociator().associate(
        GRID,
        [
            OcrToken(text="35.00", confidence=0.99, bbox=(140, 226, 160, 234)),
            OcrToken(text="35.01", confidence=0.99, bbox=(141, 226, 161, 234)),
        ],
    )
    assert next(cell for cell in ambiguous if cell.radius_m == 3.0 and cell.boom_length_m == 9.1).status == "UNRESOLVED"


def test_association_ignores_token_outside_the_confirmed_table_block():
    cells = OcrTableAssociator().associate(GRID, [OcrToken(text="35.00", confidence=0.99, bbox=(140, 300, 160, 308))])
    cell = next(cell for cell in cells if cell.radius_m == 3.0 and cell.boom_length_m == 9.1)
    assert cell.status == "UNRESOLVED"


def test_explicit_edges_prevent_one_token_from_being_assigned_to_two_cells():
    grid = GRID.model_copy(update={"x_tolerance": 50.0})
    cells = OcrTableAssociator().associate(
        grid,
        [OcrToken(text="35.00", confidence=0.99, bbox=(185, 226, 195, 234))],
    )
    assert all(cell.status == "UNRESOLVED" for cell in cells)


def test_explicit_edges_are_returned_as_cell_evidence():
    grid = GRID.model_copy(update={"column_edges": [100, 200, 300], "row_edges": [220, 240, 260]})
    cells = OcrTableAssociator().associate(
        grid,
        [OcrToken(text="35.00", confidence=0.99, bbox=(140, 226, 160, 234))],
    )
    cell = next(cell for cell in cells if cell.radius_m == 3.0 and cell.boom_length_m == 9.1)
    assert cell.status == "AVAILABLE"
    assert cell.cell_bbox == (100.0, 220.0, 200.0, 240.0)
