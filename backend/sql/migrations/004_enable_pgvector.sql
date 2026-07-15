-- Run this migration before setting USE_PGVECTOR=true.
-- The project uses text-embedding-3-small (1536 dimensions).

CREATE EXTENSION IF NOT EXISTS vector;

DO $$
DECLARE
    invalid_embedding_count integer;
BEGIN
    SELECT count(*)
    INTO invalid_embedding_count
    FROM meerkat_pjt.law_embeddings
    WHERE embedding IS NOT NULL
      AND vector_dims(embedding::text::vector) <> 1536;

    IF invalid_embedding_count > 0 THEN
        RAISE EXCEPTION
            'Expected 1536-dimensional embeddings, but found % incompatible row(s). Re-embed them before enabling pgvector.',
            invalid_embedding_count;
    END IF;
END $$;

ALTER TABLE meerkat_pjt.law_embeddings
    ALTER COLUMN embedding TYPE vector(1536)
    USING embedding::text::vector(1536);

ALTER TABLE meerkat_pjt.law_embeddings
    ALTER COLUMN embedding_vector TYPE vector(1536)
    USING embedding_vector::text::vector(1536);

CREATE INDEX IF NOT EXISTS idx_law_embeddings_vector_cosine
    ON meerkat_pjt.law_embeddings
    USING hnsw (embedding_vector vector_cosine_ops)
    WHERE embedding_vector IS NOT NULL;
