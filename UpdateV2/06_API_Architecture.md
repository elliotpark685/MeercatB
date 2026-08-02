# 6. API Architecture

> 프론트엔드와 백엔드 간의 통신 규약을 정의합니다.

---

## 6.1. 현재 API Endpoints (`/api/v1`)

- `POST /auth/login`, `/register`: 인증
- `GET /laws/search`, `/safety-standards/search`, `/kosha/search`: 통합 검색
- `POST /documents/generate`: AI 문서 생성
- `GET, POST, PATCH, DELETE /todos`: 할 일 관리
- `GET /admin/dashboard`: 관리자 대시보드

## 6.2. 향후 추가될 API Endpoints

- `GET /knowledge/posts`, `/knowledge/posts/{slug}`: 공개 콘텐츠 API
- `GET /updates`: 업데이트 소식 API
- `POST /subscriptions/checkout`: 구독 결제 세션 생성
- `GET /subscriptions/status`: 구독 상태 조회
- `POST /webhooks/stripe`: Stripe 결제 웹훅

## 6.3. 버전 관리

- URL 경로에 버전을 명시 (`/api/v1`)

## 6.4. 인증 및 권한

- **JWT (JSON Web Token)**: `Authorization: Bearer <token>` 헤더 사용
- **권한 분리**: `Public`, `Authenticated User`, `Admin` 역할에 따라 API 접근 제어

## 6.5. 응답 형식 및 예외 처리

- **성공**: `200 OK`, `201 Created` 등. 데이터는 `data` 필드에 포함.
- **실패**: `400 Bad Request`, `401 Unauthorized`, `404 Not Found`, `500 Internal Server Error` 등. 에러 메시지는 `detail` 필드에 포함.
