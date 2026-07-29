export default function Spinner({ text = '로딩 중...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-8 h-8 border-2 border-[#CBD5E1] border-t-[#2563EB] rounded-full animate-spin" />
      <span className="text-sm text-[#64748B]">{text}</span>
    </div>
  );
}
