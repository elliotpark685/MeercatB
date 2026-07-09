import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../contexts/AuthContext';
import { generateDocument, KOSHA_CATEGORY_LABEL, type DocumentType, type GeneratedDocument, type KoshaCategory } from '../api/admin';
import { LAW_SCOPE_OPTIONS } from '../types/law';
import Spinner from '../components/Spinner';
import ErrorBox from '../components/ErrorBox';
import { useToast } from '../contexts/ToastContext';

const DOC_TYPES: { value: DocumentType; label: string; description: string }[] = [
  { value: 'tbm', label: 'TBM', description: '작업 전 안전 미팅 자료' },
  { value: 'risk_assessment', label: '위험성평가', description: '작업 위험 요인 분석 및 평가' },
  { value: 'work_plan', label: '작업 계획서', description: '작업 절차와 안전 계획' },
  { value: 'inspection_checklist', label: '점검 체크리스트', description: '안전 점검 항목 목록' },
];

const KOSHA_CATEGORY_OPTIONS: { value: KoshaCategory; label: string }[] = [
  { value: '0', label: KOSHA_CATEGORY_LABEL['0'] },
  { value: '4', label: KOSHA_CATEGORY_LABEL['4'] },
  { value: '5', label: KOSHA_CATEGORY_LABEL['5'] },
  { value: '6', label: KOSHA_CATEGORY_LABEL['6'] },
  { value: '7', label: KOSHA_CATEGORY_LABEL['7'] },
];

const TITLE_MIN = 2;
const TITLE_MAX = 120;
const DETAILS_MAX = 4000;

function normalizeList(text: string): string[] {
  return Array.from(
    new Set(
      text
        .split(/[\n,]/)
        .map((value) => value.trim())
        .filter(Boolean),
    ),
  );
}

function toggleValue<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

