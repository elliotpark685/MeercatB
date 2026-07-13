import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import PolicyLanguageSwitcher from '../components/PolicyLanguageSwitcher';
import { ShieldIcon } from '../components/Icons';

type Locale = 'en' | 'ko';

const content = {
  en: {
    seoTitle: 'MeerkatAI | Privacy Policy',
    seoDescription: 'Review what MeerkatAI collects, why it is collected, how long it is retained, and how cookies, Supabase Auth, and AdSense are used.',
    badge: 'Privacy Policy', effective: 'Effective for MeerkatAI by ASEL',
    heading: 'How MeerkatAI collects, uses, and protects information.',
    intro: 'This policy explains the personal information processed by MeerkatAI, including account data, search logs, document generation records, and technical data used to keep the service secure and reliable.',
    dataEyebrow: 'Collected Data', dataTitle: 'Information we collect',
    rows: [['Email', 'Account creation, login, notifications, and support.'], ['Name', 'Account profile and service personalization.'], ['Site name', 'Workspace or site-level account organization.'], ['Search history', 'Improve search usability and retain recent context.'], ['Document generation history', 'Provide draft continuity and user review.'], ['IP address', 'Security, fraud prevention, and service diagnostics.'], ['Browser information', 'Compatibility, analytics, and technical support.']],
    purposeEyebrow: 'Purpose', purposeTitle: 'Why the information is used', purpose: ['Provide account creation and authentication through Supabase Auth.', 'Deliver search, document generation, and service history features.', 'Improve security, fraud detection, troubleshooting, and service quality.', 'Measure traffic and support advertising integration where applicable.'],
    retentionEyebrow: 'Retention', retentionTitle: 'Retention period', retention: ['Personal data is retained for as long as the account remains active or as needed to provide the service.', 'Search logs and document generation records may be retained to improve quality, troubleshoot issues, and maintain service continuity.', 'When deletion is requested or retention is no longer required, data is removed or anonymized where feasible, subject to legal and operational requirements.'],
    cookiesEyebrow: 'Cookies', cookiesTitle: 'Cookies and third-party services', adsTitle: 'Google AdSense cookies', adsText: 'Google AdSense may use cookies or similar technologies to serve and measure ads when the service enables advertising.', authText: 'Authentication data is processed through Supabase Auth to support secure sign-in, sign-up, and session management.',
    rightsEyebrow: 'User Rights', rightsTitle: 'User rights and contact', rightsText: 'Users may request access, correction, deletion, or other privacy-related support by email.', contactText: 'Email-only support for privacy inquiries and requests.',
    protectionEyebrow: 'Protection', protectionTitle: 'Privacy protection efforts', protection: ['Use of authentication and access control.', 'Limiting service data to operational needs.', 'Monitoring for errors and abnormal usage patterns.', 'Reviewing service behavior to improve reliability.'],
  },
  ko: {
    seoTitle: 'MeerkatAI | 개인정보처리방침',
    seoDescription: 'MeerkatAI가 수집하는 개인정보, 이용 목적, 보유 기간 및 쿠키·Supabase Auth·AdSense 이용 방침을 확인하세요.',
    badge: '개인정보처리방침', effective: 'MeerkatAI by ASEL에 적용',
    heading: 'MeerkatAI의 정보 수집·이용·보호 방침',
    intro: '본 방침은 계정 정보, 검색 기록, 문서 생성 기록 및 서비스의 보안과 안정적 운영을 위해 처리하는 기술 정보를 포함하여 MeerkatAI가 처리하는 개인정보에 관해 설명합니다.',
    dataEyebrow: '수집 정보', dataTitle: '수집하는 정보',
    rows: [['이메일', '계정 생성, 로그인, 알림 및 고객 지원'], ['이름', '계정 프로필 및 서비스 개인화'], ['현장명', '작업 공간 또는 현장 단위의 계정 구성'], ['검색 기록', '검색 편의성 개선 및 최근 검색 맥락 유지'], ['문서 생성 기록', '초안 연속성 제공 및 사용자 검토 지원'], ['IP 주소', '보안, 부정 이용 방지 및 서비스 진단'], ['브라우저 정보', '호환성 관리, 분석 및 기술 지원']],
    purposeEyebrow: '이용 목적', purposeTitle: '정보를 이용하는 이유', purpose: ['Supabase Auth를 통한 계정 생성 및 인증 제공', '검색, 문서 생성 및 서비스 이용 기록 기능 제공', '보안 강화, 부정 이용 탐지, 장애 해결 및 서비스 품질 개선', '필요한 경우 트래픽 측정 및 광고 연동 지원'],
    retentionEyebrow: '보유 기간', retentionTitle: '개인정보 보유 및 처리 기간', retention: ['개인정보는 계정이 활성 상태인 동안 또는 서비스 제공에 필요한 기간 동안 보유합니다.', '검색 기록과 문서 생성 기록은 품질 개선, 문제 해결 및 서비스 연속성 유지를 위해 보유될 수 있습니다.', '삭제를 요청했거나 보유가 더 이상 필요하지 않은 경우, 법적·운영상 요구 사항을 고려하여 가능한 범위에서 정보를 삭제하거나 익명화합니다.'],
    cookiesEyebrow: '쿠키', cookiesTitle: '쿠키 및 제3자 서비스', adsTitle: 'Google AdSense 쿠키', adsText: '서비스에서 광고를 제공하는 경우 Google AdSense는 광고 제공 및 측정을 위해 쿠키 또는 유사 기술을 사용할 수 있습니다.', authText: '안전한 로그인, 회원가입 및 세션 관리를 지원하기 위해 인증 정보는 Supabase Auth를 통해 처리됩니다.',
    rightsEyebrow: '이용자 권리', rightsTitle: '이용자 권리 및 문의', rightsText: '이용자는 이메일을 통해 개인정보의 열람, 정정, 삭제 또는 그 밖의 개인정보 관련 지원을 요청할 수 있습니다.', contactText: '개인정보 관련 문의와 요청은 이메일로만 받고 있습니다.',
    protectionEyebrow: '보호 조치', protectionTitle: '개인정보 보호를 위한 노력', protection: ['인증 및 접근 제어 적용', '운영상 필요한 범위로 서비스 데이터 제한', '오류 및 비정상 이용 패턴 모니터링', '신뢰성 향상을 위한 서비스 동작 검토'],
  },
} as const;

