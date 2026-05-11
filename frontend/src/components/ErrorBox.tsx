import { AxiosError } from 'axios';

interface Props {
  error: unknown;
  onRetry?: () => void;
}

interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

function formatDetail(data: unknown): string {
  if (Array.isArray(data)) {
    return (data as ValidationError[])
      .map((e) => `${e.loc?.join(' → ') ?? ''}: ${e.msg}`)
      .join('\n');
  }
  if (typeof data === 'string') return data;
  return JSON.stringify(data, null, 2);
}

export default function ErrorBox({ error, onRetry }: Props) {
  let msg = '알 수 없는 오류가 발생했습니다.';
  let detail = '';

  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const responseData = error.response?.data;

    msg = `API Error (${status ?? 'Network'})`;

    if (status === 401) {
      msg += ' - 인증이 필요하거나 토큰이 만료되었습니다';
    } else if (status === 403) {
      msg += ' - 관리자 권한이 없습니다';
    } else if (status === 404) {
      msg += ' - 데이터를 찾을 수 없습니다';
    } else if (status === 422) {
      msg += ' - 입력값을 확인해 주세요';
    }

    const detailField = responseData?.detail ?? responseData ?? error.message;
    detail = formatDetail(detailField);
  } else if (error instanceof Error) {
    msg = error.message;
  }

  return (
    <div className="bg-[#3A1C1C] border-l-4 border-[#FF453A] rounded-r-xl p-4">
      <p className="font-semibold text-[#FF453A]">{msg}</p>
      {detail && (
        <pre className="mt-2 text-xs text-[#FF453A]/80 overflow-auto max-h-52 bg-[#121212] rounded-lg p-2 whitespace-pre-wrap font-mono border border-[#FF453A]/20">
          {detail}
        </pre>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 text-sm text-[#FF453A] hover:text-white underline transition-colors"
        >
          다시 시도
        </button>
      )}
    </div>
  );
}
