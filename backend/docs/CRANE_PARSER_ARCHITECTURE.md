# Crane Parser Architecture Boundary

Decision: defer a `BaseCraneParser` abstraction until a second real crane
profile exists. A single TRT60 profile is insufficient evidence for a stable
inheritance hierarchy.

## Shared canonical contract

The following Pydantic data contracts are intended to be reusable across
manufacturers: `SourceEvidence`, `LoadChartCell`, `ConfigurationHeader`,
`LoadChart`, parser verification status, SI-normalized values, deterministic
content hashing, and validation errors.

## Profile-owned behavior

`TerexTRT60Parser` owns the PDF anchors, page coordinates, table segmentation,
configuration labels, capacity-note interpretation, Golden Dataset, and
reference-PDF SHA-256. These are deliberately not generalized.

## Next parser decision gate

When a second manufacturer/model parser is introduced, compare its actual
document flow with TRT60. Extract only the common operations that both need:
`can_parse`, `inspect_document`, `parse`, and `validate`. Until then, keep
profile-specific parsing explicit and avoid speculative base classes.

## Capacity semantics

TRT60 page 24 says hook blocks and slings are part of the load and must be
subtracted from rated capacity. The canonical chart basis
`NET_OF_HOOK_BLOCK_AND_SLINGS` therefore means the chart rating excludes those
components. Engineering Review compares one gross load
`payload + rigging + hook_block + spreader` with the rating; it does not apply
a second deduction rule.
