import type { ReactNode } from "react";

type SearchResultsSectionProps = {
  count: number;
  detail?: string;
  children: ReactNode;
};

export default function SearchResultsSection({
  count,
  detail,
  children,
}: SearchResultsSectionProps) {
  return (
    <section className="space-y-4 rounded-[28px] border border-[#2C2C2E] bg-[#1E1E1E] p-5 shadow-[0_8px_40px_rgba(0,0,0,0.14)] sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#2C2C2E] pb-4">
        <div>
          <p className="text-xs font-medium text-[#98989D]">검색 결과</p>
          <h2 className="mt-1 text-lg font-semibold text-white">총 {count}건</h2>
        </div>
        {detail && (
          <span className="rounded-full border border-[#3A3A3C] bg-[#121212] px-3 py-1.5 text-xs text-[#98989D]">
            {detail}
          </span>
        )}
      </div>
      {children}
    </section>
  );
}
