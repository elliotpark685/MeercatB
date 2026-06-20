import { useState, useRef, useEffect, useMemo } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  searchLaws,
  getLawArticle,
  type LawSearchResult,
  type ArticleDetail,
} from "../api/admin";
import Spinner from "../components/Spinner";
import ErrorBox from "../components/ErrorBox";
import EmptyState from "../components/EmptyState";
import LawScopeFilter from "../components/LawScopeFilter";
import LawResultCard from "../components/LawResultCard";
import { LAW_SCOPE_OPTIONS, getLawBadgeColor } from "../types/law";

const TOP_K_OPTIONS = [3, 5, 10];
const HISTORY_KEY = "meerkat_law_history";
const HISTORY_MAX = 8;

function loadHistory(): string[] {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? "[]");
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

export default function LawSearch() {
  const { userId, siteId } = useAuth();

  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [validateLatest, setValidateLatest] = useState(false);
  // 빈 배열 = 전체(5개 법령) 검색
  const [lawScope, setLawScope] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<LawSearchResult | null>(null);

  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<unknown>(null);
  const [detail, setDetail] = useState<ArticleDetail | null>(null);

  const [history, setHistory] = useState<string[]>(loadHistory);
  const [showHistory, setShowHistory] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 드롭다운 외부 클릭 시 닫기
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
    setDetail(null);

    try {
      const res = await searchLaws({
        query: q,
        top_k: topK,
        validate_latest: validateLatest,
        law_names: lawScope.length > 0 ? lawScope : undefined,
        userId: userId ?? undefined,
        siteId: siteId ?? undefined,
      });
      setResult(res);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleArticleClick(articleId: number) {
    setDetailLoading(true);
    setDetailError(null);
    try {
      const d = await getLawArticle(articleId);
      setDetail(d);
    } catch (e) {
      setDetailError(e);
    } finally {
      setDetailLoading(false);
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
    query ? h.toLowerCase().includes(query.toLowerCase()) : true,
  );

  const searchResults = useMemo(() => result?.results ?? [], [result]);

  const groupedResults = useMemo(() => {
    const groups = new Map<string, typeof searchResults>();
    for (const item of searchResults) {
      const key = item.law_name?.trim() || "법령명 미상";
      const list = groups.get(key);
      if (list) {
        list.push(item);
      } else {
        groups.set(key, [item]);
      }
    }
    return Array.from(groups.entries());
  }, [searchResults]);

  const scopeLabel =
    lawScope.length > 0
      ? lawScope.join(", ")
      : `전체 (${LAW_SCOPE_OPTIONS.length}개 법령)`;

  const hasNoResults =
    !!result &&
    !result.answer &&
    result.citations.length === 0 &&
    searchResults.length === 0;

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">법령 검색</h1>
        <p className="text-sm text-[#00E5FF] font-medium">
          5개 건설 안전 관련 법령 통합 검색
        </p>
        <p className="text-xs text-[#98989D]">
          산업안전보건법, 시설물안전법, 건설산업기본법, 건설기술진흥법,
          중대재해처벌법을 통합 검색합니다.
        </p>
      </div>

      {/* 검색 폼 */}
      <form
        onSubmit={handleSearch}
        className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-5 space-y-4"
      >
        {/* 검색창 + 히스토리 드롭다운 */}
        <div className="flex gap-3 relative">
          <div className="relative flex-1">
            <input
              ref={inputRef}
              type="text"
              className="w-full bg-[#121212] border border-[#2C2C2E] rounded-lg px-4 py-2.5 text-sm text-white placeholder-[#3A3A3C] focus:outline-none focus:ring-2 focus:ring-[#00E5FF]/50 focus:border-[#00E5FF]/50 transition-all"
              placeholder="예: 산업재해"
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
                  <span className="text-[10px] text-[#98989D] uppercase tracking-widest">
                    최근 검색어
                  </span>
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
            className="bg-[#00E5FF] text-[#121212] px-5 py-2.5 rounded-lg font-semibold text-sm hover:bg-[#33EAFF] disabled:opacity-40 transition-all duration-150 shrink-0"
          >
            검색
          </button>
        </div>

        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 text-sm text-[#98989D]">
            검색 결과 수
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="bg-[#121212] border border-[#2C2C2E] text-white rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-[#00E5FF]/50"
            >
              {TOP_K_OPTIONS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-2 text-sm text-[#98989D] cursor-pointer select-none">
            <input
              type="checkbox"
              checked={validateLatest}
              onChange={(e) => setValidateLatest(e.target.checked)}
              className="w-4 h-4 rounded border-[#2C2C2E] bg-[#121212] accent-[#00E5FF]"
            />
            validate_latest
          </label>
        </div>

        <LawScopeFilter selected={lawScope} onChange={setLawScope} />
      </form>

      {loading && <Spinner text="검색 중..." />}
      {!!error && <ErrorBox error={error} />}

      {/* 결과 없음 */}
      {!loading && hasNoResults && (
        <EmptyState
          icon="🔍"
          title="관련 법령을 찾지 못했습니다. 검색어를 다르게 입력해보세요."
          description="다른 키워드로 검색하거나 검색 결과 수를 늘려보세요."
        />
      )}

      {result && (
        <div className="space-y-5">
          {/* 검색 결과 요약 */}
          {!hasNoResults && (
            <div className="text-xs text-[#98989D]">
              총 {searchResults.length}건 / 검색 대상: {scopeLabel}
            </div>
          )}

          {/* 법령별 검색 결과 카드 */}
          {groupedResults.length > 0 && (
            <div className="space-y-5">
              {groupedResults.map(([lawName, items]) => (
                <div key={lawName} className="space-y-3">
                  <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded-md border text-xs ${getLawBadgeColor(lawName)}`}
                    >
                      {lawName}
                    </span>
                    <span className="text-xs text-[#98989D] font-normal">
                      {items.length}건
                    </span>
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {items.map((item, idx) => (
                      <LawResultCard
                        key={
                          item.chunk_id ??
                          item.article_id ??
                          `${lawName}-${idx}`
                        }
                        item={item}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 검색 답변 */}
          {result.answer && (
            <div className="bg-[#1E1E1E] border border-[#00E5FF]/20 rounded-2xl p-5">
              <h2 className="text-sm font-semibold text-[#00E5FF] mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#00E5FF] inline-block" />
                검색 답변
              </h2>
              <p className="text-white whitespace-pre-wrap text-sm leading-relaxed">
                {result.answer}
              </p>
            </div>
          )}

          {/* 인용 조문 */}
          {result.citations.length > 0 && (
            <div className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-5">
              <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#98989D] inline-block" />
                인용 조문
                <span className="text-xs text-[#98989D] font-normal ml-auto">
                  {result.citations.length}건
                </span>
              </h2>
              <div className="space-y-2">
                {result.citations.map((c) => (
                  <button
                    key={c.article_id}
                    onClick={() => handleArticleClick(c.article_id)}
                    className="w-full text-left text-sm px-3 py-2.5 rounded-lg border border-[#2C2C2E] bg-[#121212] text-[#98989D] hover:border-[#00E5FF]/30 hover:text-[#00E5FF] hover:bg-[#00E5FF]/5 transition-all duration-150"
                  >
                    {c.law_name} {c.article_no}{" "}
                    {c.article_title ? `(${c.article_title})` : ""}
                  </button>
                ))}
              </div>
            </div>
          )}

          {detailLoading && <Spinner text="조문 상세 조회 중..." />}
          {!!detailError && <ErrorBox error={detailError} />}

          {/* 조문 상세 */}
          {detail && (
            <div className="bg-[#1E1E1E] rounded-2xl border border-[#00E5FF]/20 p-5">
              <h3 className="font-semibold text-white mb-3">
                {detail.law_name}{" "}
                <span className="text-[#00E5FF]">{detail.article_no}</span>
              </h3>
              <pre className="text-sm text-[#98989D] whitespace-pre-wrap bg-[#121212] rounded-xl p-4 max-h-96 overflow-auto leading-relaxed font-mono border border-[#2C2C2E]">
                {detail.full_text}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
