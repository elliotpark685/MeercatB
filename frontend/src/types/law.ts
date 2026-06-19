/**
 * 5개 법령 통합 검색 관련 타입 정의
 */

/** 통합 검색 대상 5개 법령 */
export const LAW_SCOPE_OPTIONS = [
  '산업안전보건법',
  '시설물의 안전 및 유지관리에 관한 특별법',
  '건설산업기본법',
  '건설기술 진흥법',
  '중대재해 처벌 등에 관한 법률',
] as const;

export type LawScopeOption = (typeof LAW_SCOPE_OPTIONS)[number];

/**
 * 법령별 카드 배지 색상 (tailwind 클래스)
 * 백엔드 응답 law_name이 위 5개 외의 값일 수도 있으므로 fallback 색상을 둔다.
 */
export const LAW_BADGE_COLORS: Record<string, string> = {
  '산업안전보건법': 'bg-[#00E5FF]/15 text-[#00E5FF] border-[#00E5FF]/30',
  '시설물의 안전 및 유지관리에 관한 특별법': 'bg-[#34C759]/15 text-[#34C759] border-[#34C759]/30',
  '건설산업기본법': 'bg-[#FFD60A]/15 text-[#FFD60A] border-[#FFD60A]/30',
  '건설기술 진흥법': 'bg-[#BF5AF2]/15 text-[#BF5AF2] border-[#BF5AF2]/30',
  '중대재해 처벌 등에 관한 법률': 'bg-[#FF453A]/15 text-[#FF453A] border-[#FF453A]/30',
};

export const DEFAULT_LAW_BADGE_COLOR = 'bg-[#98989D]/15 text-[#98989D] border-[#98989D]/30';

export function getLawBadgeColor(lawName?: string | null): string {
  if (!lawName) return DEFAULT_LAW_BADGE_COLOR;
  return LAW_BADGE_COLORS[lawName] ?? DEFAULT_LAW_BADGE_COLOR;
}

/**
 * 법령 통합 검색 결과 항목.
 * 백엔드 필드명이 변경되거나 일부가 누락될 수 있으므로 모두 optional 처리한다.
 */
export interface LawSearchResultItem {
  law_name?: string | null;
  article_no?: string | null;
  article_title?: string | null;
  chunk_text?: string | null;
  content?: string | null;
  score?: number | null;
  source_url?: string | null;
  effective_date?: string | null;
  document_effective_date?: string | null;
  article_id?: number | null;
  chunk_id?: number | null;
  matched_reason?: string[] | null;
  references?: string[] | string | null;
}
