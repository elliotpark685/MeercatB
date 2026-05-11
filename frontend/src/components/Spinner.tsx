export default function Spinner({ text = '로딩 중...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-8 h-8 border-2 border-[#2C2C2E] border-t-[#00E5FF] rounded-full animate-spin" />
      <span className="text-sm text-[#98989D]">{text}</span>
    </div>
  );
}
