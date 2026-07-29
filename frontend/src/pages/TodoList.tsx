import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import {
  createTodo,
  deleteTodo,
  getTodos,
  updateTodo,
  type Todo,
} from "../api/todos";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];
function dateKey(value: Date) {
  return new Date(value.getTime() - value.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 10);
}
function label(date: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "long",
    day: "numeric",
    weekday: "long",
  }).format(new Date(`${date}T00:00:00`));
}

export default function TodoList() {
  const today = useMemo(() => new Date(), []);
  const [month, setMonth] = useState(
    () => new Date(today.getFullYear(), today.getMonth(), 1),
  );
  const [selectedDate, setSelectedDate] = useState(() => dateKey(today));
  const [todos, setTodos] = useState<Todo[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const range = useMemo(
    () => ({
      from: dateKey(new Date(month.getFullYear(), month.getMonth(), 1)),
      to: dateKey(new Date(month.getFullYear(), month.getMonth() + 1, 0)),
    }),
    [month],
  );
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setTodos(await getTodos(range.from, range.to));
    } catch {
      setError("할 일을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, [range]);
  useEffect(() => {
    void load();
  }, [load]);
  const days = useMemo(() => {
    const start = new Date(month.getFullYear(), month.getMonth(), 1).getDay();
    const last = new Date(
      month.getFullYear(),
      month.getMonth() + 1,
      0,
    ).getDate();
    return Array.from({ length: 42 }, (_, i) => {
      const day = i - start + 1;
      return day > 0 && day <= last
        ? new Date(month.getFullYear(), month.getMonth(), day)
        : null;
    });
  }, [month]);
  const selected = todos.filter((todo) => todo.due_date === selectedDate);
  const remaining = todos.filter((todo) => !todo.is_completed).length;
  async function add(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      const todo = await createTodo({
        title: title.trim(),
        description: description.trim() || null,
        due_date: selectedDate,
      });
      setTodos((items) => [...items, todo]);
      setTitle("");
      setDescription("");
    } catch {
      setError("할 일을 저장하지 못했습니다.");
    } finally {
      setSaving(false);
    }
  }
  async function toggle(todo: Todo) {
    try {
      const updated = await updateTodo(todo.id, {
        is_completed: !todo.is_completed,
      });
      setTodos((items) =>
        items.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch {
      setError("상태를 변경하지 못했습니다.");
    }
  }
  async function remove(id: number) {
    try {
      await deleteTodo(id);
      setTodos((items) => items.filter((item) => item.id !== id));
    } catch {
      setError("할 일을 삭제하지 못했습니다.");
    }
  }
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[#00E5FF] text-xs font-semibold tracking-[0.18em] uppercase">
            My workspace
          </p>
          <h1 className="text-2xl font-semibold text-white mt-1">
            할 일 & 캘린더
          </h1>
          <p className="text-sm text-[#98989D] mt-1">
            이 계정에만 저장되는 개인 업무 일정입니다.
          </p>
        </div>
        <div className="rounded-xl border border-[#2C2C2E] bg-[#1E1E1E] px-4 py-3 text-right">
          <p className="text-xs text-[#98989D]">이번 달 남은 할 일</p>
          <p className="text-xl font-semibold text-[#00E5FF]">{remaining}개</p>
        </div>
      </div>
      {error && (
        <div className="rounded-xl border border-[#FF453A]/30 bg-[#FF453A]/10 px-4 py-3 text-sm text-[#ff928a] flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)}>닫기</button>
        </div>
      )}
      <div className="grid xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.85fr)] gap-6">
        <section className="bg-[#1E1E1E] border border-[#2C2C2E] rounded-2xl p-4 sm:p-5">
          <div className="flex items-center justify-between mb-5">
            <button
              onClick={() =>
                setMonth((m) => new Date(m.getFullYear(), m.getMonth() - 1, 1))
              }
              className="w-9 h-9 rounded-lg text-[#98989D] hover:text-white hover:bg-[#252525]"
            >
              ‹
            </button>
            <h2 className="text-lg font-semibold text-white">
              {month.getFullYear()}년 {month.getMonth() + 1}월
            </h2>
            <button
              onClick={() =>
                setMonth((m) => new Date(m.getFullYear(), m.getMonth() + 1, 1))
              }
              className="w-9 h-9 rounded-lg text-[#98989D] hover:text-white hover:bg-[#252525]"
            >
              ›
            </button>
          </div>
          <div className="grid grid-cols-7 mb-2">
            {WEEKDAYS.map((day, i) => (
              <div
                key={day}
                className={`text-center text-xs pb-2 ${i === 0 ? "text-[#FF6B62]" : i === 6 ? "text-[#00E5FF]" : "text-[#98989D]"}`}
              >
                {day}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1 sm:gap-1.5">
            {days.map((date, i) => {
              if (!date)
                return <div key={i} className="min-h-18 sm:min-h-22" />;
              const key = dateKey(date);
              const dayTodos = todos.filter((todo) => todo.due_date === key);
              const selectedDay = key === selectedDate;
              return (
                <button
                  key={key}
                  onClick={() => setSelectedDate(key)}
                  className={`min-h-18 sm:min-h-22 rounded-xl border p-1.5 text-left ${selectedDay ? "border-[#2563EB] bg-[#00E5FF]/10" : "border-transparent hover:border-[#3A3A3C] hover:bg-[#252525]"}`}
                >
                  <span
                    className={`w-6 h-6 flex items-center justify-center rounded-full text-xs ${key === dateKey(today) ? "bg-[#00E5FF] text-[#121212] font-bold" : "text-[#d1d1d6]"}`}
                  >
                    {date.getDate()}
                  </span>
                  <div className="mt-1 space-y-1">
                    {dayTodos.slice(0, 2).map((todo) => (
                      <div
                        key={todo.id}
                        className={`hidden sm:block truncate rounded px-1 py-0.5 text-[10px] ${todo.is_completed ? "bg-[#2C2C2E] text-[#777]" : "bg-[#00E5FF]/15 text-[#7cf3ff]"}`}
                      >
                        {todo.title}
                      </div>
                    ))}
                    <div className="sm:hidden flex gap-0.5 px-1">
                      {dayTodos.slice(0, 3).map((todo) => (
                        <span
                          key={todo.id}
                          className={`w-1 h-1 rounded-full ${todo.is_completed ? "bg-[#555]" : "bg-[#00E5FF]"}`}
                        />
                      ))}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </section>
        <section className="bg-[#1E1E1E] border border-[#2C2C2E] rounded-2xl p-5 flex flex-col">
          <div className="mb-4">
            <p className="text-xs uppercase tracking-widest text-[#98989D]">
              선택한 날짜
            </p>
            <h2 className="text-lg font-semibold text-white mt-1">
              {label(selectedDate)}
            </h2>
          </div>
          <form
            onSubmit={add}
            className="space-y-2 border-b border-[#2C2C2E] pb-5"
          >
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="새 할 일을 입력하세요"
              className="w-full rounded-lg border border-[#3A3A3C] bg-[#121212] px-3 py-2.5 text-sm text-white outline-none focus:border-[#00E5FF]"
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="메모 (선택)"
              rows={2}
              className="w-full resize-none rounded-lg border border-[#3A3A3C] bg-[#121212] px-3 py-2 text-sm text-white outline-none focus:border-[#00E5FF]"
            />
            <button
              disabled={saving || !title.trim()}
              className="w-full rounded-lg bg-[#00E5FF] py-2.5 text-sm font-semibold text-[#121212] disabled:opacity-40"
            >
              {saving ? "저장 중..." : "할 일 추가"}
            </button>
          </form>
          <div className="pt-4 space-y-2 flex-1 overflow-auto max-h-[390px]">
            {loading ? (
              <p className="text-sm text-[#98989D] py-5 text-center">
                불러오는 중...
              </p>
            ) : selected.length === 0 ? (
              <p className="text-sm text-[#98989D] py-7 text-center">
                이 날짜에는 등록된 할 일이 없습니다.
              </p>
            ) : (
              selected.map((todo) => (
                <div
                  key={todo.id}
                  className="group flex gap-3 rounded-xl border border-[#2C2C2E] bg-[#121212] p-3"
                >
                  <input
                    type="checkbox"
                    checked={todo.is_completed}
                    onChange={() => void toggle(todo)}
                    className="mt-0.5 h-4 w-4 accent-[#00E5FF]"
                  />
                  <div className="min-w-0 flex-1">
                    <p
                      className={`text-sm ${todo.is_completed ? "text-[#777] line-through" : "text-white"}`}
                    >
                      {todo.title}
                    </p>
                    {todo.description && (
                      <p className="text-xs text-[#98989D] mt-1">
                        {todo.description}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => void remove(todo.id)}
                    className="text-[#777] hover:text-[#FF453A]"
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
