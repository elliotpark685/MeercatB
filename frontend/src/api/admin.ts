/**
 * 愿由ъ옄 API ?⑥닔 紐⑥쓬
 * ?몄쬆: Authorization: Bearer <access_token> (client.ts?먯꽌 ?먮룞 ?ы븿)
 * X-User-Id ?ㅻ뜑?????댁긽 ?ъ슜?섏? ?딅뒗??
 */
import { apiClient } from './client';
import type { LawSearchResultItem } from '../types/law';

export type { LawSearchResultItem } from '../types/law';

// ??? ????뺤쓽 ???????????????????????????????????????????

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
  /** 寃?????踰뺣졊紐?紐⑸줉. 鍮꾩뼱?덉쑝硫?諛깆뿏??湲곕낯媛?5媛?踰뺣졊 ?꾩껜)?쇰줈 寃?됲븳?? */
  law_names?: string[];
  /** law_names??蹂꾩묶. 諛깆뿏???명솚???꾪빐 ????吏?먰븳?? */
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
  /** 踰뺣졊蹂?寃??寃곌낵 移대뱶 紐⑸줉 (?좉퇋 ?꾨뱶, ?놁쓣 ???덉쓬) */
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
  user_id: number | null; // ?좏깮媛? null ?덉슜
  document_type: DocumentType;
  prompt: string; // 5~4000??
}

export interface GeneratedDocument {
  document_id: number;
  title: string;
  content: string;
  citations: { article_id: number; law_name: string; article_no: string }[];
}

// ??? API ?⑥닔 ?????????????????????????????????????????????

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
  // 媛?대뱶 ?ㅽ럺: user_id/site_id???놁쓣 ??null濡?紐낆떆???꾩넚
  // law_names/law_scope???좏깮媛믪씠硫? 鍮꾩뼱?덉쑝硫?蹂대궡吏 ?딆븘 諛깆뿏??湲곕낯媛?5媛?踰뺣졊 ?꾩껜)???ъ슜?쒕떎.
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

// ??? ?덉쟾湲곗? 寃??????????????????????????????????????????????????????????????

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

// ??? KOSHA GUIDE 寃???????????????????????????????????????????????????????????

export type KoshaCategory = '0' | '4' | '5' | '6' | '7';

export const KOSHA_CATEGORY_LABEL: Record<KoshaCategory, string> = {
  '0': '전체',
  '4': '산업안전보건기준에 관한 규칙',
  '5': '고시·훈령·예규',
  '6': '안전보건 미디어',
  '7': 'KOSHA GUIDE',
};

export interface KoshaResultItem {
  title: string;
  content: string;
  category: string;
  /** 寃?됱뼱? ?쇱튂??媛뺤“ ?⑥뼱 (KOSHA API??highlight_content?먯꽌 異붿텧, API ?먯껜 ?ㅼ썙???꾨뱶???놁쓬) */
  keywords: string[];
  score: number;
  /** KOSHA OpenAPI???먮Ц URL???쒓났?섏? ?딆븘 ??긽 鍮?臾몄옄??*/
  url: string;
  /** 臾몄꽌 ?앸퀎 臾몄옄??(?? "KOSHA07_..._1"), ?먮Ц 留곹겕 ?泥댁슜 李멸퀬 ?뺣낫 */
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
  error?: string | null;
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


