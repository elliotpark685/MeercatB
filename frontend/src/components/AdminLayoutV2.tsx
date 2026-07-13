import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import SiteFooter from './SiteFooter';

type NavItem = {
  to: string;
  label: string;
  icon: string;
};

const BASE_NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: '통합검색', icon: '⌕' },
  { to: '/laws', label: '법령 검색', icon: '⚖' },
  { to: '/safety-standards', label: '안전기준 검색', icon: '⛑' },
  { to: '/kosha-guide', label: 'KOSHA GUIDE', icon: '✦' },
  { to: '/documents', label: '문서 생성', icon: '✎' },
];

const ROLE_LABEL: Record<string, string> = {
  admin: '관리자',
  user: '사용자',
};

export default function AdminLayoutV2() {
  const { userId, siteId, role, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navItems: NavItem[] =
    role === 'admin'
      ? [...BASE_NAV_ITEMS, { to: '/admin', label: '관리자 대시보드', icon: '▣' }]
      : BASE_NAV_ITEMS;

  return (
    <div className="min-h-screen flex bg-[#121212]">
      <aside
        className={`sidebar-transition bg-[#1E1E1E] border-r border-[#2C2C2E] flex flex-col shrink-0 ${
          collapsed ? 'w-14' : 'w-60'
        }`}
      >
        <div className={`border-b border-[#2C2C2E] flex flex-col items-center gap-3 ${collapsed ? 'px-2 py-4' : 'px-5 py-6'}`}>
          <div className="relative">
            <img
              src="/meerkat.png"
              alt="Meerkat logo"
              className={`rounded-full border-2 border-[#2C2C2E] object-cover bg-[#121212] ${collapsed ? 'w-9 h-9' : 'w-16 h-16'}`}
            />
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-[#32D74B] rounded-full border-2 border-[#1E1E1E]" />
          </div>
          {!collapsed && (
            <div className="text-center">
              <div className="text-base font-semibold text-white tracking-wide">Meerkat Safety</div>
              <div className="text-xs text-[#98989D] mt-0.5">산업안전 통합 관리 시스템</div>
            </div>
          )}
        </div>

        <nav className="flex-1 px-2 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/dashboard'}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center rounded-lg transition-all duration-150 ${
                  collapsed ? 'justify-center px-2 py-2.5' : 'gap-3 px-3 py-2.5'
                } ${
                  isActive
                    ? 'bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/20'
                    : 'text-[#98989D] hover:bg-[#252525] hover:text-white border border-transparent'
                }`
              }
            >
              <span className="text-base leading-none shrink-0">{item.icon}</span>
              {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className={`border-t border-[#2C2C2E] ${collapsed ? 'p-2' : 'px-4 py-4'} space-y-2`}>
          {!collapsed && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-widest text-[#98989D]">계정 정보</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#00E5FF]/10 text-[#00E5FF] font-medium">
                  {ROLE_LABEL[role ?? ''] ?? role ?? '-'}
                </span>
              </div>
              <div className="text-xs text-[#98989D] space-y-0.5 pt-1">
                <p>
                  <span className="text-[#3A3A3C]">UID</span>{' '}
                  <span className="font-mono">{userId ?? '-'}</span>
                </p>
                <p>
                  <span className="text-[#3A3A3C]">SID</span>{' '}
                  <span className="font-mono">{siteId ?? '-'}</span>
                </p>
              </div>
            </div>
          )}
          <button
            onClick={logout}
            title={collapsed ? '로그아웃' : undefined}
            className={`w-full text-xs text-[#98989D] hover:text-[#FF453A] bg-[#2C2C2E] hover:bg-[#3A1C1C] border border-transparent hover:border-[#FF453A]/30 rounded-lg transition-all duration-150 ${
              collapsed ? 'px-2 py-2 flex justify-center' : 'px-3 py-2 text-left'
            }`}
          >
            {collapsed ? '↩' : '로그아웃'}
          </button>

          <button
            onClick={() => setCollapsed((v) => !v)}
            className="w-full text-xs text-[#3A3A3C] hover:text-[#98989D] rounded-lg px-2 py-1.5 transition-colors flex items-center justify-center"
            title={collapsed ? '사이드바 펼치기' : '사이드바 접기'}
          >
            {collapsed ? '⟩' : '접기'}
          </button>
        </div>
      </aside>

      <main key={location.pathname} className="page-enter flex-1 overflow-auto flex flex-col">
        <div className="flex-1 p-6">
          <Outlet />
        </div>
        <SiteFooter />
      </main>
    </div>
  );
}
