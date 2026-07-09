import { Link } from 'react-router-dom';

const FOOTER_LINKS = [
  { to: '/about', label: 'About' },
  { to: '/privacy', label: 'Privacy' },
  { to: '/terms', label: 'Terms' },
  { to: '/disclaimer', label: 'Disclaimer' },
  { to: '/contact', label: 'Contact' },
];

export default function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-[#2C2C2E] bg-[#101010]/95">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div className="space-y-2">
            <div className="text-lg font-semibold tracking-tight text-white">MeerkatAI</div>
            <p className="max-w-xl text-sm leading-6 text-[#98989D]">
              AI-powered Construction Safety Platform
            </p>
          </div>
          <nav aria-label="Footer" className="flex flex-wrap gap-2">
            {FOOTER_LINKS.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="rounded-full border border-[#2C2C2E] bg-[#1A1A1A] px-4 py-2 text-xs font-medium text-[#C7C7CC] transition-colors hover:border-[#00E5FF]/30 hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="flex flex-col gap-2 border-t border-[#1F1F1F] pt-4 text-xs text-[#3A3A3C] sm:flex-row sm:items-center sm:justify-between">
          <p>© {year} MeerkatAI by ASEL. All rights reserved.</p>
          <p>Built for transparency, compliance, and future custom domain support.</p>
        </div>
      </div>
    </footer>
  );
}
