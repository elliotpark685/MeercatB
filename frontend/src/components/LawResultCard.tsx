import type { LawSearchResultItem } from '../types/law';
import { getLawBadgeColor } from '../types/law';

interface LawResultCardProps {
  item: LawSearchResultItem;
}

function formatScore(score?: number | null): string | null {
  if (score === null || score === undefined || Number.isNaN(score)) return null;
  return score.toFixed(3);
}

function formatReferences(refs?: string[] | string | null): string | null {
  if (!refs) return null;
  if (Array.isArray(refs)) {
    const filtered = refs.filter(Boolean);
    return filtered.length > 0 ? filtered.join(', ') : null;
  }
  return refs;
}

function formatLawDate(value?: string | null): string | null {
  if (!value) return null;

  const trimmed = value.trim();
  if (!trimmed) return null;

  const isoMatch = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoMatch) return trimmed;

  const dottedMatch = trimmed.match(/^(\d{2,4})\.(\d{1,2})\.(\d{1,2})\.?$/);
  if (dottedMatch) {
    const year = dottedMatch[1].length === 2 ? `20${dottedMatch[1]}` : dottedMatch[1];
    const month = dottedMatch[2].padStart(2, '0');
    const day = dottedMatch[3].padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  const compactMatch = trimmed.match(/^(\d{4})(\d{2})(\d{2})$/);
  if (compactMatch) {
    return `${compactMatch[1]}-${compactMatch[2]}-${compactMatch[3]}`;
  }

  return trimmed;
}

export default function LawResultCard({ item }: LawResultCardProps) {
  const lawName = item.law_name?.trim() || '법령명 미상';
  const articleNo = item.article_no?.trim();
  const articleTitle = item.article_title?.trim();
  const text = (item.chunk_text ?? item.content ?? '').trim();
  const score = formatScore(item.score);
  const effectiveDate = formatLawDate(item.effective_date);
  const documentEffectiveDate = formatLawDate(item.document_effective_date);
  const sourceUrl = item.source_url?.trim();
  const references = formatReferences(item.references);
  const badgeColor = getLawBadgeColor(item.law_name);
  const showDocumentEffectiveDate =
    documentEffectiveDate && documentEffectiveDate !== effectiveDate ? documentEffectiveDate : null;
  const dateLines = [
    effectiveDate ? `시행일: ${effectiveDate}` : null,
    showDocumentEffectiveDate ? `문서 시행일: ${showDocumentEffectiveDate}` : null,
  ].filter((line): line is string => Boolean(line));

  return (
    <div className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] overflow-hidden">
      <div className={`px-4 py-2 border-b flex items-center justify-between gap-2 ${badgeColor}`}>
        <span className="text-xs font-semibold truncate">{lawName}</span>
        {score !== null && (
          <span className="text-[10px] text-[#98989D] shrink-0">유사도 {score}</span>
        )}
      </div>

      <div className="p-4 space-y-3">
        {(articleNo || articleTitle) && (
          <h3 className="text-sm font-semibold text-white">
            {articleNo && <span className="text-[#00E5FF] mr-1.5">{articleNo}</span>}
            {articleTitle}
          </h3>
        )}

        {text && (
          <p className="text-sm text-[#98989D] whitespace-pre-wrap leading-relaxed">{text}</p>
        )}

        {references && (
          <p className="text-xs text-[#3A3A3C]">관련 조문: {references}</p>
        )}

        <div className="flex items-center justify-between gap-2 pt-1">
          {dateLines.length > 0 ? (
            <div className="flex flex-col gap-0.5 text-[10px] text-[#3A3A3C]">
              {dateLines.map((line) => (
                <span key={line}>{line}</span>
              ))}
            </div>
          ) : (
            <span />
          )}

          {sourceUrl && (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs px-3 py-1.5 rounded-lg border border-[#2C2C2E] text-[#00E5FF] hover:bg-[#00E5FF]/10 hover:border-[#00E5FF]/30 transition-colors shrink-0"
            >
              법제처 원문 보기
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
