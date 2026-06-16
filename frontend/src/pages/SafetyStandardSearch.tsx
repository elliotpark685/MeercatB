import { useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  searchSafetyStandards,
  type SafetyStandardResultItem,
  type SafetyStandardSearchResult,
} from '../api/admin';
import Spinner from '../components/Spinner';
import ErrorBox from '../components/ErrorBox';
import EmptyState from '../components/EmptyState';

const TOP_K_OPTIONS = [3, 5, 10];
const HISTORY_KEY = 'meerkat_safety_history';
const HISTORY_MAX = 8;

type FilterType = 'all' | 'rule' | 'moel_standard_safety_guideline';

const FILTER_OPTIONS: { value: FilterType; label: string; shortLabel: string }[] = [
  { value: 'all', label: '전체', shortLabel: '전체' },
  {
    value: 'rule',
    label: '산업안전보건기준에 관한 규칙',
    shortLabel: '규칙',
  },
  {
    value: 'moel_standard_safety_guideline',
    label: '고용노동부 표준안전작업지침',
    shortLabel: '작업지침',
  },
];

const SOURCE_TYPE_LABEL: Record<string, string> = {
  rule: '산업안전보건기준에 관한 규칙',
  moel_standard_safety_guideline: '고용노동부 표준안전작업지침',
};

const SOURCE_TYPE_COLOR: Record<string, string> = {
  rule: 'border-[#00E5FF]/25 text-[#00E5FF] bg-[#00E5FF]/10',
  moel_standard_safety_guideline: 'border-[#FF9F0A]/25 text-[#FF9F0A] bg-[#FF9F0A]/10',
};

function loadHistory(): string[] {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? '[]');
  } catch {
    return [];
  }
}

function saveHistory(query: string) {
  const prev = loadHistory().filter((q) => q !== query);
  const next = [query, ...prev].slice(0, HISTORY_MAX);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
}

function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
}

