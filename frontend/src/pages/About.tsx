import Seo from '../components/Seo';
import PublicPageFrame from '../components/PublicPageFrame';
import PageSection from '../components/PageSection';
import { FileTextIcon, GlobeIcon, ShieldIcon, SparklesIcon } from '../components/Icons';

const features = [
  {
    title: 'Industrial safety law search',
    description: 'Find relevant occupational safety and health regulations quickly from a single interface.',
    icon: ShieldIcon,
  },
  {
    title: 'AI document generation',
    description: 'Draft workplace safety documents faster with structured, AI-assisted output.',
    icon: FileTextIcon,
  },
  {
    title: 'KOSHA Guide access',
    description: 'Surface KOSHA Guide materials alongside legal search results and related context.',
    icon: GlobeIcon,
  },
  {
    title: 'On-site safety support',
    description: 'Reduce time spent on repetitive lookup work and keep focus on field operations.',
    icon: SparklesIcon,
  },
];

export default function About() {
  return (
    <PublicPageFrame>
      <Seo
        title="MeerkatAI | About"
        description="Learn what MeerkatAI does, who it is for, and how it supports construction safety teams with AI-assisted search and document generation."
        path="/about"
      />

      <div className="mx-auto w-full max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <section className="relative overflow-hidden rounded-[32px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-6 sm:p-10">
          <div className="absolute inset-0 opacity-70">
            <div className="absolute right-[-3rem] top-[-3rem] h-52 w-52 rounded-full bg-[#00E5FF]/10 blur-3xl" />
            <div className="absolute left-10 top-10 h-36 w-36 rounded-full bg-[#BF5AF2]/10 blur-3xl" />
          </div>
          <div className="relative space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]">
              <SparklesIcon className="h-4 w-4" />
              About MeerkatAI
            </div>
            <div className="max-w-3xl space-y-4">
              <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">
                AI-powered construction safety platform for practical field work.
              </h1>
              <p className="text-sm leading-7 text-[#C7C7CC] sm:text-base">
                MeerkatAI helps users search industrial safety regulations, review KOSHA Guide materials,
                and generate structured documents with less manual overhead.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                ['Service', 'Construction safety support'],
                ['Operator', 'ASEL (Individual Developer)'],
                ['Hosting', 'Vercel with custom domain readiness'],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-[#2C2C2E] bg-[#121212]/80 p-4">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-[#98989D]">{label}</p>
                  <p className="mt-2 text-sm font-medium text-white">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="mt-6 grid gap-6">
          <PageSection
            eyebrow="Purpose"
            title="Built to reduce the friction of safety information work."
            description="MeerkatAI is designed to help users find, organize, and apply construction safety information without losing time in fragmented documents or scattered references."
          >
            <div className="grid gap-4 md:grid-cols-2">
              {[
                'Support fast lookup of safety and legal references.',
                'Help users prepare drafts for field-oriented safety documents.',
                'Present KOSHA and legal materials in a more usable format.',
                'Keep the experience focused on clarity, reliability, and mobile usability.',
              ].map((item) => (
                <div key={item} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4 text-sm leading-6 text-[#C7C7CC]">
                  {item}
                </div>
              ))}
            </div>
          </PageSection>

          <PageSection
            eyebrow="Core Features"
            title="Core capabilities designed for practical daily use."
          >
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {features.map(({ title, description, icon: Icon }) => (
                <article key={title} className="rounded-2xl border border-[#2C2C2E] bg-[#121212] p-5">
                  <div className="mb-4 inline-flex rounded-xl border border-[#2C2C2E] bg-[#1E1E1E] p-2 text-[#00E5FF]">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-sm font-semibold text-white">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#98989D]">{description}</p>
                </article>
              ))}
            </div>
          </PageSection>

          <PageSection
            eyebrow="Roadmap"
            title="Future development remains centered on trust and maintainability."
          >
            <div className="grid gap-4 md:grid-cols-3">
              {[
                'Custom domain connection support.',
                'Continued SEO and performance improvements.',
                'AdSense-friendly layout and policy transparency.',
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
