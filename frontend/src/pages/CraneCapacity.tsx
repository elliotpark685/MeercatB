import { useMemo, useState } from 'react';
import { parseTrt35Pdf, TRT35_CONFIGURATIONS, type Trt35CellStatus, type Trt35ParseResponse } from '../api/cranes';
import ErrorBox from '../components/ErrorBox';
import Spinner from '../components/Spinner';
import { useToast } from '../contexts/ToastContext';

const STATUS_LABEL: Record<Trt35CellStatus, string> = {
  AVAILABLE: '사용 가능',
  NOT_AVAILABLE: '사용 불가',
  UNRESOLVED: '판독 보류',
};

const STATUS_CLASS: Record<Trt35CellStatus, string> = {
  AVAILABLE: 'bg-[#DCFCE7] text-[#166534]',
  NOT_AVAILABLE: 'bg-[#F1F5F9] text-[#475569]',
  UNRESOLVED: 'bg-[#FEF3C7] text-[#92400E]',
};

export default function CraneCapacity() {
  const { addToast } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [configuration, setConfiguration] = useState('');
  const [result, setResult] = useState<Trt35ParseResponse | null>(null);
  const [statusFilter, setStatusFilter] = useState<'ALL' | Trt35CellStatus>('ALL');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const cells = useMemo(() => result?.parser_result.cells ?? [], [result]);
  const counts = useMemo(() => ({
    AVAILABLE: cells.filter((cell) => cell.cell_status === 'AVAILABLE').length,
    NOT_AVAILABLE: cells.filter((cell) => cell.cell_status === 'NOT_AVAILABLE').length,
    UNRESOLVED: cells.filter((cell) => cell.cell_status === 'UNRESOLVED').length,
  }), [cells]);
  const visibleCells = statusFilter === 'ALL' ? cells : cells.filter((cell) => cell.cell_status === statusFilter);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !configuration) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await parseTrt35Pdf(file, configuration as (typeof TRT35_CONFIGURATIONS)[number]['value']);
      setResult(response);
      setStatusFilter('ALL');
      addToast('용량표 판독 결과를 생성했습니다. 결과는 저장 또는 승인되지 않습니다.', 'success');
    } catch (requestError) {
      setError(requestError);
      addToast('용량표를 판독할 수 없습니다. 원본 PDF와 구성을 확인해 주세요.', 'error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="rounded-2xl border border-[#BFDBFE] bg-gradient-to-br from-[#EFF6FF] to-white p-6 shadow-[0_8px_24px_rgba(15,23,42,0.06)]">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#2563EB]">TRT35 capacity parser</p>
        <h1 className="mt-2 text-2xl font-bold text-[#0F172A]">크레인 용량표 판독</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-[#475569]">
          Golden 검증을 마친 TRT35 원본 PDF와 구성만 판독합니다. 결과는 작업 승인이나 정격 판단이 아니며, 판독 보류 셀은 원본 운전 매뉴얼과 장비 컴퓨터로 확인해야 합니다.
        </p>
      </section>

      <section className="rounded-xl border border-[#E2E8F0] bg-white p-5 shadow-[0_1px_3px_rgba(15,23,42,0.06)]">
        <form className="grid gap-5 lg:grid-cols-[1fr_1fr_auto] lg:items-end" onSubmit={handleSubmit}>
          <label className="block text-sm font-semibold text-[#334155]">원본 TRT35 PDF
            <input className="mt-2 block w-full rounded-lg border border-[#CBD5E1] bg-white px-3 py-2 text-sm text-[#334155] file:mr-3 file:rounded-md file:border-0 file:bg-[#EFF6FF] file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-[#1D4ED8]" type="file" accept="application/pdf,.pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
          </label>
          <label className="block text-sm font-semibold text-[#334155]">용량 구성
            <select className="mt-2 block w-full rounded-lg border border-[#CBD5E1] bg-white px-3 py-2 text-sm text-[#334155]" value={configuration} onChange={(event) => setConfiguration(event.target.value)}>
              <option value="">구성을 선택하세요</option>
              {TRT35_CONFIGURATIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
          <button className="rounded-lg bg-[#2563EB] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#1D4ED8] disabled:cursor-not-allowed disabled:bg-[#94A3B8]" type="submit" disabled={!file || !configuration || loading}>
            {loading ? '판독 중...' : '판독 실행'}
          </button>
        </form>
      </section>

      {loading && <Spinner text="PDF 격자와 각 셀을 안전하게 검증하고 있습니다..." />}
      {error !== null && <ErrorBox error={error} />}

      {result && <section className="space-y-5 rounded-xl border border-[#E2E8F0] bg-white p-5 shadow-[0_1px_3px_rgba(15,23,42,0.06)]">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><h2 className="text-lg font-bold text-[#0F172A]">판독 결과</h2><p className="mt-1 text-sm text-[#64748B]">페이지 {result.parser_result.source_page} · {result.parser_result.table_segment}</p></div>
          <span className="rounded-full bg-[#FEF3C7] px-3 py-1 text-xs font-bold text-[#92400E]">저장 안 됨 · 승인 안 됨</span>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {(Object.keys(STATUS_LABEL) as Trt35CellStatus[]).map((status) => <button key={status} type="button" onClick={() => setStatusFilter(statusFilter === status ? 'ALL' : status)} className={`rounded-lg p-4 text-left transition ring-1 ring-inset ${STATUS_CLASS[status]} ${statusFilter === status ? 'ring-current' : 'ring-transparent'}`}><p className="text-xs font-semibold">{STATUS_LABEL[status]}</p><p className="mt-1 text-2xl font-bold">{counts[status]} 셀</p></button>)}
        </div>
        <div className="overflow-x-auto rounded-lg border border-[#E2E8F0]"><table className="min-w-full text-sm"><thead className="bg-[#F8FAFC] text-left text-xs uppercase tracking-wide text-[#64748B]"><tr><th className="px-4 py-3">반경</th><th className="px-4 py-3">붐 길이</th><th className="px-4 py-3">상태</th><th className="px-4 py-3">정격 용량</th><th className="px-4 py-3">근거</th></tr></thead><tbody className="divide-y divide-[#E2E8F0] text-[#334155]">
          {visibleCells.map((cell) => <tr key={`${cell.row_index}-${cell.column_index}`}><td className="whitespace-nowrap px-4 py-3">{cell.radius_m.toFixed(1)} m</td><td className="whitespace-nowrap px-4 py-3">{cell.boom_length_m.toFixed(1)} m</td><td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${STATUS_CLASS[cell.cell_status]}`}>{STATUS_LABEL[cell.cell_status]}</span></td><td className="whitespace-nowrap px-4 py-3 font-mono font-semibold">{cell.cell_status === 'AVAILABLE' && cell.rated_capacity_t != null ? `${cell.rated_capacity_t.toFixed(2)} t` : '—'}</td><td className="max-w-xs px-4 py-3 text-xs text-[#64748B]">{cell.cell_status === 'UNRESOLVED' ? cell.reason ?? '원본 확인 필요' : cell.source_text ?? '—'}</td></tr>)}
        </tbody></table></div>
      </section>}
    </div>
  );
}
