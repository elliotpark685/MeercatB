import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getAdminDashboard, type DashboardData } from '../api/admin';
import Spinner from '../components/Spinner';
import ErrorBox from '../components/ErrorBox';

const DOC_TYPE_LABEL: Record<string, string> = {
  tbm: 'TBM',
  risk_assessment: 'Risk Assessment',
  work_plan: 'Work Plan',
  inspection_checklist: 'Inspection Checklist',
};

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-3xl font-bold text-slate-800 mt-1">{value.toLocaleString()}</p>
    </div>
  );
}

export default function Dashboard() {
  const { userId, siteId } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const load = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getAdminDashboard({ userId, siteId });
      setData(result);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, [userId, siteId]);

  useEffect(() => {
    load();
  }, [load]);

  if (!userId) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-yellow-800">
        화면 상단 User ID를 실제 admin 정수 id로 입력해 주세요.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">관리자 대시보드</h1>
        <button
          onClick={load}
          disabled={loading}
          className="text-sm text-blue-600 hover:text-blue-800 underline disabled:opacity-50"
        >
          새로고침
        </button>
      </div>

      {loading && <Spinner text="대시보드 데이터를 불러오는 중..." />}
      {!!error && <ErrorBox error={error} onRetry={load} />}

      {data && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="생성 문서 수" value={data.total_generated_documents} />
            <StatCard label="법령 검색 수" value={data.total_law_searches} />
            <StatCard label="오늘 퀴즈 수" value={data.today_quiz_count} />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5">
              <h2 className="font-semibold text-slate-700 mb-3">최근 생성 문서</h2>
              {data.latest_generated_documents.length === 0 ? (
                <p className="text-slate-400 text-sm">표시할 문서가 없습니다.</p>
              ) : (
                <ul className="space-y-2">
                  {data.latest_generated_documents.map((doc) => (
                    <li key={doc.id} className="flex items-center justify-between text-sm border-b border-slate-50 pb-2">
                      <div>
                        <span className="font-medium text-slate-700">{doc.title}</span>
                        <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                          {DOC_TYPE_LABEL[doc.document_type] ?? doc.document_type}
                        </span>
                      </div>
                      <span className="text-slate-400 text-xs">{new Date(doc.created_at).toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-5">
              <h2 className="font-semibold text-slate-700 mb-3">최근 법령 검색</h2>
              {data.latest_law_searches.length === 0 ? (
                <p className="text-slate-400 text-sm">표시할 검색 이력이 없습니다.</p>
              ) : (
                <ul className="space-y-2">
                  {data.latest_law_searches.map((s) => (
                    <li key={s.id} className="flex items-center justify-between text-sm border-b border-slate-50 pb-2">
                      <div className="min-w-0">
                        <p className="text-slate-700 truncate max-w-xs">{s.query}</p>
                        <p className="text-xs text-slate-400">top_k={s.top_k}, results={s.result_count}</p>
                      </div>
                      <span className="text-slate-400 text-xs shrink-0 ml-2">{new Date(s.created_at).toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
