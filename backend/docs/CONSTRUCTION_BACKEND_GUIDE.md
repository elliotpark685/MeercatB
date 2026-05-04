# 건설 앱 프로젝트 백엔드 개발 가이드 (Codex 기준)

## 1. 개발 환경
- Conda Environment: llm_env
- Python 3.10+
- FastAPI
- PostgreSQL
- SQLAlchemy
- pgvector

## 실행
```bash
conda activate llm_env
cd construction-safety-ai/backend
uvicorn app.main:app --reload
```

## 2. MVP 기능
1. 법령 검색 API
2. 조문 기반 AI 답변
3. TBM/위험성평가 문서 생성
4. 안전퀴즈
5. 관리자 대시보드

## 3. 핵심 테이블
- users
- sites
- law_documents
- law_articles
- law_embeddings
- generated_documents
- safety_quizzes

## 4. 법령 RAG 원칙
1. 조문 단위 파싱
2. 시행일 관리
3. 중복 조문은 버전 분리
4. citations 포함 응답

## 5. API 우선순위
GET /api/v1/health
POST /api/v1/laws/search
GET /api/v1/laws/articles/{id}
POST /api/v1/documents/generate

## 6. 체크리스트
- FastAPI 실행
- PostgreSQL 연결
- pgvector 설치
- PDF 파서 구현
- 검색 API 테스트
