# TRT60 ↔ Supabase Mapping Contract

Supabase schema ownership remains outside this repository. This document
defines the data boundary that the Parser API returns; it is not a migration
or a prescribed table definition.

## API

```text
POST /api/v1/cranes/trt60/parse
Content-Type: multipart/form-data
file=<TRT60 PDF>
```

The response contains:

- `parser_result`: full canonical parser output and verification status
- `supabase_rows`: proposed records grouped by logical resource

Rows are not written automatically. The application layer that owns the
Supabase client must resolve IDs and insert them transactionally.

The production writer uses the existing FastAPI SQLAlchemy PostgreSQL session;
no Supabase URL, service-role key, RPC function, or additional SQL Editor
script is required. All related inserts are committed or rolled back by one
database transaction.

## Logical resources

`cranes` → `source_documents` → `lifting_configurations` → `load_charts` → `load_chart_cells`

The mapper uses temporary `external_id` values (`config-0`, `chart-0`, etc.)
only to preserve relationships in one response. The persistence layer should
replace them with the actual Supabase IDs or user-defined unique keys.

Required traceability must survive the mapping:

- parser profile and version
- source page
- source text
- cell status
- parsed source value and canonical value
- parser verification status and validation errors

The Mapper must be updated after the user supplies the final Supabase column
names. No DB schema is inferred from this contract.
