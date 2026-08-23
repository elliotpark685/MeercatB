import { useEffect, useRef, useState } from "react";
import { getLawArticle, type ArticleDetail } from "../api/admin";
import ErrorBox from "./ErrorBox";
import Spinner from "./Spinner";

interface ArticleDetailPopoverProps {
  articleId: number;
  onClose: () => void;
}

export default function ArticleDetailPopover({ articleId, onClose }: ArticleDetailPopoverProps) {
  const [detail, setDetail] = useState<ArticleDetail | null>(null);
  const [error, setError] = useState<unknown>(null);
  const popoverRef = useRef<HTMLElement>(null);

  useEffect(() => {
    let active = true;
    setDetail(null);
    setError(null);
    getLawArticle(articleId)
      .then((response) => {
        if (active) setDetail(response);
      })
      .catch((requestError) => {
        if (active) setError(requestError);
      });
    return () => {
      active = false;
    };
  }, [articleId]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    function handlePointerDown(event: MouseEvent) {
      if (!popoverRef.current?.contains(event.target as Node)) onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [onClose]);

  const metadata = detail
    ? [
        detail.law_no ? `공포번호 ${detail.law_no}` : null,
        detail.promulgation_date ? `공포일 ${detail.promulgation_date}` : null,
        detail.document_effective_date ? `시행일 ${detail.document_effective_date}` : null,
        detail.amendment_type,
      ].filter(Boolean)
    : [];

  return (
    <section
      ref={popoverRef}
      role="dialog"
      aria-label="법령 전체 내용"
      className="absolute inset-x-0 top-full z-30 mt-2 overflow-hidden rounded-2xl border border-[#00E5FF]/30 bg-[#1E1E1E] shadow-2xl shadow-black/40"
    >
      <header className="flex items-start justify-between gap-3 border-b border-[#2C2C2E] px-4 py-3">
        <div className="min-w-0">
          {detail ? (
            <>
              <h4 className="text-sm font-semibold text-white">
                {detail.law_name} <span className="text-[#00E5FF]">{detail.article_no}</span>
                {detail.article_title ? ` ${detail.article_title}` : ""}
              </h4>
              {metadata.length > 0 && (
                <p className="mt-1 text-xs text-[#00E5FF]/80">{metadata.join(" · ")}</p>
              )}
            </>
          ) : (
            <h4 className="text-sm font-semibold text-white">전체 내용</h4>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg px-2 py-1 text-lg leading-none text-[#98989D] transition-colors hover:bg-[#2C2C2E] hover:text-white"
          aria-label="전체 내용 닫기"
        >
          ×
        </button>
      </header>
      <div className="max-h-[50vh] overflow-y-auto p-4">
        {!detail && !error && <Spinner text="전체 내용 불러오는 중..." />}
        {!!error && <ErrorBox error={error} />}
        {detail && (
          <pre className="whitespace-pre-wrap break-words rounded-xl border border-[#2C2C2E] bg-[#121212] p-4 font-sans text-sm leading-7 text-[#C7C7CC]">
            {detail.full_text}
          </pre>
        )}
      </div>
    </section>
  );
}
