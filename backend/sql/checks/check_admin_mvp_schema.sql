-- Schema check for Admin MVP additions

-- 1) users.role exists?
SELECT table_schema, table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'users'
  AND column_name = 'role';

-- 2) law_search_logs table exists?
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name = 'law_search_logs';

-- 3) law_search_logs row count
SELECT COUNT(*) AS law_search_logs_count
FROM public.law_search_logs;

-- 4) recent search logs
SELECT id, query, user_id, site_id, top_k, result_count, created_at
FROM public.law_search_logs
ORDER BY created_at DESC
LIMIT 10;

-- 5) admin/worker counts
SELECT role, COUNT(*) AS user_count
FROM public.users
GROUP BY role
ORDER BY role;

-- 6) dashboard-related table counts
SELECT
  (SELECT COUNT(*) FROM public.generated_documents) AS generated_documents_count,
  (SELECT COUNT(*) FROM public.safety_quizzes) AS safety_quizzes_count,
  (SELECT COUNT(*) FROM public.law_search_logs) AS law_search_logs_count;
