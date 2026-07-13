import type { ReactNode } from 'react';
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
