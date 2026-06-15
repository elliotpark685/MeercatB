import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { loginUser } from "../api/auth";
import { AxiosError } from "axios";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!loginId.trim() || !password) return;

    setLoading(true);
    setError("");
    try {
      const data = await loginUser({ login_id: loginId.trim(), password });
      login(data);
      navigate("/", { replace: true });
    } catch (err) {
      if (err instanceof AxiosError) {
        const status = err.response?.status;
        if (status === 400) {
          setError("입력값을 다시 확인해주세요.");
        } else if (status === 401) {
          setError("ID 또는 비밀번호를 확인해 주세요.");
        } else if (status === 403) {
          setError("관리자 권한이 없는 계정입니다.");
        } else if (status === 422) {
          setError("입력 형식을 확인해주세요.");
        } else {
          const detail = err.response?.data?.detail;
          const msg = Array.isArray(detail)
            ? detail.map((d: { msg?: string }) => d.msg ?? "").join(", ")
            : typeof detail === "string"
              ? detail
              : err.message;
          setError(`로그인 실패: ${msg}`);
        }
      } else {
        setError("서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인하세요.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center">
      <div className="w-full max-w-sm px-4">
        {/* 로고 */}
        <div className="text-center mb-8">
          <div className="relative inline-block mb-4">
            <img
              src="/meerkat.png"
              alt="Meerkat Logo"
              className="mx-auto h-20 w-20 rounded-full border-2 border-[#2C2C2E] object-cover bg-[#1E1E1E]"
            />
            <span className="absolute bottom-0.5 right-0.5 w-3 h-3 bg-[#32D74B] rounded-full border-2 border-[#121212]" />
          </div>
          <h1 className="text-2xl font-semibold text-white">Meerkat Safety</h1>
          <p className="text-[#98989D] text-sm mt-1">산업안전 관리 시스템</p>
        </div>

        {/* 폼 */}
        <form
          onSubmit={handleSubmit}
          className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-8 space-y-5"
        >
          <div>
            <label className="block text-xs font-medium text-[#98989D] uppercase tracking-widest mb-2">
              관리자 ID
            </label>
            <input
              type="text"
              autoComplete="username"
              autoFocus
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
              placeholder="admin.dev"
              className="w-full bg-[#121212] border border-[#2C2C2E] rounded-lg px-3 py-2.5 text-sm text-white placeholder-[#3A3A3C] focus:outline-none focus:ring-2 focus:ring-[#00E5FF]/50 focus:border-[#00E5FF]/50 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[#98989D] uppercase tracking-widest mb-2">
              비밀번호
            </label>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-[#121212] border border-[#2C2C2E] rounded-lg px-3 py-2.5 text-sm text-white placeholder-[#3A3A3C] focus:outline-none focus:ring-2 focus:ring-[#00E5FF]/50 focus:border-[#00E5FF]/50 transition-all"
            />
          </div>

          {error && (
            <div className="bg-[#3A1C1C] border-l-4 border-[#FF453A] rounded-r-lg px-3 py-2.5">
              <p className="text-sm text-[#FF453A]">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !loginId.trim() || !password}
            className="w-full bg-[#00E5FF] text-[#121212] py-2.5 rounded-lg font-semibold text-sm hover:bg-[#33EAFF] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150"
          >
            {loading ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <p className="text-center text-sm text-[#98989D] mt-5">
          계정이 없으신가요?{" "}
          <Link
            to="/register"
            className="text-[#00E5FF] hover:underline font-medium"
          >
            회원가입
          </Link>
        </p>
        <p className="text-center text-xs text-[#3A3A3C] mt-3">
          개발 계정:{" "}
          <code className="font-mono text-[#98989D]">
            admin.dev / devpass****
          </code>
        </p>
      </div>
    </div>
  );
}
