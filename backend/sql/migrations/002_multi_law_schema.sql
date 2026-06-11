-- Expand law storage from article-only search to document/article/chunk/embedding search.
-- This migration follows the existing project convention of SQL files under sql/migrations.

ALTER TABLE IF EXISTS public.law_documents
ADD COLUMN IF NOT EXISTS law_name varchar(255),
ADD COLUMN IF NOT EXISTS law_short_name varchar(100),
ADD COLUMN IF NOT EXISTS amendment_date date,
ADD COLUMN IF NOT EXISTS version_hash varchar(128),
ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;

UPDATE public.law_documents
SET law_name = title
WHERE law_name IS NULL;

CREATE INDEX IF NOT EXISTS idx_law_documents_law_name ON public.law_documents(law_name);
CREATE INDEX IF NOT EXISTS idx_law_documents_law_short_name ON public.law_documents(law_short_name);
CREATE INDEX IF NOT EXISTS idx_law_documents_version_hash ON public.law_documents(version_hash);
CREATE INDEX IF NOT EXISTS idx_law_documents_is_active ON public.law_documents(is_active);

ALTER TABLE IF EXISTS public.law_articles
ADD COLUMN IF NOT EXISTS article_no varchar(50),
ADD COLUMN IF NOT EXISTS article_title varchar(255),
ADD COLUMN IF NOT EXISTS article_text text;

UPDATE public.law_articles
SET
    article_no = COALESCE(article_no, article_number),
    article_title = COALESCE(article_title, title),
    article_text = COALESCE(article_text, full_text, content);

ALTER TABLE IF EXISTS public.law_articles
ALTER COLUMN full_text DROP NOT NULL,
ALTER COLUMN content DROP NOT NULL;

CREATE INDEX IF NOT EXISTS idx_law_articles_article_no ON public.law_articles(article_no);

CREATE TABLE IF NOT EXISTS public.law_chunks (
    id serial PRIMARY KEY,
    law_article_id integer NOT NULL REFERENCES public.law_articles(id) ON DELETE CASCADE,
    chunk_level varchar(50) NOT NULL DEFAULT 'article',
    chunk_no varchar(100),
    chunk_text text NOT NULL,
    token_count integer,
    metadata_json text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_law_chunks_law_article_id ON public.law_chunks(law_article_id);
CREATE INDEX IF NOT EXISTS idx_law_chunks_chunk_level ON public.law_chunks(chunk_level);
CREATE INDEX IF NOT EXISTS idx_law_chunks_chunk_no ON public.law_chunks(chunk_no);

DO $$
DECLARE
    embedding_column_type text;
BEGIN
    SELECT format_type(a.atttypid, a.atttypmod)
    INTO embedding_column_type
    FROM pg_attribute a
    JOIN pg_class c ON c.oid = a.attrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname = 'law_embeddings'
      AND a.attname = 'embedding'
      AND NOT a.attisdropped;

    IF embedding_column_type IS NOT NULL THEN
        EXECUTE format(
            'ALTER TABLE public.law_embeddings ADD COLUMN IF NOT EXISTS embedding_vector %s',
            embedding_column_type
        );
    END IF;
END $$;

ALTER TABLE IF EXISTS public.law_embeddings
ADD COLUMN IF NOT EXISTS chunk_id integer;

UPDATE public.law_embeddings
SET embedding_vector = embedding
WHERE embedding_vector IS NULL;

ALTER TABLE IF EXISTS public.law_embeddings
ALTER COLUMN article_id DROP NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'law_embeddings_chunk_id_fkey'
          AND conrelid = 'public.law_embeddings'::regclass
    ) THEN
        ALTER TABLE public.law_embeddings
        ADD CONSTRAINT law_embeddings_chunk_id_fkey
        FOREIGN KEY (chunk_id) REFERENCES public.law_chunks(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_chunk_embedding_model'
          AND conrelid = 'public.law_embeddings'::regclass
    ) THEN
        ALTER TABLE public.law_embeddings
        ADD CONSTRAINT uq_chunk_embedding_model UNIQUE (chunk_id, embedding_model);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_law_embeddings_chunk_id ON public.law_embeddings(chunk_id);
