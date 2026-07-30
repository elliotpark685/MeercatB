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
    <article className="group relative overflow-hidden rounded-2xl border border-[#2C2C2E] bg-[#1A1A1A] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#3A3A3C]">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      <div className="flex items-center justify-between gap-2 border-b border-[#2C2C2E] px-4 py-3">
        <span className={`max-w-[80%] truncate rounded-full border px-2.5 py-1 text-[11px] font-medium ${badgeColor}`}>
          {lawName}
        </span>
        {score !== null && <span className="shrink-0 font-mono text-xs text-[#98989D]">{score}</span>}
      </div>

      <div className="space-y-3 p-4 sm:p-5">
        {(articleNo || articleTitle) && (
          <h3 className="text-sm font-semibold text-white">
            {articleNo && <span className="mr-1.5 text-[#00E5FF]">{articleNo}</span>}
            {articleTitle}
          </h3>
        )}

        {metadata.length > 0 && (
          <p className="text-xs leading-5 text-[#00E5FF]/80">{metadata.join(" · ")}</p>
        )}

        {text && <p className="whitespace-pre-wrap text-sm leading-6 text-[#C7C7CC]">{text}</p>}

        {onViewDetail && (
          <div className="pt-1">
            <button
              type="button"
              onClick={() => onViewDetail(item.article_id)}
              className="text-sm font-medium text-[#00E5FF] transition-colors hover:text-[#33EAFF]"
            >
              전체 내용 보기 →
            </button>
          </div>
        )}
      </div>
    </article>
  );
}
