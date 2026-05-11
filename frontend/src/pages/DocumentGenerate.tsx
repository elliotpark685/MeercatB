import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../contexts/AuthContext';
import { generateDocument, type GeneratedDocument, type DocumentType } from '../api/admin';
import Spinner from '../components/Spinner';
import ErrorBox from '../components/ErrorBox';

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

  const [docType, setDocType] = useState<DocumentType>('tbm');
  const [prompt, setPrompt] = useState('');
  // 로그인 시 받은 siteId가 있으면 초기값으로, 없으면 빈 문자열로 시작
  const [manualSiteId, setManualSiteId] = useState<string>(
    siteId != null ? String(siteId) : ''
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<GeneratedDocument | null>(null);

  // 최종 사용할 site_id: 로그인 값 우선, 없으면 수동 입력값
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
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">문서 생성</h1>

      <form onSubmit={handleGenerate} className="bg-white rounded-xl shadow-sm border border-slate-100 p-5 space-y-5">

        {/* Site ID — 로그인 값이 없을 때만 수동 입력 표시 */}
        {siteId == null && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <label className="block text-sm font-medium text-yellow-800 mb-1.5">
              Site ID <span className="font-normal text-yellow-700">(계정에 사이트 미배정 — 직접 입력)</span>
            </label>
            <input
              type="number"
              min={1}
              value={manualSiteId}
              onChange={(e) => setManualSiteId(e.target.value)}
              placeholder="예: 1"
              className="w-32 border border-yellow-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-400 bg-white"
            />
            <p className="text-xs text-yellow-600 mt-1.5">
              백엔드 DB에 존재하는 site_id를 입력하세요. 없는 값이면 404 오류가 반환됩니다.
            </p>
          </div>
        )}

        {/* 문서 유형 */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">문서 유형</label>
          <div className="grid grid-cols-2 gap-3">
            {DOC_TYPES.map((t) => (
              <label
                key={t.value}
                className={`flex items-start gap-3 border rounded-lg p-3 cursor-pointer transition-colors ${
                  docType === t.value ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <input
                  type="radio"
                  name="docType"
                  value={t.value}
                  checked={docType === t.value}
                  onChange={() => setDocType(t.value)}
                  className="mt-0.5 accent-blue-600"
                />
                <div>
                  <p className="text-sm font-medium text-slate-800">{t.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{t.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* 프롬프트 */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-slate-700">작성 지시사항</label>
            <span className={`text-xs ${
              promptLen > PROMPT_MAX ? 'text-red-500' :
              promptLen < PROMPT_MIN && promptLen > 0 ? 'text-yellow-600' :
              'text-slate-400'
            }`}>
              {promptLen} / {PROMPT_MAX}자
            </span>
          </div>
          <textarea
            rows={5}
            className={`w-full border rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y ${
              promptLen > 0 && !promptValid ? 'border-red-300' : 'border-slate-300'
            }`}
            placeholder={`예) 지하 배관 교체 작업에 대한 TBM 자료 작성. 작업 인원 5명, 오전 9시~오후 5시 (최소 ${PROMPT_MIN}자)`}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          {promptLen > 0 && promptLen < PROMPT_MIN && (
            <p className="text-xs text-yellow-600 mt-1">{PROMPT_MIN}자 이상 입력해 주세요.</p>
          )}
          {promptLen > PROMPT_MAX && (
            <p className="text-xs text-red-500 mt-1">{PROMPT_MAX}자를 초과했습니다.</p>
          )}
        </div>

        {/* 요청 정보 요약 */}
        <div className="text-xs text-slate-400 bg-slate-50 rounded px-3 py-2 flex flex-wrap gap-x-3 gap-y-1">
          <span>site_id: <code className="font-mono text-slate-600">{effectiveSiteId ?? '(미입력)'}</code></span>
          <span>user_id: <code className="font-mono text-slate-600">{userId ?? 'null'}</code></span>
          <span>document_type: <code className="font-mono text-slate-600">{docType}</code></span>
        </div>

        <button
          type="submit"
          disabled={loading || !canSubmit}
          className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '생성 중...' : '문서 생성'}
        </button>
      </form>

      {loading && <Spinner text="AI가 문서를 생성하고 있습니다..." />}
      {!!error && <ErrorBox error={error} />}

      {/* 생성 결과 */}
      {result && (
        <div className="bg-white rounded-xl shadow-sm border border-green-200 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-800 text-lg">{result.title}</h2>
            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">생성 완료</span>
          </div>

          {result.citations.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1.5">참조 법령</p>
              <div className="flex flex-wrap gap-2">
                {result.citations.map((c) => (
                  <span
                    key={c.article_id}
                    className="text-xs px-2 py-1 bg-blue-50 text-blue-700 border border-blue-100 rounded-full"
                  >
                    {c.law_name} {c.article_no}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="border-t border-slate-100 pt-4">
            <p className="text-xs font-medium text-slate-500 mb-3">문서 내용</p>
            <div className="prose prose-sm max-w-none bg-slate-50 rounded-lg p-4 max-h-[600px] overflow-auto
              [&_h1]:text-lg [&_h1]:font-bold [&_h1]:text-slate-800 [&_h1]:mb-2 [&_h1]:mt-4
              [&_h2]:text-base [&_h2]:font-semibold [&_h2]:text-slate-700 [&_h2]:mb-2 [&_h2]:mt-3
              [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:text-slate-700 [&_h3]:mb-1 [&_h3]:mt-2
              [&_p]:text-sm [&_p]:text-slate-700 [&_p]:leading-relaxed [&_p]:mb-2
              [&_ul]:text-sm [&_ul]:text-slate-700 [&_ul]:pl-5 [&_ul]:list-disc [&_ul]:mb-2
              [&_ol]:text-sm [&_ol]:text-slate-700 [&_ol]:pl-5 [&_ol]:list-decimal [&_ol]:mb-2
              [&_li]:mb-0.5
              [&_strong]:font-semibold [&_strong]:text-slate-800
              [&_hr]:border-slate-200 [&_hr]:my-3">
              <ReactMarkdown>{result.content}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
