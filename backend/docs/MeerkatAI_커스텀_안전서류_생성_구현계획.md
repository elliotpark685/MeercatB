# MeerkatAI 커스텀 안전서류 생성 기능 구현 계획

## 0. 문서 목적

본 문서는 MeerkatAI의 기존 **문서 생성 페이지**에 다음 3종의 커스텀 안전서류 생성 기능을 단계적으로 추가하기 위한 개발 명세서다.

1. `TBM활동일지(sample).xlsx`
2. `일일안전순회일지(sample).xlsx`
3. `건진법 기준 자체 안전 점검표(샘플).hwp`

핵심 요구사항은 다음과 같다.

- 특정 사용자 ID와 관리자만 해당 문서 카드 및 작성 화면에 접근할 수 있어야 한다.
- 기존 법령·안전기준 RAG 검색 결과를 근거로 LLM이 작성 가이드를 제공해야 한다.
- 사용자가 등록한 서명 이미지 파일을 승인·결재란의 지정 위치에 자동 삽입해야 한다.
- LLM은 법적 사실과 현장 점검 결과를 임의로 확정하지 않고 **작성 보조** 역할만 수행해야 한다.
- 기존 문서 생성, 법령 검색, 인증, 관리자 기능과 CI 테스트를 훼손하지 않아야 한다.

---

# 1. 최종 목표 아키텍처

```text
사용자
  ↓
React 문서 생성 페이지
  ↓
권한 있는 문서 템플릿만 조회
  ↓
기본정보·작업정보·점검결과 입력
  ↓
FastAPI 작성 가이드 API
  ↓
기존 법령/안전기준 RAG 검색
  ↓
LLM 구조화 JSON 생성
  ↓
사용자 검토·수정·확정
  ↓
서명 이미지 선택 및 사용 확인
  ↓
XLSX 템플릿 렌더러
  ↓
최종 XLSX 생성 및 저장
  ↓
다운로드·생성 이력·감사로그 기록
```

## 1.1 역할 분리 원칙

### LLM 담당

- 작업내용 정리
- 작업별 위험요인 추천
- 위험요인별 안전대책 추천
- TBM 교육내용 추천
- 점검항목별 조치방안 추천
- 법령·안전기준 근거 요약

### 백엔드 담당

- 인증 및 권한 검증
- RAG 검색 실행
- LLM 입출력 스키마 검증
- 사용자 입력과 AI 결과 구분
- 템플릿 셀 매핑
- 서명 이미지 권한 검증
- 문서 파일 생성
- 문서 및 서명 감사로그 저장

### 사용자 담당

- 실제 작업내용 확인
- 실제 작업인원 및 장비 입력
- 점검 결과 선택
- 참석자·교육 실시 여부 확인
- AI 추천 내용 수정 및 최종 확정
- 서명 사용 최종 확인

---

# 2. 개발 원칙

## 2.1 기존 기능 보호

다음 기능을 임의로 수정하거나 제거하지 않는다.

- 기존 `/documents` 문서 생성 기능
- 기존 법령 검색 API
- 기존 Supabase Auth 인증 흐름
- 기존 관리자 대시보드
- 기존 문서 생성 로그
- 기존 CI 테스트
- 기존 Vercel 및 백엔드 배포 설정

## 2.2 브랜치 전략

```bash
git checkout main
git pull origin main
git checkout -b feature/custom-safety-documents
```

단계별 커밋 예시:

```text
feat: add custom document template permission schema
feat: add authorized template api
feat: add safety document llm draft schema
feat: add signature storage and access policy
feat: add xlsx template rendering service
feat: add tbm activity document workflow
feat: add daily safety patrol workflow
feat: add construction safety checklist workflow
feat: add audit logs and regression tests
```

## 2.3 단계 완료 원칙

각 단계는 아래 조건을 만족한 후 다음 단계로 이동한다.

- 기존 테스트 통과
- 신규 테스트 통과
- 권한 없는 사용자의 접근 차단 확인
- API 응답 스키마 확인
- 오류 로그에 개인정보·서명 URL이 노출되지 않는지 확인
- 기존 UI 동작에 회귀 문제가 없는지 확인

---

# 3. 구현 범위 및 우선순위

## 3.1 1차 MVP

1. TBM 활동일지 XLSX 생성
2. 일일 안전순회일지 XLSX 생성
3. 관리자 및 허용 사용자 ID 접근 제한
4. 안전기준 기반 LLM 작성 가이드
5. 관리자 또는 작성자 서명 이미지 삽입
6. 생성 이력 저장 및 XLSX 다운로드

## 3.2 2차 범위

1. 건진법 자체 안전점검표를 XLSX 템플릿으로 변환
2. 점검 항목별 체크 상태 입력
3. 점검 결과별 개선조치 추천
4. PDF 출력
5. 서명 다단계 결재
6. 전일 문서 복사 및 현장별 기본값 저장

## 3.3 MVP에서 제외할 기능

- LLM이 점검 결과를 자동으로 `양호` 처리하는 기능
- 실제 참석 확인 없이 참석자 서명을 일괄 삽입하는 기능
- HWP 파일을 서버에서 직접 수정하는 기능
- 관리자 동의 없이 타인의 서명을 사용하는 기능
- AI 결과를 사용자 확인 없이 최종 문서로 확정하는 기능

---

# 4. 0단계 — 현재 코드베이스 조사

## 4.1 목표

기존 구조를 파악하고 최소 수정 위치를 확정한다.

## 4.2 조사 항목

### 프론트엔드

- 문서 생성 페이지 경로
- 문서 카드 데이터 선언 위치
- 로그인 사용자 정보 및 role 조회 방식
- API 클라이언트 구조
- 파일 업로드 컴포넌트 존재 여부
- 기존 문서 생성 폼 상태관리 방식

