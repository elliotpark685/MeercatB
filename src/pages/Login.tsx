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
        } else {
          setError(`로그인 실패: ${err.response?.data?.detail ?? err.message}`);
        }
      } else {
        setError("서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인하세요.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <img
            src="/meerkat.png"
            alt="Meerkat Logo"
            className="mx-auto h-50 w-50 rounded-full border-2 border-slate-500 object-cover bg-slate-800"
          />
          <h1 className="text-2xl font-bold text-slate-800">Meerkat Safety</h1>
          <p className="text-slate-500 text-sm mt-1">산업안전 관리 시스템</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 space-y-5"
        >
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              관리자 ID
            </label>
            <input
              type="text"
              autoComplete="username"
              autoFocus
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
              placeholder="admin.dev"
              className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              비밀번호
            </label>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !loginId.trim() || !password}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-5">
          계정이 없으신가요?{" "}
          <Link
            to="/register"
            className="text-blue-600 hover:underline font-medium"
          >
            회원가입
          </Link>
        </p>
        <p className="text-center text-xs text-slate-400 mt-3">
          개발 계정: <code className="font-mono">admin.dev / devpass1234</code>
        </p>
      </div>
    </div>
  );
}
