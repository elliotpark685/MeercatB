import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import { MailIcon, LinkIcon } from '../components/Icons';

type ContactProps = {
  locale?: 'en' | 'ko';
};

export default function Contact({ locale = 'en' }: ContactProps) {
  const korean = locale === 'ko';
  const copy = korean
    ? { seoTitle: 'MeerkatAI | 문의', seoDescription: 'MeerkatAI 서비스 제안, 오류 제보, 기능 요청 및 협업 문의를 이메일로 접수합니다.', path: '/ko/contact', badge: '문의', title: '서비스 지원과 의견을 이메일로 보내주세요.', intro: '서비스 제안, 오류 제보, 기능 요청 또는 협업과 관련한 내용은 아래 이메일로 문의할 수 있습니다.', emailTitle: '주요 문의 채널', emailDescription: '개인정보, 서비스 및 협업 관련 문의는 이메일로 받고 있습니다.', inquiryTitle: '문의할 수 있는 내용', actionTitle: '메일 프로그램 열기', action: '이메일 보내기' }
    : { seoTitle: 'MeerkatAI | Contact', seoDescription: 'Contact MeerkatAI by email for suggestions, bug reports, feature requests, or collaboration inquiries.', path: '/contact', badge: 'Contact', title: 'Reach MeerkatAI by email for support and feedback.', intro: 'For service suggestions, error reports, feature requests, or collaboration inquiries, use the email address below.', emailTitle: 'Primary contact channel', emailDescription: 'Email-only support is provided for privacy, service, and partnership related inquiries.', inquiryTitle: 'What you can send', actionTitle: 'Open your mail client', action: 'Send email' };
  const inquiryTypes = korean ? ['서비스 제안', '오류 제보', '기능 요청', '협업 문의'] : ['Service suggestions', 'Bug reports', 'Feature requests', 'Collaboration inquiries'];

  return (
    <PublicPageFrame language={locale}>
      <Seo
        title={copy.seoTitle}
        description={copy.seoDescription}
        path={copy.path}
        language={locale}
      />

      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]">
            <MailIcon className="h-4 w-4" />
            {copy.badge}
          </div>
          <div className="mt-6 max-w-3xl space-y-4">
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">
              {copy.title}
            </h1>
            <p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">
              {copy.intro}
            </p>
          </div>
        </section>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <PageSection eyebrow="Email" title={copy.emailTitle}>
            <div className="rounded-3xl border border-[#00E5FF]/20 bg-[#00E5FF]/10 p-6">
              <p className="text-xs uppercase tracking-[0.24em] text-[#00E5FF]">Email</p>
              <a
                href="mailto:elliotpark685@gmail.com"
                className="mt-3 block break-all text-xl font-semibold text-white transition-colors hover:text-[#00E5FF]"
              >
                elliotpark685@gmail.com
              </a>
              <p className="mt-3 text-sm leading-6 text-[#C7C7CC]">
                {copy.emailDescription}
              </p>
            </div>
          </PageSection>

          <PageSection eyebrow={korean ? '문의 유형' : 'Inquiry Types'} title={copy.inquiryTitle}>
            <div className="grid gap-3 sm:grid-cols-2">
              {inquiryTypes.map((item) => (
                <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">
                  {item}
                </div>
              ))}
            </div>
          </PageSection>
        </div>

        <PageSection eyebrow={korean ? '문의하기' : 'Action'} title={copy.actionTitle}>
          <a
            href="mailto:elliotpark685@gmail.com"
            className="inline-flex items-center gap-2 rounded-full bg-[#00E5FF] px-5 py-3 text-sm font-semibold text-[#121212] transition-colors hover:bg-[#33EAFF]"
          >
            <LinkIcon className="h-4 w-4" />
            {copy.action}
          </a>
        </PageSection>
      </div>
    </PublicPageFrame>
  );
}
