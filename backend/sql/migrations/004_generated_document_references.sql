ALTER TABLE IF EXISTS public.generated_documents
ADD COLUMN IF NOT EXISTS references_json text;

UPDATE public.generated_documents
SET references_json = citations_json
WHERE references_json IS NULL
  AND citations_json IS NOT NULL;
