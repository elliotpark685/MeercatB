import { useEffect, useMemo, useRef, useState } from "react";
import {
  searchKosha,
  summarizeKosha,
  KOSHA_CATEGORY_LABEL,
  type KoshaCategory,
  type KoshaResultItem,
  type KoshaSearchResult,
  type KoshaSummaryResult,
} from "../api/admin";
import Spinner from "../components/Spinner";
import ErrorBox from "../components/ErrorBox";
import EmptyState from "../components/EmptyState";

const HISTORY_KEY = "meerkat_kosha_history";
const BOOKMARK_KEY = "meerkat_kosha_bookmarks";
const HISTORY_MAX = 8;
const PAGE_SIZE = 10;

const CATEGORY_OPTIONS: { value: KoshaCategory; label: string }[] = [
  { value: "7", label: KOSHA_CATEGORY_LABEL["7"] },
  { value: "4", label: KOSHA_CATEGORY_LABEL["4"] },
  { value: "5", label: KOSHA_CATEGORY_LABEL["5"] },
  { value: "6", label: KOSHA_CATEGORY_LABEL["6"] },
];

const ACCENT = "#BF5AF2";

function loadList(key: string): string[] {
  try {
    return JSON.parse(localStorage.getItem(key) ?? "[]");
  } catch {
    return [];
  }
}

function saveHistory(query: string) {
  const prev = loadList(HISTORY_KEY).filter((q) => q !== query);
  const next = [query, ...prev].slice(0, HISTORY_MAX);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
}

function bookmarkKey(item: KoshaResultItem): string {
  return item.url || `${item.category}::${item.title}`;
}

function loadBookmarks(): Record<string, KoshaResultItem> {
  try {
    return JSON.parse(localStorage.getItem(BOOKMARK_KEY) ?? "{}");
  } catch {
    return {};
  }
}

function saveBookmarks(map: Record<string, KoshaResultItem>) {
  localStorage.setItem(BOOKMARK_KEY, JSON.stringify(map));
}

function ResultCard({
  item,
  bookmarked,
  onToggleBookmark,
}: {
  item: KoshaResultItem;
  bookmarked: boolean;
  onToggleBookmark: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const categoryLabel =
    KOSHA_CATEGORY_LABEL[item.category as KoshaCategory] ?? item.category;
  const preview = expanded ? item.content : item.content.slice(0, 200);

  return (
    <article className="group relative overflow-hidden rounded-2xl border border-[#2C2C2E] bg-[#1A1A1A] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#3A3A3C]">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      <div className="p-4 sm:p-5 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <span
            className="inline-flex shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-medium"
            style={{
              borderColor: `${ACCENT}40`,
              color: ACCENT,
              backgroundColor: `${ACCENT}1A`,
            }}
          >
            {categoryLabel}
          </span>
          <button
            type="button"
            onClick={onToggleBookmark}
            aria-pressed={bookmarked}
            className={`text-lg transition-colors ${bookmarked ? "text-[#FFD60A]" : "text-[#3A3A3C] hover:text-[#FFD60A]"}`}
            title={bookmarked ? "즐겨찾기 해제" : "즐겨찾기 추가"}
          >
            {bookmarked ? "★" : "☆"}
          </button>
        </div>

        <h3 className="text-sm font-semibold text-white">{item.title}</h3>

        <div className="space-y-2">
          <p className="text-sm leading-6 text-[#C7C7CC] whitespace-pre-wrap break-words">
            {preview}
            {item.content.length > 200 && !expanded && "..."}
          </p>
          {item.content.length > 200 && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className="text-sm font-medium"
              style={{ color: ACCENT }}
            >
              {expanded ? "접기" : "더보기"}
            </button>
          )}
        </div>

        {item.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {item.keywords.map((kw) => (
              <span
                key={kw}
                className="rounded-full bg-[#121212] px-2 py-0.5 text-[11px] text-[#98989D]"
              >
                #{kw}
              </span>
            ))}
          </div>
        )}

        {item.url ? (
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm font-medium"
            style={{ color: ACCENT }}
          >
            원문 바로가기 ↗
          </a>
        ) : (
          item.doc_id && (
            <p className="truncate text-[11px] text-[#3A3A3C]" title={item.doc_id}>
              문서ID: {item.doc_id}
            </p>
          )
        )}
      </div>
    </article>
  );
}

