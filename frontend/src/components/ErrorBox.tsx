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
    <div className="rounded-xl border border-[#FECACA] border-l-4 border-l-[#DC2626] bg-[#FEF2F2] p-4">
      <p className="font-semibold text-[#991B1B]">{msg}</p>
      {detail && (
        <pre className="mt-2 max-h-52 overflow-auto rounded-lg border border-[#FECACA] bg-white p-2 font-mono text-xs whitespace-pre-wrap text-[#991B1B]">
          {detail}
        </pre>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 text-sm text-[#DC2626] underline transition-colors hover:text-[#991B1B]"
        >
          다시 시도
        </button>
      )}
    </div>
  );
}
