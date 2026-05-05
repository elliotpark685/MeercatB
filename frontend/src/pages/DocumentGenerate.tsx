import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { generateDocument, type GeneratedDocument, type DocumentType } from '../api/admin';
import Spinner from '../components/Spinner';
import ErrorBox from '../components/ErrorBox';

const DOC_TYPES: { value: DocumentType; label: string }[] = [
  { value: 'tbm', label: 'TBM' },
  { value: 'risk_assessment', label: 'Risk Assessment' },
  { value: 'work_plan', label: 'Work Plan' },
  { value: 'inspection_checklist', label: 'Inspection Checklist' },
];

export default function DocumentGenerate() {
  const { userId, siteId } = useAuth();

  const [docType, setDocType] = useState<DocumentType>('tbm');
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<GeneratedDocument | null>(null);

  const numericUserId = Number(userId);
  const numericSiteId = Number(siteId);
  const canSubmit = Number.isInteger(numericUserId) && Number.isInteger(numericSiteId) && !!prompt.trim();

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const doc = await generateDocument({
        site_id: numericSiteId,
        user_id: numericUserId,
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
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">문서 유형</label>
          <div className="grid grid-cols-2 gap-3">
            {DOC_TYPES.map((t) => (
              <label
                key={t.value}
                className={`flex items-center gap-3 border rounded-lg p-3 cursor-pointer ${
                  docType === t.value ? 'border-blue-500 bg-blue-50' : 'border-slate-200'
                }`}
              >
                <input
                  type="radio"
                  name="docType"
                  value={t.value}
                  checked={docType === t.value}
                  onChange={() => setDocType(t.value)}
                />
                <span className="text-sm font-medium text-slate-800">{t.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Prompt</label>
          <textarea
            rows={5}
            className="w-full border border-slate-300 rounded-lg px-4 py-3 text-sm"
            placeholder="고소작업 추락 방지 TBM 작성"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
        </div>

        <div className="text-xs text-slate-500 bg-slate-50 rounded px-3 py-2">
          user_id: <code>{userId || '(미설정)'}</code> / site_id: <code>{siteId || '(미설정)'}</code>
        </div>

        <button
          type="submit"
          disabled={loading || !canSubmit}
          className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '생성 중...' : '문서 생성'}
        </button>
      </form>

      {loading && <Spinner text="문서 생성 중..." />}
      {!!error && <ErrorBox error={error} />}

      {result && (
        <div className="bg-white rounded-xl shadow-sm border border-green-200 p-5 space-y-4">
          <h2 className="font-semibold text-slate-800">{result.title}</h2>
          {result.citations.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1.5">citations</p>
              <ul className="text-sm text-slate-700 list-disc pl-5">
                {result.citations.map((c) => (
                  <li key={c.article_id}>{c.law_name} {c.article_no}</li>
                ))}
              </ul>
            </div>
          )}
          <pre className="text-sm text-slate-700 whitespace-pre-wrap bg-slate-50 rounded-lg p-4 max-h-[500px] overflow-auto leading-relaxed font-sans">
            {result.content}
          </pre>
        </div>
      )}
    </div>
  );
}
