# Equipment Parser Onboarding

## Product flow

Every equipment PDF first passes through `POST /api/v1/cranes/inspect`.

- `SUPPORTED_PROFILE`: a registered profile can safely select its parser.
- `ONBOARDING_REQUIRED`: the document is retained only in the response; it is
  not sent to an unrelated parser, no load-chart result is claimed, and no data
  is written to the operating database.

The initial registered profile is `Terex TRT60 / TEREX_TRT`. This is a registry
entry, not a generic claim that every Terex or TRT PDF uses the TRT60 parser.

## Required onboarding for each manufacturer/model/revision

1. Register strict manufacturer and model identity rules.
2. Implement a dedicated parser profile; do not copy TRT60 page coordinates.
3. Capture PDF SHA-256, parser profile/version, canonical content hash, and
   page/bbox evidence for each parsed value.
4. Add a model-specific Capacity Golden Dataset and Critical Error suite.
5. Add a human-verified Range Graph Dataset before enabling Reach review.
6. Verify the capacity basis, hook/rigging treatment, units, configuration,
   support mode, working area, and all manufacturer operating limitations.
7. Keep persistence OFF until the profile passes its acceptance gate.

Unknown PDFs can be classified and queued for onboarding, but they must never
receive a Capacity, Reach, Geometry, or equipment-approval result.
