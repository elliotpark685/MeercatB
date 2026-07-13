import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import PolicyLanguageSwitcher from '../components/PolicyLanguageSwitcher';
import { AlertIcon } from '../components/Icons';

type Locale = 'en' | 'ko';

const content = {
  en: {
    seoTitle: 'MeerkatAI | Disclaimer', seoDescription: 'Review the MeerkatAI AI disclaimer, including that generated results are reference material only and do not replace legal or safety responsibility.', badge: 'AI Disclaimer', heading: 'AI-generated results are useful references, not final authority.', intro: 'MeerkatAI is designed to help users work faster, but the final responsibility for legal compliance and safety decisions always remains with the user.',
    noticeEyebrow: 'Required Notice', noticeTitle: 'Important points every user should understand', notices: ['AI-generated results are reference material only.', 'The service is not a substitute for legal advice.', 'Final responsibility for industrial safety and health decisions rests with the user.', 'Latest laws and regulations must always be verified before use.', 'MeerkatAI continuously improves results but does not guarantee completeness or accuracy.'], practicalEyebrow: 'Practical Use', practicalTitle: 'Recommended verification steps', practical: ['Cross-check the output against official legal sources.', 'Apply internal company rules and site-specific conditions.', 'Use professional judgment before taking action in the field.'],
  },
  ko: {
    seoTitle: 'MeerkatAI | AI 면책조항', seoDescription: 'MeerkatAI의 AI 생성 결과물은 참고 자료이며 법률 및 안전 책임을 대체하지 않는다는 면책조항을 확인하세요.', badge: 'AI 면책조항', heading: 'AI 생성 결과물은 유용한 참고 자료이며 최종 판단이 아닙니다.', intro: 'MeerkatAI는 이용자의 업무를 더 빠르게 돕기 위해 설계되었지만, 법령 준수와 안전에 관한 최종 책임은 언제나 이용자에게 있습니다.',
    noticeEyebrow: '필수 안내', noticeTitle: '모든 이용자가 알아야 할 중요 사항', notices: ['AI가 생성한 결과물은 참고 자료입니다.', '본 서비스는 법률 자문을 대체하지 않습니다.', '산업안전 및 보건에 관한 최종 판단과 책임은 이용자에게 있습니다.', '최신 법령과 규정은 이용 전 반드시 확인해야 합니다.', 'MeerkatAI는 결과를 지속적으로 개선하지만 완전성이나 정확성을 보장하지 않습니다.'], practicalEyebrow: '실무 활용', practicalTitle: '권장 확인 절차', practical: ['결과물을 공식 법령 출처와 대조하여 확인하세요.', '회사 내부 규정과 현장별 조건을 적용하세요.', '현장에서 조치하기 전 전문가의 판단을 활용하세요.'],
  },
} as const;

export default function Disclaimer({ locale }: { locale: Locale }) {
  const t = content[locale];
  const path = locale === 'ko' ? '/ko/disclaimer' : '/disclaimer';
  return (
    <PublicPageFrame>
      <Seo title={t.seoTitle} description={t.seoDescription} path={path} language={locale} alternatePaths={{ en: '/disclaimer', ko: '/ko/disclaimer' }} />
      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10"><div className="flex flex-wrap items-center gap-2"><span className="inline-flex items-center gap-2 rounded-full border border-[#FF9F0A]/20 bg-[#FF9F0A]/10 px-3 py-1 text-xs font-medium text-[#FF9F0A]"><AlertIcon className="h-4 w-4" />{t.badge}</span><PolicyLanguageSwitcher locale={locale} englishPath="/disclaimer" koreanPath="/ko/disclaimer" /></div><div className="mt-6 max-w-3xl space-y-4"><h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">{t.heading}</h1><p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">{t.intro}</p></div></section>
        <div className="mt-6 grid gap-6"><PageSection eyebrow={t.noticeEyebrow} title={t.noticeTitle}><div className="grid gap-4 md:grid-cols-2">{t.notices.map((item) => <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">{item}</div>)}</div></PageSection><PageSection eyebrow={t.practicalEyebrow} title={t.practicalTitle}><div className="grid gap-3 md:grid-cols-3">{t.practical.map((item) => <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">{item}</div>)}</div></PageSection></div>
      </div>
    </PublicPageFrame>
  );
}