function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function SafetyResultCard({ item }: { item: SafetyStandardResultItem }) {
  const [expanded, setExpanded] = useState(false);
  const typeLabel = SOURCE_TYPE_LABEL[item.source_type] ?? item.source_type;
  const typeColor = SOURCE_TYPE_COLOR[item.source_type] ?? 'border-[#98989D]/30 text-[#98989D] bg-[#98989D]/10';
  const preview = expanded ? item.content : item.content.slice(0, 200);
  const scoreColor =
    item.score >= 0.7 ? 'text-[#32D74B]' : item.score >= 0.4 ? 'text-[#FF9F0A]' : 'text-[#98989D]';

  return (
    <article className="group relative overflow-hidden rounded-2xl border border-[#2C2C2E] bg-[#1A1A1A] shadow-[0_0_0_1px_rgba(255,255,255,0.02)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#3A3A3C]">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      <div className="p-4 sm:p-5 space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex min-w-0 flex-1 items-center gap-2">
            <span className={`inline-flex shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-medium ${typeColor}`}>
              {typeLabel}
            </span>
            <span className={`text-xs font-mono ${scoreColor}`}>{formatScore(item.score)}</span>
          </div>
          <span className="rounded-full border border-[#2C2C2E] bg-[#121212] px-2.5 py-1 text-[11px] text-[#98989D]">
            {item.provider}
          </span>
        </div>

        <div className="space-y-1.5">
          <p className="truncate text-[13px] font-medium text-[#C7C7CC]">{item.source_name}</p>
          <div className="flex flex-wrap items-center gap-2">
            {item.article_no && (
              <span className="inline-flex rounded-md bg-[#FF9F0A]/10 px-2 py-1 text-xs font-semibold text-[#FF9F0A]">
                {item.article_no}
              </span>
            )}
            {item.article_title && (
              <h3 className="text-sm font-semibold text-white">
                {item.article_title}
              </h3>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm leading-6 text-[#C7C7CC] whitespace-pre-wrap break-words">
            {preview}
            {item.content.length > 200 && !expanded && '...'}
          </p>
          {item.content.length > 200 && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="inline-flex items-center gap-1 text-sm font-medium text-[#FF9F0A] transition-colors hover:text-[#FFB347]"
            >
              {expanded ? '접기' : '더보기'}
              <span aria-hidden="true">{expanded ? '−' : '+'}</span>
            </button>
          )}
        </div>
      </div>
    </article>
  );
}

function FilterTab({
  active,
  label,
  shortLabel,
  count,
  onClick,
}: {
  active: boolean;
  label: string;
  shortLabel: string;
  count: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all ${
        active
          ? 'border-[#FF9F0A]/35 bg-[#FF9F0A]/10 text-[#FF9F0A] shadow-[0_0_0_1px_rgba(255,159,10,0.12)]'
          : 'border-[#2C2C2E] bg-[#121212] text-[#98989D] hover:border-[#3A3A3C] hover:text-white'
      }`}
    >
      <span className="sm:hidden">{shortLabel}</span>
      <span className="hidden sm:inline">{label}</span>
      <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${active ? 'bg-[#FF9F0A]/15' : 'bg-[#1E1E1E]'}`}>
        {count}
      </span>
    </button>
  );
}

export default function SafetyStandardSearch() {
  const { userId, siteId } = useAuth();

  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [filterType, setFilterType] = useState<FilterType>('all');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<SafetyStandardSearchResult | null>(null);

  const [history, setHistory] = useState<string[]>(loadHistory);
  const [showHistory, setShowHistory] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        !inputRef.current?.contains(e.target as Node)
      ) {
        setShowHistory(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  async function handleSearch(e: React.FormEvent, overrideQuery?: string) {
    e.preventDefault();
    const q = (overrideQuery ?? query).trim();
    if (!q) return;

    setQuery(q);
    setShowHistory(false);
    saveHistory(q);
    setHistory(loadHistory());
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const sourceTypes = filterType === 'all' ? undefined : [filterType];
      const res = await searchSafetyStandards({
        query: q,
        top_k: topK,
        source_types: sourceTypes,
        userId: userId ?? undefined,
        siteId: siteId ?? undefined,
      });
      setResult(res);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  function handleHistorySelect(q: string) {
    setQuery(q);
    setShowHistory(false);
    inputRef.current?.focus();
  }

  function handleClearHistory() {
    clearHistory();
    setHistory([]);
    setShowHistory(false);
  }

  const filteredHistory = history.filter((h) =>
    query ? h.toLowerCase().includes(query.toLowerCase()) : true
  );

  const allResults = useMemo(() => result?.results ?? [], [result]);

  const displayResults = useMemo(
    () =>
      filterType === 'all'
        ? allResults
        : allResults.filter((r) => r.source_type === filterType),
    [allResults, filterType]
  );

  const countsByFilter = useMemo(() => {
    const ruleCount = allResults.filter((item) => item.source_type === 'rule').length;
    const guidelineCount = allResults.filter(
      (item) => item.source_type === 'moel_standard_safety_guideline'
    ).length;
    return {
      all: allResults.length,
      rule: ruleCount,
      moel_standard_safety_guideline: guidelineCount,
    };
  }, [allResults]);

  const activeFilterLabel =
    FILTER_OPTIONS.find((option) => option.value === filterType)?.label ?? '전체';
  const hasNoResults = !!result && displayResults.length === 0;
  const searchSummary =
    result && allResults.length > 0
      ? `${result.query} · ${allResults.length}건`
      : null;

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[28px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-5 sm:p-6">
        <div className="pointer-events-none absolute inset-0 opacity-60">
          <div className="absolute -right-24 -top-24 h-64 w-64 rounded-full bg-[#FF9F0A]/10 blur-3xl" />
          <div className="absolute -left-16 bottom-0 h-48 w-48 rounded-full bg-[#FF9F0A]/5 blur-3xl" />
        </div>
        <div className="relative space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[#FF9F0A]/20 bg-[#FF9F0A]/10 px-3 py-1 text-xs font-medium text-[#FF9F0A]">
              안전기준 검색
            </span>
            <span className="rounded-full border border-[#2C2C2E] bg-[#121212] px-3 py-1 text-xs text-[#98989D]">
              /laws와 동일한 탐색 경험
            </span>
          </div>
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-white sm:text-3xl">안전기준 검색</h1>
            <p className="text-sm font-medium text-[#FF9F0A]">
              산업안전보건기준에 관한 규칙과 표준안전작업지침을 함께 찾습니다.
            </p>
            <p className="max-w-2xl text-xs leading-5 text-[#98989D]">
              결과 카드에서 출처 유형, 유사도, 조문번호, 본문 미리보기를 한 번에 확인할 수 있습니다.
            </p>
          </div>
        </div>
      </section>

      <form
        onSubmit={handleSearch}
        className="space-y-4 rounded-[28px] border border-[#2C2C2E] bg-[#1E1E1E] p-5 shadow-[0_8px_40px_rgba(0,0,0,0.18)]"
      >
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
          <div className="relative min-w-0">
            <input
              ref={inputRef}
              type="text"
              className="w-full rounded-2xl border border-[#2C2C2E] bg-[#121212] px-4 py-3 text-sm text-white placeholder:text-[#3A3A3C] outline-none transition focus:border-[#FF9F0A]/50 focus:ring-2 focus:ring-[#FF9F0A]/20"
              placeholder="예: 이동식비계 작업발판 기준"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => history.length > 0 && setShowHistory(true)}
              autoComplete="off"
            />

            {showHistory && filteredHistory.length > 0 && (
              <div
                ref={dropdownRef}
                className="absolute left-0 right-0 top-full z-20 mt-2 overflow-hidden rounded-2xl border border-[#2C2C2E] bg-[#1E1E1E] shadow-2xl"
              >
                <div className="flex items-center justify-between border-b border-[#2C2C2E] px-4 py-3">
                  <span className="text-[10px] uppercase tracking-[0.2em] text-[#98989D]">
                    최근 검색어
                  </span>
                  <button
                    type="button"
                    onClick={handleClearHistory}
                    className="text-xs text-[#98989D] transition-colors hover:text-[#FF9F0A]"
                  >
                    전체 삭제
                  </button>
                </div>
                <div className="max-h-64 overflow-auto">
                  {filteredHistory.map((h) => (
                    <button
                      key={h}
                      type="button"
                      onClick={() => handleHistorySelect(h)}
                      className="flex w-full items-center gap-2 px-4 py-3 text-left text-sm text-[#C7C7CC] transition-colors hover:bg-[#252525] hover:text-white"
                    >
                      <span className="text-xs text-[#3A3A3C]">↺</span>
                      <span className="truncate">{h}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="inline-flex items-center justify-center rounded-2xl bg-[#FF9F0A] px-5 py-3 text-sm font-semibold text-[#121212] transition-all hover:bg-[#FFB347] disabled:cursor-not-allowed disabled:opacity-40 sm:min-w-28"
          >
            검색
          </button>
        </div>

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-[#98989D]">
              결과 수
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="rounded-xl border border-[#2C2C2E] bg-[#121212] px-3 py-2 text-sm text-white outline-none focus:border-[#FF9F0A]/50 focus:ring-1 focus:ring-[#FF9F0A]/20"
              >
                {TOP_K_OPTIONS.map((k) => (
                  <option key={k} value={k}>
                    {k}
                  </option>
                ))}
              </select>
            </label>

            {searchSummary && (
              <div className="rounded-full border border-[#2C2C2E] bg-[#121212] px-3 py-2 text-xs text-[#98989D]">
                {searchSummary}
              </div>
            )}
          </div>

          <div className="text-xs text-[#3A3A3C]">
            {allResults.length > 0 ? '필터는 탭으로 전환됩니다.' : '검색 후 필터 탭이 활성화됩니다.'}
          </div>
        </div>

        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.2em] text-[#98989D]">출처 필터</div>
          <div
            role="tablist"
            aria-label="출처 필터"
            className="flex gap-2 overflow-x-auto pb-1"
          >
            {FILTER_OPTIONS.map((option) => (
              <FilterTab
                key={option.value}
                active={filterType === option.value}
                label={option.label}
                shortLabel={option.shortLabel}
                count={countsByFilter[option.value]}
                onClick={() => setFilterType(option.value)}
              />
            ))}
          </div>
        </div>
      </form>

      {loading && <Spinner text="안전기준 검색 중..." />}
      {!!error && <ErrorBox error={error} />}

      {!loading && hasNoResults && (
        <EmptyState
          icon="🦺"
          title={`선택한 필터(${activeFilterLabel})에서 일치하는 안전기준을 찾지 못했습니다.`}
          description="다른 키워드로 다시 검색하거나, 출처 필터를 전체로 바꿔보세요."
        />
      )}

      {!loading && !result && (
        <div className="rounded-[28px] border border-[#2C2C2E] bg-[#1E1E1E] p-6 text-center shadow-[0_8px_40px_rgba(0,0,0,0.14)]">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-[#FF9F0A]/20 bg-[#FF9F0A]/10 text-2xl text-[#FF9F0A]">
            🦺
          </div>
          <p className="mt-4 text-sm font-medium text-[#C7C7CC]">
            안전기준 데이터가 준비되면 검색 결과가 여기에 표시됩니다.
          </p>
          <p className="mt-2 text-xs leading-5 text-[#3A3A3C]">
            ingestion 실행 예시:
            <code className="ml-1 rounded bg-[#121212] px-1.5 py-0.5 font-mono text-[#FF9F0A]">
              python ingestion/ingest_admrul_safety_guidelines.py --embed
            </code>
          </p>
        </div>
      )}

      {!loading && displayResults.length > 0 && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[#98989D]">
            <span>총 {displayResults.length}건</span>
            <span>필터: {activeFilterLabel}</span>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {displayResults.map((item, idx) => (
              <SafetyResultCard key={item.chunk_id ?? item.article_id ?? idx} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
