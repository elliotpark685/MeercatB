import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import { ShieldIcon } from '../components/Icons';

const dataRows = [
  ['Email', 'Account creation, login, notifications, and support.'],
  ['Name', 'Account profile and service personalization.'],
  ['Site name', 'Workspace or site-level account organization.'],
  ['Search history', 'Improve search usability and retain recent context.'],
  ['Document generation history', 'Provide draft continuity and user review.'],
  ['IP address', 'Security, fraud prevention, and service diagnostics.'],
  ['Browser information', 'Compatibility, analytics, and technical support.'],
];

export default function Privacy() {
  return (
    <PublicPageFrame>
      <Seo
        title="MeerkatAI | Privacy Policy"
        description="Review what MeerkatAI collects, why it is collected, how long it is retained, and how cookies, Supabase Auth, and AdSense are used."
        path="/privacy"
      />

      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]">
              <ShieldIcon className="mr-1 inline h-4 w-4 align-[-2px]" />
              Privacy Policy
            </span>
            <span className="rounded-full border border-[#2C2C2E] bg-[#121212] px-3 py-1 text-xs text-[#98989D]">
              Effective for MeerkatAI by ASEL
            </span>
          </div>
          <div className="mt-6 max-w-3xl space-y-4">
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">
              How MeerkatAI collects, uses, and protects information.
            </h1>
            <p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">
              This policy explains the personal information processed by MeerkatAI, including account data,
              search logs, document generation records, and technical data used to keep the service secure and
              reliable.
            </p>
          </div>
        </section>

        <div className="mt-6 grid gap-6">
          <PageSection eyebrow="Collected Data" title="Information we collect">
            <div className="grid gap-3 md:grid-cols-2">
              {dataRows.map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4">
                  <p className="text-sm font-semibold text-white">{label}</p>
                  <p className="mt-2 text-sm leading-6 text-[#98989D]">{value}</p>
                </div>
              ))}
            </div>
          </PageSection>

          <div className="grid gap-6 xl:grid-cols-2">
            <PageSection eyebrow="Purpose" title="Why the information is used">
              <ul className="space-y-3 text-sm leading-6 text-[#C7C7CC]">
                {[
                  'Provide account creation and authentication through Supabase Auth.',
                  'Deliver search, document generation, and service history features.',
                  'Improve security, fraud detection, troubleshooting, and service quality.',
                  'Measure traffic and support advertising integration where applicable.',
                ].map((item) => (
                  <li key={item} className="flex gap-3">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#00E5FF]" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </PageSection>

            <PageSection eyebrow="Retention" title="Retention period">
              <div className="space-y-4 text-sm leading-6 text-[#C7C7CC]">
                <p>
                  Personal data is retained for as long as the account remains active or as needed to provide the
                  service.
                </p>
                <p>
                  Search logs and document generation records may be retained to improve quality, troubleshoot
                  issues, and maintain service continuity.
                </p>
                <p>
                  When deletion is requested or retention is no longer required, data is removed or anonymized
                  where feasible, subject to legal and operational requirements.
                </p>
              </div>
            </PageSection>
          </div>

          <PageSection eyebrow="Cookies" title="Cookies and third-party services">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4">
                <h3 className="text-sm font-semibold text-white">Google AdSense cookies</h3>
                <p className="mt-2 text-sm leading-6 text-[#98989D]">
                  Google AdSense may use cookies or similar technologies to serve and measure ads when the service
                  enables advertising.
                </p>
              </div>
              <div className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4">
                <h3 className="text-sm font-semibold text-white">Supabase Auth</h3>
                <p className="mt-2 text-sm leading-6 text-[#98989D]">
                  Authentication data is processed through Supabase Auth to support secure sign-in, sign-up, and
                  session management.
                </p>
              </div>
            </div>
          </PageSection>

          <PageSection eyebrow="User Rights" title="User rights and contact">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">
                Users may request access, correction, deletion, or other privacy-related support by email.
              </div>
              <a
                href="mailto:elliotpark685@gmail.com"
                className="rounded-2xl border border-[#00E5FF]/20 bg-[#00E5FF]/10 p-4 text-sm font-medium text-[#00E5FF] transition-colors hover:bg-[#00E5FF]/15"
              >
                Contact: elliotpark685@gmail.com
                <span className="mt-2 block text-xs font-normal text-[#C7C7CC]">
                  Email-only support for privacy inquiries and requests.
                </span>
              </a>
            </div>
          </PageSection>

          <PageSection eyebrow="Protection" title="Privacy protection efforts">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {[
                'Use of authentication and access control.',
                'Limiting service data to operational needs.',
                'Monitoring for errors and abnormal usage patterns.',
                'Reviewing service behavior to improve reliability.',
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
