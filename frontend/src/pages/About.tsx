import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import { FileTextIcon, GlobeIcon, ShieldIcon, SparklesIcon } from '../components/Icons';

const features = [
  {
    title: 'Industrial safety law search',
    description: 'Find relevant occupational safety and health regulations quickly from a single interface.',
    icon: ShieldIcon,
  },
  {
    title: 'AI document generation',
    description: 'Draft workplace safety documents faster with structured, AI-assisted output.',
    icon: FileTextIcon,
  },
  {
    title: 'KOSHA Guide access',
    description: 'Surface KOSHA Guide materials alongside legal search results and related context.',
    icon: GlobeIcon,
  },
  {
    title: 'On-site safety support',
    description: 'Reduce time spent on repetitive lookup work and keep focus on field operations.',
    icon: SparklesIcon,
  },
];

type AboutProps = {
  locale?: 'en' | 'ko';
};

export default function About({ locale = 'en' }: AboutProps) {
  const korean = locale === 'ko';
  const copy = korean
    ? {
        seoTitle: 'MeerkatAI | 서비스 소개', seoDescription: 'MeerkatAI의 건설 안전 법령 검색, KOSHA GUIDE 확인 및 AI 문서 생성 지원 방식을 소개합니다.', path: '/ko/about', badge: 'MeerkatAI 소개', title: '현장 업무에 바로 쓰는 AI 기반 건설 안전 플랫폼', intro: 'MeerkatAI는 산업안전 법령 검색, KOSHA GUIDE 확인, 안전 문서 초안 작성을 한곳에서 지원합니다.', purpose: '안전 정보 업무의 반복 작업을 줄입니다.', purposeDescription: '흩어진 자료를 찾고 정리하는 시간을 줄여 현장 업무에 집중할 수 있도록 설계했습니다.',
      }
    : { seoTitle: 'MeerkatAI | About', seoDescription: 'Learn what MeerkatAI does, who it is for, and how it supports construction safety teams with AI-assisted search and document generation.', path: '/about', badge: 'About MeerkatAI', title: 'AI-powered construction safety platform for practical field work.', intro: 'MeerkatAI helps users search industrial safety regulations, review KOSHA Guide materials, and generate structured documents with less manual overhead.', purpose: 'Built to reduce the friction of safety information work.', purposeDescription: 'MeerkatAI is designed to help users find, organize, and apply construction safety information without losing time in fragmented documents or scattered references.' };

  const featureCopy = korean
    ? [
        ['산업안전 법령 검색', '관련 법령과 조문을 한 화면에서 빠르게 찾을 수 있습니다.'],
        ['AI 안전 문서 생성', '현장 안전 문서 초안 작성을 구조화된 방식으로 지원합니다.'],
        ['KOSHA GUIDE 확인', '법령 검색 결과와 함께 관련 KOSHA GUIDE 자료를 확인합니다.'],
        ['현장 안전 업무 지원', '반복적인 자료 확인 시간을 줄이고 현장 업무에 집중하도록 돕습니다.'],
      ]
    : features.map(({ title, description }) => [title, description]);

  return (
    <PublicPageFrame language={locale}>
      <Seo
        title={copy.seoTitle}
        description={copy.seoDescription}
        path={copy.path}
        language={locale}
      />

      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="relative overflow-hidden rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10">
          <div className="absolute inset-0 opacity-70">
            <div className="absolute right-[-3rem] top-[-3rem] h-52 w-52 rounded-full bg-[#00E5FF]/10 blur-3xl" />
            <div className="absolute left-10 top-10 h-36 w-36 rounded-full bg-[#BF5AF2]/10 blur-3xl" />
          </div>
          <div className="relative space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]">
              <SparklesIcon className="h-4 w-4" />
              {copy.badge}
            </div>
            <div className="max-w-3xl space-y-4">
              <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">
                {copy.title}
              </h1>
              <p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">
                {copy.intro}
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {(korean
                ? [['서비스', '건설 안전 업무 지원'], ['운영자', 'ASEL (개인 개발자)'], ['호스팅', 'Vercel 기반']]
                : [['Service', 'Construction safety support'], ['Operator', 'ASEL (Individual Developer)'], ['Hosting', 'Vercel with custom domain readiness']]
              ).map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-[#2C2C2E] bg-[#121212]/80 p-4">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-[#98989D]">{label}</p>
                  <p className="mt-2 text-sm font-medium text-white">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="mt-6 grid gap-6">
          <PageSection
            eyebrow={korean ? '목적' : 'Purpose'}
            title={copy.purpose}
            description={copy.purposeDescription}
          >
            <div className="grid gap-4 md:grid-cols-2">
              {[
                ...(korean ? ['안전 및 법령 자료를 빠르게 찾도록 지원합니다.', '현장 중심 안전 문서의 초안 작성을 돕습니다.', 'KOSHA 및 법령 자료를 활용하기 쉽게 제공합니다.', '명확성과 모바일 사용성을 중심으로 경험을 개선합니다.'] : ['Support fast lookup of safety and legal references.', 'Help users prepare drafts for field-oriented safety documents.', 'Present KOSHA and legal materials in a more usable format.', 'Keep the experience focused on clarity, reliability, and mobile usability.']),
              ].map((item) => (
                <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">
                  {item}
                </div>
              ))}
            </div>
          </PageSection>

          <PageSection
            eyebrow={korean ? '주요 기능' : 'Core Features'}
            title={korean ? '일상적인 현장 업무를 위한 핵심 기능' : 'Core capabilities designed for practical daily use.'}
          >
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {features.map(({ icon: Icon }, index) => {
                const [title, description] = featureCopy[index];
                return (
                <article key={title} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-5">
                  <div className="mb-4 inline-flex rounded-xl border border-[#2C2C2E] bg-[#1E1E1E] p-2 text-[#00E5FF]">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-sm font-semibold text-white">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#98989D]">{description}</p>
                </article>
                );
              })}
            </div>
          </PageSection>

          <PageSection
            eyebrow={korean ? '개선 방향' : 'Roadmap'}
            title={korean ? '신뢰성과 유지 관리성을 중심으로 개선합니다.' : 'Future development remains centered on trust and maintainability.'}
          >
            <div className="grid gap-4 md:grid-cols-3">
              {[
                ...(korean ? ['사용자 경험 및 성능 개선', '검색 노출과 정보 구조 개선', '정책 정보의 투명한 안내'] : ['Custom domain connection support.', 'Continued SEO and performance improvements.', 'AdSense-friendly layout and policy transparency.']),
              ].map((item) => (
                <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">
                  {item}
                </div>
              ))}
            </div>
          </PageSection>
        </div>
      </div>
    </PublicPageFrame>
  );
}
