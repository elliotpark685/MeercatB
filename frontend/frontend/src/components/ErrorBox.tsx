import { AxiosError } from 'axios';

interface Props {
  error: unknown;
  onRetry?: () => void;
}

export default function ErrorBox({ error, onRetry }: Props) {
  let msg = '알 수 없는 오류가 발생했습니다.';
  let detail = '';

  if (error instanceof AxiosError) {
    const status = error.response?.status;
    msg = `API Error (${status ?? 'Network'})`;

    if (status === 401 || status === 403) {
      msg += ' - X-User-Id가 없거나 admin 권한이 아닙니다';
    } else if (status === 404) {
      msg += ' - 데이터가 없거나 id가 잘못되었습니다';
    }

    detail = JSON.stringify(error.response?.data ?? error.message, null, 2);
  } else if (error instanceof Error) {
    msg = error.message;
  }

  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
      <p className="font-semibold text-red-700">{msg}</p>
      {detail && (
        <pre className="mt-2 text-xs text-red-600 overflow-auto max-h-52 bg-red-100 rounded p-2">
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