function SummaryPanel({
  summary,
  loading,
  error,
}: {
  summary: KoshaSummaryResult | null;
  loading: boolean;
  error: unknown;
}) {
  if (loading) return <Spinner text="AI 요약 생성 중..." />;
  if (error) return <ErrorBox error={error} />;
  if (!summary) return null;

  const rows: { label: string; value: string }[] = [
    { label: "핵심 내용", value: summary.core_content },
    { label: "적용 대상", value: summary.applicable_scope },
    { label: "현장 적용 방법", value: summary.field_application },
    { label: "주의사항", value: summary.precautions },
    { label: "관련 법령", value: summary.related_regulations },
  ];

  return (
    <div className="space-y-4 rounded-[24px] border border-[#2C2C2E] bg-[#1E1E1E] p-5">
      <h2 className="text-sm font-semibold text-white">AI 요약 — {summary.query}</h2>
      <div className="space-y-3">
        {rows.map((row) => (
          <div key={row.label}>
            <div
              className="text-xs font-semibold uppercase tracking-wide"
              style={{ color: ACCENT }}
            >
              {row.label}
            </div>
            <p className="mt-1 text-sm leading-6 text-[#C7C7CC] whitespace-pre-wrap">
              {row.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function KoshaGuide() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<KoshaCategory>("7");
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<KoshaSearchResult | null>(null);

  const [summary, setSummary] = useState<KoshaSummaryResult | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<unknown>(null);

  const [history, setHistory] = useState<string[]>(() => loadList(HISTORY_KEY));
  const [showHistory, setShowHistory] = useState(false);
  const [bookmarks, setBookmarks] = useState<Record<string, KoshaResultItem>>(loadBookmarks);
  const [showBookmarks, setShowBookmarks] = useState(false);

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
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function runSearch(q: string, cat: KoshaCategory, p: number) {
    setLoading(true);
    setError(null);
    setSummary(null);
    setSummaryError(null);
    try {
      const res = await searchKosha({ query: q, category: cat, page: p, size: PAGE_SIZE });
      setResult(res);
    } catch (err) {
      setError(err);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e: React.FormEvent, overrideQuery?: string) {
    e.preventDefault();
    const q = (overrideQuery ?? query).trim();
    if (!q) return;

    setQuery(q);
    setShowHistory(false);
    saveHistory(q);
    setHistory(loadList(HISTORY_KEY));
    setPage(1);
    await runSearch(q, category, 1);
  }

  function handleCategoryChange(next: KoshaCategory) {
    setCategory(next);
    setPage(1);
    if (result) runSearch(result.query, next, 1);
  }

  function handlePageChange(next: number) {
    setPage(next);
    if (result) runSearch(result.query, category, next);
  }

  function handleRelatedKeywordClick(keyword: string) {
    setQuery(keyword);
    handleSearch({ preventDefault: () => {} } as React.FormEvent, keyword);
  }

  function toggleBookmark(item: KoshaResultItem) {
    const key = bookmarkKey(item);
    const next = { ...bookmarks };
    if (next[key]) {
      delete next[key];
    } else {
      next[key] = item;
    }
    setBookmarks(next);
    saveBookmarks(next);
  }

  async function handleSummarize() {
    if (!result || result.results.length === 0) return;
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const top3 = result.results.slice(0, 3);
      const res = await summarizeKosha(result.query, top3);
      setSummary(res);
    } catch (err) {
      setSummaryError(err);
    } finally {
      setSummaryLoading(false);
    }
  }

  const filteredHistory = history.filter((h) =>
    query ? h.toLowerCase().includes(query.toLowerCase()) : true,
  );
  const bookmarkList = useMemo(() => Object.values(bookmarks), [bookmarks]);
  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[28px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-5 sm:p-6">
        <div className="pointer-events-none absolute inset-0 opacity-60">
          <div
            className="absolute -right-24 -top-24 h-64 w-64 rounded-full blur-3xl"
            style={{ backgroundColor: `${ACCENT}1A` }}
          />
        </div>
        <div className="relative space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className="rounded-full border px-3 py-1 text-xs font-medium"
              style={{ borderColor: `${ACCENT}33`, color: ACCENT, backgroundColor: `${ACCENT}1A` }}
            >
              KOSHA GUIDE
            </span>
            <button
              type="button"
              onClick={() => setShowBookmarks((v) => !v)}
              className="rounded-full border border-[#2C2C2E] bg-[#121212] px-3 py-1 text-xs text-[#98989D] hover:text-white"
            >
              ★ 즐겨찾기 ({bookmarkList.length})
            </button>
          </div>
          <h1 className="text-2xl font-semibold text-white sm:text-3xl">
            KOSHA GUIDE 검색
          </h1>
          <p className="max-w-2xl text-xs leading-5 text-[#98989D]">
            한국산업안전보건공단 안전보건법령 스마트검색을 이용해 KOSHA GUIDE, 고시·훈령·예규,
            안전보건 미디어, 산업안전보건기준에 관한 규칙을 검색합니다.
          </p>
        </div>
      </section>

      {showBookmarks && (
        <div className="space-y-3 rounded-[24px] border border-[#2C2C2E] bg-[#1E1E1E] p-5">
          <h2 className="text-sm font-semibold text-white">즐겨찾기</h2>
          {bookmarkList.length === 0 ? (
            <p className="text-sm text-[#98989D]">즐겨찾기한 항목이 없습니다.</p>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {bookmarkList.map((item) => (
                <ResultCard
                  key={bookmarkKey(item)}
                  item={item}
                  bookmarked
                  onToggleBookmark={() => toggleBookmark(item)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      <form
        onSubmit={handleSearch}
        className="space-y-4 rounded-[28px] border border-[#2C2C2E] bg-[#1E1E1E] p-5"
      >
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
          <div className="relative min-w-0">
            <input
              ref={inputRef}
              type="text"
              className="w-full rounded-2xl border border-[#2C2C2E] bg-[#121212] px-4 py-3 text-sm text-white placeholder:text-[#3A3A3C] outline-none transition focus:ring-2"
              style={{ borderColor: undefined }}
              placeholder="예: 추락재해방지"
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
                <div className="border-b border-[#2C2C2E] px-4 py-3 text-[10px] uppercase tracking-[0.2em] text-[#98989D]">
                  최근 검색어
                </div>
                <div className="max-h-64 overflow-auto">
                  {filteredHistory.map((h) => (
                    <button
                      key={h}
                      type="button"
                      onClick={() => {
                        setQuery(h);
                        setShowHistory(false);
                        inputRef.current?.focus();
                      }}
                      className="flex w-full items-center gap-2 px-4 py-3 text-left text-sm text-[#C7C7CC] hover:bg-[#252525] hover:text-white"
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
            className="inline-flex items-center justify-center rounded-2xl px-5 py-3 text-sm font-semibold text-[#121212] transition-all disabled:cursor-not-allowed disabled:opacity-40 sm:min-w-28"
            style={{ backgroundColor: ACCENT }}
          >
            검색
          </button>
        </div>

        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.2em] text-[#98989D]">카테고리</div>
          <div role="tablist" aria-label="카테고리 필터" className="flex gap-2 overflow-x-auto pb-1">
            {CATEGORY_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                role="tab"
                aria-selected={category === option.value}
                onClick={() => handleCategoryChange(option.value)}
                className={`inline-flex items-center rounded-full border px-4 py-2 text-sm font-medium transition-all ${
                  category === option.value
                    ? "border-transparent text-[#121212]"
                    : "border-[#2C2C2E] bg-[#121212] text-[#98989D] hover:border-[#3A3A3C] hover:text-white"
                }`}
                style={category === option.value ? { backgroundColor: ACCENT } : undefined}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </form>

      {loading && <Spinner text="KOSHA GUIDE 검색 중..." />}
      {!!error && <ErrorBox error={error} />}

      {!loading && result && result.related_keywords.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-[#2C2C2E] bg-[#1A1A1A] p-4">
          <span className="text-xs text-[#98989D]">연관검색어</span>
          {result.related_keywords.map((kw) => (
            <button
              key={kw}
              type="button"
              onClick={() => handleRelatedKeywordClick(kw)}
              className="rounded-full bg-[#121212] px-3 py-1 text-xs text-[#C7C7CC] hover:text-white"
            >
              {kw}
            </button>
          ))}
        </div>
      )}

      {!loading && result && result.results.length > 0 && (
        <button
          type="button"
          onClick={handleSummarize}
          disabled={summaryLoading}
          className="rounded-2xl border px-4 py-2 text-sm font-semibold disabled:opacity-40"
          style={{ borderColor: `${ACCENT}40`, color: ACCENT }}
        >
          {summaryLoading ? "요약 생성 중..." : "상위 3건 AI 요약 보기"}
        </button>
      )}

      <SummaryPanel summary={summary} loading={summaryLoading} error={summaryError} />

      {!loading && result && result.results.length === 0 && (
        <EmptyState
          icon="📘"
          title="검색 결과가 없습니다."
          description="다른 키워드로 다시 검색하거나 카테고리를 변경해보세요. (API 키 미설정 시에도 빈 결과가 표시됩니다.)"
        />
      )}

      {!loading && !result && (
        <div className="rounded-[28px] border border-[#2C2C2E] bg-[#1E1E1E] p-6 text-center">
          <p className="text-sm font-medium text-[#C7C7CC]">
            검색어를 입력하면 KOSHA GUIDE 결과가 여기에 표시됩니다.
          </p>
        </div>
      )}

      {!loading && result && result.results.length > 0 && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[#98989D]">
            <span>총 {result.total}건 · {result.page}페이지</span>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {result.results.map((item, idx) => (
              <ResultCard
                key={bookmarkKey(item) + idx}
                item={item}
                bookmarked={!!bookmarks[bookmarkKey(item)]}
                onToggleBookmark={() => toggleBookmark(item)}
              />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => handlePageChange(page - 1)}
                className="rounded-xl border border-[#2C2C2E] bg-[#121212] px-3 py-2 text-sm text-[#98989D] disabled:opacity-30"
              >
                이전
              </button>
              <span className="text-sm text-[#98989D]">
                {page} / {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => handlePageChange(page + 1)}
                className="rounded-xl border border-[#2C2C2E] bg-[#121212] px-3 py-2 text-sm text-[#98989D] disabled:opacity-30"
              >
                다음
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
