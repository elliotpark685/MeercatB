-- WARNING: DEV/STAGING SEED ONLY
-- DO NOT RUN IN PRODUCTION DATABASE

BEGIN;

-- users: 1 admin + 2 workers (upsert by email)
INSERT INTO public.users (email, full_name, hashed_password, is_active, role)
VALUES ('admin.dev@meerkat.local', 'Dev Admin', '__SET_WITH_SCRIPT__', TRUE, 'admin')
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    is_active = EXCLUDED.is_active,
    role = EXCLUDED.role;

INSERT INTO public.users (email, full_name, hashed_password, is_active, role)
VALUES
('worker1.dev@meerkat.local', 'Dev Worker One', '__SET_WITH_SCRIPT__', TRUE, 'worker'),
('worker2.dev@meerkat.local', 'Dev Worker Two', '__SET_WITH_SCRIPT__', TRUE, 'worker')
ON CONFLICT (email) DO UPDATE
SET full_name = EXCLUDED.full_name,
    is_active = EXCLUDED.is_active,
    role = EXCLUDED.role;

-- site: 1 row (dedupe by name)
INSERT INTO public.sites (name, location, description)
VALUES ('Dev Sample Site', 'Seoul', 'Development sample construction site')
ON CONFLICT DO NOTHING;

-- generated_documents: sample 2 rows (avoid duplicates by title)
INSERT INTO public.generated_documents (site_id, created_by, document_type, title, prompt, content, citations_json)
SELECT s.id, a.id, 'tbm', 'TBM - Dev Sample Site', '고소작업 TBM', '# TBM sample', '[]'
FROM public.sites s
JOIN public.users a ON a.email = 'admin.dev@meerkat.local'
WHERE s.name = 'Dev Sample Site'
  AND NOT EXISTS (
    SELECT 1 FROM public.generated_documents gd WHERE gd.title = 'TBM - Dev Sample Site'
  );

INSERT INTO public.generated_documents (site_id, created_by, document_type, title, prompt, content, citations_json)
SELECT s.id, a.id, 'risk_assessment', 'RISK_ASSESSMENT - Dev Sample Site', '굴착 위험성평가', '# Risk sample', '[]'
FROM public.sites s
JOIN public.users a ON a.email = 'admin.dev@meerkat.local'
WHERE s.name = 'Dev Sample Site'
  AND NOT EXISTS (
    SELECT 1 FROM public.generated_documents gd WHERE gd.title = 'RISK_ASSESSMENT - Dev Sample Site'
  );

-- safety_quizzes: sample 2 rows (dedupe by date+question)
INSERT INTO public.safety_quizzes (quiz_date, site_id, user_id, question, choices_json, answer_index, explanation, is_active, category)
SELECT CURRENT_DATE, s.id, NULL,
       '고소작업 시작 전 가장 먼저 확인할 것은?',
       '["커피 시간", "추락방지 설비", "차량 연료", "날씨 앱"]',
       1,
       '추락재해 예방이 최우선입니다.',
       TRUE,
       'working-at-height'
FROM public.sites s
WHERE s.name = 'Dev Sample Site'
  AND NOT EXISTS (
    SELECT 1 FROM public.safety_quizzes q
    WHERE q.quiz_date = CURRENT_DATE
      AND q.question = '고소작업 시작 전 가장 먼저 확인할 것은?'
  );

INSERT INTO public.safety_quizzes (quiz_date, site_id, user_id, question, choices_json, answer_index, explanation, is_active, category)
SELECT CURRENT_DATE, s.id, NULL,
       '굴착 작업 시 붕괴 위험 감소 조치로 가장 적절한 것은?',
       '["장비 속도 증가", "흙막이 점검", "야간 단독작업", "출입통제 해제"]',
       1,
       '흙막이/지보공 점검은 붕괴 예방 핵심입니다.',
       TRUE,
       'excavation'
FROM public.sites s
WHERE s.name = 'Dev Sample Site'
  AND NOT EXISTS (
    SELECT 1 FROM public.safety_quizzes q
    WHERE q.quiz_date = CURRENT_DATE
      AND q.question = '굴착 작업 시 붕괴 위험 감소 조치로 가장 적절한 것은?'
  );

-- law_search_logs: sample 3 rows (dedupe by query+created date)
INSERT INTO public.law_search_logs (query, user_id, site_id, top_k, result_count)
SELECT '추락 방지 조치', u.id, s.id, 5, 3
FROM public.users u, public.sites s
WHERE u.email = 'admin.dev@meerkat.local'
  AND s.name = 'Dev Sample Site'
  AND NOT EXISTS (
    SELECT 1 FROM public.law_search_logs l
    WHERE l.query = '추락 방지 조치' AND l.created_at::date = CURRENT_DATE
  );

INSERT INTO public.law_search_logs (query, user_id, site_id, top_k, result_count)
SELECT '굴착 붕괴 위험', u.id, s.id, 5, 2
FROM public.users u, public.sites s
WHERE u.email = 'worker1.dev@meerkat.local'
  AND s.name = 'Dev Sample Site'
  AND NOT EXISTS (
    SELECT 1 FROM public.law_search_logs l
    WHERE l.query = '굴착 붕괴 위험' AND l.created_at::date = CURRENT_DATE
  );

INSERT INTO public.law_search_logs (query, user_id, site_id, top_k, result_count)
SELECT '작업계획서 필수 항목', u.id, s.id, 3, 1
FROM public.users u, public.sites s
WHERE u.email = 'worker2.dev@meerkat.local'
  AND s.name = 'Dev Sample Site'
  AND NOT EXISTS (
    SELECT 1 FROM public.law_search_logs l
    WHERE l.query = '작업계획서 필수 항목' AND l.created_at::date = CURRENT_DATE
  );

COMMIT;
