/**
 * AuthContext: JWT Bearer 기반 인증 컨텍스트
 *
 * 토큰 주입: client.ts의 request interceptor가 localStorage에서 자동으로 읽는다.
 * 이 파일은 토큰을 localStorage에 저장/삭제하는 역할만 담당한다.
 * 추후 토큰 갱신(refresh) 추가 시 이 파일만 수정하면 된다.
 *
 * STORAGE_KEY는 client.ts의 'meerkat_auth'와 동일해야 한다.
 */
import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { getMe, type LoginResponse } from '../api/auth';

export const STORAGE_KEY = 'meerkat_auth';

interface StoredAuth {
  access_token: string;
  user_id: number;
  site_id: number | null;
  role: string;
}

export interface AuthContextValue {
  accessToken: string | null;
  userId: number | null;
  siteId: number | null;
  role: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginResponse) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function loadStoredAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredAuth) : null;
  } catch {
    return null;
  }
}

function saveAuth(data: StoredAuth) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function removeAuth() {
  localStorage.removeItem(STORAGE_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<number | null>(null);
  const [siteId, setSiteId] = useState<number | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    // localStorage에서 삭제하면 request interceptor가 자동으로 토큰을 제외한다
    removeAuth();
    setAccessToken(null);
    setUserId(null);
    setSiteId(null);
    setRole(null);
  }, []);

  const login = useCallback((data: LoginResponse) => {
    const stored: StoredAuth = {
      access_token: data.access_token,
      user_id: data.user_id,
      site_id: data.site_id ?? null,
      role: data.role,
    };
    // localStorage에 저장하면 request interceptor가 자동으로 토큰을 주입한다
    saveAuth(stored);
    setAccessToken(data.access_token);
    setUserId(data.user_id);
    setSiteId(data.site_id ?? null);
    setRole(data.role);
  }, []);

  // 앱 시작 시 저장된 토큰으로 /auth/me 호출해 세션 복원
  useEffect(() => {
    const stored = loadStoredAuth();
    if (!stored) {
      setIsLoading(false);
      return;
    }
    // request interceptor가 localStorage에서 토큰을 읽으므로 별도 주입 불필요
    getMe()
      .then((me) => {
        setAccessToken(stored.access_token);
        setUserId(me.user_id);
        // 백엔드 /me 응답에 site_id 없음 → localStorage 저장값 fallback
        setSiteId(me.site_id ?? stored.site_id ?? null);
        setRole(me.role);
      })
      .catch(() => {
        // 토큰 만료 또는 무효 → localStorage에서 삭제
        removeAuth();
      })
      .finally(() => setIsLoading(false));
  }, []);

  // 401 이벤트(client.ts 응답 인터셉터)에서 자동 로그아웃
  useEffect(() => {
    const handler = () => logout();
    window.addEventListener('auth:unauthorized', handler);
    return () => window.removeEventListener('auth:unauthorized', handler);
  }, [logout]);

  const value: AuthContextValue = {
    accessToken,
    userId,
    siteId,
    role,
    isAuthenticated: !!accessToken,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
