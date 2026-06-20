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

const GUIDE_REFERENCE = [
  {
    code: "G",
    field: "일반안전보건",
    info: "위험성평가 방법, 안전보건교육, 보호구 선택 및 관리 기준",
  },
  {
    code: "M",
    field: "기계안전",
    info: "프레스, 크레인, 로봇 등 위험 기계장치의 안전장치 설치 및 정비 가이드",
  },
  {
    code: "E",
    field: "전기안전",
    info: "감전 재해 예방, 접지 시스템 설계, 방폭(폭발방지) 설비 기준",
  },
  {
    code: "C",
    field: "건설안전",
    info: "비계·거푸집 조립, 추락 방지 시설 설치, 건설기계 작업계획서 작성법",
  },
  {
    code: "X",
    field: "화학공장안전",
    info: "유해화학물질 취급법, 공정안전관리(PSM) 작성, 정량적 위험성평가(QRA)",
  },
  {
    code: "H",
    field: "산업보건",
    info: "밀폐공간 질식 예방, 국소배기장치 설계, 유해물질 노출 가이드",
  },
  {
    code: "W",
    field: "작업환경관리",
    info: "소음·진동 측정 및 저감 기술, 작업장 조명 및 환기 기준",
  },
  {
    code: "P",
    field: "제조공정안전",
    info: "용접, 도장, 주조 등 특정 제조 공정별 안전작업 절차",
  },
] as const;

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
            title={bookmarked ? "利먭꺼李얘린 ?댁젣" : "利먭꺼李얘린 異붽?"}
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
              臾몄꽌ID: {item.doc_id}
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
  if (loading) return <Spinner text="AI ?붿빟 ?앹꽦 以?.." />;
  if (error) return <ErrorBox error={error} />;
  if (!summary) return null;

  const rows: { label: string; value: string }[] = [
    { label: "?듭떖 ?댁슜", value: summary.core_content },
    { label: "적용 대상", value: summary.applicable_scope },
    { label: "?꾩옣 ?곸슜 諛⑸쾿", value: summary.field_application },
    { label: "二쇱쓽?ы빆", value: summary.precautions },
    { label: "愿??踰뺣졊", value: summary.related_regulations },
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
  const relatedKeywords = result?.related_keywords ?? [];
  const hasResults = !!result && result.results.length > 0;
  const currentCategoryLabel =
    CATEGORY_OPTIONS.find((option) => option.value === category)?.label ?? category;

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
              ??利먭꺼李얘린 ({bookmarkList.length})
            </button>
          </div>
          <h1 className="text-2xl font-semibold text-white sm:text-3xl">
            KOSHA GUIDE 寃??          </h1>
          <p className="max-w-2xl text-xs leading-5 text-[#98989D]">
            ?쒓뎅?곗뾽?덉쟾蹂닿굔怨듬떒 ?덉쟾蹂닿굔踰뺣졊 ?ㅻ쭏?멸??됱쓣 ?댁슜??KOSHA GUIDE, 怨좎떆쨌?덈졊쨌?덇퇋,
            ?덉쟾蹂닿굔 誘몃뵒?? ?곗뾽?덉쟾蹂닿굔湲곗???愿??洹쒖튃??寃?됲빀?덈떎.
          </p>
        </div>
      </section>

      <section className="space-y-3 rounded-[24px] border border-[#2C2C2E] bg-[#1E1E1E] p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-semibold text-white">KOSHA GUIDE 분류 참고</h2>
            <p className="mt-1 text-xs leading-5 text-[#98989D]">
              알파벳 분류를 기준으로 업종·공정에 맞는 가이드를 빠르게 좁힐 수 있습니다.
            </p>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {GUIDE_REFERENCE.map((item) => (
            <div
              key={item.code}
              className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4"
            >
              <div className="flex items-center gap-2">
                <span
                  className="inline-flex h-7 min-w-7 items-center justify-center rounded-full border border-[#3A3A3C] text-sm font-semibold text-white"
                  style={{ backgroundColor: `${ACCENT}1A` }}
                >
                  {item.code}
                </span>
                <div>
                  <div className="text-sm font-medium text-white">{item.field}</div>
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-[#C7C7CC]">{item.info}</p>
            </div>
          ))}
        </div>
      </section>

      {showBookmarks && (
        <div className="space-y-3 rounded-[24px] border border-[#2C2C2E] bg-[#1E1E1E] p-5">
          <h2 className="text-sm font-semibold text-white">利먭꺼李얘린</h2>
          {bookmarkList.length === 0 ? (
            <p className="text-sm text-[#98989D]">利먭꺼李얘린????ぉ???놁뒿?덈떎.</p>
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
              placeholder="?? 異붾씫?ы빐諛⑹?"
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
                  理쒓렐 寃?됱뼱
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
            寃??          </button>
        </div>

        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.2em] text-[#98989D]">移댄뀒怨좊━</div>
          <div role="tablist" aria-label="移댄뀒怨좊━ ?꾪꽣" className="flex gap-2 overflow-x-auto pb-1">
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

      {loading && <Spinner text="KOSHA GUIDE 寃??以?.." />}
      {!!error && <ErrorBox error={error} />}

            {!loading && result && relatedKeywords.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-[#2C2C2E] bg-[#1A1A1A] p-4">
          <span className="text-xs text-[#98989D]">?곌?寃?됱뼱</span>
          {relatedKeywords.map((kw) => (
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

      {!loading && result && hasResults && (
        <button
          type="button"
          onClick={handleSummarize}
          disabled={summaryLoading}
          className="rounded-2xl border px-4 py-2 text-sm font-semibold disabled:opacity-40"
          style={{ borderColor: `${ACCENT}40`, color: ACCENT }}
        >
          {summaryLoading ? "?붿빟 ?앹꽦 以?.." : "?곸쐞 3嫄?AI ?붿빟 蹂닿린"}
        </button>
      )}

      <SummaryPanel summary={summary} loading={summaryLoading} error={summaryError} />

      {!loading && result && !hasResults && (
        <div className="space-y-4 rounded-[28px] border border-[#2C2C2E] bg-[#1E1E1E] p-6">
          <EmptyState
            icon="?뱲"
            title="寃??寃곌낵媛 ?놁뒿?덈떎."
            description={`"${query}"에 대한 직접 결과가 없었습니다. 검색어를 더 구체적으로 바꾸거나 연관 키워드로 다시 검색해 보세요.`}
          />
          <div className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm text-[#C7C7CC]">
            <p className="font-medium text-white">다음 방법을 권장합니다</p>
            <ul className="mt-2 space-y-1.5 text-[#98989D]">
              <li>• 더 짧은 명사로 검색하기</li>
              <li>• 문서 제목에 가까운 용어로 바꿔보기</li>
              <li>• 현재 카테고리: {currentCategoryLabel}</li>
            </ul>
          </div>
          {relatedKeywords.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-[#2C2C2E] bg-[#1A1A1A] p-4">
              <span className="text-xs text-[#98989D]">연관 키워드로 재검색</span>
              {relatedKeywords.map((kw) => (
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
        </div>
      )}

      {!loading && !result && (
        <div className="rounded-[28px] border border-[#2C2C2E] bg-[#1E1E1E] p-6 text-center">
          <p className="text-sm font-medium text-[#C7C7CC]">
            寃?됱뼱瑜??낅젰?섎㈃ KOSHA GUIDE 寃곌낵媛 ?ш린???쒖떆?⑸땲??
          </p>
        </div>
      )}

      {!loading && result && hasResults && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[#98989D]">
            <span>珥?{result.total}嫄?쨌 {result.page}?섏씠吏</span>
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
                ?댁쟾
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
                ?ㅼ쓬
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