### 백엔드

- 문서 생성 라우터 경로
- 사용자 인증 의존성
- 관리자 권한 확인 방식
- RAG 서비스 호출 구조
- OpenAI 또는 LLM 서비스 모듈
- Supabase Storage 사용 여부
- 문서 생성 로그 테이블 및 모델

### DB

- `users` 테이블의 기본키와 `role`
- `sites`와 사용자 관계
- 기존 문서 로그 테이블
- RLS 활성화 여부
- Storage bucket 및 정책

## 4.3 산출물

Codex는 코드 수정 전에 다음 내용을 보고한다.

```text
1. 프론트 문서 생성 페이지 파일 경로
2. 백엔드 문서 생성 라우터 파일 경로
3. 인증 및 role 검증 파일 경로
4. RAG 서비스 파일 경로
5. LLM 호출 파일 경로
6. DB migration 방식
7. 기존 테스트 파일 위치
8. 변경 예정 파일 목록
9. 재사용 가능한 기존 모듈
10. 예상 충돌 또는 위험요소
```

## 4.4 완료 조건

- 코드 변경 없이 조사 결과만 보고한다.
- 추측하지 않고 실제 파일 경로와 함수명을 명시한다.
- 이후 단계의 수정 범위를 최소화한다.

---

# 5. 1단계 — 업로드 양식 분석 및 템플릿 표준화

## 5.1 목표

각 문서의 입력 항목과 출력 셀을 명시적인 템플릿 매핑 파일로 정의한다.

## 5.2 원본 파일 보존

원본 샘플은 직접 수정하지 않는다.

권장 디렉터리:

```text
backend/
  app/
    templates/
      safety_documents/
        originals/
          tbm_activity_sample.xlsx
          daily_safety_patrol_sample.xlsx
          construction_safety_checklist_sample.hwp
        runtime/
          tbm_activity_v1.xlsx
          daily_safety_patrol_v1.xlsx
          construction_safety_checklist_v1.xlsx
        mappings/
          tbm_activity_v1.json
          daily_safety_patrol_v1.json
          construction_safety_checklist_v1.json
```

## 5.3 문서별 입력 항목

### TBM 활동일지

필수 입력 후보:

- 현장명
- 작성일
- 날씨
- 업체명
- 공종
- 관리자
- 출력 인원
- TBM 참석 인원
- 당일 작업내용
- 작업별 위험요인
- 위험요인별 안전대책
- TBM 교육내용
- 참석자 성명
- 참석자 직종
- 참석자 서명 여부
- 작성자 또는 관리자 서명

### 일일 안전순회일지

필수 입력 후보:

- 현장명
- 작성일
- 날씨
- 작성자
- 현장대리인
- 작업사항
- TBM 교육내용
- 인원 투입현황
- 장비 투입현황
- 안전교육 현황
- 순회점검 항목
- 점검 결과: 양호/보통/불량/해당 없음
- 지적사항
- 조치사항
- 조치 완료 여부
- 현장대리인 서명

### 건진법 기준 자체 안전점검표

HWP 원본을 직접 자동 편집하지 않는다.

먼저 다음 작업을 수행한다.

1. HWP 내용을 XLSX 템플릿으로 재작성한다.
2. 원본의 제목, 항목 순서, 점검 문구, 표 구조를 최대한 유지한다.
3. 체크 가능한 각 점검항목에 고유 ID를 부여한다.
4. 점검 결과와 조치내용 입력 셀을 분리한다.
5. 결재란을 이미지 삽입이 가능한 병합셀로 구성한다.

## 5.4 템플릿 매핑 예시

실제 셀 주소는 파일 조사 후 확정한다.

```json
{
  "template_code": "tbm_activity",
  "template_version": 1,
  "sheet_name": "작성양식",
  "fields": {
    "site_name": { "cell": "B3", "type": "text" },
    "work_date": { "cell": "F3", "type": "date" },
    "weather": { "cell": "H3", "type": "text" },
    "work_description": {
      "range": "B8:H11",
      "type": "multiline_text"
    }
  },
  "repeat_sections": {
    "risk_items": {
      "start_row": 14,
      "max_rows": 6,
      "columns": {
        "work": "B",
        "risk": "D",
        "measure": "F"
      }
    }
  },
  "signatures": {
    "manager": {
      "anchor_cell": "J3",
      "max_width_px": 90,
      "max_height_px": 40
    }
  }
}
```

## 5.5 매핑 검증 스크립트

각 템플릿에 대해 자동 검증한다.

- 지정 sheet가 존재하는지
- 지정 cell/range가 존재하는지
- 반복 영역 최대 행 수가 올바른지
- 병합셀과 이미지 anchor가 충돌하지 않는지
- 템플릿 버전이 DB와 일치하는지

## 5.6 완료 조건

- 두 XLSX 원본에서 실제 셀 주소를 확인한다.
- HWP는 직접 서버 편집 대상에서 제외한다.
- 세 문서의 mapping JSON 초안을 만든다.
- 원본 파일은 변경하지 않는다.
- 매핑 검증 테스트를 통과한다.

---

# 6. 2단계 — DB 스키마 설계

## 6.1 목표

문서 템플릿 권한, 초안, 서명, 최종 파일, 감사로그를 관리할 스키마를 추가한다.

## 6.2 권장 테이블

### `document_templates`

