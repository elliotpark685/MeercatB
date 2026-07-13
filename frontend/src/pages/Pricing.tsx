import { Link } from 'react-router-dom';
import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';

const plans = [
  {
    name: 'Free', status: '현재 제공', accent: 'text-[#00E5FF]',
    description: '현장 안전 정보 탐색을 위한 기본 검색 기능',
    items: ['산업안전 법령 검색', '안전기준 검색', 'KOSHA GUIDE 검색', '기본 검색 기록'],
  },
  {
    name: 'Pro', status: '유료 전환 준비 중', accent: 'text-[#BF5AF2]',
    description: 'LLM 비용이 발생하는 문서 생성 기능을 위한 요금제',
    items: ['AI 안전 문서 생성', '월별 생성 한도 및 사용량 관리', '생성 문서 활용 기능', '추가 관리 기능 검토'],
  },
];

export default function Pricing() {
  return (
    <PublicPageFrame>
      <Seo title="MeerkatAI | 요금제" description="MeerkatAI의 무료 검색 기능과 AI 문서 생성 유료 전환 계획을 확인하세요." path="/pricing" language="ko" />
      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10"><p className="text-xs font-medium uppercase tracking-[.22em] text-[#00E5FF]">Pricing</p><h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-5xl">비용 구조에 맞춰 기능을 구분합니다.</h1><p className="mt-5 max-w-3xl text-sm leading-7 text-[#C7C7CC]">DB 기반 검색 기능은 무료로 제공하고, 외부 LLM 호출 비용이 발생하는 문서 생성은 결제와 사용량 관리가 준비된 뒤 유료 기능으로 전환합니다.</p></section>
        <div className="mt-6 grid gap-6 md:grid-cols-2">{plans.map((plan) => <article key={plan.name} className="rounded-[28px] border border-[#2C2C2E] bg-[#1A1A1A] p-6 sm:p-8"><div className="flex items-center justify-between gap-3"><h2 className="text-2xl font-semibold">{plan.name}</h2><span className={`text-xs font-medium ${plan.accent}`}>{plan.status}</span></div><p className="mt-4 text-sm leading-6 text-[#98989D]">{plan.description}</p><ul className="mt-6 space-y-3 text-sm text-[#C7C7CC]">{plan.items.map((item) => <li key={item} className="flex gap-3"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#00E5FF]" />{item}</li>)}</ul></article>)}</div>
        <div className="mt-6"><PageSection eyebrow="운영 원칙" title="가격과 결제는 확정 후 안내합니다."><p className="max-w-3xl text-sm leading-7 text-[#C7C7CC]">현재 결제와 구독 관리 기능은 아직 연결하지 않았으므로, 확정 가격을 표시하지 않습니다. 유료 전환 시에는 문서 생성 횟수, 실패 요청 처리, 월별 사용량과 같은 운영 기준을 함께 안내할 예정입니다.</p><div className="mt-6 flex flex-wrap gap-3"><Link to="/signup" className="rounded-xl bg-[#00E5FF] px-4 py-2.5 text-sm font-semibold text-[#121212]">무료 기능 시작하기</Link><Link to="/contact" className="rounded-xl border border-[#2C2C2E] px-4 py-2.5 text-sm text-[#C7C7CC]">요금제 문의하기</Link></div></PageSection></div>
      </div>
    </PublicPageFrame>
  );
}
