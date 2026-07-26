import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getLawDocumentCatalog, type LawDocumentCatalogItem } from '../api/admin';

type Category = 'all' | 'law' | 'safety_standard';
type SortKey = 'amendment' | 'effective' | 'name';

const dateText = (value: string | null) => value || '정보 미수집';
const dateRank = (value: string | null) => (value ? new Date(value).getTime() : 0);

function CategoryBadge({ category }: { category: LawDocumentCatalogItem['category'] }) {
  const isSafety = category === 'safety_standard';
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${isSafety ? 'bg-violet-400/10 text-violet-300' : 'bg-cyan-400/10 text-cyan-300'}`}>{isSafety ? '안전기준' : '법령'}</span>;
}

export default function RegulationStatus() {
  const [items, setItems] = useState<LawDocumentCatalogItem[]>([]);
  const [category, setCategory] = useState<Category>('all');
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState<SortKey>('amendment');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getLawDocumentCatalog().then((response) => setItems(response.items)).catch(() => setError('현황 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.')).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return items.filter((item) => category === 'all' || item.category === category).filter((item) => !keyword || [item.name, item.law_no, item.document_type, item.source_type, item.provider].some((value) => value?.toLowerCase().includes(keyword))).sort((a, b) => {
      if (sort === 'name') return a.name.localeCompare(b.name, 'ko');
      const aDate = dateRank(sort === 'amendment' ? a.latest_amendment_date : a.effective_date);
      const bDate = dateRank(sort === 'amendment' ? b.latest_amendment_date : b.effective_date);
      return bDate - aDate || a.name.localeCompare(b.name, 'ko');
    });
  }, [items, category, query, sort]);

  const lawCount = items.filter((item) => item.category === 'law').length;
  const standardCount = items.filter((item) => item.category === 'safety_standard').length;
  const latest = items.reduce<string | null>((current, item) => dateRank(item.latest_amendment_date) > dateRank(current) ? item.latest_amendment_date : current, null);

  return <section className="mx-auto max-w-7xl space-y-6 text-[#F5F5F7]">
    <div className="flex flex-col justify-between gap-4 rounded-2xl border border-[#2C2C2E] bg-gradient-to-br from-[#1D2830] to-[#1B1B1D] p-6 md:flex-row md:items-end md:p-8">
      <div><p className="mb-2 text-xs font-semibold tracking-[0.18em] text-[#00E5FF]">REGULATIONS OVERVIEW</p><h1 className="text-2xl font-bold tracking-tight md:text-3xl">법령·안전기준 현황</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-[#AEAEB2]">서비스에 수집된 최신 법령과 안전기준의 시행·개정 현황을 한눈에 확인하세요.</p></div>
      <Link to="/search" className="inline-flex items-center justify-center rounded-lg bg-[#00E5FF] px-4 py-2.5 text-sm font-semibold text-[#111] transition hover:bg-[#54EDFF]">통합검색으로 이동 →</Link>
    </div>
    <div className="grid gap-3 sm:grid-cols-3"><SummaryCard label="전체 문서" value={items.length} detail="현재 활성 문서" accent="text-white" /><SummaryCard label="법령" value={lawCount} detail="법·시행령·시행규칙" accent="text-cyan-300" /><SummaryCard label="안전기준" value={standardCount} detail={latest ? `최신 개정 ${latest}` : '개정일 수집 중'} accent="text-violet-300" /></div>
    <div className="rounded-2xl border border-[#2C2C2E] bg-[#1E1E1E]">
      <div className="flex flex-col gap-3 border-b border-[#2C2C2E] p-4 md:flex-row md:items-center md:justify-between"><div className="flex rounded-lg bg-[#151515] p-1">{([['all', '전체'], ['law', '법령'], ['safety_standard', '안전기준']] as const).map(([value, label]) => <button key={value} onClick={() => setCategory(value)} className={`rounded-md px-3 py-1.5 text-sm transition ${category === value ? 'bg-[#303033] text-white shadow-sm' : 'text-[#98989D] hover:text-white'}`}>{label}</button>)}</div><div className="flex flex-col gap-2 sm:flex-row"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="명칭·번호로 찾기" className="rounded-lg border border-[#3A3A3C] bg-[#151515] px-3 py-2 text-sm text-white outline-none placeholder:text-[#636366] focus:border-[#00E5FF]" /><select value={sort} onChange={(event) => setSort(event.target.value as SortKey)} className="rounded-lg border border-[#3A3A3C] bg-[#151515] px-3 py-2 text-sm text-[#D1D1D6] outline-none focus:border-[#00E5FF]"><option value="amendment">최종 개정일 순</option><option value="effective">시행일 순</option><option value="name">명칭 순</option></select></div></div>
      {loading ? <div className="p-12 text-center text-sm text-[#98989D]">현황 정보를 불러오는 중입니다.</div> : error ? <div className="p-12 text-center text-sm text-[#FF9F0A]">{error}</div> : <><div className="hidden overflow-x-auto md:block"><table className="w-full min-w-[900px] text-left"><thead className="bg-[#191919] text-xs font-medium text-[#98989D]"><tr><th className="px-5 py-3">문서명</th><th className="px-4 py-3">구분</th><th className="px-4 py-3">공포·발령번호</th><th className="px-4 py-3">시행일</th><th className="px-4 py-3">최종 개정일</th><th className="px-4 py-3">수록 조문</th><th className="px-5 py-3 text-right">원문</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id} className="border-t border-[#2C2C2E] text-sm transition hover:bg-[#252525]"><td className="px-5 py-4"><div className="font-medium text-[#F5F5F7]">{item.name}</div><div className="mt-1 text-xs text-[#8E8E93]">{item.document_type || item.source_type || item.provider || '문서 유형 미수집'}</div></td><td className="px-4 py-4"><CategoryBadge category={item.category} /></td><td className="px-4 py-4 text-[#D1D1D6]">{item.law_no || '정보 미수집'}</td><td className="px-4 py-4 text-[#D1D1D6]">{dateText(item.effective_date)}</td><td className="px-4 py-4 text-[#D1D1D6]">{dateText(item.latest_amendment_date)}</td><td className="px-4 py-4 text-[#D1D1D6]">{item.article_count.toLocaleString()}개</td><td className="px-5 py-4 text-right">{item.source_url ? <a href={item.source_url} target="_blank" rel="noreferrer" className="text-[#00E5FF] hover:underline">열기 ↗</a> : <span className="text-[#636366]">미연결</span>}</td></tr>)}</tbody></table></div><div className="space-y-3 p-4 md:hidden">{filtered.map((item) => <article key={item.id} className="rounded-xl border border-[#303033] bg-[#191919] p-4"><div className="flex items-start justify-between gap-3"><div><h2 className="font-medium">{item.name}</h2><p className="mt-1 text-xs text-[#8E8E93]">{item.law_no || '번호 정보 미수집'}</p></div><CategoryBadge category={item.category} /></div><dl className="mt-4 grid grid-cols-2 gap-3 text-xs"><div><dt className="text-[#8E8E93]">시행일</dt><dd className="mt-1 text-[#D1D1D6]">{dateText(item.effective_date)}</dd></div><div><dt className="text-[#8E8E93]">최종 개정일</dt><dd className="mt-1 text-[#D1D1D6]">{dateText(item.latest_amendment_date)}</dd></div></dl>{item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer" className="mt-4 inline-block text-sm text-[#00E5FF]">원문 열기 ↗</a>}</article>)}</div>{!filtered.length && <div className="border-t border-[#2C2C2E] p-12 text-center text-sm text-[#98989D]">조건에 맞는 문서가 없습니다.</div>}</>}
    </div>
  </section>;
}

function SummaryCard({ label, value, detail, accent }: { label: string; value: number; detail: string; accent: string }) {
  return <div className="rounded-xl border border-[#2C2C2E] bg-[#1E1E1E] p-5"><p className="text-sm text-[#98989D]">{label}</p><p className={`mt-2 text-3xl font-semibold ${accent}`}>{value.toLocaleString()}</p><p className="mt-2 text-xs text-[#8E8E93]">{detail}</p></div>;
}
