import { useEffect } from 'react';

declare global {
  interface Window {
    adsbygoogle?: unknown[];
  }
}

type AdSenseSlotProps = {
  slot?: string;
  className?: string;
};

const ADSENSE_CLIENT = import.meta.env.VITE_ADSENSE_CLIENT as string | undefined;
const ADSENSE_SLOT = import.meta.env.VITE_ADSENSE_SLOT as string | undefined;
const ADSENSE_SCRIPT_ID = 'adsense-script';

function ensureAdSenseScript() {
  if (!ADSENSE_CLIENT || document.getElementById(ADSENSE_SCRIPT_ID)) return;

  const script = document.createElement('script');
  script.id = ADSENSE_SCRIPT_ID;
  script.async = true;
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(
    ADSENSE_CLIENT,
  )}`;
  script.crossOrigin = 'anonymous';
  document.head.appendChild(script);
}

export default function AdSenseSlot({ slot, className }: AdSenseSlotProps) {
  useEffect(() => {
    if (!ADSENSE_CLIENT) return;

    ensureAdSenseScript();

    try {
      window.adsbygoogle = window.adsbygoogle ?? [];
      window.adsbygoogle.push({});
    } catch {
      // AdSense may no-op during local development or before the script finishes loading.
    }
  }, []);

  if (!ADSENSE_CLIENT || !ADSENSE_SLOT && !slot) {
    return (
      <div
        className={`rounded-[24px] border border-dashed border-[#2C2C2E] bg-[#121212] px-4 py-5 text-center text-xs text-[#3A3A3C] ${className ?? ''}`}
      >
        AdSense placement reserved
      </div>
    );
  }

  return (
    <div className={className}>
      <ins
        className="adsbygoogle block"
        style={{ display: 'block' }}
        data-ad-client={ADSENSE_CLIENT}
        data-ad-slot={slot ?? ADSENSE_SLOT}
        data-ad-format="auto"
        data-full-width-responsive="true"
      />
    </div>
  );
}
