import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {
  searchLaws,
  getLawArticle,
  type LawSearchResult,
  type ArticleDetail,
} from "../api/admin";
import Spinner from "../components/Spinner";
import ErrorBox from "../components/ErrorBox";

const TOP_K_OPTIONS = [3, 5, 10];

export default function LawSearch() {
  const { userId, siteId } = useAuth();

  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [validateLatest, setValidateLatest] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<LawSearchResult | null>(null);

  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<unknown>(null);
  const [detail, setDetail] = useState<ArticleDetail | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setDetail(null);

    try {
      const res = await searchLaws({
        query: query.trim(),
        top_k: topK,
        validate_latest: validateLatest,
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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">법령 검색</h1>

      <form
        onSubmit={handleSearch}
        className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 space-y-4"
      >
        <div className="flex gap-3">
          <input
            type="text"
            className="flex-1 border border-slate-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="예: 추락 방지"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            검색
          </button>
        </div>

        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            검색 결과 수
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="border border-slate-300 rounded px-2 py-1 text-sm"
            >
              {TOP_K_OPTIONS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </label>

          <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              checked={validateLatest}
              onChange={(e) => setValidateLatest(e.target.checked)}
              className="rounded"
            />
            validate_latest
          </label>
        </div>
      </form>

      {loading && <Spinner text="검색 중..." />}
      {!!error && <ErrorBox error={error} />}

      {result && (
        <div className="space-y-5">
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
            <h2 className="font-semibold text-blue-800 mb-2">검색 답변</h2>
            <p className="text-slate-700 whitespace-pre-wrap text-sm leading-relaxed">
              {result.answer}
            </p>
          </div>

          {result.citations.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
              <h2 className="font-semibold text-slate-700 mb-3">인용 조문</h2>
              <div className="space-y-2">
                {result.citations.map((c) => (
                  <button
                    key={c.article_id}
                    onClick={() => handleArticleClick(c.article_id)}
                    className="w-full text-left text-sm px-3 py-2 rounded border bg-white hover:bg-blue-50"
                  >
                    {c.law_name} {c.article_no}{" "}
                    {c.article_title ? `(${c.article_title})` : ""}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* {result.raw_hits.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
              <h2 className="font-semibold text-slate-700 mb-3">raw_hits</h2>
              <ul className="space-y-2 text-sm">
                {result.raw_hits.map((hit) => (
                  <li key={hit.article_id} className="border-b border-slate-100 pb-2">
                    article_id={hit.article_id}, score={hit.score.toFixed(3)}, matched={hit.matched_reason.join(', ')}
                  </li>
                ))}
              </ul>
            </div>
          )} */}

          {detailLoading && <Spinner text="조문 상세 조회 중..." />}
          {!!detailError && <ErrorBox error={detailError} />}
          {detail && (
            <div className="bg-white rounded-xl border border-blue-200 shadow-sm p-5">
              <h3 className="font-semibold text-slate-800 mb-2">
                {detail.law_name} {detail.article_no}
              </h3>
              <pre className="text-sm text-slate-700 whitespace-pre-wrap bg-slate-50 rounded-lg p-4 max-h-96 overflow-auto leading-relaxed">
                {detail.full_text}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
