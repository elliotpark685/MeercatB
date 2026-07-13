import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import PolicyLanguageSwitcher from '../components/PolicyLanguageSwitcher';
import { FileTextIcon, ShieldIcon } from '../components/Icons';

type Locale = 'en' | 'ko';

const content = {
  en: {
    seoTitle: 'MeerkatAI | Terms of Service', seoDescription: 'Read the terms of service for MeerkatAI, including user responsibilities, prohibited conduct, AI output use, account management, and service changes.', badge: 'Terms of Service', operator: 'MeerkatAI by ASEL', heading: 'Terms that keep the service clear, usable, and predictable.', intro: 'These terms explain how MeerkatAI should be used, how AI output should be handled, and what users can expect as the service evolves.',
    rulesEyebrow: 'Key Terms', rulesTitle: 'Main service rules', rules: [['Service purpose', 'MeerkatAI provides construction safety search, AI-assisted document generation, and related informational tools.'], ['Member responsibility', 'Users are responsible for reviewing output, verifying applicability, and using the service in accordance with law and internal policy.'], ['Prohibited conduct', 'Users must not misuse the service, attempt unauthorized access, disrupt operations, or submit unlawful content.'], ['AI output use', 'AI-generated results are reference material only and must be checked before operational or legal use.'], ['Account management', 'Users are responsible for maintaining account security and for providing accurate registration details.'], ['Copyright and ownership', 'Service content, UI, and proprietary assets remain protected by applicable intellectual property law.']],
    changesEyebrow: 'Service Changes', changesTitle: 'The service may change over time', changes: ['MeerkatAI may update features, UI, supported workflows, pricing, or access conditions without prior notice when needed.', 'Temporary interruptions may occur for maintenance, security updates, or infrastructure changes.'], liabilityEyebrow: 'Liability', liabilityTitle: 'Disclaimer and limitation', liability: ['AI output is informational only. Users remain responsible for verifying safety, legal, and operational decisions before relying on it.', 'MeerkatAI does not guarantee completeness, accuracy, or fitness for a specific purpose.'],
  },
  ko: {
    seoTitle: 'MeerkatAI | 이용약관', seoDescription: 'MeerkatAI의 이용자 책임, 금지 행위, AI 결과물 이용, 계정 관리 및 서비스 변경에 관한 이용약관을 확인하세요.', badge: '이용약관', operator: 'MeerkatAI by ASEL', heading: '명확하고 예측 가능한 서비스 이용을 위한 약관', intro: '본 약관은 MeerkatAI의 이용 방법, AI 생성 결과물의 취급 방식 및 서비스 변경에 대해 이용자가 알아야 할 사항을 설명합니다.',
    rulesEyebrow: '주요 약관', rulesTitle: '서비스 이용의 기본 원칙', rules: [['서비스 목적', 'MeerkatAI는 건설 안전 검색, AI 기반 문서 생성 및 관련 정보 도구를 제공합니다.'], ['이용자 책임', '이용자는 결과물을 검토하고 적용 가능성을 확인하며 법령과 내부 정책에 따라 서비스를 이용할 책임이 있습니다.'], ['금지 행위', '이용자는 서비스를 부정하게 이용하거나 무단 접근을 시도하거나 운영을 방해하거나 불법적인 내용을 제출해서는 안 됩니다.'], ['AI 결과물 이용', 'AI가 생성한 결과물은 참고 자료이며, 현장 운영 또는 법적 목적으로 이용하기 전에 반드시 확인해야 합니다.'], ['계정 관리', '이용자는 계정 보안을 유지하고 정확한 가입 정보를 제공할 책임이 있습니다.'], ['저작권 및 소유권', '서비스 콘텐츠, UI 및 독점 자산은 적용되는 지식재산권 법령의 보호를 받습니다.']],
    changesEyebrow: '서비스 변경', changesTitle: '서비스는 변경될 수 있습니다', changes: ['필요한 경우 MeerkatAI는 사전 고지 없이 기능, UI, 지원 워크플로, 요금 또는 접근 조건을 변경할 수 있습니다.', '유지보수, 보안 업데이트 또는 인프라 변경으로 일시적인 서비스 중단이 발생할 수 있습니다.'], liabilityEyebrow: '책임 제한', liabilityTitle: '면책 및 책임의 제한', liability: ['AI 결과물은 정보 제공을 위한 참고 자료입니다. 이용자는 이를 신뢰하기 전에 안전, 법률 및 운영상의 판단을 직접 확인할 책임이 있습니다.', 'MeerkatAI는 특정 목적에 대한 완전성, 정확성 또는 적합성을 보장하지 않습니다.'],
  },
} as const;

export default function Terms({ locale }: { locale: Locale }) {
  const t = content[locale];
  const path = locale === 'ko' ? '/ko/terms' : '/terms';
  return (
    <PublicPageFrame>
      <Seo title={t.seoTitle} description={t.seoDescription} path={path} language={locale} alternatePaths={{ en: '/terms', ko: '/ko/terms' }} />
      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10"><div className="flex flex-wrap items-center gap-2"><span className="rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]"><FileTextIcon className="mr-1 inline h-4 w-4 align-[-2px]" />{t.badge}</span><span className="rounded-full border border-[#2C2C2E] bg-[#121212] px-3 py-1 text-xs text-[#98989D]">{t.operator}</span><PolicyLanguageSwitcher locale={locale} englishPath="/terms" koreanPath="/ko/terms" /></div><div className="mt-6 max-w-3xl space-y-4"><h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">{t.heading}</h1><p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">{t.intro}</p></div></section>
        <div className="mt-6 grid gap-6"><PageSection eyebrow={t.rulesEyebrow} title={t.rulesTitle}><div className="grid gap-4 md:grid-cols-2">{t.rules.map(([title, text]) => <article key={title} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-5"><div className="mb-3 inline-flex rounded-xl border border-[#2C2C2E] bg-[#1E1E1E] p-2 text-[#00E5FF]"><ShieldIcon className="h-5 w-5" /></div><h3 className="text-sm font-semibold text-white">{title}</h3><p className="mt-2 text-sm leading-6 text-[#98989D]">{text}</p></article>)}</div></PageSection><div className="grid gap-6 xl:grid-cols-2"><PageSection eyebrow={t.changesEyebrow} title={t.changesTitle}><div className="space-y-3 text-sm leading-6 text-[#C7C7CC]">{t.changes.map((item) => <p key={item}>{item}</p>)}</div></PageSection><PageSection eyebrow={t.liabilityEyebrow} title={t.liabilityTitle}><div className="space-y-3 text-sm leading-6 text-[#C7C7CC]">{t.liability.map((item) => <p key={item}>{item}</p>)}</div></PageSection></div></div>
      </div>
    </PublicPageFrame>
  );
}
