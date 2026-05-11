import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getAdminDashboard, type DashboardData } from '../api/admin';
import ErrorBox from '../components/ErrorBox';
import EmptyState from '../components/EmptyState';
import { StatCardSkeleton, ListItemSkeleton } from '../components/Skeleton';
import { useCountUp } from '../hooks/useCountUp';
import { AxiosError } from 'axios';

const DOC_TYPE_LABEL: Record<string, string> = {
  tbm: 'TBM',
  risk_assessment: 'Risk Assessment',
  work_plan: 'Work Plan',
  inspection_checklist: 'Inspection Checklist',
};

function StatCard({ label, value }: { label: string; value: number }) {
  const animated = useCountUp(value);
  return (
    <div className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-5 hover:border-[#3A3A3C] transition-colors">
      <p className="text-xs font-medium text-[#98989D] uppercase tracking-widest">{label}</p>
      <p
        className="text-3xl font-bold mt-2 text-[#00E5FF]"
        style={{ fontFamily: "'JetBrains Mono', monospace" }}
      >
        {animated.toLocaleString()}
      </p>
    </div>
  );
}

export default function Dashboard() {
  const { siteId } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getAdminDashboard(siteId ?? undefined);
      setData(result);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [siteId]);

  useEffect(() => { load(); }, [load]);

  const isFirstLoad = loading && !data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-white">관리자 대시보드</h1>
        <button
          onClick={load}
          disabled={loading}
          className="text-xs text-[#00E5FF] hover:text-white border border-[#00E5FF]/30 hover:border-[#00E5FF] rounded-lg px-3 py-1.5 transition-all duration-150 disabled:opacity-40 flex items-center gap-1.5"
        >
          <span className={loading ? 'animate-spin inline-block' : ''}>↻</span>
          새로고침
        </button>
      </div>

      {/* 에러 상태 */}
      {!!error && (() => {
        const status = error instanceof AxiosError ? error.response?.status : undefined;
        if (status === 403) {
          return (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <img src="/403error.png" alt="403 Forbidden" className="max-w-sm w-full opacity-80" />
              <p className="text-[#98989D] text-sm">관리자 권한이 없습니다.</p>
              <button onClick={load} className="text-sm text-[#00E5FF] hover:underline">다시 시도</button>
            </div>
          );
        }
        if (status === 404) {
          return (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <img src="/404error.png" alt="404 Not Found" className="max-w-sm w-full opacity-80" />
              <p className="text-[#98989D] text-sm">데이터를 찾을 수 없습니다.</p>
              <button onClick={load} className="text-sm text-[#00E5FF] hover:underline">다시 시도</button>
            </div>
          );
        }
        return <ErrorBox error={error} onRetry={load} />;
      })()}

      {/* ── KPI 카드 ── */}
      <div className="grid grid-cols-3 gap-4">
        {isFirstLoad ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </>
        ) : data ? (
          <>
            <StatCard label="생성 문서 수" value={data.total_generated_documents} />
            <StatCard label="법령 검색 수" value={data.total_law_searches} />
            <StatCard label="오늘 퀴즈 수" value={data.today_quiz_count} />
          </>
        ) : null}
      </div>

      {/* ── 최근 데이터 ── */}
      {isFirstLoad ? (
        <div className="grid grid-cols-2 gap-6">
          {[0, 1].map((i) => (
            <div key={i} className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-5">
              <div className="h-4 bg-[#2C2C2E] rounded w-32 mb-4 animate-pulse" />
              {Array.from({ length: 4 }).map((_, j) => (
                <ListItemSkeleton key={j} />
              ))}
            </div>
          ))}
        </div>
      ) : data ? (
        <div className="grid grid-cols-2 gap-6">
          {/* 최근 생성 문서 */}
          <div className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-5">
            <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00E5FF] inline-block" />
              최근 생성 문서
            </h2>
            {data.latest_generated_documents.length === 0 ? (
              <EmptyState icon="📄" title="생성된 문서가 없습니다" description="문서 생성 메뉴에서 첫 번째 문서를 만들어보세요." />
            ) : (
              <ul className="space-y-0">
                {data.latest_generated_documents.map((doc) => (
                  <li
                    key={doc.id}
                    className="flex items-center justify-between text-sm border-b border-[#2C2C2E] py-2.5 last:border-0 hover:bg-[#252525] -mx-2 px-2 rounded transition-colors"
                  >
                    <div className="min-w-0">
                      <span className="font-medium text-white truncate block max-w-[160px]">{doc.title}</span>
                      <span className="text-[10px] bg-[#00E5FF]/10 text-[#00E5FF] px-1.5 py-0.5 rounded mt-1 inline-block">
                        {DOC_TYPE_LABEL[doc.document_type] ?? doc.document_type}
                      </span>
                    </div>
                    <span className="text-[#98989D] text-xs shrink-0 ml-2 font-mono">
                      {new Date(doc.created_at).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* 최근 법령 검색 */}
          <div className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-5">
            <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#32D74B] inline-block" />
              최근 법령 검색
            </h2>
            {data.latest_law_searches.length === 0 ? (
              <EmptyState icon="⚖️" title="검색 기록이 없습니다" description="법령 검색 메뉴에서 관련 법령을 조회할 수 있습니다." />
            ) : (
              <ul className="space-y-0">
                {data.latest_law_searches.map((s) => (
                  <li
                    key={s.id}
                    className="flex items-center justify-between text-sm border-b border-[#2C2C2E] py-2.5 last:border-0 hover:bg-[#252525] -mx-2 px-2 rounded transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="text-white truncate max-w-xs">{s.query}</p>
                      <p className="text-[10px] text-[#98989D] mt-0.5 font-mono">
                        top_k={s.top_k} · results={s.result_count}
                      </p>
                    </div>
                    <span className="text-[#98989D] text-xs shrink-0 ml-2 font-mono">
                      {new Date(s.created_at).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}

      {/* 재로딩 인디케이터 (데이터 이미 있을 때) */}
      {loading && data && (
        <div className="flex items-center justify-center gap-2 py-2">
          <div className="w-3 h-3 border border-[#2C2C2E] border-t-[#00E5FF] rounded-full animate-spin" />
          <span className="text-xs text-[#98989D]">업데이트 중...</span>
        </div>
      )}
    </div>
  );
}
