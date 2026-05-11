interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
}

export default function EmptyState({ icon = '📭', title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-3">
      <div className="text-4xl opacity-30">{icon}</div>
      <p className="text-sm font-medium text-[#98989D]">{title}</p>
      {description && (
        <p className="text-xs text-[#3A3A3C] text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
