# TRT35 pages 10/14 Geometry Golden review

This review is for range-graph evidence only. It is separate from the six
capacity-table Goldens.

For every selected curve, enter representative points into
`backend/evaluation/datasets/trt35_geometry_human_review_template.csv`:

- `boom_length_m`: the curve label, in metres.
- `working_radius_m`: the x-axis value read at the point.
- `maximum_hook_height_m`: the y-axis value read from the curve.
- `source_bbox_*`: the PDF/rendered evidence box around the curve point.
- `human_verified`, `verified_at`, and `verification_note`: mandatory review evidence.

Do not enter interpolated values. Initially select points at the left edge,
middle, right edge, and every visible curve bend or limit. A point is usable at
runtime only after all fields are valid and independently verified.

The initial runtime must perform exact boom-length/radius lookup. Pixel
tolerance may be used to match evidence boxes, but height decisions must be
conservative: an uncertain or borderline point is `REFERENCE_DATASET_REQUIRED`
or `POINT_NOT_FOUND`, never an automatic PASS.
