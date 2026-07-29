import type { ReactNode } from 'react';

type PageSectionProps = {
  title: string;
  description?: string;
  children: ReactNode;
  eyebrow?: string;
};

export default function PageSection({ title, description, children, eyebrow }: PageSectionProps) {
  return (
    <section className="rounded-xl border border-[#E2E8F0] bg-white p-6 shadow-[0_1px_3px_rgba(15,23,42,0.06)] sm:p-8">
      <div className="mb-6 space-y-2">
        {eyebrow && <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#2563EB]">{eyebrow}</p>}
        <h2 className="text-xl font-bold tracking-tight text-[#0F172A] sm:text-2xl">{title}</h2>
        {description && <p className="max-w-3xl text-sm leading-6 text-[#475569]">{description}</p>}
      </div>
      {children}
    </section>
  );
}
