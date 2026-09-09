# Terex TRT35 Parser Onboarding Discovery

## Selected source

`C:\Meerkat\MobileCrane\Terex\trt35_datasheet_metric_en-fr-de-it-es-pt-ru.pdf`

TRT35 is the second parser-onboarding candidate. It is deliberately not routed
to the TRT60 parser, even though both documents are Terex rough-terrain crane
datasheets.

## Confirmed layout evidence

- PDF page 11 is a `LOAD CHART - MAIN BOOM` page.
- Page 11 contains **two vertically separate** capacity tables.
- Upper table configuration: 4.2 t counterweight, Outrigger 100%, 5.9 m x
  5.8 m, 360 degrees.
- Lower table configuration: 4.2 t counterweight, Outrigger 50%, 5.9 m x
  3.3 m, 360 degrees.
- Both tables use boom-length columns 9.1, 14.4, 19.6, 24.9, and 30.1 m.
- A blank/dash cell is a non-available cell, never a zero-capacity cell.

## Parser constraints

1. A page is not a chart identity: each vertical table block must become a
   separate chart with its own Configuration source evidence.
2. Cell source bbox must remain inside its owning table block.
3. 100% and 50% Outrigger cells must be critical-tested for cross-chart
   contamination.
4. Exact radius/boom lookup only; interpolation remains disabled.
5. Capacity-basis wording must be extracted from the TRT35 document itself;
   TRT60 evidence cannot be reused.
6. The PDF's native text layer does not faithfully preserve the visible radius
   row labels on page 11. Native-text parsing is therefore rejected for this
   source revision; use a visual/OCR table-extraction path with its own Golden
   Dataset and row/column association checks.

## OCR feasibility result

The page 11 upper table was rendered at 3x and examined with image OCR. The
OCR result recovered the visible grid with PDF-coordinate evidence:

- Radius labels: 3.0 m through 27.0 m.
- Boom headers: 9.1, 14.4, 19.6, 24.9, and 30.1 m.
- Sample exact cells: `(3.0, 9.1) -> 35.00 t`, `(3.0, 14.4) -> 21.70 t`,
  `(4.5, 30.1) -> 5.00 t`.
- Cell and header coordinates are recoverable after converting the rendered
  image coordinates back to PDF coordinates.

This proves OCR is a viable extraction source for TRT35. It does not yet
authorize a parser: low-confidence tokens, dash cells, table-block bounds, and
all four Main Boom configuration blocks still require model-specific tests and
Golden verification.

## Acceptance work remaining

1. Implement `TEREX_TRT35` parser profile and strict model identity.
2. Cover all TRT35 Main Boom configuration blocks/pages.
3. Create 20-30 human-reviewed Golden cells, including both 100% and 50%
   Outrigger configurations, short/middle/long radii, and blank cells.
4. Locate and verify TRT35 capacity-basis/operational-limit evidence.
5. Add deterministic hash, bbox-coverage, and Critical Error tests before
   enabling Capacity or Reach review.
