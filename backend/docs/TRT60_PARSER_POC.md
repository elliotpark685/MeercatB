# TRT60 Parser PoC

v0.5 is the Implementation Baseline. The first vertical slice is intentionally
limited to:

`PDF → document inspection → page classification → configuration header → main-boom load chart → unit normalization → validation → source traceability → deterministic JSON`

Engineering review inputs and calculations are not included: required height,
reach/geometry, gross-load calculation, capacity judgment, user confirmation,
and engineer approval remain out of scope.

The Engineering Review boundary may use the PDF's explicit capacity note only:
TRT60 page 24 states that hook blocks and slings are part of the load and must
be subtracted from capacity ratings. This is retained as
`NET_OF_HOOK_BLOCK_AND_SLINGS` with page/bbox evidence. The same page requires
the crane's computer charts and operating manual for actual operation; a PoC
PASS/FAIL is traceable preliminary review output, not an operational lifting
authorization.

Before an Engineering Review query can use a chart cell, the user-selected
configuration must exactly match that chart's parsed counterweight, support
mode, outrigger setting, and working area. Missing confirmation and mismatched
confirmation are both blocked; a selected page number alone is not approval.

`POST /api/v1/cranes/trt60/review` accepts a PDF and the JSON-encoded review
input as multipart form data. It permits only the Golden-validated TRT60 PDF
SHA-256 revision, never writes to the database, and always returns
`approval: NOT_GRANTED`. Geometry remains `NOT_IMPLEMENTED` until the range
envelope is separately verified.

Both TRT60 upload endpoints enforce `CRANE_PDF_MAX_UPLOAD_BYTES` (10 MiB by
default), a `.pdf` filename, an accepted PDF media type, and the `%PDF-` file
signature. Parsing runs in FastAPI's threadpool so CPU-bound PDF extraction
does not block the async request loop.

## Input contract

The current PoC uses PyMuPDF native text extraction. For fixture and parser
unit tests, page markers may be supplied as `[PAGE:n]`. A load-chart page must
contain the following explicit anchors:

```text
Terex TRT60 MAIN BOOM LOAD CHART
Counterweight: 6.0 t
Outrigger: 100%
Outrigger Width: 7.0 m
Working Area: 360 deg
Radius (m) 12m 18m
5 12.5 12500kg
10 8.0 -
```

The PoC fails closed when the document identity, configuration header, or
table structure is ambiguous. It does not interpolate missing cells.

## Run

The current reference document is:

`C:\Meerkat\MobileCrane\Terex\trt60_datasheet_metric_en-fr-de-it-es-pt-ru.pdf`

The supplied datasheet contains Main Boom chart pages 11–15 and a Jib chart
on page 17. Main Boom pages 11–15 are parsed as five independent chart
configurations: Outrigger 100%, 50%, 0%, and On Tires 0/2 km/h. Page 17 is
classified as a Jib chart but its cells are intentionally excluded from this
Main Boom Parser PoC.

From `backend`:

```text
python scripts/parse_trt60.py path/to/TRT60.pdf --output trt60.json
```

The result includes file and canonical SHA-256 hashes, `parser_profile`,
`parser_version`, `parser_verification_status`, validation errors, and source
page/bbox evidence for every Main Boom cell. Parsing alone yields
`AUTO_PARSED`; only the separate Golden Dataset and Critical Validation checks
may promote the reference parse to `AUTO_VALIDATED`.
