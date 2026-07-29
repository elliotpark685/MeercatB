import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import AdSenseSlot from './AdSenseSlot';
import SiteFooter from './SiteFooter';

type PublicPageFrameProps = {
  children: ReactNode;
  language?: 'en' | 'ko';
};

export default function PublicPageFrame({ children, language }: PublicPageFrameProps) {
  return (
    <div className="min-h-screen bg-[#121212] text-white flex flex-col">
      <main className="relative flex-1 overflow-hidden">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-[-8rem] top-[-6rem] h-72 w-72 rounded-full bg-[#00E5FF]/8 blur-3xl" />
          <div className="absolute right-[-6rem] top-24 h-80 w-80 rounded-full bg-[#BF5AF2]/8 blur-3xl" />
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#2C2C2E] to-transparent" />
        </div>
        <div className="relative">
          <header className="relative z-10 mx-auto flex h-16 w-full max-w-7xl items-center justify-end px-4 sm:px-6 lg:px-8">
            <Link
              to="/"
              className="rounded-lg border border-[#2C2C2E] bg-[#1A1A1A]/90 px-3 py-2 text-sm font-medium text-[#C7C7CC] transition hover:border-[#00E5FF]/40 hover:text-white"
            >
              홈으로
            </Link>
          </header>
          {children}
          <div className="mx-auto w-full max-w-7xl px-4 pb-10 sm:px-6 lg:px-8">
            <AdSenseSlot />
          </div>
        </div>
      </main>
      <SiteFooter language={language} />
    </div>
  );
}
