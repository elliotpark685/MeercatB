import { LAW_SCOPE_OPTIONS } from '../types/law';

interface LawScopeFilterProps {
  /** 선택된 법령명 목록. 빈 배열이면 전체 법령 검색을 의미한다. */
  selected: string[];
  onChange: (next: string[]) => void;
}

export default function LawScopeFilter({ selected, onChange }: LawScopeFilterProps) {
  const allSelected = selected.length === 0;

  function toggleAll() {
    onChange([]);
  }

  function toggleLaw(lawName: string) {
    if (selected.includes(lawName)) {
      onChange(selected.filter((name) => name !== lawName));
    } else {
      onChange([...selected, lawName]);
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-[#98989D]">검색 대상 법령</p>
      <div className="flex flex-wrap gap-2">
        <label
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs cursor-pointer select-none transition-colors ${
            allSelected
              ? 'border-[#00E5FF]/50 bg-[#00E5FF]/10 text-[#00E5FF]'
              : 'border-[#2C2C2E] bg-[#121212] text-[#98989D] hover:text-white'
          }`}
        >
          <input
            type="checkbox"
            checked={allSelected}
            onChange={toggleAll}
            className="w-3.5 h-3.5 rounded border-[#2C2C2E] bg-[#121212] accent-[#00E5FF]"
          />
          전체 (5개 법령)
        </label>

        {LAW_SCOPE_OPTIONS.map((lawName) => {
          const checked = selected.includes(lawName);
          return (
            <label
              key={lawName}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs cursor-pointer select-none transition-colors ${
                checked
                  ? 'border-[#00E5FF]/50 bg-[#00E5FF]/10 text-[#00E5FF]'
                  : 'border-[#2C2C2E] bg-[#121212] text-[#98989D] hover:text-white'
              }`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggleLaw(lawName)}
                className="w-3.5 h-3.5 rounded border-[#2C2C2E] bg-[#121212] accent-[#00E5FF]"
              />
              {lawName}
            </label>
          );
        })}
      </div>
    </div>
  );
}
