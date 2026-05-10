import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { setAuthUserId } from '../api/client';

const ENV_USER_ID = import.meta.env.VITE_DEV_ADMIN_USER_ID as string | undefined;
const ENV_SITE_ID = import.meta.env.VITE_DEV_SITE_ID as string | undefined;

interface AuthContextValue {
  userId: string;
  siteId: string;
  setUserId: (id: string) => void;
  setSiteId: (id: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [userId, setUserIdState] = useState<string>(
    ENV_USER_ID ?? localStorage.getItem('adminUserId') ?? ''
  );
  const [siteId, setSiteIdState] = useState<string>(
    ENV_SITE_ID ?? localStorage.getItem('adminSiteId') ?? ''
  );

  useEffect(() => {
    if (userId) {
      setAuthUserId(userId);
      localStorage.setItem('adminUserId', userId);
    }
  }, [userId]);

  useEffect(() => {
    localStorage.setItem('adminSiteId', siteId);
  }, [siteId]);

  function setUserId(id: string) {
    setUserIdState(id.trim());
  }

  function setSiteId(id: string) {
    setSiteIdState(id.trim());
  }

  return (
    <AuthContext.Provider value={{ userId, siteId, setUserId, setSiteId }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
