# MeercatB WORKGUIDE

> 이 파일 하나만 읽으면 전체 프로젝트를 즉시 파악할 수 있다.
> 새 기능 추가/수정 시 이 파일도 함께 업데이트할 것.

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|---|---|
| 서비스명 | Meerkat Safety — 건설 현장 산업안전 관리 AI 시스템 |
| Backend | FastAPI + SQLAlchemy + Supabase(PostgreSQL) |
| Frontend | React 18 + TypeScript + Vite + TailwindCSS |
| DB | Supabase PostgreSQL (`schema: meerkat_pjt`) |
| 배포 | Backend → Render / Frontend → Vercel |
| 현재 브랜치 기준 | `feature/safety-standards` (main 병합 대기) |

---

## 2. 디렉토리 구조

```
MeercatB/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI 앱 생성, CORS, init_db
│   │   ├── api/
│   │   │   ├── deps.py              # Depends: get_db, get_current_user, require_admin
│   │   │   └── v1/
│   │   │       ├── api.py           # 라우터 집합 (여기에 include_router)
│   │   │       └── endpoints/
│   │   │           ├── auth.py      # POST /auth/login, /register, GET /auth/me
│   │   │           ├── laws.py      # POST /laws/search, GET /laws/articles/{id}
│   │   │           ├── safety_standards.py  # POST /safety-standards/search ★신규
│   │   │           ├── documents.py # POST /documents/generate
│   │   │           ├── quizzes.py   # GET /quizzes/daily
│   │   │           ├── admin.py     # GET /admin/dashboard
│   │   │           └── health.py    # GET /health
│   │   ├── core/
│   │   │   ├── config.py            # Settings (pydantic-settings, .env)
│   │   │   ├── database.py          # SessionLocal, get_db, init_db, Base
│   │   │   └── security.py          # JWT encode/decode, bcrypt
│   │   ├── models/                  # SQLAlchemy ORM (모두 Base 상속)
│   │   │   ├── law_document.py      # ★ source_category/source_type/provider 컬럼 추가됨
│   │   │   ├── law_article.py
│   │   │   ├── law_chunk.py
│   │   │   ├── law_embedding.py     # pgvector or JSON
│   │   │   ├── law_search_log.py
│   │   │   ├── user.py
│   │   │   ├── site.py
│   │   │   ├── generated_document.py
│   │   │   ├── safety_quiz.py
│   │   │   └── mixins.py            # TimestampMixin (created_at, updated_at)
│   │   ├── schemas/
│   │   │   ├── law.py               # LawSearchRequest/Response, CitationItem 등
│   │   │   ├── safety_standard.py   # ★신규: SafetyStandardSearchRequest/Response
│   │   │   ├── auth.py
│   │   │   ├── document.py
│   │   │   ├── health.py
│   │   │   ├── quiz.py
│   │   │   └── admin.py
│   │   ├── services/
│   │   │   ├── law_search_service.py          # 기존 5개 법령 하이브리드 검색
│   │   │   ├── safety_standard_search_service.py  # ★신규: 안전기준 검색
│   │   │   ├── admrul_ingestion_service.py    # ★신규: 행정규칙 ingestion
│   │   │   ├── law_ingestion_service.py       # PDF/TXT 법령 파싱·저장
│   │   │   ├── law_chunking_service.py        # 조문→청크 분할
│   │   │   ├── law_embedding_service.py       # OpenAI embedding (없으면 SHA256 mock)
│   │   │   ├── law_validation_service.py      # 법령 최신 여부 확인
│   │   │   ├── document_generation_service.py # RAG 기반 문서 생성 (GPT-4o-mini)
│   │   │   ├── embedding_service.py           # 범용 embedding 래퍼
│   │   │   └── query_analyzer.py              # 쿼리 의도 분석
│   │   ├── repositories/
│   │   │   └── law_repository.py    # DB 접근 레이어 (LawRepository)
│   │   └── utils/
│   │       ├── admrul_api_client.py # ★신규: 법제처 행정규칙 API 클라이언트
│   │       ├── law_parser.py        # 한국 법령 조문 파서
│   │       ├── pdf_loader.py
│   │       ├── text_loader.py
│   │       └── embedding_text_builder.py
│   ├── ingestion/
│   │   ├── ingest_laws.py                       # CLI: 5개 법령 수집
│   │   ├── embed_law_chunks.py                  # CLI: 청크 임베딩 생성
│   │   └── ingest_admrul_safety_guidelines.py   # ★신규: 표준안전작업지침 수집
│   ├── sql/
│   │   └── migrations/
│   │       ├── 001~004_*.sql        # 기존 마이그레이션
│   │       └── 005_safety_standard_columns.sql  # ★신규
│   ├── tests/
│   │   ├── conftest.py              # autouse: OpenAI stub (OPENAI_API_KEY 없어도 통과)
│   │   ├── test_safety_standard_search.py  # ★신규 (9개)
│   │   └── test_law_*.py, test_auth_*.py 등 기존 39개
│   ├── .env.example
│   ├── pytest.ini
│   └── requirements.txt
└── frontend/
    └── src/
        ├── main.tsx
        ├── App.tsx                  # 라우터 정의
        ├── api/
        │   ├── client.ts            # Axios (JWT 자동 주입, 401→auth:unauthorized 이벤트)
        │   └── admin.ts             # API 함수 모음 (searchLaws, searchSafetyStandards 등)
        ├── pages/
        │   ├── Login.tsx
        │   ├── Register.tsx
        │   ├── Dashboard.tsx        # KPI 카드 + 최근 활동 (admin 전용)
        │   ├── LawSearch.tsx        # 기존 5개 법령 검색
        │   ├── SafetyStandardSearch.tsx  # ★신규: 안전기준 검색
        │   └── DocumentGenerate.tsx
        ├── components/
        │   ├── AdminLayout.tsx      # 사이드바 + Outlet (nav: 대시보드/법령/안전기준/문서)
        │   ├── LawResultCard.tsx
        │   ├── LawScopeFilter.tsx
        │   ├── Spinner.tsx
        │   ├── ErrorBox.tsx
        │   ├── EmptyState.tsx
        │   └── Skeleton.tsx
        ├── contexts/
        │   ├── AuthContext.tsx       # JWT → localStorage "meerkat_auth", userId/siteId/role
        │   └── ToastContext.tsx
        ├── hooks/
        │   └── useCountUp.ts
        └── types/
            └── law.ts               # LAW_SCOPE_OPTIONS, getLawBadgeColor
```

