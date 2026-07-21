import { useEffect, useState } from "react";
import { getLawArticle, type ArticleDetail } from "../api/admin";
import ErrorBox from "./ErrorBox";
import Spinner from "./Spinner";

interface ArticleDetailModalProps {
  articleId: number;
  onClose: () => void;
}

/**
 * 검색 결과의 본문은 사용자가 요청할 때만 불러온다.
 * 법령과 안전기준은 동일한 article_id 저장소를 사용한다.
 */
export default function ArticleDetailModal({
  articleId,
  onClose,
}: ArticleDetailModalProps) {
  const [detail, setDetail] = useState<ArticleDetail | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    let active = true;

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

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const metadata = detail
    ? [
        detail.law_no ? `공포번호 ${detail.law_no}` : null,
        detail.promulgation_date ? `공포일 ${detail.promulgation_date}` : null,
        detail.document_effective_date
          ? `시행일 ${detail.document_effective_date}`
          : null,
        detail.amendment_type,
      ].filter(Boolean)
    : [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      role="presentation"
      onMouseDown={onClose}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-label="원문 상세 내용"
        className="flex max-h-[85vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-[#2C2C2E] bg-[#1E1E1E] shadow-2xl"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="flex items-start justify-between gap-4 border-b border-[#2C2C2E] px-5 py-4">
          <div className="min-w-0">
            {detail ? (
              <>
                <h2 className="text-base font-semibold text-white">
                  {detail.law_name}{" "}
                  <span className="text-[#00E5FF]">{detail.article_no}</span>
                  {detail.article_title ? ` ${detail.article_title}` : ""}
                </h2>
                {metadata.length > 0 && (
                  <p className="mt-1 text-xs text-[#00E5FF]/80">
                    {metadata.join(" · ")}
                  </p>
                )}
              </>
            ) : (
              <h2 className="text-base font-semibold text-white">전체 내용</h2>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-xl leading-none text-[#98989D] transition-colors hover:bg-[#2C2C2E] hover:text-white"
            aria-label="상세 내용 닫기"
          >
            ×
          </button>
        </header>

        <div className="min-h-32 overflow-y-auto p-5">
          {!detail && !error && <Spinner text="전체 내용 불러오는 중..." />}
          {!!error && <ErrorBox error={error} />}
          {detail && (
            <pre className="whitespace-pre-wrap break-words rounded-xl border border-[#2C2C2E] bg-[#121212] p-4 font-sans text-sm leading-7 text-[#C7C7CC]">
              {detail.full_text}
            </pre>
          )}
        </div>
      </section>
    </div>
  );
}
