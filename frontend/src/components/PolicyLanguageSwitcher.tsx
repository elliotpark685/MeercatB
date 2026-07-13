import { Link } from 'react-router-dom';

type PolicyLanguageSwitcherProps = {
  locale: 'en' | 'ko';
  englishPath: string;
  koreanPath: string;
};

export default function PolicyLanguageSwitcher({ locale, englishPath, koreanPath }: PolicyLanguageSwitcherProps) {
  return (
    <nav aria-label="Policy language" className="ml-auto inline-flex rounded-full border border-[#2C2C2E] bg-[#121212] p-1 text-xs">
      <Link
        to={englishPath}
        aria-current={locale === 'en' ? 'page' : undefined}
        className={`rounded-full px-3 py-1.5 transition-colors ${locale === 'en' ? 'bg-[#00E5FF]/15 text-[#00E5FF]' : 'text-[#98989D] hover:text-white'}`}
      >
        English
      </Link>
      <Link
        to={koreanPath}
        aria-current={locale === 'ko' ? 'page' : undefined}
        className={`rounded-full px-3 py-1.5 transition-colors ${locale === 'ko' ? 'bg-[#00E5FF]/15 text-[#00E5FF]' : 'text-[#98989D] hover:text-white'}`}
      >
        한국어
      </Link>
    </nav>
  );
}
