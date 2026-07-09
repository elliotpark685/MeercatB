import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import { AlertIcon } from '../components/Icons';

export default function Disclaimer() {
  return (
    <PublicPageFrame>
      <Seo
        title="MeerkatAI | Disclaimer"
        description="Review the MeerkatAI AI disclaimer, including that generated results are reference material only and do not replace legal or safety responsibility."
        path="/disclaimer"
      />

      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#FF9F0A]/20 bg-[#FF9F0A]/10 px-3 py-1 text-xs font-medium text-[#FF9F0A]">
            <AlertIcon className="h-4 w-4" />
            AI Disclaimer
          </div>
          <div className="mt-6 max-w-3xl space-y-4">
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">
              AI-generated results are useful references, not final authority.
            </h1>
            <p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">
              MeerkatAI is designed to help users work faster, but the final responsibility for legal compliance
              and safety decisions always remains with the user.
            </p>
          </div>
        </section>

        <div className="mt-6 grid gap-6">
          <PageSection eyebrow="Required Notice" title="Important points every user should understand">
            <div className="grid gap-4 md:grid-cols-2">
              {[
                'AI-generated results are reference material only.',
                'The service is not a substitute for legal advice.',
                'Final responsibility for industrial safety and health decisions rests with the user.',
                'Latest laws and regulations must always be verified before use.',
                'MeerkatAI continuously improves results but does not guarantee completeness or accuracy.',
              ].map((item) => (
                <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">
                  {item}
                </div>
              ))}
            </div>
          </PageSection>

          <PageSection eyebrow="Practical Use" title="Recommended verification steps">
            <div className="grid gap-3 md:grid-cols-3">
              {[
                'Cross-check the output against official legal sources.',
                'Apply internal company rules and site-specific conditions.',
                'Use professional judgment before taking action in the field.',
              ].map((item) => (
                <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">
                  {item}
                </div>
              ))}
            </div>
          </PageSection>
        </div>
      </div>
    </PublicPageFrame>
  );
}
