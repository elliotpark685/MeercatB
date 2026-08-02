# 5. Database Architecture

> 데이터의 구조, 관계, 제약조건을 정의합니다. 백엔드 개발의 핵심 설계 문서입니다.

---

## 5.1. 핵심 설계 사상: 통합 문서 모델 및 2축 분류 체계

MeerkatAI는 법령, 행정규칙, KOSHA GUIDE 등 다양한 유형의 안전 관련 문서를 **`law_documents`라는 단일 테이블**에서 통합 관리합니다.

특히 '행정규칙'은 **발령 형식(form)**과 **업무 성격(purpose)**을 분리하는 2축으로 분류하여 검색 정확도와 확장성을 확보합니다.

### 행정규칙 분류 필드

| 필드              | 예시                    | 용도                                             |
| :---------------- | :---------------------- | :----------------------------------------------- |
| `source_category` | `administrative_rule`   | 법령·안전기준과 분리하기 위한 최상위 분류        |
| `source_type`     | `instruction`           | 발령 형식의 영문 key (훈령, 예규, 고시, 지침 등) |
| `rule_form`       | `훈령`                  | 발령 형식의 한글명 (UI 표시용)                   |
| `rule_domain`     | `labor_inspection`      | 업무 대분류 (근로감독, 산업안전, 건설 등)        |
| `rule_purpose`    | `enforcement_procedure` | 업무 성격 (감독절차, 기술기준, 행정처리 등)      |
| `ministry`        | `고용노동부`            | 소관 부처 (필터링용)                             |
| `related_law_ids` | `[1, 5]`                | 관련 법령 ID 배열 (복수 법령 연결)               |

### 예시: `근로감독관 집무규정(산업안전보건)`

- **`source_category`**: `administrative_rule`
- **`source_type`**: `instruction`
- **`rule_form`**: `훈령`
- **`rule_domain`**: `labor_inspection`
- **`rule_purpose`**: `enforcement_procedure`
- **`ministry`**: `고용노동부`

이 구조는 향후 새로운 유형의 문서(예: 판례, 고시)가 추가되더라도 DB 스키마 변경 없이 유연하게 확장할 수 있도록 설계되었습니다.

---

## 5.2. 현재 핵심 테이블

- `users`: 사용자 정보
- `sites`: 현장 정보
- `law_documents`: 법령/안전기준 원문 정보
- `law_articles`: 조문 정보
- `law_chunks`: 검색을 위한 조문 분할 단위
- `law_embeddings`: 벡터 임베딩
- `generated_documents`: AI가 생성한 문서
- `law_search_logs`: 법령 검색 기록
- `todos`: 개인 할 일

## 5.3. 향후 추가될 테이블

- `subscriptions`: 사용자 구독 플랜 정보
- `payments`: 결제 기록
- `knowledge_posts`: 'Knowledge' 페이지 콘텐츠 (블로그, 가이드)
- `update_logs`: 'Updates' 페이지 콘텐츠 (법령 변경, 서비스 공지)

## 5.4. ERD (Entity-Relationship Diagram)

_(ERD 이미지를 여기에 첨부하거나 링크)_

## 5.5. 주요 관계

- `users` (1) : (N) `sites`
- `law_documents` (1) : (N) `law_articles`
- `law_articles` (1) : (N) `law_chunks`
- `law_chunks` (1) : (1) `law_embeddings`
- `users` (1) : (N) `generated_documents`
- `users` (1) : (N) `todos`

## 5.6. 주요 인덱싱 전략

- `law_chunks.chunk_text`: Full-Text Search (pg_trgm)
- `law_embeddings.embedding`: IVFFlat (pgvector)
- `law_documents.source_category`, `source_type`: 복합 인덱스
- `todos.user_id`, `due_date`: 복합 인덱스
