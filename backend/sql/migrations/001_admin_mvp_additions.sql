-- DEV/STAGING/PROD SAFE MIGRATION SCRIPT (idempotent)
-- Purpose: Admin MVP schema additions without Alembic

BEGIN;

-- 1) users.role add + normalize + constraint
ALTER TABLE IF EXISTS public.users
ADD COLUMN IF NOT EXISTS role VARCHAR(20);

UPDATE public.users
SET role = 'worker'
WHERE role IS NULL;

ALTER TABLE public.users
ALTER COLUMN role SET DEFAULT 'worker';

ALTER TABLE public.users
ALTER COLUMN role SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'users_role_check'
          AND conrelid = 'public.users'::regclass
    ) THEN
        ALTER TABLE public.users
        ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'worker'));
    END IF;
END $$;

-- 2) law_search_logs table create
CREATE TABLE IF NOT EXISTS public.law_search_logs (
    id BIGSERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    user_id BIGINT NULL,
    site_id BIGINT NULL,
    top_k INTEGER NOT NULL DEFAULT 5,
    result_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'law_search_logs_user_id_fkey'
          AND conrelid = 'public.law_search_logs'::regclass
    ) THEN
        ALTER TABLE public.law_search_logs
        ADD CONSTRAINT law_search_logs_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'law_search_logs_site_id_fkey'
          AND conrelid = 'public.law_search_logs'::regclass
    ) THEN
        ALTER TABLE public.law_search_logs
        ADD CONSTRAINT law_search_logs_site_id_fkey
        FOREIGN KEY (site_id) REFERENCES public.sites(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 3) Required indexes for logs
CREATE INDEX IF NOT EXISTS idx_law_search_logs_user_id ON public.law_search_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_law_search_logs_site_id ON public.law_search_logs(site_id);
CREATE INDEX IF NOT EXISTS idx_law_search_logs_created_at ON public.law_search_logs(created_at DESC);

-- 4) Dashboard aggregation/read optimization indexes
CREATE INDEX IF NOT EXISTS idx_generated_documents_site_created
ON public.generated_documents(site_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_safety_quizzes_site_date_active
ON public.safety_quizzes(site_id, quiz_date, is_active);

CREATE INDEX IF NOT EXISTS idx_law_search_logs_site_created
ON public.law_search_logs(site_id, created_at DESC);

COMMIT;
