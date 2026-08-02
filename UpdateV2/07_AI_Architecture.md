# 7. AI Architecture

> MeerkatAI의 핵심인 AI 모델과 데이터 처리 파이프라인을 정의합니다.

---

## 7.1. RAG (Retrieval-Augmented Generation) 파이프라인

> 사용자 질문에 대해 AI가 답변하고 문서를 생성하는 흐름

1.  **Query Analysis**: 사용자 질문의 의도(법령 검색, 문서 생성 등)를 분석
2.  **Retrieval**: 분석된 의도에 따라 VectorDB와 Full-Text Search를 결합한 하이브리드 검색 실행
3.  **Re-ranking**: 검색된 Chunk들을 관련도 순으로 재정렬
4.  **Prompt Engineering**: 사용자 질문 + 재정렬된 Chunk + 컨텍스트를 LLM에 맞는 프롬프트로 조합
5.  **LLM (Large Language Model)**: 프롬프트를 GPT-4o-mini 등 LLM에 전달하여 답변/문서 초안 생성
6.  **Citation**: 생성된 내용의 근거가 된 원본 조문(Chunk) 정보 추출
7.  **Validation & Formatting**: 생성된 결과물을 최종 사용자에게 보여주기 전에 유효성을 검증하고 마크다운 등으로 포맷팅

## 7.2. 법령 데이터 수집 (Ingestion) 파이프라인

> 법령/안전기준 데이터를 수집하여 검색 가능한 형태로 가공하는 흐름

1.  **Data Source**: 법제처 API, KOSHA API, 공공데이터포털 등
2.  **Parser**: 각 소스(PDF, HWP, XML, JSON)에 맞는 파서로 텍스트와 메타데이터 추출
3.  **Chunking**: 추출된 텍스트를 의미 단위(조, 항, 호)로 분할 (RecursiveCharacterTextSplitter 등)
4.  **Embedding**: 분할된 Chunk를 OpenAI `text-embedding-3-large` 등 임베딩 모델을 통해 벡터로 변환
5.  **VectorDB Storage**: 원본 텍스트, 메타데이터, 벡터를 PostgreSQL (pgvector)에 저장

## 7.3. 핵심 모델 및 기술

- **LLM**: GPT-4o-mini (비용과 성능의 균형)
- **Embedding Model**: text-embedding-3-large
- **VectorDB**: PostgreSQL with pgvector extension
- **Framework**: FastAPI, SQLAlchemy, LangChain (필요시)
