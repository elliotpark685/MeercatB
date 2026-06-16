import { useState, useRef, useEffect, useMemo } from 'react';
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

const FILTER_OPTIONS: { value: FilterType; label: string }[] = [
  { value: 'all', label: '전체' },
  { value: 'rule', label: '산업안전보건기준에 관한 규칙' },
  { value: 'moel_standard_safety_guideline', label: '고용노동부 표준안전작업지침' },
];

const SOURCE_TYPE_LABEL: Record<string, string> = {
  rule: '산업안전보건기준에 관한 규칙',
  moel_standard_safety_guideline: '표준안전작업지침',
};

const SOURCE_TYPE_COLOR: Record<string, string> = {
  rule: 'border-[#32D74B]/30 text-[#32D74B] bg-[#32D74B]/10',
  moel_standard_safety_guideline: 'border-[#FF9F0A]/30 text-[#FF9F0A] bg-[#FF9F0A]/10',
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

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 70 ? 'text-[#32D74B]' : pct >= 40 ? 'text-[#FF9F0A]' : 'text-[#98989D]';
  return (
    <span className={`text-xs font-mono ${color}`}>{pct}%</span>
  );
}

function SafetyResultCard({ item }: { item: SafetyStandardResultItem }) {
  const [expanded, setExpanded] = useState(false);
  const typeLabel = SOURCE_TYPE_LABEL[item.source_type] ?? item.source_type;
  const typeColor = SOURCE_TYPE_COLOR[item.source_type] ?? 'border-[#98989D]/30 text-[#98989D]';
  const preview = expanded ? item.content : item.content.slice(0, 200);

  return (
    <div className="bg-[#1A1A1A] rounded-xl border border-[#2C2C2E] p-4 space-y-2 hover:border-[#3A3A3C] transition-colors">
      {/* 헤더 */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <span className={`text-[10px] px-2 py-0.5 rounded border font-medium shrink-0 ${typeColor}`}>
          {typeLabel}
        </span>
        <ScoreBadge score={item.score} />
      </div>

      {/* 문서명 + 조문번호 */}
      <div className="space-y-0.5">
        <p className="text-xs text-[#98989D] truncate">{item.source_name}</p>
        {(item.article_no || item.article_title) && (
          <p className="text-sm font-semibold text-white">
            {item.article_no && <span className="text-[#00E5FF]">{item.article_no} </span>}
            {item.article_title}
          </p>
        )}
      </div>

      {/* 본문 */}
      <p className="text-xs text-[#C7C7CC] leading-relaxed whitespace-pre-wrap break-words">
        {preview}
        {item.content.length > 200 && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="ml-1 text-[#00E5FF] hover:underline"
          >
            {expanded ? '접기' : '...더보기'}
          </button>
        )}
      </p>

      {/* 출처 */}
      <p className="text-[10px] text-[#3A3A3C]">출처: {item.provider}</p>
    </div>
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
      const sourceTypes =
        filterType === 'all' ? undefined : [filterType];
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

  // 클라이언트 측 필터 (서버 필터와 이중 적용 가능)
  const displayResults = useMemo(
    () =>
      filterType === 'all'
        ? allResults
        : allResults.filter((r) => r.source_type === filterType),
    [allResults, filterType]
  );

  const hasNoResults = !!result && displayResults.length === 0;

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">안전기준 검색</h1>
        <p className="text-sm text-[#FF9F0A] font-medium">산업안전보건기준에 관한 규칙 + 표준안전작업지침 통합 검색</p>
        <p className="text-xs text-[#98989D]">
          산업안전보건기준에 관한 규칙 및 고용노동부 표준안전작업지침을 통합 검색합니다.
        </p>
      </div>

      {/* 검색 폼 */}
      <form
        onSubmit={handleSearch}
        className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-5 space-y-4"
      >
        {/* 검색창 */}
        <div className="flex gap-3 relative">
          <div className="relative flex-1">
            <input
              ref={inputRef}
              type="text"
              className="w-full bg-[#121212] border border-[#2C2C2E] rounded-lg px-4 py-2.5 text-sm text-white placeholder-[#3A3A3C] focus:outline-none focus:ring-2 focus:ring-[#FF9F0A]/50 focus:border-[#FF9F0A]/50 transition-all"
              placeholder="예: 이동식비계 작업발판 기준"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => history.length > 0 && setShowHistory(true)}
              autoComplete="off"
            />

            {/* 히스토리 드롭다운 */}
            {showHistory && filteredHistory.length > 0 && (
              <div
                ref={dropdownRef}
                className="absolute top-full left-0 right-0 mt-1 bg-[#1E1E1E] border border-[#2C2C2E] rounded-xl shadow-xl z-20 overflow-hidden"
              >
                <div className="flex items-center justify-between px-3 py-2 border-b border-[#2C2C2E]">
                  <span className="text-[10px] text-[#98989D] uppercase tracking-widest">최근 검색어</span>
                  <button
                    type="button"
                    onClick={handleClearHistory}
                    className="text-[10px] text-[#98989D] hover:text-[#FF453A] transition-colors"
                  >
                    전체 삭제
                  </button>
                </div>
                {filteredHistory.map((h) => (
                  <button
                    key={h}
                    type="button"
                    onClick={() => handleHistorySelect(h)}
                    className="w-full text-left px-3 py-2 text-sm text-[#98989D] hover:bg-[#252525] hover:text-white flex items-center gap-2 transition-colors"
                  >
                    <span className="text-[#3A3A3C] text-xs">↺</span>
                    {h}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-[#FF9F0A] text-[#121212] px-5 py-2.5 rounded-lg font-semibold text-sm hover:bg-[#FFAD30] disabled:opacity-40 transition-all duration-150 shrink-0"
          >
            검색
          </button>
        </div>

        {/* 옵션 */}
        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 text-sm text-[#98989D]">
            검색 결과 수
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="bg-[#121212] border border-[#2C2C2E] text-white rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-[#FF9F0A]/50"
            >
              {TOP_K_OPTIONS.map((k) => (
                <option key={k} value={k}>{k}</option>
              ))}
            </select>
          </label>
        </div>

        {/* 출처 필터 */}
        <div className="flex flex-wrap gap-2">
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setFilterType(opt.value)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                filterType === opt.value
                  ? 'bg-[#FF9F0A]/10 border-[#FF9F0A]/40 text-[#FF9F0A]'
                  : 'bg-transparent border-[#2C2C2E] text-[#98989D] hover:border-[#3A3A3C] hover:text-white'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </form>

      {loading && <Spinner text="안전기준 검색 중..." />}
      {!!error && <ErrorBox error={error} />}

      {/* 결과 없음 */}
      {!loading && hasNoResults && (
        <EmptyState
          icon="🔍"
          title="관련 안전기준을 찾지 못했습니다."
          description="다른 키워드로 검색하거나, 표준안전작업지침 ingestion이 완료됐는지 확인해 주세요."
        />
      )}

      {/* 결과 목록 */}
      {!loading && displayResults.length > 0 && (
        <div className="space-y-4">
          <div className="text-xs text-[#98989D]">
            총 {displayResults.length}건
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {displayResults.map((item, idx) => (
              <SafetyResultCard
                key={item.chunk_id ?? item.article_id ?? idx}
                item={item}
              />
            ))}
          </div>
        </div>
      )}

      {/* 데이터 없음 안내 (결과 0건 + 검색 미실행 상태) */}
      {!loading && !result && (
        <div className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-6 text-center space-y-2">
          <p className="text-[#98989D] text-sm">
            안전기준 데이터가 없으면 검색 결과가 나오지 않습니다.
          </p>
          <p className="text-[#3A3A3C] text-xs">
            ingestion 먼저 실행: <code className="font-mono bg-[#121212] px-1 rounded">python ingestion/ingest_admrul_safety_guidelines.py --embed</code>
          </p>
        </div>
      )}
    </div>
  );
}
