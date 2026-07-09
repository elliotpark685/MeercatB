import type { LawSearchResultItem } from '../types/law';
import { getLawBadgeColor } from '../types/law';

interface LawResultCardProps {
  item: LawSearchResultItem;
}

function formatScore(score?: number | null): string | null {
  if (score === null || score === undefined || Number.isNaN(score)) return null;
  return score.toFixed(3);
}

export default function LawResultCard({ item }: LawResultCardProps) {
  const lawName = item.law_name?.trim() || '법령명 미상';
  const articleNo = item.article_no?.trim();
  const articleTitle = item.title?.trim();
  const text = item.content_preview.trim();
  const score = formatScore(item.score);
  const badgeColor = getLawBadgeColor(item.law_name);

  return (
    <div className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] overflow-hidden">
      <div className={`px-4 py-2 border-b flex items-center justify-between gap-2 ${badgeColor}`}>
        <span className="text-xs font-semibold truncate">{lawName}</span>
        {score !== null && <span className="text-[10px] text-[#98989D] shrink-0">{score}</span>}
      </div>

      <div className="p-4 space-y-3">
        {(articleNo || articleTitle) && (
          <h3 className="text-sm font-semibold text-white">
            {articleNo && <span className="text-[#00E5FF] mr-1.5">{articleNo}</span>}
            {articleTitle}
          </h3>
        )}

        {text && <p className="text-sm text-[#98989D] whitespace-pre-wrap leading-relaxed">{text}</p>}
      </div>
    </div>
  );
}
