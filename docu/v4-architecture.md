# Q-CMS RAG 챗봇 — v4 아키텍처

## 목적

Q-CMS 솔루션의 문서/소스코드를 RAG로 검색하고, LLM으로 답변하는 챗봇.
문서와 수집 설정을 웹 UI에서 직접 관리할 수 있도록 개선.

---

## v3 → v4 변경점

| 항목 | v3 (현재) | v4 (개선) |
|---|---|---|
| 문서 관리 | 외부 경로 glob 수집만 | UI에서 업로드/삭제/수정 + 자체 저장 |
| 소스 수집 | curl body에 glob 패턴 직접 입력 | UI에서 경로/패턴 설정 후 버튼 색인 |
| 프로젝트 교체 | docker-compose 수정 후 재시작 | UI에서 경로만 변경 후 재색인 |
| 삭제 파일 | DB에 남아있음 | 색인 시 자동 정리 |
| UI | 채팅만 | 채팅 + 문서관리 + 수집설정 |

---

## 아키텍처

```
브라우저 (http://host:3200/ui/)
  ├── /ui/              채팅 페이지
  ├── /ui/docs          문서 관리 페이지
  └── /ui/settings      수집 설정 페이지
       │
       ▼
┌──────────────────────────────────────┐
│  FastAPI (:3200)                     │
│                                      │
│  [채팅]                              │
│  POST /chat                          │
│                                      │
│  [검색]                              │
│  GET  /search                        │
│                                      │
│  [문서 관리]                          │
│  GET    /api/docs                    │  문서 목록
│  POST   /api/docs                    │  문서 업로드 (MD 파일)
│  GET    /api/docs/:id                │  문서 내용 조회
│  PUT    /api/docs/:id                │  문서 수정
│  DELETE /api/docs/:id                │  문서 삭제
│                                      │
│  [수집 설정]                          │
│  GET    /api/settings                │  현재 설정 조회
│  PUT    /api/settings                │  설정 변경 (경로, 패턴)
│  POST   /api/settings/index          │  수동 색인 실행
│  GET    /api/settings/index/status   │  색인 상태 조회
│                                      │
│  [기존]                              │
│  GET  /health                        │
│  GET  /stats                         │
│                                      │
│  sentence-transformers (384d)        │
└──────────────┬───────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌─────────────────┐
│ PostgreSQL  │  │ VLLM (:7100)    │
│ + pgvector  │  │ gemma-4-E4B-it  │
│ (:5432)     │  │ (외부 서버)      │
└─────────────┘  └─────────────────┘
```

---

## 데이터 소스

### 1. 문서 (MD) — 자체 관리

```
data/
└── docs/
    ├── 게시판_렌더_흐름.md
    ├── API_설계_규칙.md
    ├── 미들웨어_체인.md
    └── ...
```

- RAG 서버 내부 `data/docs/` 디렉토리에 저장
- UI에서 업로드/수정/삭제
- 업로드 시 자동 색인 (청킹 → 임베딩 → DB 저장)
- 수정 시 해당 파일 청크 삭제 후 재색인
- 삭제 시 청크도 함께 삭제
- Docker volume으로 영속화

### 2. 소스코드 — 외부 경로 마운트

```
/source/                      ← Docker 마운트 포인트
├── backend/                  ← 설정에서 지정한 백엔드 경로
│   └── src/**/service/**/*.java
└── frontend/                 ← 설정에서 지정한 프론트 경로
    ├── components/**/*.vue
    ├── composables/**/*.ts
    └── ...
```

- 호스트의 프로젝트 소스를 Docker에 마운트
- UI 설정에서 경로 + glob 패턴 관리
- 프로젝트 교체 시: docker-compose에서 마운트 경로만 변경하거나, 여러 경로 마운트 후 UI에서 선택
- "색인 실행" 버튼으로 수동 색인

---

## DB 스키마 변경

### 기존 유지
- `documents` 테이블 — 그대로 사용

### 신규 추가

```sql
-- 수집 설정 (소스코드 경로 + glob 패턴)
CREATE TABLE index_settings (
    id          SERIAL PRIMARY KEY,
    label       VARCHAR(100) NOT NULL,       -- "백엔드 Service", "프론트 컴포넌트" 등
    base_path   VARCHAR(500) NOT NULL,       -- /source/backend, /source/frontend
    glob        VARCHAR(300) NOT NULL,       -- src/**/service/**/*.java
    doc_type    VARCHAR(50) NOT NULL,        -- source, convention 등
    enabled     BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

- 문서(MD)는 별도 설정 불필요 — `data/docs/` 전체를 자동 관리
- 소스코드 수집 대상만 이 테이블로 관리

---

## UI 페이지 구성

### 1. 채팅 (`/ui/` — index.html)
- 기존과 동일
- 상단에 문서관리/설정 페이지 링크 추가

### 2. 문서 관리 (`/ui/docs` — docs.html)
- MD 파일 목록 (파일명, 크기, 청크 수, 최종 수정일)
- 파일 업로드 (드래그 앤 드롭 또는 파일 선택)
- 파일 내용 보기/수정 (textarea)
- 파일 삭제
- 전체 재색인 버튼

### 3. 수집 설정 (`/ui/settings` — settings.html)
- 소스코드 수집 대상 목록 (label, base_path, glob, doc_type, 활성/비활성)
- 대상 추가/수정/삭제
- "색인 실행" 버튼 → 활성화된 대상만 색인
- 색인 결과 표시 (indexed, skipped, deleted, errors)
- 현재 색인 통계 (총 청크, 타입별, 언어별)

---

## API 상세

### 문서 관리 API

```
GET /api/docs
→ { "docs": [
    { "id": 1, "filename": "게시판_렌더_흐름.md", "size": 2048,
      "chunks": 5, "updated_at": "2026-06-30T..." }
  ]}

