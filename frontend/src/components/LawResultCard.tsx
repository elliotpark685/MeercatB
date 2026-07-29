import type { LawSearchResultItem } from '../types/law';
import { getLawBadgeColor } from '../types/law';

interface LawResultCardProps {
  item: LawSearchResultItem;
  onViewDetail?: (articleId: number) => void;
}

function formatScore(score?: number | null): string | null {
  if (score === null || score === undefined || Number.isNaN(score)) return null;
  return score.toFixed(3);
}

export default function LawResultCard({ item, onViewDetail }: LawResultCardProps) {
  const lawName = item.law_name?.trim() || '법령명 미상';
  const articleNo = item.article_no?.trim();
  const articleTitle = item.title?.trim();
  const text = item.content_preview.trim();
  const score = formatScore(item.score);
  const badgeColor = getLawBadgeColor(item.law_name);
  const metadata = [
    item.law_no ? `공포번호 ${item.law_no}` : null,
    item.promulgation_date ? `공포일 ${item.promulgation_date}` : null,
    item.document_effective_date ? `시행일 ${item.document_effective_date}` : null,
    item.amendment_type ? item.amendment_type : null,
  ].filter(Boolean);

  return (
    <div className="overflow-hidden rounded-xl border border-[#E2E8F0] border-l-4 border-l-[#2563EB] bg-white shadow-[0_1px_3px_rgba(15,23,42,0.06)]">
      <div className={`px-4 py-2 border-b flex items-center justify-between gap-2 ${badgeColor}`}>
        <span className="text-xs font-semibold truncate">{lawName}</span>
        {score !== null && <span className="text-[10px] text-[#98989D] shrink-0">{score}</span>}
      </div>

      <div className="p-4 space-y-3">
        {(articleNo || articleTitle) && (
          <h3 className="text-sm font-semibold text-[#0F172A]">
            {articleNo && <span className="text-[#00E5FF] mr-1.5">{articleNo}</span>}
            {articleTitle}
          </h3>
        )}

        {metadata.length > 0 && (
          <p className="text-xs leading-5 text-[#00E5FF]/80">{metadata.join(' · ')}</p>
        )}

        {text && <p className="text-sm text-[#475569] whitespace-pre-wrap leading-relaxed">{text}</p>}

        {onViewDetail && (
          <div className="flex justify-end pt-1">
            <button
              type="button"
              onClick={() => onViewDetail(item.article_id)}
              className="rounded-lg border border-[#CBD5E1] bg-white px-3 py-1.5 text-xs font-medium text-[#2563EB] transition-colors hover:bg-[#EFF6FF]"
            >
              전체 내용 보기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