export default function DocumentGenerate() {
  const { userId, siteId } = useAuth();
  const { addToast } = useToast();

  const [docType, setDocType] = useState<DocumentType>('tbm');
  const [workTitle, setWorkTitle] = useState('');
  const [safetyKeywordText, setSafetyKeywordText] = useState('');
  const [selectedLawNames, setSelectedLawNames] = useState<string[]>([]);
  const [selectedKoshaCategories, setSelectedKoshaCategories] = useState<KoshaCategory[]>([]);
  const [details, setDetails] = useState('');
  const [manualSiteId, setManualSiteId] = useState<string>(siteId != null ? String(siteId) : '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<GeneratedDocument | null>(null);

  const effectiveSiteId: number | null = (() => {
    if (siteId != null) return siteId;
    const parsed = Number.parseInt(manualSiteId, 10);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
  })();

  const normalizedTitle = workTitle.trim();
  const safetyKeywords = normalizeList(safetyKeywordText);
  const detailsText = details.trim();
  const titleValid = normalizedTitle.length >= TITLE_MIN && normalizedTitle.length <= TITLE_MAX;
  const keywordsValid = safetyKeywords.length > 0;
  const canSubmit = effectiveSiteId != null && titleValid && keywordsValid;

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || effectiveSiteId == null) return;

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const doc = await generateDocument({
        site_id: effectiveSiteId,
        user_id: userId,
        document_type: docType,
        work_title: normalizedTitle,
        safety_keywords: safetyKeywords,
        law_names: selectedLawNames,
        kosha_categories: selectedKoshaCategories,
        prompt: detailsText,
      });
      setResult(doc);
      addToast('문서가 성공적으로 생성되었습니다.', 'success');
    } catch (e) {
      setError(e);
      addToast('문서 생성에 실패했습니다.', 'error');
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.content);
      addToast('클립보드에 복사했습니다.', 'success');
    } catch {
      addToast('복사에 실패했습니다.', 'error');
    }
  }

  function handleDownload() {
    if (!result) return;
    const blob = new Blob([result.content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.title.replace(/\s+/g, '_')}.md`;
    a.click();
    URL.revokeObjectURL(url);
    addToast('파일 다운로드를 시작했습니다.', 'info');
  }

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-[#2C2C2E] bg-gradient-to-br from-[#1E1E1E] via-[#171717] to-[#121212] p-5 sm:p-6">
        <div className="space-y-2">
          <span className="inline-flex rounded-full border border-[#00E5FF]/25 bg-[#00E5FF]/10 px-3 py-1 text-xs font-medium text-[#00E5FF]">
            문서 생성
          </span>
          <h1 className="text-2xl font-semibold text-white sm:text-3xl">작업명과 안전 키워드로 문서 생성</h1>
          <p className="max-w-3xl text-sm leading-6 text-[#98989D]">
            작업 제목을 기준으로 문서 구조를 만들고, 안전 키워드와 선택한 법령·KOSHA 범위를 LLM에 함께 전달합니다.
          </p>
        </div>
      </section>

      <form onSubmit={handleGenerate} className="space-y-5 rounded-[28px] border border-[#2C2C2E] bg-[#1E1E1E] p-5">
        {siteId == null && (
          <div className="rounded-2xl border border-[#3A2E00] bg-[#2A2200] p-4">
            <label className="mb-2 block text-xs font-medium uppercase tracking-widest text-[#F5A623]">
              Site ID
            </label>
            <input
              type="number"
              min={1}
              value={manualSiteId}
              onChange={(e) => setManualSiteId(e.target.value)}
              placeholder="예: 1"
              className="w-36 rounded-lg border border-[#3A2E00] bg-[#121212] px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-[#F5A623]/40"
            />
            <p className="mt-2 text-xs text-[#C8892A]">
              로그인 site_id가 없으면 여기서 현장 ID를 지정해야 합니다.
            </p>
          </div>
        )}

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-2">
            <label className="block text-xs font-medium uppercase tracking-widest text-[#98989D]">
              작업명
            </label>
            <input
              type="text"
              value={workTitle}
              onChange={(e) => setWorkTitle(e.target.value)}
              placeholder="예: 3층 A구역 미장공사"
              className={`w-full rounded-2xl border bg-[#121212] px-4 py-3 text-sm text-white outline-none transition focus:ring-2 ${
                workTitle && !titleValid
                  ? 'border-[#FF453A]/50 focus:ring-[#FF453A]/30'
                  : 'border-[#2C2C2E] focus:border-[#00E5FF]/50 focus:ring-[#00E5FF]/30'
              }`}
            />
            <p className="text-xs text-[#98989D]">문서 제목과 LLM의 중심 맥락으로 사용됩니다.</p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-medium uppercase tracking-widest text-[#98989D]">
                안전 키워드
              </label>
              <span className="text-xs text-[#98989D]">쉼표 또는 줄바꿈으로 구분</span>
            </div>
            <textarea
              rows={3}
              value={safetyKeywordText}
              onChange={(e) => setSafetyKeywordText(e.target.value)}
              placeholder="예: 추락, 낙하, 비계, 보호구"
              className={`w-full rounded-2xl border bg-[#121212] px-4 py-3 text-sm text-white outline-none transition focus:ring-2 ${
                safetyKeywords.length === 0 && safetyKeywordText.trim().length > 0
                  ? 'border-[#FF453A]/50 focus:ring-[#FF453A]/30'
                  : 'border-[#2C2C2E] focus:border-[#00E5FF]/50 focus:ring-[#00E5FF]/30'
              }`}
            />
            <p className="text-xs text-[#98989D]">
              {safetyKeywords.length > 0 ? `${safetyKeywords.length}개 키워드가 입력되었습니다.` : '최소 1개 이상 입력하세요.'}
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <label className="block text-xs font-medium uppercase tracking-widest text-[#98989D]">
                관련 법령 / 기준 선택
              </label>
              <p className="mt-1 text-xs text-[#98989D]">선택한 범위만 법령 검색과 문서 생성에 반영됩니다.</p>
            </div>
            <button
              type="button"
              onClick={() => setSelectedLawNames([])}
              className="rounded-full border border-[#2C2C2E] px-3 py-1 text-xs text-[#98989D] transition hover:border-[#3A3A3C] hover:text-white"
            >
              선택 해제
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {LAW_SCOPE_OPTIONS.map((lawName) => {
              const active = selectedLawNames.includes(lawName);
              return (
                <button
                  key={lawName}
                  type="button"
                  onClick={() => setSelectedLawNames((prev) => toggleValue(prev, lawName))}
                  className={`rounded-full border px-4 py-2 text-sm transition ${
                    active
                      ? 'border-transparent bg-[#00E5FF] text-[#121212]'
                      : 'border-[#2C2C2E] bg-[#121212] text-[#98989D] hover:border-[#3A3A3C] hover:text-white'
                  }`}
                >
                  {lawName}
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium uppercase tracking-widest text-[#98989D]">
              KOSHA Guide 선택
            </label>
            <p className="mt-1 text-xs text-[#98989D]">문서에 참고할 KOSHA 분류를 선택하세요.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {KOSHA_CATEGORY_OPTIONS.map((option) => {
              const active = selectedKoshaCategories.includes(option.value);
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setSelectedKoshaCategories((prev) => toggleValue(prev, option.value))}
                  className={`rounded-full border px-4 py-2 text-sm transition ${
                    active
                      ? 'border-transparent bg-[#32D74B] text-[#121212]'
                      : 'border-[#2C2C2E] bg-[#121212] text-[#98989D] hover:border-[#3A3A3C] hover:text-white'
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-medium uppercase tracking-widest text-[#98989D]">
              작업 세부 설명
            </label>
            <span className="text-xs font-mono text-[#98989D]">{detailsText.length} / {DETAILS_MAX}</span>
          </div>
          <textarea
            rows={5}
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            placeholder="예: 3층 A구역 미장공사, 자재 반입 동선, 작업 인원 4명, 고소 작업 포함"
            className="w-full resize-y rounded-2xl border border-[#2C2C2E] bg-[#121212] px-4 py-3 text-sm text-white outline-none transition focus:border-[#00E5FF]/50 focus:ring-2 focus:ring-[#00E5FF]/30"
          />
        </div>

        <div className="rounded-2xl border border-[#2C2C2E] bg-[#121212] px-4 py-3 text-xs text-[#98989D]">
          <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono">
            <span>site_id: <span className="text-white">{effectiveSiteId ?? '(미입력)'}</span></span>
            <span>user_id: <span className="text-white">{userId ?? 'null'}</span></span>
            <span>document_type: <span className="text-[#00E5FF]">{docType}</span></span>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium uppercase tracking-widest text-[#98989D] mb-3">
            문서 종류
          </label>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {DOC_TYPES.map((t) => (
              <label
                key={t.value}
                className={`flex cursor-pointer items-start gap-3 rounded-2xl border p-4 transition ${
                  docType === t.value
                    ? 'border-[#00E5FF]/40 bg-[#00E5FF]/5'
                    : 'border-[#2C2C2E] bg-[#121212] hover:border-[#3A3A3C]'
                }`}
              >
                <input
                  type="radio"
                  name="docType"
                  value={t.value}
                  checked={docType === t.value}
                  onChange={() => setDocType(t.value)}
                  className="mt-0.5 accent-[#00E5FF]"
                />
                <div>
                  <p className={`text-sm font-medium ${docType === t.value ? 'text-[#00E5FF]' : 'text-white'}`}>
                    {t.label}
                  </p>
                  <p className="mt-1 text-xs text-[#98989D]">{t.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !canSubmit}
          className="w-full rounded-2xl bg-[#00E5FF] py-3 text-sm font-semibold text-[#121212] transition hover:bg-[#33EAFF] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? '생성 중...' : '문서 생성'}
        </button>
      </form>

      {loading && <Spinner text="AI가 문서를 생성하고 있습니다..." />}
      {!!error && <ErrorBox error={error} />}

      {result && (
        <div className="space-y-4 rounded-[28px] border border-[#32D74B]/30 bg-[#1E1E1E] p-5">
          <div className="flex items-center justify-between gap-3">
            <h2 className="truncate text-lg font-semibold text-white">{result.title}</h2>
            <div className="flex shrink-0 items-center gap-2">
              <span className="rounded-full border border-[#32D74B]/20 bg-[#32D74B]/10 px-2.5 py-1 text-xs text-[#32D74B]">
                생성 완료
              </span>
              <button
                type="button"
                onClick={handleCopy}
                className="rounded-lg border border-[#2C2C2E] px-2.5 py-1 text-xs text-[#98989D] transition hover:border-[#00E5FF]/40 hover:text-[#00E5FF]"
              >
                복사
              </button>
              <button
                type="button"
                onClick={handleDownload}
                className="rounded-lg border border-[#2C2C2E] px-2.5 py-1 text-xs text-[#98989D] transition hover:border-[#32D74B]/40 hover:text-[#32D74B]"
              >
                다운로드
              </button>
            </div>
          </div>

          {result.citations.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-widest text-[#98989D]">참고 법령</p>
              <div className="flex flex-wrap gap-2">
                {result.citations.map((citation) => (
                  <span
                    key={citation.article_id}
                    className="rounded-full border border-[#00E5FF]/20 bg-[#00E5FF]/10 px-2.5 py-1 text-xs text-[#00E5FF]"
                  >
                    {citation.law_name} {citation.article_no}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="border-t border-[#2C2C2E] pt-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-widest text-[#98989D]">문서 내용</p>
            <div className="max-h-[600px] overflow-auto rounded-2xl border border-[#2C2C2E] bg-[#121212] p-4
              [&_h1]:mb-2 [&_h1]:mt-4 [&_h1]:text-lg [&_h1]:font-bold [&_h1]:text-white
              [&_h2]:mb-2 [&_h2]:mt-3 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:text-[#00E5FF]
              [&_h3]:mb-1 [&_h3]:mt-2 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:text-white
              [&_p]:mb-2 [&_p]:text-sm [&_p]:leading-relaxed [&_p]:text-[#98989D]
              [&_ul]:mb-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:text-sm [&_ul]:text-[#98989D]
              [&_ol]:mb-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:text-sm [&_ol]:text-[#98989D]
              [&_li]:mb-0.5
              [&_strong]:font-semibold [&_strong]:text-white
              [&_hr]:my-3 [&_hr]:border-[#2C2C2E]">
              <ReactMarkdown>{result.content}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
