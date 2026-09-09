# TRT60 Geometry v1 Baseline

## Boundary

Geometry v1 is a Main Boom **reach** check only. It is independent from the
capacity engine and never grants lifting approval. It does not calculate boom
or building clearance, ground bearing, wind limits, rigging geometry, or a
lift plan.

## Source requirement

The TRT60 datasheet contains a Main Boom range graph on PDF page 10 and Main
Boom length/luffing-angle specifications on page 18. Page 10 is a visual
diagram, so its curves must not be converted to a numerical hook-height model
by inference.

Before enabling a TRT60 reach result, create a human-reviewed dataset with
exact points in this form:

```json
{
  "boom_length_m": 33.0,
  "working_radius_m": 16.0,
  "maximum_hook_height_m": 0.0,
  "source": {
    "source_page": 10,
    "source_bbox": [0, 0, 0, 0],
    "source_text": "Human-verified range graph point"
  }
}
```

Each dataset is bound to the PDF SHA-256, parser profile, and parser version.
The `maximum_hook_height_m` value must be read or otherwise verified by a human
from an authoritative manufacturer source. Placeholder values must never be
enabled.

## Engine rules

- Exact `(boom_length_m, working_radius_m)` matching only; no interpolation.
- `required_hook_height_m <= maximum_hook_height_m` yields `PASS`; otherwise
  `FAIL`.
- Missing point yields `POINT_NOT_FOUND`.
- Missing reviewed dataset yields `REFERENCE_DATASET_REQUIRED`.
- Every result remains `approval: NOT_GRANTED`.

## Acceptance before UI/API integration

1. Review 20-30 Main Boom points across short/middle/long boom lengths and
   short/middle/long radii.
2. Record page/bbox/source text for every point.
3. Add exact-match, source mismatch, missing-point, and deterministic dataset
   tests.
4. Confirm hook-height datum and any block/reeving adjustment with the
   manufacturer operating manual.
