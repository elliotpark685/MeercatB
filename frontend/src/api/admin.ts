/**
 * 관리자 API 함수 모음
 * 인증: Authorization: Bearer <access_token> (client.ts에서 자동 포함)
 * X-User-Id 헤더는 더 이상 사용하지 않는다.
 */
import { apiClient } from './client';

// ─── 타입 정의 ───────────────────────────────────────────

export interface DashboardData {
  site_id: number | null;
  total_generated_documents: number;
  total_law_searches: number;
  today_quiz_count: number;
  latest_generated_documents: RecentDocument[];
  latest_law_searches: RecentLawSearch[];
}

export interface RecentDocument {
  id: number;
  site_id: number;
  title: string;
  document_type: string;
  created_at: string;
}

export interface RecentLawSearch {
  id: number;
  query: string;
  top_k: number;
  result_count: number;
  created_at: string;
}

export interface LawSearchParams {
  query: string;
  top_k?: number;
  validate_latest?: boolean;
}

export interface CitationItem {
  article_id: number;
  law_name: string;
  article_no: string;
  article_title: string | null;
  chapter: string | null;
  section: string | null;
  status: string;
  effective_date: string | null;
}

export interface RawHitItem {
  article_id: number;
  score: number;
  matched_reason: string[];
}

export interface LawSearchResult {
  query: string;
  answer: string;
  citations: CitationItem[];
  raw_hits: RawHitItem[];
}

export interface ArticleDetail {
  article_id: number;
  law_document_id: number;
  law_name: string;
  article_no: string;
  article_title: string | null;
  chapter: string | null;
  section: string | null;
  full_text: string;
  status: string;
  effective_date: string | null;
  source_page_start: number | null;
  source_page_end: number | null;
  law_type: string | null;
  law_no: string | null;
  document_effective_date: string | null;
  source_file_path: string | null;
}

export type DocumentType = 'tbm' | 'risk_assessment' | 'work_plan' | 'inspection_checklist';

export interface GenerateDocumentParams {
  site_id: number;
  user_id: number | null; // 선택값, null 허용
  document_type: DocumentType;
  prompt: string; // 5~4000자
}

export interface GeneratedDocument {
  document_id: number;
  title: string;
  content: string;
  citations: { article_id: number; law_name: string; article_no: string }[];
}

// ─── API 함수 ─────────────────────────────────────────────

export async function getAdminDashboard(siteId?: number): Promise<DashboardData> {
  const res = await apiClient.get('/api/v1/admin/dashboard', {
    params: siteId != null ? { site_id: siteId } : undefined,
  });
  return res.data;
}

export async function searchLaws(
  params: LawSearchParams & { userId?: number | null; siteId?: number | null }
): Promise<LawSearchResult> {
  const { userId, siteId, ...body } = params;
  // 가이드 스펙: user_id/site_id는 없을 때 null로 명시적 전송
  const res = await apiClient.post('/api/v1/laws/search', {
    ...body,
    user_id: Number.isFinite(userId) ? userId : null,
    site_id: Number.isFinite(siteId) ? siteId : null,
  });
  return res.data;
}

export async function getLawArticle(articleId: number): Promise<ArticleDetail> {
  const res = await apiClient.get(`/api/v1/laws/articles/${articleId}`);
  return res.data;
}

export async function generateDocument(params: GenerateDocumentParams): Promise<GeneratedDocument> {
  const res = await apiClient.post('/api/v1/documents/generate', params);
  return res.data;
}

export async function getDailyQuizzes(siteId?: number, userId?: number) {
  const res = await apiClient.get('/api/v1/quizzes/daily', {
    params: {
      ...(siteId != null ? { site_id: siteId } : {}),
      ...(userId != null ? { user_id: userId } : {}),
    },
  });
  return res.data;
}
