/**
 * API 기본 클라이언트
 * 인증: Authorization: Bearer <access_token> (JWT)
 *
 * 토큰 주입: request interceptor가 매 요청마다 localStorage에서 읽어 주입한다.
 * - React 렌더링 타이밍과 무관하게 항상 최신 토큰을 사용할 수 있다.
 * - AuthContext에서 별도로 setAuthToken을 호출할 필요가 없다.
 *
 * 'meerkat_auth' 키는 AuthContext.tsx의 STORAGE_KEY와 동일해야 한다.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// localStorage에서 토큰을 읽는 내부 헬퍼
function getStoredToken(): string | null {
  try {
    const raw = localStorage.getItem('meerkat_auth');
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { access_token?: string };
    return parsed.access_token ?? null;
  } catch {
    return null;
  }
}

// 요청 인터셉터: 매 요청마다 토큰을 localStorage에서 읽어 헤더에 주입
apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 응답 인터셉터: 에러 로깅 + 401 시 자동 로그아웃 이벤트
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response) {
      console.error('[API Error]', err.response.status, err.response.data);
      if (err.response.status === 401) {
        // AuthContext의 logout과 중복을 피하기 위해 이벤트로 처리
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
      }
    } else {
      console.error('[API Error]', err.message);
    }
    return Promise.reject(err);
  }
);