export default function Privacy({ locale }: { locale: Locale }) {
  const t = content[locale];
  const path = locale === 'ko' ? '/ko/privacy' : '/privacy';

  return (
    <PublicPageFrame>
      <Seo title={t.seoTitle} description={t.seoDescription} path={path} language={locale} alternatePaths={{ en: '/privacy', ko: '/ko/privacy' }} />
      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10">
          <div className="flex flex-wrap items-center gap-2"><span className="rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]"><ShieldIcon className="mr-1 inline h-4 w-4 align-[-2px]" />{t.badge}</span><span className="rounded-full border border-[#2C2C2E] bg-[#121212] px-3 py-1 text-xs text-[#98989D]">{t.effective}</span><PolicyLanguageSwitcher locale={locale} englishPath="/privacy" koreanPath="/ko/privacy" /></div>
          <div className="mt-6 max-w-3xl space-y-4"><h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">{t.heading}</h1><p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">{t.intro}</p></div>
        </section>
        <div className="mt-6 grid gap-6">
          <PageSection eyebrow={t.dataEyebrow} title={t.dataTitle}><div className="grid gap-3 md:grid-cols-2">{t.rows.map(([label, value]) => <div key={label} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4"><p className="text-sm font-semibold text-white">{label}</p><p className="mt-2 text-sm leading-6 text-[#98989D]">{value}</p></div>)}</div></PageSection>
          <div className="grid gap-6 xl:grid-cols-2"><PageSection eyebrow={t.purposeEyebrow} title={t.purposeTitle}><ul className="space-y-3 text-sm leading-6 text-[#C7C7CC]">{t.purpose.map((item) => <li key={item} className="flex gap-3"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#00E5FF]" /><span>{item}</span></li>)}</ul></PageSection><PageSection eyebrow={t.retentionEyebrow} title={t.retentionTitle}><div className="space-y-4 text-sm leading-6 text-[#C7C7CC]">{t.retention.map((item) => <p key={item}>{item}</p>)}</div></PageSection></div>
          <PageSection eyebrow={t.cookiesEyebrow} title={t.cookiesTitle}><div className="grid gap-4 md:grid-cols-2"><div className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4"><h3 className="text-sm font-semibold text-white">{t.adsTitle}</h3><p className="mt-2 text-sm leading-6 text-[#98989D]">{t.adsText}</p></div><div className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4"><h3 className="text-sm font-semibold text-white">Supabase Auth</h3><p className="mt-2 text-sm leading-6 text-[#98989D]">{t.authText}</p></div></div></PageSection>
          <PageSection eyebrow={t.rightsEyebrow} title={t.rightsTitle}><div className="grid gap-4 md:grid-cols-2"><div className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">{t.rightsText}</div><a href="mailto:elliotpark685@gmail.com" className="rounded-2xl border border-[#00E5FF]/20 bg-[#00E5FF]/10 p-4 text-sm font-medium text-[#00E5FF] transition-colors hover:bg-[#00E5FF]/15">Contact: elliotpark685@gmail.com<span className="mt-2 block text-xs font-normal text-[#C7C7CC]">{t.contactText}</span></a></div></PageSection>
          <PageSection eyebrow={t.protectionEyebrow} title={t.protectionTitle}><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">{t.protection.map((item) => <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">{item}</div>)}</div></PageSection>
        </div>
      </div>
    </PublicPageFrame>
  );
}
