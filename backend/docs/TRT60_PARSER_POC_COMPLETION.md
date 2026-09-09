# TRT60 Parser PoC Completion Record

Implementation baseline: `meerkat_crane_lifting_review_plan_v0.5.md`

Scope: Terex TRT60 reference PDF, Main Boom pages 11-15 only. Jib is
classified but its load-chart cells are outside this PoC.

## Reference artifact

- Source file: `trt60_datasheet_metric_en-fr-de-it-es-pt-ru.pdf`
- PDF SHA-256: `004427e03e8751bb0b1c956d97641305a2d3e5f51fe47f349d5bb42ec3d13210`
- Parser profile/version: `TEREX_TRT` / `0.5.0-poc.2`
- Canonical content SHA-256:
  `78bcb224ccbc8b1e0edad5250e6f9d144233f5b4a296cc27a15119bec731d72a`

## Reproducible technical verification

Run from repository root:

```powershell
pytest -q backend/tests/test_trt60_parser.py backend/tests/test_trt60_upload_api.py backend/tests/test_engineering_review.py
```

Latest result: `16 passed`.

| Check | Result |
| --- | --- |
| Golden Dataset exact match | 24 / 24 pass / 0 fail |
| Main Boom configuration pages | 11, 12, 13, 14, 15 |
| Main Boom parsed cells | 795 |
| Cell source bbox coverage | 795 / 795 |
| Critical validation errors | 0 |
| Deterministic canonical hash | pass |
| Jib load-chart cell parsing/persistence | excluded |
| Persistence default | off |
| Upload resource protection | 10 MiB bounded read, media/signature validation |
| Async event-loop protection | PDF parsing dispatched to threadpool |
| CI SQLite mode | `USE_PGVECTOR=false`, 99 passed locally |

The Golden Dataset is [trt60_golden.json](../evaluation/datasets/trt60_golden.json).
It contains 24 cells across outrigger configurations, short/middle/long
radii, multiple boom columns, and available/unavailable cells.

Generate the human review pack with:

```powershell
$env:PYTHONPATH='backend'
python backend/scripts/generate_trt60_golden_review_pack.py <reference-trt60.pdf> --output backend/output/pdf/TRT60_Golden_Review_Pack.pdf
```

Critical tests cover configuration association, row/column swap, wrong
capacity association, blank-as-capacity, unit normalization, cross-chart
contamination, source page/bbox mismatch, and interpolation markers.

## Existing backend regression baseline

`pytest -q backend/tests --tb=no` latest result: `85 passed, 14 failed`.
The 14 failures are confined to existing law/admin/safety-standard search
tests that require PostgreSQL/pgvector behavior while running against SQLite.
No TRT60 test failed. This record does not claim those unrelated failures are
fixed.

The repository's local `.env` may set `USE_PGVECTOR=true` for deployment
connectivity. Do not use that setting with SQLite tests: the pgvector `<=>`
operator is PostgreSQL-only. GitHub Actions has no PostgreSQL/pgvector service,
so its backend suite explicitly uses `USE_PGVECTOR=false`. There is currently
no dedicated pgvector integration suite; one must be added with an actual
PostgreSQL+pgvector service rather than skipped or simulated.

## Required human acceptance

The v0.5 PoC requires the Golden Dataset cells to be directly checked against
the PDF by a human reviewer. Automated tests cannot truthfully substitute for
that acceptance. The reviewer must open pages 11-15, compare all 24 dataset
rows with the visible table, and then record the result below.

- [ ] I directly verified all 24 Golden Dataset cells against the reference PDF.
- [ ] I confirmed configuration, radius, boom length, capacity, and cell status.
- [ ] I accept this reference PDF revision as the TRT60 Parser PoC baseline.

Reviewer: ____________________  Date: ____________________

Once all three boxes are signed, the TRT60 Parser PoC is accepted as 100%.
This acceptance does not authorize Engineering Review geometry, operational
lifting, database persistence, or production deployment.
