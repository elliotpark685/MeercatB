import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { registerUser } from "../api/auth";
import { AxiosError } from "axios";

const PASSWORD_MIN = 4;

function getErrorMessage(err: unknown): string {
  if (!(err instanceof AxiosError)) {
    return "서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인하세요.";
  }

  const status = err.response?.status;
  const detail = err.response?.data?.detail;

  if (status === 409) return "이미 가입된 이메일입니다.";
  if (status === 400) return "입력값을 다시 확인해주세요.";
  if (status === 422) {
    // detail이 배열인 경우 (FastAPI 유효성 오류)
    if (Array.isArray(detail)) {
      return detail.map((e) => e.msg).join(", ");
    }
    return "입력 형식을 확인해주세요.";
  }

  return `회원가입 실패: ${detail ?? err.message}`;
}

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const passwordValid = password.length >= PASSWORD_MIN;
  const canSubmit =
    email.trim() !== "" && fullName.trim() !== "" && passwordValid;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    setError("");
    try {
      const data = await registerUser({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
      });
      // 성공 시 바로 로그인 상태로 전환
      login(data);
      navigate("/", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Meerkat Safety</h1>
          <p className="text-slate-500 text-sm mt-1">신규 계정 등록</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 space-y-4"
        >
          {/* 이메일 */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              이메일
            </label>
            <input
              type="email"
              autoComplete="email"
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* 이름 */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              이름
            </label>
            <input
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="홍길동"
              className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* 비밀번호 */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm font-medium text-slate-700">
                비밀번호
              </label>
              {password.length > 0 && !passwordValid && (
                <span className="text-xs text-yellow-600">
                  {PASSWORD_MIN}자 이상 필요
                </span>
              )}
            </div>
            <input
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className={`w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                password.length > 0 && !passwordValid
                  ? "border-yellow-400"
                  : "border-slate-300"
              }`}
            />
          </div>

          {/* 에러 메시지 */}
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          {/* 제출 버튼 */}
          <button
            type="submit"
            disabled={loading || !canSubmit}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "가입 중..." : "회원가입"}
          </button>

          {/* 로그인 링크 */}
          <p className="text-center text-sm text-slate-500">
            이미 계정이 있으신가요?{" "}
            <Link
              to="/login"
              className="text-blue-600 hover:underline font-medium"
            >
              로그인
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
