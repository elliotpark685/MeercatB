import { Link } from 'react-router-dom';
import Seo from '../components/Seo';
import SiteFooter from '../components/SiteFooter';
import { FileTextIcon, ShieldIcon, SparklesIcon } from '../components/Icons';
import { useAuth } from '../contexts/AuthContext';

const features = [
  { title: '산업안전 법령 검색', description: '관련 법령과 조문을 빠르게 찾아 현장 판단에 필요한 근거를 확인합니다.', icon: ShieldIcon, to: '/laws' },
  { title: 'AI 안전 문서 생성', description: 'TBM, 작업계획서, 위험성평가, 점검 체크리스트 초안 작성을 지원합니다.', icon: FileTextIcon, to: '/documents' },
  { title: '현장 안전 업무 지원', description: '검색 기록과 생성 문서를 바탕으로 반복적인 안전 업무를 더 효율적으로 정리합니다.', icon: SparklesIcon, to: '/dashboard' },
];

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  const startPath = isAuthenticated ? '/dashboard' : '/signup';

  return (
    <div className="min-h-screen bg-[#121212] text-white">
      <Seo
        title="MeerkatAI | AI 기반 건설 안전 법령 검색 및 문서 작성"
        description="MeerkatAI는 산업안전 법령 검색, AI 안전 문서 작성, 현장 안전관리 업무를 지원하는 건설 안전 플랫폼입니다."
        path="/"
        language="ko"
      />

      <header className="sticky top-0 z-20 border-b border-[#2C2C2E]/80 bg-[#121212]/90 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="text-lg font-semibold tracking-tight text-white">MeerkatAI</Link>
          <nav className="hidden items-center gap-5 text-sm text-[#98989D] md:flex">
            <a href="#features" className="hover:text-white">주요 기능</a>
            <Link to="/pricing" className="hover:text-white">요금제</Link>
            <Link to="/about" className="hover:text-white">서비스 소개</Link>
            <Link to="/contact" className="hover:text-white">문의</Link>
          </nav>
          <div className="flex items-center gap-2">
            <Link to={isAuthenticated ? '/dashboard' : '/login'} className="rounded-lg px-3 py-2 text-sm text-[#C7C7CC] transition hover:text-white">
              {isAuthenticated ? '대시보드' : '로그인'}
            </Link>
            <Link to={startPath} className="rounded-lg bg-[#00E5FF] px-3 py-2 text-sm font-semibold text-[#121212] transition hover:bg-[#33EAFF]">
              {isAuthenticated ? '서비스 이용' : '무료로 시작하기'}
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute -left-24 -top-24 h-80 w-80 rounded-full bg-[#00E5FF]/10 blur-3xl" />
            <div className="absolute -right-24 top-20 h-96 w-96 rounded-full bg-[#BF5AF2]/10 blur-3xl" />
          </div>
          <div className="relative mx-auto grid w-full max-w-7xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-[1.2fr_.8fr] lg:px-8 lg:py-28">
            <div className="max-w-3xl">
              <span className="inline-flex rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]">Construction safety workflow</span>
              <h1 className="mt-6 text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">건설 안전 업무를 더 빠르고 명확하게</h1>
              <p className="mt-6 max-w-2xl text-base leading-8 text-[#C7C7CC]">MeerkatAI는 산업안전 법령 검색, 안전 문서 초안 작성, 현장 안전관리 업무를 지원하는 AI 기반 건설 안전 플랫폼입니다.</p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link to={startPath} className="rounded-xl bg-[#00E5FF] px-5 py-3 text-sm font-semibold text-[#121212] transition hover:bg-[#33EAFF]">무료로 시작하기</Link>
                <a href="#features" className="rounded-xl border border-[#2C2C2E] bg-[#1A1A1A] px-5 py-3 text-sm font-medium text-[#C7C7CC] transition hover:border-[#00E5FF]/30 hover:text-white">서비스 기능 보기</a>
              </div>
            </div>
            <div className="rounded-[28px] border border-[#2C2C2E] bg-[#1A1A1A]/90 p-6 shadow-[0_20px_80px_rgba(0,0,0,.25)]">
              <p className="text-xs font-medium uppercase tracking-[.22em] text-[#00E5FF]">Workflow</p>
              <ol className="mt-6 space-y-5 text-sm text-[#C7C7CC]">
                {['회원가입 또는 로그인', '법령·안전기준·KOSHA GUIDE 검색', '필요한 경우 AI 문서 생성', '현장 적용 전 공식 자료와 함께 최종 확인'].map((item, index) => (
                  <li key={item} className="flex gap-3"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[#00E5FF]/30 bg-[#00E5FF]/10 text-xs text-[#00E5FF]">{index + 1}</span><span className="pt-0.5">{item}</span></li>
                ))}
              </ol>
            </div>
          </div>
        </section>

        <section id="features" className="mx-auto w-full max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="max-w-2xl"><p className="text-xs font-medium uppercase tracking-[.22em] text-[#00E5FF]">Core features</p><h2 className="mt-3 text-3xl font-semibold tracking-tight">실제 제공 중인 안전 업무 기능</h2></div>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {features.map(({ title, description, icon: Icon, to }) => (
              <Link key={title} to={to} className="group rounded-3xl border border-[#2C2C2E] bg-[#1A1A1A] p-6 transition hover:border-[#00E5FF]/35 hover:bg-[#1D1D1D]">
                <span className="inline-flex rounded-xl border border-[#00E5FF]/20 bg-[#00E5FF]/10 p-2 text-[#00E5FF]"><Icon className="h-5 w-5" /></span>
                <h3 className="mt-5 text-lg font-semibold group-hover:text-[#00E5FF]">{title}</h3><p className="mt-3 text-sm leading-6 text-[#98989D]">{description}</p>
              </Link>
            ))}
          </div>
        </section>

        <section className="border-y border-[#2C2C2E] bg-[#171717]"><div className="mx-auto grid w-full max-w-7xl gap-8 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:px-8"><div><p className="text-xs font-medium uppercase tracking-[.22em] text-[#FF9F0A]">Use with care</p><h2 className="mt-3 text-3xl font-semibold tracking-tight">현장 적용 전 최종 확인이 필요합니다.</h2></div><p className="text-sm leading-7 text-[#C7C7CC]">MeerkatAI가 제공하는 법령 검색 결과와 AI 생성 문서는 업무 지원을 위한 참고 자료입니다. 실제 현장 적용 전에는 최신 법령·고시·지침과 관계 기관의 공식 자료를 반드시 확인해야 합니다.</p></div></section>

        <section className="mx-auto w-full max-w-7xl px-4 py-16 sm:px-6 lg:px-8"><div className="rounded-[28px] border border-[#00E5FF]/20 bg-gradient-to-r from-[#00E5FF]/10 to-[#BF5AF2]/10 p-7 sm:p-10"><p className="text-xs font-medium uppercase tracking-[.22em] text-[#00E5FF]">Plan</p><h2 className="mt-3 text-3xl font-semibold">법령 검색은 무료, AI 문서 생성은 유료 전환을 준비 중입니다.</h2><p className="mt-4 max-w-3xl text-sm leading-7 text-[#C7C7CC]">무료 기능은 법령·안전기준·KOSHA GUIDE 검색에 집중합니다. LLM 비용이 발생하는 AI 문서 생성은 결제 연동과 사용량 관리가 준비된 뒤 Pro 기능으로 제공할 예정입니다.</p><Link to="/pricing" className="mt-6 inline-flex rounded-xl border border-[#2C2C2E] bg-[#121212] px-4 py-2.5 text-sm font-medium text-white transition hover:border-[#00E5FF]/40">요금제 운영 방향 보기</Link></div></section>
      </main>
      <SiteFooter language="ko" />
    </div>
  );
}
