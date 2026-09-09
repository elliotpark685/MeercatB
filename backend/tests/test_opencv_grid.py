import cv2
import numpy as np
import pytest

from app.crane.opencv_grid import GridReconstructionConfig, TableStructureUnresolved, reconstruct_grid


def _grid_image():
    image = np.full((120, 180), 255, dtype=np.uint8)
    for x in (10, 70, 130, 170):
        cv2.line(image, (x, 10), (x, 110), 0, 2)
    for y in (10, 35, 60, 85, 110):
        cv2.line(image, (10, y), (170, y), 0, 2)
    return image


def test_reconstruct_grid_returns_monotonic_explicit_cell_edges():
    grid = reconstruct_grid(
        _grid_image(),
        GridReconstructionConfig(source_page=11, table_bbox=(0, 0, 180, 120), expected_columns=3, expected_rows=4),
    )
    assert len(grid.column_edges) == 4
    assert len(grid.row_edges) == 5
    assert grid.column_edges == sorted(grid.column_edges)
    assert grid.row_edges == sorted(grid.row_edges)


def test_reconstruct_grid_fails_closed_when_expected_shape_is_wrong():
    with pytest.raises(TableStructureUnresolved):
        reconstruct_grid(
            _grid_image(),
            GridReconstructionConfig(source_page=11, table_bbox=(0, 0, 180, 120), expected_columns=4, expected_rows=4),
        )


def test_reconstruct_grid_accepts_validated_header_centres_when_internal_vertical_rules_are_absent():
    image = _grid_image()
    # Remove internal vertical rules, retaining only the outer boundary.
    image[:, 70:130] = 255
    grid = reconstruct_grid(
        image,
        GridReconstructionConfig(
            source_page=11,
            table_bbox=(0, 0, 180, 120),
            expected_columns=3,
            expected_rows=4,
            column_centers_px=(40, 100, 150),
            min_line_length_ratio=0.5,
        ),
    )
    assert grid.column_edges == [0.0, 70.0, 125.0, 180.0]


def test_reconstruct_grid_accepts_validated_radius_centres_when_some_row_rules_are_absent():
    image = _grid_image()
    image[35:60, :] = 255
    grid = reconstruct_grid(
        image,
        GridReconstructionConfig(
            source_page=11,
            table_bbox=(0, 0, 180, 120),
            expected_columns=3,
            expected_rows=4,
            row_centers_px=(12, 44, 76, 108),
            min_line_length_ratio=0.5,
        ),
    )
    assert grid.row_edges == [0.0, 28.0, 60.0, 92.0, 120.0]
