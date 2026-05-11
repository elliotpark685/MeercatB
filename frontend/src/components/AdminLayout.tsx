import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "대시보드", icon: "🏠" },
  { to: "/laws", label: "법령 검색", icon: "⚖️" },
  { to: "/documents", label: "문서 생성", icon: "📄" },
];

const ROLE_LABEL: Record<string, string> = {
  admin: "관리자",
  user: "사용자",
};

export default function AdminLayout() {
  const { userId, siteId, role, logout } = useAuth();

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-800 text-white flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-slate-700 flex flex-col items-center gap-3">
          <img
            src="/meerkat.png"
            alt="Meerkat logo"
            className="w-16 h-16 rounded-full border-2 border-slate-500 object-cover bg-slate-700"
          />
          <div className="text-center">
            <div className="text-lg font-bold text-white">Meerkat Safety</div>
            <div className="text-xs text-slate-400 mt-0.5">산업안전 관리 시스템</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-slate-300 hover:bg-slate-700 hover:text-white"
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* 로그인 사용자 정보 */}
        <div className="px-4 py-4 border-t border-slate-700 space-y-2">
          <div className="text-xs text-slate-400 space-y-0.5">
            <p>
              <span className="text-slate-500">역할:</span>{" "}
              <span className="text-slate-300">
                {ROLE_LABEL[role ?? ""] ?? role ?? "-"}
              </span>
            </p>
            <p>
              <span className="text-slate-500">User ID:</span>{" "}
              <span className="text-slate-300 font-mono">{userId ?? "-"}</span>
            </p>
            <p>
              <span className="text-slate-500">Site ID:</span>{" "}
              <span className="text-slate-300 font-mono">{siteId ?? "-"}</span>
            </p>
          </div>
          <button
            onClick={logout}
            className="w-full text-xs text-slate-400 hover:text-white bg-slate-700 hover:bg-slate-600 rounded px-2 py-1.5 transition-colors text-left"
          >
            로그아웃
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
