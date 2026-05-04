# Construction Safety Backend

## Environment (local)
`backend/.env` example:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/meerkat
DB_SCHEMA=meerkat_pjt
USE_PGVECTOR=false
```

Notes:
- `LAW_API_OC` can exist in `.env`, but is not called in current flow.
- Current search mode is keyword-only (`USE_PGVECTOR=false`).

## Run server (Windows)
```bash
conda activate llm_env
cd /d C:\Meerkat\Backend\backend
uvicorn app.main:app --reload
```

## Local data folder convention
Put raw law files under:

```text
backend/data/raw/laws/
```

## Ingestion (canonical article-title index mode)
```bash
conda activate llm_env
cd /d C:\Meerkat\Backend\backend
python -m ingestion.ingest_laws ^
  --file-path "data/raw/laws/산업안전보건기준에_관한_규칙_20260302.pdf" ^
  --article-title-index-path "data/raw/laws/산업안전보건기준에_관한_규칙_조문제목_20260302.txt" ^
  --law-name "산업안전보건기준에 관한 규칙" ^
  --law-type "고용노동부령" ^
  --law-no "제450호" ^
  --effective-date "2026-03-02"
```

## DB verification SQL
```sql
SELECT current_database();
SELECT schema_name FROM information_schema.schemata WHERE schema_name='meerkat_pjt';
SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema='meerkat_pjt' ORDER BY table_name;
SELECT COUNT(*) FROM meerkat_pjt.law_documents;
SELECT COUNT(*) FROM meerkat_pjt.law_articles;
SELECT COUNT(*) FROM meerkat_pjt.law_embeddings;
```

The same SQL is available at:
- [verify_law_flow.sql](C:\Meerkat\Backend\backend\scripts\sql\verify_law_flow.sql)