POST /api/docs
Content-Type: multipart/form-data
file: (MD 파일)
→ 파일 저장 + 자동 색인
→ { "id": 1, "filename": "...", "chunks": 5 }

GET /api/docs/:id
→ { "id": 1, "filename": "...", "content": "# 문서 내용..." }

PUT /api/docs/:id
Body: { "content": "수정된 내용..." }
→ 파일 덮어쓰기 + 재색인
→ { "id": 1, "filename": "...", "chunks": 4 }

DELETE /api/docs/:id
→ 파일 삭제 + 청크 삭제
→ { "deleted": "게시판_렌더_흐름.md" }
```

### 수집 설정 API

```
GET /api/settings
→ { "settings": [
    { "id": 1, "label": "백엔드 Service", "base_path": "/source/backend",
      "glob": "src/**/service/**/*.java", "doc_type": "source", "enabled": true }
  ]}

PUT /api/settings
Body: { "settings": [ ... ] }
→ 전체 설정 교체

POST /api/settings/index
→ 활성화된 설정으로 색인 실행
→ { "indexed": 50, "skipped": 200, "deleted": 3, "errors": 0 }

GET /api/settings/index/status
→ { "running": false, "last_run": "2026-06-30T...", "last_result": {...} }
```

---

## 디렉토리 구조 (v4)

```
RAG/
├── docu/                        # 설계 문서
│   ├── plan.md                  # v3 계획 (아카이브)
│   ├── v4-architecture.md       # v4 아키텍처 (이 문서)
│   └── 검증.txt
├── data/
│   └── docs/                    # MD 문서 저장소 (Docker volume)
├── server/
│   ├── main.py                  # FastAPI 앱
│   ├── config.py                # 환경변수 설정
│   ├── routers/
│   │   ├── chat.py              # POST /chat
│   │   ├── search.py            # GET /search
│   │   ├── index.py             # GET /stats (색인 통계)
│   │   ├── docs.py              # 문서 CRUD API
│   │   └── settings.py          # 수집 설정 API
│   ├── services/
│   │   ├── chunker.py           # 청킹
│   │   ├── embedder.py          # 임베딩 (E5)
│   │   ├── indexer.py           # 색인 오케스트레이션
│   │   └── llm.py               # VLLM 연결
│   ├── db/
│   │   └── database.py          # SQLAlchemy
│   ├── models/
│   │   └── models.py            # SQLAlchemy 모델
│   ├── static/
│   │   ├── index.html           # 채팅 UI
│   │   ├── docs.html            # 문서 관리 UI
│   │   └── settings.html        # 수집 설정 UI
│   ├── requirements.txt
│   └── Dockerfile
├── db/
│   └── init.sql                 # 테이블 + pgvector
├── docker-compose.yml           # 로컬 개발용
├── docker-compose.prod.yml      # 회사 서버 배포용
└── README.md
```

---

## docker-compose.yml (v4)

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: rag
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports: ["5432:5432"]
    volumes:
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev -d rag"]
      interval: 5s
      timeout: 5s
      retries: 5

  server:
    build: ./server
    ports: ["3200:3200"]
    environment:
      DATABASE_URL: postgresql://dev:dev@postgres:5432/rag
      MODEL_NAME: intfloat/multilingual-e5-small
      PROJECT_ID: qcms
      VLLM_BASE_URL: http://host.docker.internal:7100/v1
      VLLM_MODEL: google/gemma-4-E4B-it
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./data/docs:/app/data/docs              # MD 문서 저장소
      - /c/Users/user/Desktop/Project:/source:ro # 소스코드 마운트
      - model-cache:/root/.cache/huggingface

volumes:
  pgdata:
  model-cache:
```

**프로젝트 교체 시**: `/source` 마운트 경로만 변경 + UI에서 base_path 수정 후 재색인.

---

## 배포 방식 (수동)

```bash
# 1. 로컬에서 이미지 빌드
docker compose build

# 2. 이미지 저장
docker save rag-server:latest | gzip > rag-server.tar.gz
docker save pgvector/pgvector:pg16 | gzip > pgvector.tar.gz

# 3. 회사 서버로 전송
scp -P 58322 rag-server.tar.gz pgvector.tar.gz itid@49.254.140.96:~/rag/

# 4. 회사 서버에서 로드 + 실행
ssh -p 58322 itid@49.254.140.96
cd ~/rag
gunzip -c rag-server.tar.gz | docker load
gunzip -c pgvector.tar.gz | docker load
docker compose -f docker-compose.prod.yml up -d
```

---

## 구현 순서

| 단계 | 작업 | 산출물 |
|---|---|---|
| 1 | DB 스키마 추가 (index_settings) | init.sql 수정 |
| 2 | SQLAlchemy 모델 추가 | models.py 수정 |
| 3 | 문서 관리 API (docs.py) | 업로드/수정/삭제 + 자동 색인 |
| 4 | 수집 설정 API (settings.py) | 설정 CRUD + 색인 실행 |
| 5 | indexer.py 개선 | 삭제 파일 감지, 설정 기반 색인 |
| 6 | 문서 관리 UI (docs.html) | 파일 목록/업로드/수정/삭제 |
| 7 | 수집 설정 UI (settings.html) | 경로/패턴 관리 + 색인 버튼 |
| 8 | 채팅 UI 네비게이션 추가 | 페이지 간 이동 |
| 9 | data/docs 기존 MD 정리 | 문서 이관 |
| 10 | 회사 서버 수동 배포 | 이미지 전송 + 실행 |
