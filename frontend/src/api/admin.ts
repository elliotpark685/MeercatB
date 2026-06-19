/**
 * 관리자 API 함수 모음
 * 인증: Authorization: Bearer <access_token> (client.ts에서 자동 포함)
 * X-User-Id 헤더는 더 이상 사용하지 않는다.
 */
import { apiClient } from './client';
import type { LawSearchResultItem } from '../types/law';

export type { LawSearchResultItem } from '../types/law';

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
  /** 검색 대상 법령명 목록. 비어있으면 백엔드 기본값(5개 법령 전체)으로 검색한다. */
  law_names?: string[];
  /** law_names의 별칭. 백엔드 호환을 위해 둘 다 지원한다. */
  law_scope?: string[];
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
  /** 법령별 검색 결과 카드 목록 (신규 필드, 없을 수 있음) */
  results?: LawSearchResultItem[];
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
  const { userId, siteId, law_names, law_scope, ...body } = params;
  // 가이드 스펙: user_id/site_id는 없을 때 null로 명시적 전송
  // law_names/law_scope는 선택값이며, 비어있으면 보내지 않아 백엔드 기본값(5개 법령 전체)을 사용한다.
  const scope = law_names && law_names.length > 0 ? law_names : law_scope;
  const res = await apiClient.post('/api/v1/laws/search', {
    ...body,
    user_id: Number.isFinite(userId) ? userId : null,
    site_id: Number.isFinite(siteId) ? siteId : null,
    ...(scope && scope.length > 0 ? { law_names: scope } : {}),
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

// ─── 안전기준 검색 ────────────────────────────────────────────────────────────

export interface SafetyStandardResultItem {
  source_type: string;
  source_name: string;
  article_no: string | null;
  article_title: string | null;
  content: string;
  score: number;
  provider: string;
  article_id: number | null;
  chunk_id: number | null;
  matched_reason: string[];
}

export interface SafetyStandardSearchResult {
  query: string;
  results: SafetyStandardResultItem[];
}

export interface SafetyStandardSearchParams {
  query: string;
  top_k?: number;
  source_types?: string[];
  userId?: number | null;
  siteId?: number | null;
}

export async function searchSafetyStandards(
  params: SafetyStandardSearchParams
): Promise<SafetyStandardSearchResult> {
  const { userId, siteId, ...body } = params;
  const res = await apiClient.post('/api/v1/safety-standards/search', {
    ...body,
    user_id: Number.isFinite(userId) ? userId : null,
    site_id: Number.isFinite(siteId) ? siteId : null,
  });
  return res.data;
}

// ─── KOSHA GUIDE 검색 ─────────────────────────────────────────────────────────

export type KoshaCategory = '4' | '5' | '6' | '7';

export const KOSHA_CATEGORY_LABEL: Record<KoshaCategory, string> = {
  '4': '산업안전보건기준에 관한 규칙',
  '5': '고시·훈령·예규',
  '6': '안전보건 미디어',
  '7': 'KOSHA GUIDE',
};

export interface KoshaResultItem {
  title: string;
  content: string;
  category: string;
  /** 검색어와 일치한 강조 단어 (KOSHA API의 highlight_content에서 추출, API 자체 키워드 필드는 없음) */
  keywords: string[];
  score: number;
  /** KOSHA OpenAPI는 원문 URL을 제공하지 않아 항상 빈 문자열 */
  url: string;
  /** 문서 식별 문자열 (예: "KOSHA07_..._1"), 원문 링크 대체용 참고 정보 */
  doc_id: string;
}

export interface KoshaSearchResult {
  query: string;
  category: KoshaCategory;
  page: number;
  size: number;
  total: number;
  results: KoshaResultItem[];
  related_keywords: string[];
}

export interface KoshaSearchParams {
  query: string;
  category?: KoshaCategory;
  page?: number;
  size?: number;
}

export async function searchKosha(params: KoshaSearchParams): Promise<KoshaSearchResult> {
  const res = await apiClient.get('/api/v1/kosha/search', { params });
  return res.data;
}

export interface KoshaSummaryResult {
  query: string;
  core_content: string;
  applicable_scope: string;
  field_application: string;
  precautions: string;
  related_regulations: string;
}

export async function summarizeKosha(
  query: string,
  items: KoshaResultItem[]
): Promise<KoshaSummaryResult> {
  const res = await apiClient.post('/api/v1/kosha/summarize', { query, items });
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