```sql
create table document_templates (
  id uuid primary key default gen_random_uuid(),
  template_code text not null unique,
  template_name text not null,
  description text,
  template_type text not null check (template_type in ('xlsx', 'docx', 'pdf')),
  template_version integer not null default 1,
  storage_path text not null,
  mapping_path text not null,
  allowed_roles text[] not null default array['admin']::text[],
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

### `document_template_users`

```sql
create table document_template_users (
  id uuid primary key default gen_random_uuid(),
  template_id uuid not null references document_templates(id) on delete cascade,
  user_id uuid not null,
  granted_by uuid,
  created_at timestamptz not null default now(),
  unique(template_id, user_id)
);
```

### `user_signatures`

```sql
create table user_signatures (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  display_name text,
  storage_path text not null,
  mime_type text not null,
  file_size integer not null,
  file_hash text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

### `custom_document_drafts`

```sql
create table custom_document_drafts (
  id uuid primary key default gen_random_uuid(),
  template_id uuid not null references document_templates(id),
  user_id uuid not null,
  site_id uuid,
  status text not null check (
    status in ('draft', 'ai_generated', 'user_confirmed', 'exported', 'cancelled')
  ),
  input_data jsonb not null default '{}'::jsonb,
  ai_data jsonb not null default '{}'::jsonb,
  final_data jsonb not null default '{}'::jsonb,
  legal_sources jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

### `custom_document_exports`

```sql
create table custom_document_exports (
  id uuid primary key default gen_random_uuid(),
  draft_id uuid not null references custom_document_drafts(id),
  generated_by uuid not null,
  file_type text not null check (file_type in ('xlsx', 'pdf')),
  storage_path text not null,
  file_hash text not null,
  template_version integer not null,
  generated_at timestamptz not null default now()
);
```

### `document_signature_logs`

```sql
create table document_signature_logs (
  id uuid primary key default gen_random_uuid(),
  export_id uuid not null references custom_document_exports(id),
  signature_id uuid not null references user_signatures(id),
  signature_owner_id uuid not null,
  inserted_by uuid not null,
  signature_role text not null,
  inserted_at timestamptz not null default now(),
  ip_address inet,
  user_agent text
);
```

## 6.3 권한 판정 규칙

사용자가 템플릿을 이용할 수 있는 조건:

```text
사용자 role이 allowed_roles에 포함
OR
사용자 ID가 document_template_users에 등록
```

관리자는 기본적으로 접근 가능하게 하되, `super_admin` 등 별도 체계가 존재한다면 현재 프로젝트의 실제 role 체계를 따른다.

## 6.4 완료 조건

- migration 생성
- migration rollback 또는 복구 방법 확보
- 기존 테이블 변경 최소화
- 인덱스 추가
- RLS 정책 추가
- 권한 단위 테스트 통과

---

# 7. 3단계 — Supabase Storage 및 서명 보안

## 7.1 목표

서명 원본과 생성 문서를 공개 URL 없이 안전하게 저장한다.

## 7.2 권장 bucket

```text
user-signatures      private
custom-document-templates  private
custom-document-exports    private
```

## 7.3 파일 저장 경로

```text
user-signatures/{user_id}/{signature_id}.png
custom-document-templates/{template_code}/v{version}/template.xlsx
custom-document-exports/{site_id}/{yyyy}/{mm}/{document_id}.xlsx
```

## 7.4 서명 업로드 제한

- 허용 형식: PNG, JPEG
- 권장 형식: 투명 배경 PNG
- 최대 크기: 2MB 이하
- 서버에서 실제 MIME type 확인
- 확장자만 신뢰하지 않음
- 이미지 decoding 검사
- 최대 해상도 제한
- EXIF metadata 제거
- 파일명 무작위화
- SHA-256 해시 저장

## 7.5 서명 사용 규칙

- 기본적으로 본인 서명만 사용 가능
- 관리자가 다른 사용자의 서명을 사용할 경우 명시적 위임 데이터 필요
- 서명 삽입 전 사용자가 체크박스로 최종 확인
- 문서 export 시점에 감사로그 생성
- Signed URL은 짧은 만료시간으로 발급
- 로그에 Signed URL과 원본 경로 전체를 노출하지 않음

## 7.6 완료 조건

- 비로그인 사용자의 파일 접근 차단
- 다른 사용자 서명 접근 차단
- 허용 형식 외 업로드 거부
- 비정상 이미지 업로드 거부
- 삭제 및 비활성화 API 구현

---

# 8. 4단계 — 권한 서비스와 API

## 8.1 목표

프론트 숨김과 별개로 모든 API에서 서버 권한을 검증한다.

## 8.2 공통 권한 함수

예시:

```python
async def ensure_template_access(
    *,
    db: AsyncSession,
    user: CurrentUser,
    template_code: str,
) -> DocumentTemplate:
    """관리자 또는 허용 사용자만 템플릿에 접근하도록 검증한다."""
```

## 8.3 API 목록

```text
GET    /api/v1/document-templates/authorized
GET    /api/v1/document-templates/{template_code}
POST   /api/v1/custom-documents/drafts
GET    /api/v1/custom-documents/drafts/{draft_id}
PATCH  /api/v1/custom-documents/drafts/{draft_id}
POST   /api/v1/custom-documents/drafts/{draft_id}/ai-guide
POST   /api/v1/custom-documents/drafts/{draft_id}/confirm
POST   /api/v1/custom-documents/drafts/{draft_id}/export
GET    /api/v1/custom-documents/exports/{export_id}/download
POST   /api/v1/signatures
GET    /api/v1/signatures/me
DELETE /api/v1/signatures/{signature_id}
```

## 8.4 보안 테스트

- 일반 사용자에게 허용되지 않은 템플릿 목록이 반환되지 않아야 한다.
- URL 직접 입력 시 403 반환
- 타인의 draft ID 접근 시 403 또는 404 반환
- 타인의 export 다운로드 차단
- 비활성 템플릿 생성 차단
- 프론트에서 숨겨도 API 검증은 반드시 수행

## 8.5 완료 조건

- 권한 함수가 모든 관련 API에 적용됨
- 401/403/404 구분이 일관됨
- 테스트에서 IDOR 취약점이 없어야 함

---

# 9. 5단계 — LLM 작성 가이드 서비스

## 9.1 목표

기존 안전기준 RAG를 재사용하여 문서별 구조화된 작성 가이드를 생성한다.

## 9.2 핵심 원칙

- LLM이 최종 점검 결과를 사실로 확정하지 않는다.
- 법령 근거는 RAG 검색 결과에서만 인용한다.
- 검색되지 않은 조문 번호를 생성하지 않는다.
- 근거가 없으면 `근거 확인 필요`로 표시한다.
- 사용자 입력과 AI 생성값을 별도 필드로 유지한다.
- 최종 저장 전에 사용자 확인이 필요하다.

## 9.3 공통 입력 스키마

```json
{
  "template_code": "tbm_activity",
  "site": {
    "site_id": "uuid",
    "site_name": "현장명"
  },
  "work_date": "2026-08-03",
  "weather": "맑음, 오후 강풍 가능",
  "work_items": [
    {
      "trade": "비계공사",
      "description": "외부비계 해체",
      "workers": 6,
      "equipment": ["이동식 크레인"]
    }
  ],
  "site_conditions": [
    "고소작업",
    "하부 통행로 인접"
  ],
  "user_notes": "강풍 시 작업 중지기준 확인 필요"
}
```

## 9.4 공통 출력 스키마

```json
{
  "summary": "당일 작업 및 주요 안전관리 방향",
  "work_items": [
    {
      "work": "외부비계 해체",
      "hazards": [
        {
          "hazard": "해체 중 추락",
          "measures": [
            "안전대 부착설비 확인",
            "해체 순서 및 작업구역 통제"
          ],
          "severity": "high",
          "source_ids": ["source-1"]
        }
      ]
    }
  ],
  "tbm_topics": [
    "비계 해체 순서",
    "추락방호 및 안전대 사용",
    "낙하물 위험구역 통제"
  ],
  "sources": [
    {
      "id": "source-1",
      "document_name": "검색된 문서명",
      "article": "검색된 조문 또는 항목",
      "excerpt": "검색 결과 요약",
      "verified": true
    }
  ],
  "warnings": [
    "실제 현장 상태와 점검 결과는 사용자가 확인해야 합니다."
  ]
}
```

## 9.5 문서별 LLM 스키마

### TBM 활동일지

- 작업내용
- 위험요인
- 안전대책
- TBM 교육내용
- 작업 전 확인사항
- 관련 근거

### 일일 안전순회일지

- 작업사항 요약
- TBM 교육내용
- 점검 권장항목
- 사용자가 선택한 불량 항목에 대한 지적사항 초안
- 개선조치 초안
- 관련 근거

LLM이 생성하지 않는 필드:

- 양호/보통/불량 판정
- 실제 조치 완료 여부
- 실제 안전교육 실시 여부

### 건진법 자체 안전점검표

- 점검항목별 확인 가이드
- 사용자가 입력한 부적합 내용의 정리
- 조치방안 추천
- 근거 기준 연결

LLM이 생성하지 않는 필드:

- 실제 점검 결과
- 실제 수치 측정값
- 실제 서명 및 결재

## 9.6 LLM 실패 대응

- JSON schema validation 실패 시 1회만 자동 재시도
- 재시도 실패 시 사용자에게 수동 작성 화면 제공
- RAG 결과가 없으면 일반 안전 제안임을 명시
- API timeout 시 기존 입력 내용 보존
- 동일 draft에 대한 중복 요청 방지

## 9.7 완료 조건

- Pydantic 또는 동등한 스키마 검증
- 조문 환각 방지 테스트
- RAG source ID와 출력 source ID 연결 검증
- LLM 오류 시 draft가 손상되지 않음

---

# 10. 6단계 — XLSX 문서 생성 엔진

## 10.1 목표

LLM JSON 및 사용자 확정값을 원본 양식의 지정 셀에 안전하게 입력한다.

## 10.2 서비스 구조

```text
app/services/document_rendering/
  base_renderer.py
  xlsx_renderer.py
  image_processor.py
  mapping_loader.py
  validators.py
```

## 10.3 렌더링 절차

```text
1. template_code와 version 검증
2. 원본 template 파일 복사
3. mapping JSON 로드
4. final_data schema 검증
5. 단일 셀 값 입력
6. 반복 영역 입력
7. 줄바꿈, 행 높이, 인쇄영역 확인
8. 서명 이미지 리사이징
9. 지정 anchor에 서명 삽입
10. 임시 파일 저장
11. 파일 무결성 확인
12. SHA-256 계산
13. Storage 업로드
14. export 및 감사로그 저장
```

## 10.4 템플릿 보존 요구사항

- 병합셀 유지
- 열 너비 유지
- 행 높이 유지 또는 필요한 범위만 조정
- 테두리와 폰트 유지
- 인쇄영역 유지
- 페이지 방향 유지
- 기존 수식 유지
- 원본 이미지와 로고 유지
- 정의된 이름과 숨김 시트 훼손 금지

## 10.5 텍스트 초과 처리

각 매핑 필드에 다음 옵션을 둔다.

```json
{
  "cell": "B8",
  "max_chars": 300,
  "overflow_policy": "truncate_with_warning",
  "wrap_text": true,
  "auto_row_height": true
}
```

정책 후보:

- `reject`
- `truncate_with_warning`
- `split_rows`
- `shrink_font`

안전 문서에서는 무음 잘라내기를 금지하고 경고를 반환한다.

## 10.6 서명 삽입

- 원본 비율 유지
- 최대 너비·높이 제한
- 중앙 정렬
- 투명 배경 유지
- 결재란을 벗어나지 않도록 자동 축소
- 이미지 삽입 실패 시 문서 생성 중단
- 서명 없는 문서 생성 허용 여부는 템플릿별 설정

## 10.7 완료 조건

- 생성 XLSX가 Excel에서 정상 열림
- 원본 양식과 레이아웃 차이가 허용 범위 내
- 입력값이 올바른 셀에 위치
- 서명이 결재란 안에 위치
- 수식 및 인쇄영역 유지
- 템플릿 원본 해시가 변경되지 않음

---

# 11. 7단계 — TBM 활동일지 구현

## 11.1 작성 흐름

```text
기본정보 입력
→ 작업내용 입력
→ AI 위험요인·대책 추천
→ TBM 교육내용 추천
→ 사용자 수정
→ 참석자 정보 입력
→ 서명 선택
→ 미리보기
→ XLSX 생성
```

## 11.2 화면 필드

### 기본정보

- 현장
- 날짜
- 날씨
- 업체명
- 공종
- 관리자
- 출력 인원
- 참석 인원

### 작업 및 안전관리

- 작업내용
- 위험요인
- 안전대책
- TBM 교육내용
- 법령 및 안전기준 근거

### 참석자

- 성명
- 직종
- 참석 여부
- 서명 상태

## 11.3 참석자 서명 원칙

MVP에서는 다음 중 하나를 선택한다.

### 권장 MVP

- 관리자 또는 교육실시자 서명만 자동 삽입
- 참석자는 성명과 직종만 입력
- 참석자 개별 서명 자동삽입은 2차 개발

### 개별 서명 기능 추가 조건

- 참석자별 사용자 ID가 존재
- 서명 등록 및 사용 동의가 존재
- 당일 참석 여부를 실제 확인
- 일괄 삽입 전 최종 확인
- 각 서명마다 감사로그 생성

## 11.4 완료 조건

- 권한 사용자만 카드와 작성 화면 확인
- LLM 결과가 표에 정상 반영
- 사용자가 AI 결과 수정 가능
- 최종 XLSX 다운로드 가능
- 서명 사용 로그 확인 가능

---

# 12. 8단계 — 일일 안전순회일지 구현

## 12.1 작성 흐름

```text
기본정보 입력
→ 작업·인원·장비 현황 입력
→ 점검항목 표시
→ 사용자가 점검 결과 선택
→ 불량/보통 항목에 대해 AI 조치안 생성
→ 사용자 수정 및 조치상태 입력
→ 현장대리인 서명
→ XLSX 생성
```

## 12.2 점검 결과 데이터

```json
{
  "check_item_id": "work_area_housekeeping",
  "label": "작업장 정리정돈 상태",
  "result": "poor",
  "user_observation": "자재 적치로 통로 폭이 부족함",
  "ai_finding_draft": "통행로에 자재가 적치되어 이동 및 비상대피에 지장이 우려됨",
  "ai_action_draft": "통행로 내 자재를 지정 적치장으로 이동하고 통로 폭을 확보함",
  "final_finding": "사용자가 확정한 지적사항",
  "final_action": "사용자가 확정한 조치사항",
  "action_status": "pending"
}
```

## 12.3 필수 제약

- AI가 `result` 값을 생성하지 않는다.
- 점검 결과는 사용자가 직접 선택한다.
- 실제 조치 완료는 사용자가 직접 체크한다.
- 조치 전/후 사진 기능은 별도 범위로 관리한다.

## 12.4 완료 조건

- 점검 결과 사용자 선택 강제
- 불량 항목만 선택적으로 AI 조치 생성 가능
- 조치사항 미확정 상태에서 최종 출력 시 경고
- 서명과 문서 로그 정상 생성

---

# 13. 9단계 — 건진법 자체 안전점검표 구현

## 13.1 선행 조건

- HWP 원본을 XLSX 템플릿으로 변환
- 원본과 변환본의 항목 대조 완료
- 법적 문구 누락 여부를 사람이 검토
- 각 점검항목에 stable ID 부여

## 13.2 데이터 모델

```json
{
  "section_id": "temporary_structure",
  "section_name": "가설구조물",
  "items": [
    {
      "item_id": "temporary_structure_001",
      "requirement_text": "원본 점검 문구",
      "result": "not_checked",
      "measured_value": null,
      "observation": "",
      "action": "",
      "source": {
        "document": "원본 기준명",
        "article": "원본 표기"
      }
    }
  ]
}
```

## 13.3 완료 조건

- 원본 HWP 항목과 XLSX 항목 수 일치
- 문구 비교 체크리스트 완료
- 실제 측정값을 AI가 생성하지 않음
- 점검 결과를 AI가 확정하지 않음
- 서명 및 결재란 정상 출력

---

# 14. 10단계 — 프론트엔드 UI

## 14.1 문서 카드 노출

페이지 진입 시 다음 API만 사용한다.

```text
GET /api/v1/document-templates/authorized
```

프론트에서 user ID를 하드코딩하여 권한을 판정하지 않는다.

## 14.2 화면 구성

### 문서 선택

- 기존 문서 카드 유지
- 허용된 커스텀 문서 카드만 추가
- `커스텀 문서` 또는 `제한 문서` 배지 표시

### 작성 단계

```text
1. 기본정보
2. 작업 및 점검정보
3. AI 작성 가이드
4. 사용자 확인·수정
5. 서명 및 결재
6. 미리보기·다운로드
```

## 14.3 AI 결과 표시

AI 결과는 명확하게 구분한다.

```text
[AI 추천]
[사용자 수정됨]
[근거 확인됨]
[근거 확인 필요]
```

각 항목 기능:

- 적용
- 수정
- 삭제
- 근거 보기
- 원래 AI 제안 보기

## 14.4 상태 보존

- 페이지 새로고침 시 draft 복구
- LLM 오류 시 사용자 입력 유지
- 다른 단계 이동 시 자동 저장
- export 후에도 원본 draft 유지

## 14.5 완료 조건

- 비권한 사용자에게 카드 미노출
- 직접 URL 접근 시 403 처리 화면
- 모바일 및 데스크톱 기본 사용 가능
- 기존 문서 생성 UI에 회귀 문제 없음

---

# 15. 11단계 — 테스트 계획

## 15.1 백엔드 단위 테스트

### 권한

- 관리자 접근 허용
- 허용 ID 접근 허용
- 일반 사용자 접근 거부
- 비로그인 접근 거부
- 타인의 draft 접근 거부
- 타인의 export 접근 거부

### LLM

- 정상 JSON 응답
- schema 오류 재시도
- RAG 결과 없음 처리
- 잘못된 source ID 거부
- 조문 번호 환각 차단
- timeout 시 draft 유지

### 파일 생성

- 템플릿 로드
- 셀 값 입력
- 반복행 처리
- 긴 텍스트 경고
- 서명 삽입
- 잘못된 이미지 거부
- 생성 파일 재오픈
- 원본 템플릿 불변

## 15.2 프론트엔드 테스트

- 허용 카드만 노출
- 작성 단계 이동
- 자동 저장
- AI 적용/수정/삭제
- 근거보기
- 서명 선택
- export 오류 처리

## 15.3 통합 테스트

```text
로그인
→ 허용 템플릿 조회
→ draft 생성
→ AI 가이드 생성
→ 사용자 수정
→ 서명 선택
→ 최종 확정
→ XLSX export
→ Storage 업로드
→ 감사로그 확인
→ 다운로드
```

## 15.4 회귀 테스트

- 기존 법령 검색
- 기존 문서 생성
- 기존 관리자 대시보드
- 기존 로그인
- 기존 CI 전체 테스트

---

# 16. 12단계 — 배포 및 운영

## 16.1 환경변수

예시:

```text
CUSTOM_DOCUMENTS_ENABLED=true
CUSTOM_DOCUMENT_TEMPLATE_BUCKET=custom-document-templates
CUSTOM_DOCUMENT_EXPORT_BUCKET=custom-document-exports
USER_SIGNATURE_BUCKET=user-signatures
DOCUMENT_EXPORT_SIGNED_URL_TTL=300
MAX_SIGNATURE_FILE_SIZE=2097152
```

## 16.2 feature flag

초기에는 기능을 feature flag로 제한한다.

```text
CUSTOM_DOCUMENTS_ENABLED=false
```

배포 후 관리자 계정으로만 검증한 다음 활성화한다.

## 16.3 배포 순서

```text
1. DB migration 적용
2. Storage bucket 및 RLS 적용
3. 템플릿 업로드
4. 백엔드 배포
5. API smoke test
6. 프론트 배포
7. 관리자 검증
8. 특정 사용자 ID 권한 부여
9. 기능 활성화
```

## 16.4 롤백

- feature flag 비활성화
- 프론트 카드 숨김
- 신규 API 라우터 비활성화
- 기존 문서 기능은 계속 사용 가능
- 신규 테이블 데이터는 즉시 삭제하지 않음

---

# 17. 보안 및 법적 리스크 체크리스트

## 17.1 필수

- [ ] 서명 Storage는 private bucket이다.
- [ ] Signed URL 만료시간이 짧다.
- [ ] 사용자 본인 또는 위임된 서명만 사용한다.
- [ ] 서명 삽입 시 감사로그를 남긴다.
- [ ] LLM은 실제 점검 결과를 확정하지 않는다.
- [ ] LLM은 실제 참석 여부를 확정하지 않는다.
- [ ] 법령 근거 없는 내용을 의무사항으로 표시하지 않는다.
- [ ] 최종 확정 전에 사용자 확인을 받는다.
- [ ] 타인의 draft와 export를 조회할 수 없다.
- [ ] 로그에 개인정보와 서명 URL이 노출되지 않는다.

## 17.2 권장

- [ ] 서명 이미지 등록 시 사용 목적 동의 문구를 표시한다.
- [ ] 최종 파일에 AI 작성 보조 사용 이력을 내부적으로 기록한다.
- [ ] 생성 문서의 템플릿 버전과 file hash를 저장한다.
- [ ] 원본과 최종 파일의 변경 이력을 보존한다.
- [ ] 문서 보존기간과 삭제정책을 정의한다.

---

# 18. 단계별 Codex Terra 작업 지시 프롬프트

아래 프롬프트를 **한 번에 전부 실행하지 말고 순서대로 하나씩** 사용한다.

---

## Prompt 0 — 코드베이스 조사

```text
현재 MeerkatAI 프로젝트에 커스텀 안전서류 생성 기능을 추가하려고 한다.
아직 코드를 수정하지 말고 기존 구조만 조사하라.

조사 대상:
1. 프론트 문서 생성 페이지와 문서 카드 정의 위치
2. 사용자 인증 정보와 role을 가져오는 방식
3. 백엔드 문서 생성 API 및 service 구조
4. 기존 RAG 법령 검색 service
5. 기존 LLM 호출 service와 출력 schema
6. Supabase Storage 사용 여부
7. DB migration 방식
8. 기존 문서 생성 로그 구조
9. 관련 테스트 파일
10. 배포 및 CI 구조

반드시 실제 파일 경로, 함수명, 컴포넌트명, 모델명을 근거로 보고하라.
추측하지 말고, 변경이 필요한 파일 후보와 재사용 가능한 기존 모듈을 구분하라.
기존 기능을 수정하지 말고 조사 보고서만 작성하라.
```

---

## Prompt 1 — 구현 설계 확정

```text
이전 조사 결과와 `MeerkatAI_커스텀_안전서류_생성_구현계획.md`를 기준으로 구현 설계를 확정하라.

요구사항:
- TBM 활동일지 XLSX
- 일일 안전순회일지 XLSX
- 건진법 자체 안전점검표는 HWP 직접 편집 대신 XLSX 변환 대상으로 분류
- 관리자 또는 허용된 특정 사용자 ID만 접근
- 기존 RAG를 이용한 LLM 작성 가이드
- 사용자 서명 이미지 자동 삽입
- 기존 기능과 CI 테스트 보호

아직 전체 기능을 구현하지 말고 다음만 산출하라.
1. 최종 디렉터리 구조
2. DB 변경안
3. API 명세
4. Pydantic schema 목록
5. 프론트 페이지 및 컴포넌트 구조
6. 템플릿 mapping 구조
7. 테스트 계획
8. 단계별 변경 파일 목록
9. 위험요소와 대응방안

현재 프로젝트의 실제 코드 구조에 맞춰 문서의 예시를 조정하라.
```

---

## Prompt 2 — DB 및 권한 구현

```text
확정된 설계에 따라 DB migration과 템플릿 접근 권한 기능만 구현하라.

범위:
- document_templates
- document_template_users
- user_signatures
- custom_document_drafts
- custom_document_exports
- document_signature_logs
- 필요한 인덱스와 RLS
- 관리자 또는 허용 사용자 ID 접근 판정 service
- GET /api/v1/document-templates/authorized

주의사항:
- 기존 users, documents, logs 구조를 불필요하게 변경하지 않는다.
- 프론트 숨김만으로 보안을 처리하지 않는다.
- 모든 접근은 백엔드에서 다시 검증한다.
- 프로젝트의 기존 migration 방식과 코드 스타일을 따른다.
- 테스트를 추가한다.

완료 후 다음을 보고하라.
1. 변경 파일
2. migration 내용
3. 권한 판정 로직
4. 신규 테스트
5. 전체 테스트 결과
6. 다음 단계에서 필요한 사항
```

---

## Prompt 3 — 서명 업로드 및 보안 구현

```text
사용자 서명 이미지 등록·조회·비활성화 기능을 구현하라.

요구사항:
- PNG/JPEG만 허용
- 최대 2MB
- 실제 MIME type 및 이미지 decoding 검증
- EXIF metadata 제거
- SHA-256 hash 저장
- private Supabase Storage bucket 사용
- 사용자 본인 서명만 조회 가능
- Signed URL은 짧은 만료시간 사용
- 로그에 Signed URL과 민감정보 노출 금지

API:
- POST /api/v1/signatures
- GET /api/v1/signatures/me
- DELETE /api/v1/signatures/{signature_id}

아직 문서에 삽입하지 말고 서명 저장과 보안만 구현하라.
테스트를 추가하고 기존 전체 테스트를 실행하라.
```

---

## Prompt 4 — 템플릿 분석 및 매핑

```text
다음 원본 양식을 분석하고 문서별 mapping JSON을 작성하라.
- TBM활동일지(sample).xlsx
- 일일안전순회일지(sample).xlsx
- 건진법 기준 자체 안전 점검표(샘플).hwp

원칙:
- 원본 파일을 직접 수정하지 않는다.
- 두 XLSX는 sheet, 병합셀, 인쇄영역, 이미지, 수식, 입력 가능 셀을 조사한다.
- HWP는 직접 렌더링 대상으로 삼지 말고 XLSX 변환 요구사항을 작성한다.
- 실제 셀 주소를 근거로 mapping을 작성한다.
- mapping의 모든 셀과 범위를 자동 검증하는 테스트를 만든다.

산출물:
1. 문서별 필드 목록
2. 필드별 실제 셀 주소
3. 반복 영역 정의
4. 서명 anchor 위치
5. 텍스트 최대 길이와 overflow 정책
6. mapping JSON
7. mapping 검증 테스트

불확실한 셀은 추측하지 말고 명시적으로 보고하라.
```

---

## Prompt 5 — LLM 작성 가이드 구현

```text
기존 RAG 법령 검색 service를 재사용하여 커스텀 안전서류용 LLM 작성 가이드 API를 구현하라.

API:
POST /api/v1/custom-documents/drafts/{draft_id}/ai-guide

지원 문서:
- tbm_activity
- daily_safety_patrol
- construction_safety_checklist

핵심 제한:
- LLM은 점검 결과를 양호/보통/불량으로 판정하지 않는다.
- LLM은 참석 여부, 교육 실시 여부, 조치 완료 여부를 생성하지 않는다.
- RAG에서 검색되지 않은 조문 번호를 생성하지 않는다.
- source_id가 실제 검색 결과와 일치해야 한다.
- 사용자 입력, AI 결과, 최종 확정값을 분리한다.
- JSON schema validation을 적용한다.
- 실패 시 1회만 재시도하고 draft를 보존한다.

문서별 Pydantic schema와 테스트를 추가하라.
기존 LLM service를 무리하게 변경하지 말고 확장 가능한 adapter 구조를 우선 검토하라.
```

---

## Prompt 6 — XLSX 렌더링 엔진 구현

```text
mapping JSON과 final_data를 이용하여 XLSX 문서를 생성하는 렌더링 엔진을 구현하라.

요구사항:
- 원본 템플릿 복사 후 작업
- 병합셀, 스타일, 테두리, 인쇄영역, 수식, 로고 유지
- 단일 셀 및 반복 행 입력
- 긴 텍스트 overflow 정책
- 서명 이미지 비율 유지 및 결재란 내부 자동 축소
- 서명 삽입 실패 시 export 중단
- 생성 XLSX 재오픈 검증
- 원본 템플릿 불변 검증
- SHA-256 생성

아직 프론트 UI는 수정하지 않는다.
TBM 활동일지와 일일 안전순회일지의 샘플 데이터를 이용한 통합 테스트를 작성하라.
```

---

## Prompt 7 — TBM 활동일지 전체 흐름 구현

```text
TBM 활동일지 커스텀 문서 생성 흐름을 프론트와 백엔드에 연결하라.

흐름:
1. 권한 있는 사용자에게만 카드 노출
2. 기본정보 입력
3. 작업내용 입력
4. AI 위험요인·대책 및 TBM 교육내용 생성
5. 사용자 적용·수정·삭제
6. 관리자 또는 작성자 서명 선택
7. 최종 확인
8. XLSX export
9. 생성 이력 및 서명 감사로그 저장
10. 다운로드

MVP에서는 참석자 개별 서명 자동 삽입을 구현하지 않는다.
참석자 성명과 직종 입력은 가능하게 한다.

기존 문서 생성 페이지의 UI와 기능을 최대한 유지하고 커스텀 문서 영역만 확장하라.
전체 테스트와 회귀 테스트를 실행하라.
```

---

## Prompt 8 — 일일 안전순회일지 전체 흐름 구현

```text
일일 안전순회일지 생성 흐름을 구현하라.

핵심 원칙:
- 점검 결과는 사용자가 직접 양호/보통/불량/해당 없음 중 선택한다.
- LLM은 사용자가 보통 또는 불량으로 선택한 항목에 대해서만 지적사항과 조치사항 초안을 생성한다.
- 실제 조치 완료 여부는 사용자가 선택한다.
- 현장대리인 서명은 권한과 사용 확인 후 삽입한다.

작업·인원·장비·교육 현황 입력, AI 추천, 사용자 수정, XLSX export, 감사로그를 연결하라.
기존 기능 회귀 테스트를 포함하라.
```

---

## Prompt 9 — 건진법 점검표 변환 설계

```text
건진법 기준 자체 안전 점검표 HWP 원본을 서버에서 직접 편집하지 않는다.
원본의 표 구조와 점검 문구를 유지한 XLSX 템플릿으로 전환하기 위한 변환 작업을 수행하라.

요구사항:
- 원본 항목 순서 유지
- 원본 점검 문구 임의 수정 금지
- 각 점검항목에 stable item_id 부여
- 점검 결과, 측정값, 관찰내용, 조치내용 입력 영역 분리
- 결재란 이미지 삽입 영역 확보
- 원본과 변환본 항목 수 및 문구 대조표 작성
- 사람이 확인해야 할 항목 표시

변환본 검증이 끝나기 전에는 운영 기능에 연결하지 않는다.
```

---

## Prompt 10 — 최종 보안·회귀 검토

```text
커스텀 안전서류 생성 기능 전체를 보안 및 회귀 관점에서 최종 검토하라.

검토 대상:
1. IDOR 및 권한 우회
2. 프론트 숨김과 백엔드 검증 불일치
3. Supabase RLS
4. 서명 이미지 노출
5. Signed URL 만료
6. 파일 업로드 검증
7. LLM 조문 환각
8. AI가 사실을 자동 확정하는지
9. XLSX formula injection 가능성
10. 로그 개인정보 노출
11. 기존 문서 생성 기능 회귀
12. CI/CD 및 배포 영향

발견한 문제는 위험도별로 분류하고 최소 수정으로 보완하라.
전체 테스트 결과와 배포 체크리스트를 보고하라.
```

---

# 19. 최종 완료 정의

다음 조건을 모두 만족하면 1차 구현 완료로 판단한다.

- [ ] TBM 활동일지 XLSX 생성 가능
- [ ] 일일 안전순회일지 XLSX 생성 가능
- [ ] 관리자와 허용 사용자 ID만 접근 가능
- [ ] 직접 URL 및 API 호출도 차단됨
- [ ] 기존 RAG 기반 안전기준 근거 표시
- [ ] LLM 결과를 사용자가 수정·확정 가능
- [ ] LLM이 실제 점검 결과를 확정하지 않음
- [ ] 서명 이미지가 지정 결재란에 삽입됨
- [ ] 서명 사용 감사로그 저장
- [ ] 생성 XLSX가 정상 열리고 인쇄 가능
- [ ] 기존 기능 회귀 테스트 통과
- [ ] 기능 비활성화 및 롤백 가능

---

# 20. 권장 실행 순서 요약

```text
0. 코드베이스 조사
1. 구현 설계 확정
2. DB 및 권한
3. 서명 저장·보안
4. 템플릿 분석·매핑
5. LLM 작성 가이드
6. XLSX 렌더링 엔진
7. TBM 활동일지 연결
8. 일일 안전순회일지 연결
9. 건진법 점검표 XLSX 변환
10. 보안·회귀 검토
11. 관리자 제한 베타 테스트
12. 특정 사용자 권한 확대
```

가장 중요한 원칙은 **문서 생성과 AI 판단을 분리하는 것**, **서명을 이미지 기능이 아닌 민감 인증자산으로 관리하는 것**, **프론트 노출 제한과 백엔드 권한 검증을 동시에 적용하는 것**이다.
