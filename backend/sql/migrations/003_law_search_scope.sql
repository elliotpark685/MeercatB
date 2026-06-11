ALTER TABLE IF EXISTS public.law_search_logs
ADD COLUMN IF NOT EXISTS law_scope text;
