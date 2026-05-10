import { NavLink, Outlet } from 'react-router-dom';
import UserIdBar from './UserIdBar';

const NAV_ITEMS = [
  { to: '/', label: '대시보드', icon: '🏠' },
  { to: '/laws', label: '법령 검색', icon: '⚖️' },
  { to: '/documents', label: '문서 생성', icon: '📄' },
];

export default function AdminLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <UserIdBar />

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-56 bg-slate-800 text-white flex flex-col shrink-0">
          <div className="px-5 py-5 border-b border-slate-700">
            <div className="text-lg font-bold text-white">Meerkat Admin</div>
            <div className="text-xs text-slate-400 mt-0.5">산업안전 관리 시스템</div>
          </div>
          <nav className="flex-1 px-3 py-4 space-y-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`
                }
              >
                <span>{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="px-4 py-3 border-t border-slate-700 text-xs text-slate-500">
            MVP v0.1 · X-User-Id 인증
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
