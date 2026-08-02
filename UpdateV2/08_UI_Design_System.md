# 8. UI Design System

> UI의 일관성을 유지하고 재사용성을 높이기 위한 시각적/인터랙션 규칙을 정의합니다.

---

## 8.1. 색상 (Colors)

- **Primary Background**: `#121212`
- **Card/Component Background**: `#1E1E1E`
- **Primary Accent (법령, CTA)**: `#00E5FF`
- **Secondary Accent (안전기준)**: `#FF9F0A`
- **Tertiary Accent (KOSHA, Pro)**: `#BF5AF2`
- **Primary Text**: `#F5F5F7`
- **Secondary Text**: `#98989D`
- **Success**: `#32D74B`
- **Error**: `#FF453A`

## 8.2. 타이포그래피 (Typography)

- **Font Family**: System UI (산세리프), JetBrains Mono (코드)
- **Heading Scale**: `text-3xl`, `text-2xl`, `text-xl`, `text-lg`
- **Body Scale**: `text-base`, `text-sm`, `text-xs`

## 8.3. 컴포넌트 (Components)

- **Buttons**: `rounded-lg` 또는 `rounded-xl`, 명확한 `hover`/`disabled` 상태
- **Cards**: `rounded-2xl` 또는 `rounded-3xl`, `border-[#2C2C2E]`
- **Modals**: 중앙 정렬, 배경 어둡게 처리

## 8.4. 레이아웃 및 간격 (Layout & Spacing)

- **Max Width**: `max-w-7xl`
- **Spacing System**: TailwindCSS 기본 스케일 (4, 8, 12, 16, 24...)
- **Responsive Breakpoints**: `sm`, `md`, `lg`, `xl`
