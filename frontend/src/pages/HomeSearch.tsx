import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  searchLaws,
  searchSafetyStandards,
  searchKosha,
  KOSHA_CATEGORY_LABEL,
  type LawSearchResult,
  type SafetyStandardSearchResult,
  type KoshaResultItem,
  type KoshaSearchResult,
} from "../api/admin";
import LawResultCard from "../components/LawResultCard";
import ArticleDetailModal from "../components/ArticleDetailModal";
import Spinner from "../components/Spinner";
import ErrorBox from "../components/ErrorBox";
import EmptyState from "../components/EmptyState";

const HISTORY_KEY = "meerkat_home_search_history";
const HISTORY_MAX = 8;
const TOP_K = 5;

type SearchSnapshot = {
  laws: LawSearchResult | null;
  safety: SafetyStandardSearchResult | null;
  kosha: KoshaSearchResult | null;
  errors: {
    laws?: string;
    safety?: string;
    kosha?: string;
  };
};

function loadHistory(): string[] {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function saveHistory(query: string) {
  const prev = loadHistory().filter((item) => item !== query);
  const next = [query, ...prev].slice(0, HISTORY_MAX);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
}

function formatKoshaCategory(value: string): string {
  return (
    KOSHA_CATEGORY_LABEL[value as keyof typeof KOSHA_CATEGORY_LABEL] ?? value
  );
}

function dedupeByKey<T>(items: T[], getKey: (item: T) => string): T[] {
  const seen = new Set<string>();
  const unique: T[] = [];

  for (const item of items) {
    const key = getKey(item).trim();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    unique.push(item);
  }

  return unique;
}

function ResultHeader({
  title,
  count,
  subtitle,
  accent,
  action,
}: {
  title: string;
  count: number;
  subtitle: string;
  accent: string;
  action: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className={`inline-flex h-2.5 w-2.5 rounded-full ${accent}`} />
          <h2 className="text-sm font-semibold text-white">{title}</h2>
          <span className="rounded-full border border-[#2C2C2E] bg-[#121212] px-2 py-0.5 text-[10px] text-[#98989D]">
            {count}건
          </span>
        </div>
        <p className="text-xs text-[#98989D]">{subtitle}</p>
      </div>
      {action}
    </div>
  );
}

function SafetyResultCard({
  item,
  onViewDetail,
}: {
  item: NonNullable<SafetyStandardSearchResult["results"]>[number];
  onViewDetail: (articleId: number) => void;
}) {
  const text = item.content_preview?.trim() ?? "";
  const preview = text.length > 260 ? `${text.slice(0, 260)}...` : text;

  return (
    <article className="rounded-2xl border border-[#2C2C2E] bg-[#1E1E1E] p-4 transition-colors hover:border-[#FF9F0A]/30">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-[#FF9F0A]/25 bg-[#FF9F0A]/10 px-2.5 py-1 text-[11px] font-medium text-[#FF9F0A]">
          {item.source_type === "rule" ? "규칙" : "지침"}
        </span>
        <span className="text-xs text-[#98989D]">{item.provider}</span>
        <span className="ml-auto text-[11px] font-mono text-[#FF9F0A]">
          {Math.round((item.score ?? 0) * 100)}%
        </span>
      </div>
      <div className="mt-3 space-y-1">
        <p className="text-sm font-medium text-white">{item.source_name}</p>
        <div className="flex flex-wrap items-center gap-2">
          {item.article_no && (
            <span className="rounded-md border border-[#FF9F0A]/25 bg-[#FF9F0A]/10 px-2 py-0.5 text-xs text-[#FF9F0A]">
              {item.article_no}
            </span>
          )}
          {item.article_title && (
            <span className="text-sm text-[#C7C7CC]">{item.article_title}</span>
          )}
        </div>
      </div>
      {preview && (
        <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-[#98989D]">
          {preview}
        </p>
      )}
      <div className="mt-4 flex items-center justify-end gap-2">
        {item.article_id != null && (
          <button
            type="button"
            onClick={() => onViewDetail(item.article_id!)}
            className="rounded-lg border border-[#FF9F0A]/25 px-3 py-1.5 text-xs font-medium text-[#FF9F0A] transition-colors hover:bg-[#FF9F0A]/10"
          >
            전체 내용 보기
          </button>
        )}
        <Link
          to="/safety-standards"
          className="rounded-lg border border-[#2C2C2E] px-3 py-1.5 text-xs text-[#FF9F0A] transition-colors hover:border-[#FF9F0A]/30 hover:bg-[#FF9F0A]/10"
        >
          안전기준 페이지 열기
        </Link>
      </div>
    </article>
  );
}

function KoshaResultCard({ item }: { item: KoshaResultItem }) {
  const [expanded, setExpanded] = useState(false);
  const keywords = item.keywords.slice(0, 4);
  const text = item.content.trim();
  const preview = expanded || text.length <= 260 ? text : `${text.slice(0, 260)}...`;
  const categoryLabel = formatKoshaCategory(item.category);

  return (
    <article className="rounded-2xl border border-[#2C2C2E] bg-[#1E1E1E] p-4 transition-colors hover:border-[#BF5AF2]/30">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-[#BF5AF2]/25 bg-[#BF5AF2]/10 px-2.5 py-1 text-[11px] font-medium text-[#BF5AF2]">
          {categoryLabel}
        </span>
        <span className="text-xs text-[#98989D]">{item.doc_id}</span>
        <span className="ml-auto text-[11px] font-mono text-[#BF5AF2]">
          {item.score.toFixed(2)}
        </span>
      </div>
      <div className="mt-3 space-y-1">
        <p className="text-sm font-medium text-white">{item.title}</p>
        {keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {keywords.map((keyword) => (
              <span
                key={keyword}
                className="rounded-md bg-[#BF5AF2]/10 px-2 py-0.5 text-[11px] text-[#BF5AF2]"
              >
                {keyword}
              </span>
            ))}
          </div>
        )}
      </div>
      {preview && (
        <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-[#98989D]">
          {preview}
        </p>
      )}
      <div className="mt-4 flex items-center justify-end gap-2">
        {text.length > 260 && (
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            className="rounded-lg border border-[#BF5AF2]/25 px-3 py-1.5 text-xs font-medium text-[#BF5AF2] transition-colors hover:bg-[#BF5AF2]/10"
          >
            {expanded ? "접기" : "전체 내용 보기"}
          </button>
        )}
        {item.url && (
          <a
            href={item.url}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-[#BF5AF2]/25 px-3 py-1.5 text-xs text-[#BF5AF2] transition-colors hover:bg-[#BF5AF2]/10"
          >
            원문 열기
          </a>
        )}
        <Link
          to="/kosha-guide"
          className="rounded-lg border border-[#2C2C2E] px-3 py-1.5 text-xs text-[#BF5AF2] transition-colors hover:border-[#BF5AF2]/30 hover:bg-[#BF5AF2]/10"
        >
          KOSHA 페이지 열기
        </Link>
      </div>
    </article>
  );
}

export default function HomeSearch() {
  const { userId, siteId } = useAuth();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchSnapshot>({
    laws: null,
    safety: null,
    kosha: null,
    errors: {},
  });
  const [history, setHistory] = useState<string[]>(loadHistory);
  const [detailArticleId, setDetailArticleId] = useState<number | null>(null);
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

    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function handleSearch(e: FormEvent, overrideQuery?: string) {
    e.preventDefault();
    const q = (overrideQuery ?? query).trim();
    if (!q) return;

    setQuery(q);
    setShowHistory(false);
    saveHistory(q);
    setHistory(loadHistory());
    setLoading(true);
    setResult({ laws: null, safety: null, kosha: null, errors: {} });

    const [laws, safety, kosha] = await Promise.allSettled([
      searchLaws({
        query: q,
        top_k: TOP_K,
        userId: userId ?? undefined,
        siteId: siteId ?? undefined,
      }),
      searchSafetyStandards({
        query: q,
        top_k: TOP_K,
        userId: userId ?? undefined,
        siteId: siteId ?? undefined,
      }),
      searchKosha({
        query: q,
        category: "0",
        page: 1,
        size: TOP_K,
      }),
    ]);

    setResult({
      laws: laws.status === "fulfilled" ? laws.value : null,
      safety: safety.status === "fulfilled" ? safety.value : null,
      kosha: kosha.status === "fulfilled" ? kosha.value : null,
      errors: {
        laws: laws.status === "rejected" ? "법령 검색 실패" : undefined,
        safety: safety.status === "rejected" ? "안전기준 검색 실패" : undefined,
        kosha: kosha.status === "rejected" ? "KOSHA 검색 실패" : undefined,
      },
    });
    setLoading(false);
  }

  function handleHistorySelect(value: string) {
    setQuery(value);
    setShowHistory(false);
    inputRef.current?.focus();
  }

  const filteredHistory = history.filter((item) =>
    query ? item.toLowerCase().includes(query.toLowerCase()) : true,
  );

  const lawResults = useMemo(
    () =>
      dedupeByKey(result.laws?.results ?? [], (item) =>
        item.article_id != null
          ? `article:${item.article_id}`
          : `law:${item.law_name?.trim() ?? ""}:${item.article_no?.trim() ?? ""}:${item.title?.trim() ?? ""}`,
      ),
    [result.laws],
  );

  const safetyResults = useMemo(
    () =>
      dedupeByKey(result.safety?.results ?? [], (item) =>
        item.chunk_id != null
          ? `chunk:${item.chunk_id}`
          : item.article_id != null
            ? `article:${item.article_id}`
            : `safety:${item.source_type}:${item.source_name?.trim() ?? ""}:${item.article_no?.trim() ?? ""}:${item.article_title?.trim() ?? ""}:${item.content_preview.trim()}`,
      ),
    [result.safety],
  );

  const koshaResults = useMemo(
    () =>
      dedupeByKey(result.kosha?.results ?? [], (item) =>
        `doc:${item.doc_id.trim()}:${item.title.trim()}:${item.category}`,
      ),
    [result.kosha],
  );

  const summary = useMemo(() => {
    return lawResults.length + safetyResults.length + koshaResults.length;
  }, [lawResults.length, safetyResults.length, koshaResults.length]);

  const hasAnyResult =
    lawResults.length > 0 ||
    safetyResults.length > 0 ||
    koshaResults.length > 0;
  const hasError = Object.values(result.errors).some(Boolean);

  return (
    <div className="space-y-6">
      <section className="relative overflow-visible rounded-[28px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-8">
        <div className="pointer-events-none absolute inset-0 opacity-70">
          <div className="absolute -right-20 -top-20 h-56 w-56 rounded-full bg-[#00E5FF]/10 blur-3xl" />
          <div className="absolute left-8 top-8 h-40 w-40 rounded-full bg-[#BF5AF2]/10 blur-3xl" />
        </div>
        <div className="relative space-y-5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[#00E5FF]/25 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]">
              통합검색
            </span>
            <span className="rounded-full border border-[#2C2C2E] bg-[#121212] px-3 py-1 text-xs text-[#98989D]">
              법령 · 안전기준 · KOSHA 결과만 한 화면에서 확인
            </span>
            {summary > 0 && (
              <span className="rounded-full border border-[#2C2C2E] bg-[#121212] px-3 py-1 text-xs text-[#98989D]">
                총 {summary}건
              </span>
            )}
          </div>

          <div className="max-w-3xl space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              첫 화면에서 바로 찾는 통합 안전 검색
            </h1>
            <p className="text-sm leading-6 text-[#C7C7CC]">
              상세 기능은 각 페이지에 두고, 여기서는 검색 결과만 빠르게
              노출합니다. 관리자 대시보드는 관리자 계정에서만 볼 수 있습니다.
            </p>
          </div>

          <form
            onSubmit={handleSearch}
            className="rounded-[24px] border border-[#2C2C2E] bg-[#1A1A1A]/90 p-4 shadow-[0_8px_40px_rgba(0,0,0,0.18)]"
          >
            <div className="relative flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onFocus={() => history.length > 0 && setShowHistory(true)}
                  autoComplete="off"
                  placeholder="예: 추락방지, 안전모, 작업계획서"
                  className="w-full rounded-xl border border-[#2C2C2E] bg-[#121212] px-4 py-3 text-sm text-white placeholder-[#3A3A3C] outline-none transition-all focus:border-[#00E5FF]/45 focus:ring-2 focus:ring-[#00E5FF]/15"
                />

                {showHistory && filteredHistory.length > 0 && (
                  <div
                    ref={dropdownRef}
                    className="absolute left-0 right-0 top-full z-30 mt-2 rounded-xl border border-[#2C2C2E] bg-[#1E1E1E] shadow-xl"
                  >
                    <div className="flex items-center justify-between border-b border-[#2C2C2E] px-3 py-2">
                      <span className="text-[10px] uppercase tracking-[0.2em] text-[#98989D]">
                        최근 검색어
                      </span>
                    </div>
                    {filteredHistory.map((item) => (
                      <button
                        key={item}
                        type="button"
                        onClick={() => handleHistorySelect(item)}
                        className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm text-[#C7C7CC] transition-colors hover:bg-[#252525] hover:text-white"
                      >
                        <span className="text-xs text-[#3A3A3C]">↺</span>
                        <span className="truncate">{item}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="inline-flex shrink-0 items-center justify-center rounded-xl bg-[#00E5FF] px-5 py-3 text-sm font-semibold text-[#121212] transition-all hover:bg-[#33EAFF] disabled:opacity-40"
              >
                검색
              </button>
            </div>
          </form>
        </div>
      </section>

      {loading && <Spinner text="통합 검색 중..." />}
      {hasError && !hasAnyResult && (
        <ErrorBox
          error={
            new Error(
              "일부 검색 소스에서 결과를 가져오지 못했습니다. 다른 소스는 계속 표시될 수 있습니다.",
            )
          }
        />
      )}

      {!loading && !hasAnyResult && query.trim() && (
        <EmptyState
          icon="🔎"
          title="검색 결과가 없습니다."
          description="검색어를 바꾸거나 다른 표현으로 다시 시도해보세요."
        />
      )}

      {!loading && !query.trim() && (
        <div className="grid gap-4 md:grid-cols-3">
          {[
            ["법령", "산업안전보건법을 포함한 5개 법령 결과", "bg-[#00E5FF]"],
            ["안전기준", "규칙과 표준안전작업지침 결과", "bg-[#FF9F0A]"],
            ["KOSHA", "안전보건 가이드와 미디어 자료", "bg-[#BF5AF2]"],
          ].map(([title, desc, accent]) => (
            <div
              key={title}
              className="rounded-[24px] border border-[#2C2C2E] bg-[#1E1E1E] p-5"
            >
              <div className="mb-3 flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${accent}`} />
                <h2 className="text-sm font-semibold text-white">{title}</h2>
              </div>
              <p className="text-sm leading-6 text-[#98989D]">{desc}</p>
            </div>
          ))}
        </div>
      )}

      {!loading && hasAnyResult && (
        <div className="space-y-6">
          {result.errors.laws && (
            <div className="text-xs text-[#FF453A]">{result.errors.laws}</div>
          )}
          {lawResults.length > 0 && (
            <section className="space-y-3">
              <ResultHeader
                title="법령"
                count={lawResults.length}
                subtitle="기존 5개 법령 통합 검색 결과"
                accent="bg-[#00E5FF]"
                action={
                  <Link
                    to="/laws"
                    className="rounded-lg border border-[#2C2C2E] px-3 py-1.5 text-xs text-[#00E5FF] transition-colors hover:border-[#00E5FF]/30 hover:bg-[#00E5FF]/10"
                  >
                    법령 페이지
                  </Link>
                }
              />
              <div className="grid gap-3 md:grid-cols-2">
                {lawResults.map((item, index) => (
                  <LawResultCard
                    key={item.article_id ?? index}
                    item={item}
                    onViewDetail={setDetailArticleId}
                  />
                ))}
              </div>
            </section>
          )}

          {result.errors.safety && (
            <div className="text-xs text-[#FF453A]">{result.errors.safety}</div>
          )}
          {safetyResults.length > 0 && (
            <section className="space-y-3">
              <ResultHeader
                title="안전기준"
                count={safetyResults.length}
                subtitle="산업안전보건기준에 관한 규칙과 지침 검색 결과"
                accent="bg-[#FF9F0A]"
                action={
                  <Link
                    to="/safety-standards"
                    className="rounded-lg border border-[#2C2C2E] px-3 py-1.5 text-xs text-[#FF9F0A] transition-colors hover:border-[#FF9F0A]/30 hover:bg-[#FF9F0A]/10"
                  >
                    안전기준 페이지
                  </Link>
                }
              />
              <div className="grid gap-3 md:grid-cols-2">
                {safetyResults.map((item, index) => (
                  <SafetyResultCard
                    key={item.article_id ?? index}
                    item={item}
                    onViewDetail={setDetailArticleId}
                  />
                ))}
              </div>
            </section>
          )}

          {result.errors.kosha && (
            <div className="text-xs text-[#FF453A]">{result.errors.kosha}</div>
          )}
          {koshaResults.length > 0 && (
            <section className="space-y-3">
              <ResultHeader
                title="KOSHA"
                count={koshaResults.length}
                subtitle="KOSHA GUIDE 및 관련 자료 검색 결과"
                accent="bg-[#BF5AF2]"
                action={
                  <Link
                    to="/kosha-guide"
                    className="rounded-lg border border-[#2C2C2E] px-3 py-1.5 text-xs text-[#BF5AF2] transition-colors hover:border-[#BF5AF2]/30 hover:bg-[#BF5AF2]/10"
                  >
                    KOSHA 페이지
                  </Link>
                }
              />
              <div className="grid gap-3 md:grid-cols-2">
                {koshaResults.map((item) => (
                  <KoshaResultCard
                    key={`${item.doc_id}-${item.title}`}
                    item={item}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#2C2C2E] bg-[#1E1E1E] px-4 py-3 text-xs text-[#98989D]">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-[#00E5FF]/25 bg-[#00E5FF]/10 px-2.5 py-1 text-[#00E5FF]">
            법령
          </span>
          <span className="rounded-full border border-[#FF9F0A]/25 bg-[#FF9F0A]/10 px-2.5 py-1 text-[#FF9F0A]">
            안전기준
          </span>
          <span className="rounded-full border border-[#BF5AF2]/25 bg-[#BF5AF2]/10 px-2.5 py-1 text-[#BF5AF2]">
            KOSHA
          </span>
        </div>
        <span className="text-[#3A3A3C]">
          상세 조회는 각 페이지에서 계속 진행합니다.
        </span>
      </div>

      {detailArticleId != null && (
        <ArticleDetailModal
          articleId={detailArticleId}
          onClose={() => setDetailArticleId(null)}
        />
      )}
    </div>
  );
}
