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
      login(data);
      navigate("/", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center">
      <div className="w-full max-w-sm px-4">
        {/* 헤더 */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold text-white">Meerkat Safety</h1>
          <p className="text-[#98989D] text-sm mt-1">신규 계정 등록</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-8 space-y-4"
        >
          {/* 이메일 */}
          <div>
            <label className="block text-xs font-medium text-[#98989D] uppercase tracking-widest mb-2">
              이메일
            </label>
            <input
              type="email"
              autoComplete="email"
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              className="w-full bg-[#121212] border border-[#2C2C2E] rounded-lg px-3 py-2.5 text-sm text-white placeholder-[#3A3A3C] focus:outline-none focus:ring-2 focus:ring-[#00E5FF]/50 focus:border-[#00E5FF]/50 transition-all"
            />
          </div>

          {/* 이름 */}
          <div>
            <label className="block text-xs font-medium text-[#98989D] uppercase tracking-widest mb-2">
              이름
            </label>
            <input
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="홍길동"
              className="w-full bg-[#121212] border border-[#2C2C2E] rounded-lg px-3 py-2.5 text-sm text-white placeholder-[#3A3A3C] focus:outline-none focus:ring-2 focus:ring-[#00E5FF]/50 focus:border-[#00E5FF]/50 transition-all"
            />
          </div>

          {/* 비밀번호 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-[#98989D] uppercase tracking-widest">
                비밀번호
              </label>
              {password.length > 0 && !passwordValid && (
                <span className="text-xs text-[#FF453A]">
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
              className={`w-full bg-[#121212] rounded-lg px-3 py-2.5 text-sm text-white placeholder-[#3A3A3C] focus:outline-none focus:ring-2 transition-all border ${
                password.length > 0 && !passwordValid
                  ? "border-[#FF453A]/50 focus:ring-[#FF453A]/30"
                  : "border-[#2C2C2E] focus:ring-[#00E5FF]/50 focus:border-[#00E5FF]/50"
              }`}
            />
          </div>

          {/* 에러 메시지 */}
          {error && (
            <div className="bg-[#3A1C1C] border-l-4 border-[#FF453A] rounded-r-lg px-3 py-2.5">
              <p className="text-sm text-[#FF453A]">{error}</p>
            </div>
          )}

          {/* 제출 버튼 */}
          <button
            type="submit"
            disabled={loading || !canSubmit}
            className="w-full bg-[#00E5FF] text-[#121212] py-2.5 rounded-lg font-semibold text-sm hover:bg-[#33EAFF] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150"
          >
            {loading ? "가입 중..." : "회원가입"}
          </button>

          {/* 로그인 링크 */}
          <p className="text-center text-sm text-[#98989D]">
            이미 계정이 있으신가요?{" "}
            <Link to="/login" className="text-[#00E5FF] hover:underline font-medium">
              로그인
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
