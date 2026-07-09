import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import { FileTextIcon, ShieldIcon } from '../components/Icons';

const terms = [
  {
    title: 'Service purpose',
    text: 'MeerkatAI provides construction safety search, AI-assisted document generation, and related informational tools.',
  },
  {
    title: 'Member responsibility',
    text: 'Users are responsible for reviewing output, verifying applicability, and using the service in accordance with law and internal policy.',
  },
  {
    title: 'Prohibited conduct',
    text: 'Users must not misuse the service, attempt unauthorized access, disrupt operations, or submit unlawful content.',
  },
  {
    title: 'AI output use',
    text: 'AI-generated results are reference material only and must be checked before operational or legal use.',
  },
  {
    title: 'Account management',
    text: 'Users are responsible for maintaining account security and for providing accurate registration details.',
  },
  {
    title: 'Copyright and ownership',
    text: 'Service content, UI, and proprietary assets remain protected by applicable intellectual property law.',
  },
];

export default function Terms() {
  return (
    <PublicPageFrame>
      <Seo
        title="MeerkatAI | Terms of Service"
        description="Read the terms of service for MeerkatAI, including user responsibilities, prohibited conduct, AI output use, account management, and service changes."
        path="/terms"
      />

      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]">
              <FileTextIcon className="mr-1 inline h-4 w-4 align-[-2px]" />
              Terms of Service
            </span>
            <span className="rounded-full border border-[#2C2C2E] bg-[#121212] px-3 py-1 text-xs text-[#98989D]">
              MeerkatAI by ASEL
            </span>
          </div>
          <div className="mt-6 max-w-3xl space-y-4">
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">
              Terms that keep the service clear, usable, and predictable.
            </h1>
            <p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">
              These terms explain how MeerkatAI should be used, how AI output should be handled, and what users
              can expect as the service evolves.
            </p>
          </div>
        </section>

        <div className="mt-6 grid gap-6">
          <PageSection eyebrow="Key Terms" title="Main service rules">
            <div className="grid gap-4 md:grid-cols-2">
              {terms.map(({ title, text }) => (
                <article key={title} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-5">
                  <div className="mb-3 inline-flex rounded-xl border border-[#2C2C2E] bg-[#1E1E1E] p-2 text-[#00E5FF]">
                    <ShieldIcon className="h-5 w-5" />
                  </div>
                  <h3 className="text-sm font-semibold text-white">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#98989D]">{text}</p>
                </article>
              ))}
            </div>
          </PageSection>

          <div className="grid gap-6 xl:grid-cols-2">
            <PageSection eyebrow="Service Changes" title="The service may change over time">
              <div className="space-y-3 text-sm leading-6 text-[#C7C7CC]">
                <p>
                  MeerkatAI may update features, UI, supported workflows, pricing, or access conditions without
                  prior notice when needed.
                </p>
                <p>
                  Temporary interruptions may occur for maintenance, security updates, or infrastructure changes.
                </p>
              </div>
            </PageSection>

            <PageSection eyebrow="Liability" title="Disclaimer and limitation">
              <div className="space-y-3 text-sm leading-6 text-[#C7C7CC]">
                <p>
                  AI output is informational only. Users remain responsible for verifying safety, legal, and
                  operational decisions before relying on it.
                </p>
                <p>
                  MeerkatAI does not guarantee completeness, accuracy, or fitness for a specific purpose.
                </p>
              </div>
            </PageSection>
          </div>
        </div>
      </div>
    </PublicPageFrame>
  );
}
