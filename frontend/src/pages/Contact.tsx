import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import { MailIcon, LinkIcon } from '../components/Icons';

export default function Contact() {
  return (
    <PublicPageFrame>
      <Seo
        title="MeerkatAI | Contact"
        description="Contact MeerkatAI by email for suggestions, bug reports, feature requests, or collaboration inquiries."
        path="/contact"
      />

      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]">
            <MailIcon className="h-4 w-4" />
            Contact
          </div>
          <div className="mt-6 max-w-3xl space-y-4">
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">
              Reach MeerkatAI by email for support and feedback.
            </h1>
            <p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">
              For service suggestions, error reports, feature requests, or collaboration inquiries, use the email
              address below.
            </p>
          </div>
        </section>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <PageSection eyebrow="Email" title="Primary contact channel">
            <div className="rounded-3xl border border-[#00E5FF]/20 bg-[#00E5FF]/10 p-6">
              <p className="text-xs uppercase tracking-[0.24em] text-[#00E5FF]">Email</p>
              <a
                href="mailto:elliotpark685@gmail.com"
                className="mt-3 block break-all text-xl font-semibold text-white transition-colors hover:text-[#00E5FF]"
              >
                elliotpark685@gmail.com
              </a>
              <p className="mt-3 text-sm leading-6 text-[#C7C7CC]">
                Email-only support is provided for privacy, service, and partnership related inquiries.
              </p>
            </div>
          </PageSection>

          <PageSection eyebrow="Inquiry Types" title="What you can send">
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                'Service suggestions',
                'Bug reports',
                'Feature requests',
                'Collaboration inquiries',
              ].map((item) => (
                <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">
                  {item}
                </div>
              ))}
            </div>
          </PageSection>
        </div>

        <PageSection eyebrow="Action" title="Open your mail client">
          <a
            href="mailto:elliotpark685@gmail.com"
            className="inline-flex items-center gap-2 rounded-full bg-[#00E5FF] px-5 py-3 text-sm font-semibold text-[#121212] transition-colors hover:bg-[#33EAFF]"
          >
            <LinkIcon className="h-4 w-4" />
            Send email
          </a>
        </PageSection>
      </div>
    </PublicPageFrame>
  );
}
