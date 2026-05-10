import { AxiosError } from 'axios';

interface Props {
  error: unknown;
  onRetry?: () => void;
}

// FastAPI 422 detail 항목 형태
interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

function formatDetail(data: unknown): string {
  // 422: detail이 배열인 경우
  if (Array.isArray(data)) {
    return (data as ValidationError[])
      .map((e) => `${e.loc?.join(' → ') ?? ''}: ${e.msg}`)
      .join('\n');
  }
  // 그 외: 문자열 또는 객체
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

    // detail 필드 추출 (문자열 또는 배열 모두 처리)
    const detailField = responseData?.detail ?? responseData ?? error.message;
    detail = formatDetail(detailField);
  } else if (error instanceof Error) {
    msg = error.message;
  }

  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
      <p className="font-semibold text-red-700">{msg}</p>
      {detail && (
        <pre className="mt-2 text-xs text-red-600 overflow-auto max-h-52 bg-red-100 rounded p-2 whitespace-pre-wrap">
          {detail}
        </pre>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 text-sm text-red-700 underline hover:text-red-900"
        >
          다시 시도
        </button>
      )}
    </div>
  );
}
