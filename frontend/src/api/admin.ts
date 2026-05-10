import { apiClient } from './client';

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
  user_id: number;
  document_type: DocumentType;
  prompt: string;
}

export interface GeneratedDocument {
  document_id: number;
  title: string;
  content: string;
  citations: { article_id: number; law_name: string; article_no: string }[];
}

function parseOptionalInt(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const n = Number(value);
  return Number.isInteger(n) ? n : undefined;
}

export async function getAdminDashboard(params: { siteId?: string; userId: string }): Promise<DashboardData> {
  const parsedSiteId = parseOptionalInt(params.siteId);
  const res = await apiClient.get('/api/v1/admin/dashboard', {
    params: parsedSiteId !== undefined ? { site_id: parsedSiteId } : undefined,
    headers: { 'X-User-Id': params.userId },
  });
  return res.data;
}

export async function searchLaws(
  params: LawSearchParams & { userId?: string; siteId?: string }
): Promise<LawSearchResult> {
  const { userId, siteId, ...body } = params;
  const parsedUserId = parseOptionalInt(userId);
  const parsedSiteId = parseOptionalInt(siteId);

  const res = await apiClient.post('/api/v1/laws/search', {
    ...body,
    ...(parsedUserId !== undefined ? { user_id: parsedUserId } : {}),
    ...(parsedSiteId !== undefined ? { site_id: parsedSiteId } : {}),
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
