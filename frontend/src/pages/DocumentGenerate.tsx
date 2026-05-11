import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../contexts/AuthContext';
import { generateDocument, type GeneratedDocument, type DocumentType } from '../api/admin';
import Spinner from '../components/Spinner';
import ErrorBox from '../components/ErrorBox';
import { useToast } from '../contexts/ToastContext';

const DOC_TYPES: { value: DocumentType; label: string; description: string }[] = [
  { value: 'tbm', label: 'TBM', description: '툴박스 미팅 안전교육' },
  { value: 'risk_assessment', label: '위험성 평가서', description: '작업 위험 요인 식별·평가' },
  { value: 'work_plan', label: '작업 계획서', description: '작업 절차 및 안전 계획' },
  { value: 'inspection_checklist', label: '점검 체크리스트', description: '안전 점검 항목 목록' },
];

const PROMPT_MIN = 5;
const PROMPT_MAX = 4000;

export default function DocumentGenerate() {
  const { userId, siteId } = useAuth();
  const { addToast } = useToast();

  const [docType, setDocType] = useState<DocumentType>('tbm');
  const [prompt, setPrompt] = useState('');
  const [manualSiteId, setManualSiteId] = useState<string>(
    siteId != null ? String(siteId) : ''
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<GeneratedDocument | null>(null);

  const effectiveSiteId: number | null = (() => {
    if (siteId != null) return siteId;
    const parsed = parseInt(manualSiteId, 10);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
  })();

  const promptLen = prompt.trim().length;
  const promptValid = promptLen >= PROMPT_MIN && promptLen <= PROMPT_MAX;
  const canSubmit = effectiveSiteId != null && promptValid;

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
        prompt: prompt.trim(),
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
      addToast('클립보드에 복사되었습니다.', 'success');
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
    addToast('파일 다운로드를 시작합니다.', 'info');
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">문서 생성</h1>

      <form onSubmit={handleGenerate} className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-5 space-y-5">

        {/* Site ID 수동 입력 */}
        {siteId == null && (
          <div className="bg-[#2A2200] border-l-4 border-[#F5A623] rounded-r-lg p-4">
            <label className="block text-xs font-medium text-[#F5A623] uppercase tracking-widest mb-2">
              Site ID <span className="font-normal text-[#C8892A] normal-case">(계정에 사이트 미배정 — 직접 입력)</span>
            </label>
            <input
              type="number"
              min={1}
              value={manualSiteId}
              onChange={(e) => setManualSiteId(e.target.value)}
              placeholder="예: 1"
              className="w-32 bg-[#121212] border border-[#3A2E00] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-[#F5A623]/40 transition-all"
            />
            <p className="text-xs text-[#C8892A] mt-1.5">
              백엔드 DB에 존재하는 site_id를 입력하세요. 없는 값이면 404 오류가 반환됩니다.
            </p>
          </div>
        )}

        {/* 문서 유형 */}
        <div>
          <label className="block text-xs font-medium text-[#98989D] uppercase tracking-widest mb-3">문서 유형</label>
          <div className="grid grid-cols-2 gap-3">
            {DOC_TYPES.map((t) => (
              <label
                key={t.value}
                className={`flex items-start gap-3 border rounded-xl p-3 cursor-pointer transition-all duration-150 ${
                  docType === t.value
                    ? 'border-[#00E5FF]/40 bg-[#00E5FF]/5'
                    : 'border-[#2C2C2E] hover:border-[#3A3A3C] bg-[#121212]'
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
                  <p className="text-xs text-[#98989D] mt-0.5">{t.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* 프롬프트 */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-medium text-[#98989D] uppercase tracking-widest">작성 지시사항</label>
            <span className={`text-xs font-mono ${
              promptLen > PROMPT_MAX ? 'text-[#FF453A]' :
              promptLen < PROMPT_MIN && promptLen > 0 ? 'text-[#F5A623]' :
              'text-[#98989D]'
            }`}>
              {promptLen} / {PROMPT_MAX}
            </span>
          </div>
          <textarea
            rows={5}
            className={`w-full bg-[#121212] border rounded-xl px-4 py-3 text-sm text-white placeholder-[#3A3A3C] focus:outline-none focus:ring-2 resize-y transition-all ${
              promptLen > 0 && !promptValid
                ? 'border-[#FF453A]/50 focus:ring-[#FF453A]/30'
                : 'border-[#2C2C2E] focus:ring-[#00E5FF]/50 focus:border-[#00E5FF]/50'
            }`}
            placeholder={`예) 지하 배관 교체 작업에 대한 TBM 자료 작성. 작업 인원 5명, 오전 9시~오후 5시 (최소 ${PROMPT_MIN}자)`}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          {promptLen > 0 && promptLen < PROMPT_MIN && (
            <p className="text-xs text-[#F5A623] mt-1">{PROMPT_MIN}자 이상 입력해 주세요.</p>
          )}
          {promptLen > PROMPT_MAX && (
            <p className="text-xs text-[#FF453A] mt-1">{PROMPT_MAX}자를 초과했습니다.</p>
          )}
        </div>

        {/* 요청 정보 요약 */}
        <div className="text-xs text-[#98989D] bg-[#121212] rounded-lg px-3 py-2 flex flex-wrap gap-x-4 gap-y-1 border border-[#2C2C2E] font-mono">
          <span>site_id: <span className="text-white">{effectiveSiteId ?? '(미입력)'}</span></span>
          <span>user_id: <span className="text-white">{userId ?? 'null'}</span></span>
          <span>document_type: <span className="text-[#00E5FF]">{docType}</span></span>
        </div>

        <button
          type="submit"
          disabled={loading || !canSubmit}
          className="w-full bg-[#00E5FF] text-[#121212] py-2.5 rounded-lg font-semibold text-sm hover:bg-[#33EAFF] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150"
        >
          {loading ? '생성 중...' : '문서 생성'}
        </button>
      </form>

      {loading && <Spinner text="AI가 문서를 생성하고 있습니다..." />}
      {!!error && <ErrorBox error={error} />}

      {/* 생성 결과 */}
      {result && (
        <div className="bg-[#1E1E1E] rounded-2xl border border-[#32D74B]/30 p-5 space-y-4">
          {/* 헤더 */}
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-semibold text-white text-lg truncate">{result.title}</h2>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs bg-[#32D74B]/10 text-[#32D74B] border border-[#32D74B]/20 px-2.5 py-1 rounded-full">
                생성 완료
              </span>
              {/* 복사 버튼 */}
              <button
                onClick={handleCopy}
                className="text-xs text-[#98989D] hover:text-[#00E5FF] border border-[#2C2C2E] hover:border-[#00E5FF]/40 rounded-lg px-2.5 py-1 transition-all duration-150 flex items-center gap-1"
                title="클립보드에 복사"
              >
                ⎘ 복사
              </button>
              {/* 다운로드 버튼 */}
              <button
                onClick={handleDownload}
                className="text-xs text-[#98989D] hover:text-[#32D74B] border border-[#2C2C2E] hover:border-[#32D74B]/40 rounded-lg px-2.5 py-1 transition-all duration-150 flex items-center gap-1"
                title=".md 파일 다운로드"
              >
                ↓ 저장
              </button>
            </div>
          </div>

          {/* 참조 법령 */}
          {result.citations.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[#98989D] uppercase tracking-widest mb-2">참조 법령</p>
              <div className="flex flex-wrap gap-2">
                {result.citations.map((c) => (
                  <span
                    key={c.article_id}
                    className="text-xs px-2.5 py-1 bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/20 rounded-full"
                  >
                    {c.law_name} {c.article_no}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 문서 내용 */}
          <div className="border-t border-[#2C2C2E] pt-4">
            <p className="text-xs font-medium text-[#98989D] uppercase tracking-widest mb-3">문서 내용</p>
            <div className="bg-[#121212] rounded-xl border border-[#2C2C2E] p-4 max-h-[600px] overflow-auto
              [&_h1]:text-lg [&_h1]:font-bold [&_h1]:text-white [&_h1]:mb-2 [&_h1]:mt-4
              [&_h2]:text-base [&_h2]:font-semibold [&_h2]:text-[#00E5FF] [&_h2]:mb-2 [&_h2]:mt-3
              [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:text-white [&_h3]:mb-1 [&_h3]:mt-2
              [&_p]:text-sm [&_p]:text-[#98989D] [&_p]:leading-relaxed [&_p]:mb-2
              [&_ul]:text-sm [&_ul]:text-[#98989D] [&_ul]:pl-5 [&_ul]:list-disc [&_ul]:mb-2
              [&_ol]:text-sm [&_ol]:text-[#98989D] [&_ol]:pl-5 [&_ol]:list-decimal [&_ol]:mb-2
              [&_li]:mb-0.5
              [&_strong]:font-semibold [&_strong]:text-white
              [&_hr]:border-[#2C2C2E] [&_hr]:my-3">
              <ReactMarkdown>{result.content}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
