-- Migration 005: Add safety standard classification columns to law_documents
-- Run on Supabase production:
--   psql -h <host> -U <user> -d <db> -f 005_safety_standard_columns.sql
--
-- After migration, tag "산업안전보건기준에 관한 규칙" document(s) as safety_standard:
--   UPDATE meerkat_pjt.law_documents
--     SET source_category = 'safety_standard',
--         source_type     = 'rule',
--         provider        = 'law.go.kr'
--   WHERE law_name LIKE '%산업안전보건기준에 관한 규칙%';

SET search_path TO meerkat_pjt, public;

ALTER TABLE law_documents
  ADD COLUMN IF NOT EXISTS source_category VARCHAR(50),
  ADD COLUMN IF NOT EXISTS source_type     VARCHAR(100),
  ADD COLUMN IF NOT EXISTS provider        VARCHAR(100);

CREATE INDEX IF NOT EXISTS ix_law_documents_source_category ON law_documents (source_category);
CREATE INDEX IF NOT EXISTS ix_law_documents_source_type     ON law_documents (source_type);

-- 기존 5개 법령은 source_category = NULL (기본값) 유지
-- 산업안전보건기준에 관한 규칙이 이미 ingestion돼 있으면 아래 UPDATE 실행:
-- UPDATE law_documents
--   SET source_category = 'safety_standard',
--       source_type     = 'rule',
--       provider        = 'law.go.kr'
-- WHERE law_name LIKE '%산업안전보건기준에 관한 규칙%';
