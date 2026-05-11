interface SkeletonProps {
  className?: string;
  lines?: number;
}

export default function Skeleton({ className = '', lines }: SkeletonProps) {
  if (lines && lines > 1) {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`animate-pulse bg-[#2C2C2E] rounded-md h-4 ${i === lines - 1 ? 'w-2/3' : 'w-full'}`}
          />
        ))}
      </div>
    );
  }
  return <div className={`animate-pulse bg-[#2C2C2E] rounded-md ${className}`} />;
}

export function StatCardSkeleton() {
  return (
    <div className="bg-[#1E1E1E] rounded-2xl border border-[#2C2C2E] p-5">
      <Skeleton className="h-3 w-24 mb-3" />
      <Skeleton className="h-9 w-20" />
    </div>
  );
}

export function ListItemSkeleton() {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-[#2C2C2E]">
      <div className="space-y-1.5 flex-1">
        <Skeleton className="h-3.5 w-48" />
        <Skeleton className="h-3 w-20" />
      </div>
      <Skeleton className="h-3 w-28 shrink-0 ml-4" />
    </div>
  );
}
