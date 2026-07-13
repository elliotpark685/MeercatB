import { Link, useLocation } from 'react-router-dom';

type SiteFooterProps = {
  language?: 'en' | 'ko';
};

const FOOTER_LINKS = [
  { to: '/about', label: 'About', koreanLabel: '서비스 소개' },
  { to: '/pricing', label: 'Pricing', koreanLabel: '요금제' },
  { to: '/contact', label: 'Contact', koreanLabel: '문의' },
  { to: '/privacy', label: 'Privacy', koreanLabel: '개인정보처리방침' },
  { to: '/terms', label: 'Terms', koreanLabel: '이용약관' },
  { to: '/login', label: 'Login', koreanLabel: '로그인' },
];

const POLICY_PATHS = ['/privacy', '/terms', '/disclaimer'];

export default function SiteFooter({ language }: SiteFooterProps) {
  const { pathname } = useLocation();
  const year = new Date().getFullYear();
  const korean = language === 'ko' || (!language && pathname.startsWith('/ko/'));

  const links = FOOTER_LINKS.map((link) => ({
    ...link,
    to: korean && POLICY_PATHS.includes(link.to) ? `/ko${link.to}` : link.to,
    label: korean ? link.koreanLabel : link.label,
  }));

  return (
    <footer className="border-t border-[#2C2C2E] bg-[#101010]/95">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div className="space-y-2">
            <div className="text-lg font-semibold tracking-tight text-white">MeerkatAI</div>
            <p className="max-w-xl text-sm leading-6 text-[#98989D]">
              {korean ? 'AI 기반 건설 안전 플랫폼' : 'AI-powered Construction Safety Platform'}
            </p>
          </div>
          <nav aria-label="Footer" className="flex flex-wrap gap-2">
            {links.map((item) => (
              <Link key={item.to} to={item.to} className="rounded-full border border-[#2C2C2E] bg-[#1A1A1A] px-4 py-2 text-xs font-medium text-[#C7C7CC] transition-colors hover:border-[#00E5FF]/30 hover:text-white">
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex flex-col gap-2 border-t border-[#1F1F1F] pt-4 text-xs text-[#3A3A3C] sm:flex-row sm:items-center sm:justify-between">
          <p>© {year} MeerkatAI by ASEL. {korean ? '모든 권리 보유.' : 'All rights reserved.'}</p>
          <p>{korean ? '운영자: 개인 개발자 · 문의: elliotpark685@gmail.com' : 'Built for transparency, compliance, and future custom domain support.'}</p>
        </div>
      </div>
    </footer>
  );
}
