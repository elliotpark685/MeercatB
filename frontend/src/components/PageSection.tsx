import type { ReactNode } from 'react';

type PageSectionProps = {
  title: string;
  description?: string;
  children: ReactNode;
  eyebrow?: string;
};

export default function PageSection({ title, description, children, eyebrow }: PageSectionProps) {
  return (
    <section className="rounded-[28px] border border-[#2C2C2E] bg-[#1A1A1A]/95 p-6 shadow-[0_20px_80px_rgba(0,0,0,0.18)] sm:p-8">
      <div className="mb-6 space-y-2">
        {eyebrow && <p className="text-xs uppercase tracking-[0.24em] text-[#00E5FF]">{eyebrow}</p>}
        <h2 className="text-xl font-semibold tracking-tight text-white sm:text-2xl">{title}</h2>
        {description && <p className="max-w-3xl text-sm leading-6 text-[#C7C7CC]">{description}</p>}
      </div>
      {children}
    </section>
  );
}
