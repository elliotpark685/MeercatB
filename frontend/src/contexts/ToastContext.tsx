import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from 'react';

type ToastType = 'success' | 'error' | 'info';

interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  addToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be inside ToastProvider');
  return ctx;
}

let _id = 0;

const ICON: Record<ToastType, string> = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
};

const COLOR: Record<ToastType, string> = {
  success: 'border-[#32D74B] text-[#32D74B]',
  error:   'border-[#FF453A] text-[#FF453A]',
  info:    'border-[#00E5FF] text-[#00E5FF]',
};

function Toast({ item, onClose }: { item: ToastItem; onClose: () => void }) {
  return (
    <div
      className={`flex items-start gap-3 bg-[#1E1E1E] border-l-4 rounded-r-xl px-4 py-3 shadow-xl pointer-events-auto toast-enter ${COLOR[item.type]}`}
      style={{ minWidth: 260, maxWidth: 360 }}
    >
      <span className="font-bold text-sm mt-0.5 shrink-0">{ICON[item.type]}</span>
      <p className="text-sm text-white flex-1">{item.message}</p>
      <button
        onClick={onClose}
        className="text-[#98989D] hover:text-white text-xs shrink-0 mt-0.5 transition-colors"
      >
        ✕
      </button>
    </div>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (message: string, type: ToastType = 'info') => {
      const id = ++_id;
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => remove(id), 3500);
    },
    [remove]
  );

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <Toast key={t.id} item={t} onClose={() => remove(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