---

## 3. 환경 변수 (backend/.env)

| 변수 | 필수 | 설명 |
|---|---|---|
| `DATABASE_URL` | ✅ | Supabase 연결 문자열 (이게 있으면 POSTGRES_* 무시) |
| `DB_SCHEMA` | - | 기본값 `meerkat_pjt` |
| `OPENAI_API_KEY` | - | 없으면 mock 임베딩 사용 |
| `LAW_API_OC` | 법령/행정규칙 수집 시 필수 | 법제처 Open API 키 (법령 검색 + 행정규칙 ingestion 공용) |
| `AUTH_SECRET_KEY` | ✅ | JWT 서명 키 |
| `USE_PGVECTOR` | - | `true`면 pgvector, 기본 `false`(JSON 저장) |
| `EMBEDDING_MODEL` | - | 기본 `text-embedding-3-large` (dim=1536) |
| `CORS_ORIGINS` | - | 쉼표 구분 허용 Origin 목록 |

프론트엔드: `VITE_API_BASE_URL` (기본 로컬 http://localhost:8000)

---

## 4. DB 모델 핵심 구조

```
LawDocument (law_documents)
  ├── id, title, law_name, law_short_name, law_type, law_no
  ├── effective_date, amendment_date, jurisdiction, version, version_hash
  ├── source_url, source_file_path, raw_text, is_active
  ├── source_category  ★ NULL=기존5개법령 / "safety_standard"=안전기준
  ├── source_type      ★ "rule" / "moel_standard_safety_guideline"
  ├── provider         ★ "law.go.kr"
  └── → articles (1:N, cascade delete)

LawArticle (law_articles)
  ├── id, law_document_id (FK)
  ├── article_number, article_no, title, article_title
  ├── chapter, section
  ├── full_text, content, article_text
  ├── effective_date, status (effective/scheduled/unknown)
  ├── source_page_start, source_page_end
  ├── version_group_key
  ├── → embeddings (1:N, cascade delete)
  └── → chunks (1:N, cascade delete)

LawChunk (law_chunks)
  ├── id, law_article_id (FK)
  ├── chunk_level (article/paragraph/subparagraph/item)
  ├── chunk_no, chunk_text, token_count, metadata_json
  └── → embeddings (1:N, cascade delete)

LawEmbedding (law_embeddings)
  ├── id, article_id(FK nullable), chunk_id(FK nullable)
  ├── embedding_model, embedding (Vector or JSON), embedding_vector
  └── UniqueConstraint: (article_id, model), (chunk_id, model)

User, Site, GeneratedDocument, SafetyQuiz, LawSearchLog — 기타 모델
```

---

## 5. API 엔드포인트 전체 목록

```
GET  /api/v1/health

POST /api/v1/auth/login
POST /api/v1/auth/register
GET  /api/v1/auth/me

POST /api/v1/laws/search             # 기존 5개 법령 검색 (변경 금지)
GET  /api/v1/laws/articles/{id}

POST /api/v1/safety-standards/search # ★신규: 안전기준 검색

POST /api/v1/documents/generate       # RAG 문서 생성

GET  /api/v1/quizzes/daily

GET  /api/v1/admin/dashboard          # admin 역할 필요
```

---

## 6. 법령 검색 vs 안전기준 검색 차이

| 항목 | 법령 검색 `/laws/search` | 안전기준 검색 `/safety-standards/search` |
|---|---|---|
| 검색 대상 | 5개 건설안전 법령 | source_category = `safety_standard` |
| 기본 필터 | `law_name IN (DEFAULT_LAW_SCOPE)` | `source_category = 'safety_standard'` |
| source_type | N/A | `rule` (산안보건기준규칙), `moel_standard_safety_guideline` |
| 응답 구조 | `{query, answer, citations, raw_hits, results}` | `{query, results: [{source_type, source_name, article_no, ...}]}` |
| 서비스 클래스 | `LawSearchService` | `SafetyStandardSearchService` |

---

## 7. 검색 알고리즘 (공통 패턴)

1. 쿼리 키워드 확장 (`_expand_query_keywords`) — 공백 제거, 접미사 분리
2. **키워드 검색** — `chunk_text/article_text/article_title` ILIKE
3. **벡터 검색** — scope 전체 청크 로드 → 코사인 유사도
4. **점수 계산** = `keyword_score × 0.7 + vector_score × 0.3`
   - 제목 매칭 +0.4, 법령명 매칭 +0.5
5. 청크 없으면 article 레벨 fallback

---

## 8. 안전기준 ingestion 흐름

```
법제처 API lawSearch.do (target=admrul, query=표준안전작업지침)
  → 목록(AdmrulListItem) 수집
  → 각 ID로 lawService.do (target=admrul, ID={id}) 본문 조회
  → AdmrulDocument 파싱 (조문 → AdmrulArticle)
  → LawDocument(source_category='safety_standard', source_type='moel_standard_safety_guideline')
  → LawArticle (조문 단위)
  → LawChunk (청크)
  → (--embed 옵션 시) LawEmbedding 생성
```

중복 방지: `version_hash = SHA256(doc_id + "::" + name)` — 동일 해시 있으면 skip

실행 명령:
```bash
cd backend
python ingestion/ingest_admrul_safety_guidelines.py --embed
```

---

## 9. 프론트엔드 라우팅

```
/login          → Login (PublicRoute)
/register       → Register (PublicRoute)
/ (ProtectedRoute + AdminLayout)
  ├── /               → Dashboard
  ├── /laws           → LawSearch (기존 5개 법령)
  ├── /safety-standards → SafetyStandardSearch ★신규
  └── /documents      → DocumentGenerate
```

사이드바 색상 기조: `#121212` bg / `#00E5FF` accent(법령) / `#FF9F0A` accent(안전기준)

---

## 10. 프론트엔드 API 함수 (api/admin.ts)

| 함수 | 엔드포인트 | 설명 |
|---|---|---|
| `searchLaws(params)` | POST /laws/search | 법령 검색 |
| `getLawArticle(id)` | GET /laws/articles/{id} | 조문 상세 |
| `searchSafetyStandards(params)` | POST /safety-standards/search | 안전기준 검색 ★신규 |
| `generateDocument(params)` | POST /documents/generate | 문서 생성 |
| `getAdminDashboard(siteId)` | GET /admin/dashboard | 대시보드 |
| `getDailyQuizzes(siteId, userId)` | GET /quizzes/daily | 퀴즈 |

---

## 11. 테스트

```bash
cd backend
python -m pytest -q   # 48 passed (2025-06 기준)
```

- `conftest.py`: `autouse` fixture — OpenAI API 키 없어도 통과 (mock embedding)
- 새 테스트 시 ORM 모델 모두 import 필요 (LawSearchLog → User 관계 때문):
  ```python
  import app.models.user, app.models.site, app.models.generated_document
  import app.models.safety_quiz, app.models.law_search_log
  ```

---

## 12. 배포 전 체크리스트

1. `sql/migrations/005_safety_standard_columns.sql` Supabase 실행
2. 산업안전보건기준에 관한 규칙 레코드 `source_category` UPDATE (규칙 8 SQL 참조)
3. Render 환경변수 `LAW_API_OC` 설정 확인
4. ingestion 실행 후 `/safety-standards` 검색 확인

---

## 13. 남은 TODO

- [ ] KOSHA Guide (한국산업안전보건공단 기술지침) 연동 — 별도 API 클라이언트 필요
- [ ] `feature/safety-standards` → `main` PR 머지
- [ ] 산업안전보건기준에 관한 규칙 DB 레코드 source_category 태깅 (운영 DB)
