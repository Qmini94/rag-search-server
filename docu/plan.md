# RAG 검색 서버 — 프로젝트 계획서 v3 (구현 완료)

## 목적

Claude Code 개발 환경에서 코드 작성 전 기존 컨벤션, 아키텍처, 비즈니스 정책, 소스 패턴을 자동 검색하여 일관된 코드를 생성하도록 지원하는 로컬 RAG 서버.

멀티 프로젝트 지원 — 프로젝트별로 문서를 분리 저장하고, 검색 시 프로젝트를 지정.

---

## 기술 스택

| 컴포넌트 | 기술 | 선택 이유 |
|---|---|---|
| API 서버 | **Python + FastAPI** | 검색 + 색인 단일 서버. 임베딩 모델과 같은 런타임 |
| 벡터 DB | **PostgreSQL + pgvector** | 별도 DB 불필요 |
| 임베딩 모델 | **intfloat/multilingual-e5-small** | 로컬 무료, 한국어+영어, 384차원 |
| 컨테이너 | **Docker Compose** | 로컬 원클릭 실행 |

※ Go + Gin은 별도 사이드 프로젝트로 분리 (NHN JD 매칭용)

---

## 아키텍처

```
CLAUDE.md (또는 hooks)
  "curl http://localhost:3200/projects/jh/search?q=게시판+API"
       │
       ▼
┌──────────────────────────────────┐
│  FastAPI (:3200)                 │  ← 단일 서버
│                                  │
│  [검색]                          │
│  GET  /projects                  │  프로젝트 목록
│  GET  /projects/:id/search       │  프로젝트 내 검색
│  GET  /health                    │
│                                  │
│  [색인]                          │
│  POST /projects                  │  프로젝트 등록
│  POST /projects/:id/index        │  전체 색인 (증분)
│  POST /projects/:id/file         │  단일 파일 색인
│  DELETE /projects/:id            │  프로젝트 삭제
│  GET  /projects/:id/stats        │  색인 통계
│                                  │
│  sentence-transformers           │  ← 임베딩 모델 내장
│  multilingual-e5-small (384d)    │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  PostgreSQL + pgvector (:5432)   │
│                                  │
│  projects 테이블                  │
│  documents 테이블 (HNSW 인덱스)   │
└──────────────────────────────────┘
```

---

## DB 스키마

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- 프로젝트
CREATE TABLE projects (
    id          VARCHAR(50) PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    base_path   VARCHAR(500) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- 문서 청크
CREATE TABLE documents (
    id           BIGSERIAL PRIMARY KEY,
    project_id   VARCHAR(50) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    content      TEXT NOT NULL,
    embedding    vector(384) NOT NULL,
    source       VARCHAR(500) NOT NULL,
    file_hash    VARCHAR(64) NOT NULL,        -- SHA-256 (증분 색인용)
    doc_type     VARCHAR(50) NOT NULL,         -- convention, architecture, source, policy, deploy
    language     VARCHAR(20),                  -- java, vue, typescript, markdown
    chunk_index  INT NOT NULL DEFAULT 0,
    updated_at   TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_project_source_chunk UNIQUE(project_id, source, chunk_index)
);

-- HNSW 인덱스 (데이터 양 무관, IVFFlat보다 검색 품질 좋음)
CREATE INDEX idx_documents_embedding
    ON documents USING hnsw (embedding vector_cosine_ops);

-- 프로젝트 + doc_type 필터용
CREATE INDEX idx_documents_project_type ON documents(project_id, doc_type);

-- 증분 색인 시 hash 비교용
CREATE INDEX idx_documents_source ON documents(project_id, source);
```

---

## API 명세

### 프로젝트 관리

```
GET /projects
→ {
    "projects": [
      { "id": "jh", "name": "장흥반값", "doc_count": 850 },
      { "id": "seo", "name": "SEO 분석 솔루션", "doc_count": 120 }
    ]
  }

POST /projects
Body: {
  "id": "jh",
  "name": "장흥반값",
  "base_path": "C:/Users/user/Desktop/Project/JH/half"
}

DELETE /projects/:id
→ 프로젝트 + 소속 문서 전체 삭제
```

### 색인

```
POST /projects/:id/index
Body: {
  "targets": [
    { "glob": "장흥반값/**/*.md", "doc_type": "convention" },
    { "glob": "jh-half-backend/src/**/service/**/*.java", "doc_type": "source" },
    { "glob": "jh-half-backend/src/**/controller/**/*.java", "doc_type": "source" },
    { "glob": "jh-half-frontend/src/components/**/*.vue", "doc_type": "source" },
    { "glob": "jh-half-frontend/src/composables/**/*.ts", "doc_type": "source" }
  ]
}
→ 증분 색인: file_hash 비교 → 변경된 파일만 재색인

POST /projects/:id/file
Body: { "file_path": "jh-half-backend/src/.../BoardService.java", "doc_type": "source" }
→ 단일 파일 색인

GET /projects/:id/stats
→ {
    "project": "jh",
    "total_chunks": 850,
    "by_type": { "source": 750, "convention": 50, "architecture": 30 },
    "by_language": { "java": 400, "vue": 200, "typescript": 100, "markdown": 50 }
  }
```

### 검색

```
GET /projects/:id/search?q={query}&top_k={5}&type={doc_type}
→ {
    "project": "jh",
    "query": "게시판 Service",
    "results": [
      {
        "content": "BoardService에서는 반드시 Repository를 통해...",
        "source": "jh-half-backend/src/.../BoardService.java",
        "doc_type": "source",
        "language": "java",
        "similarity": 0.89
      }
    ]
  }

GET /health
→ { "status": "ok", "projects": 2, "total_docs": 970 }
```

---

## 임베딩 모델 규칙 (E5 프리픽스)

multilingual-e5-small은 반드시 프리픽스를 붙여야 검색 품질이 보장됨:

```python
# 색인 시 (문서 저장)
text = "passage: " + chunk_text

# 검색 시 (쿼리)
text = "query: " + query_text
```

이걸 빠뜨리면 유사도 점수가 크게 떨어짐. embedder 서비스에서 용도별로 자동 처리.

---

## 색인 대상 (핵심 로직 위주)

### 포함 (가치 높음)
- 컨벤션/아키텍처/정책 문서 (.md)
- Service 클래스 — 비즈니스 로직 패턴
- Controller 클래스 — API 설계 패턴
- Vue Composable — 프론트 로직 패턴
- Vue Component — UI 구조 패턴
- 미들웨어, 설정 파일

### 제외 (노이즈)
- Entity/DTO/VO — getter/setter만 있음
- Repository — JPA 인터페이스만
- node_modules, build, .git
- 테스트 코드 (선택)

---

## 청킹 전략

### v1 (초기 — 단순하게 시작)

```
모든 파일: 고정 라인 기반
- 80줄 청크, 20줄 오버랩
- 파일 경로 + 언어 메타데이터 포함

Markdown만 예외:
- ## 헤딩 단위 분할 (자연스러운 의미 단위)
- 헤딩 없으면 80줄 기반
```

### v2 (추후 — 필요 시)
- Java: 메서드 단위 분할 (tree-sitter 파서)
- Vue: <script> 블록 내 함수 단위

---

## 증분 색인

```
전체 색인 요청 시:
1. glob으로 대상 파일 목록 수집
2. 각 파일의 SHA-256 hash 계산
3. DB에 저장된 file_hash와 비교
4. hash가 다른 파일만 → 해당 파일 청크 삭제 → 재청킹 → 재임베딩 → 저장
5. DB에 있지만 파일 시스템에 없는 문서 → 삭제 (파일 삭제 감지)
```

---

## 디렉토리 구조

```
RAG/
├── docu/                      # 설계 문서
│   ├── plan.md
│   └── 검증.txt
├── server/                    # FastAPI 단일 서버
│   ├── main.py                # FastAPI 앱 + 라우터 등록
│   ├── routers/
│   │   ├── project.py         # 프로젝트 CRUD
│   │   ├── index.py           # 색인 엔드포인트
│   │   └── search.py          # 검색 엔드포인트
│   ├── services/
│   │   ├── chunker.py         # 청킹 (라인 기반 + MD 헤딩)
│   │   ├── embedder.py        # sentence-transformers + E5 프리픽스
│   │   └── indexer.py         # 증분 색인 오케스트레이션
│   ├── db/
│   │   └── database.py        # SQLAlchemy + pgvector 연결
│   ├── models/
│   │   └── models.py          # SQLAlchemy 모델
│   ├── config.py
│   ├── requirements.txt
│   └── Dockerfile
├── db/
│   └── init.sql               # 테이블 + pgvector 확장
├── docker-compose.yml
├── .env.example
└── CLAUDE.md
```

---

## docker-compose.yml

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

  server:
    build: ./server
    ports: ["3200:3200"]
    environment:
      DATABASE_URL: postgresql://dev:dev@postgres:5432/rag
      MODEL_NAME: intfloat/multilingual-e5-small
    depends_on: [postgres]
    volumes:
      - /c/Users/user/Desktop/Project:/project:ro
      - model-cache:/root/.cache/huggingface

volumes:
  pgdata:
  model-cache:
```

---

## CLAUDE.md 연동

### 방법 1: CLAUDE.md 규칙 (수동)

```markdown
## RAG 검색 규칙
코드를 작성하거나 수정하기 전에 반드시 관련 패턴을 검색하세요:

curl -s "http://localhost:3200/projects/jh/search?q={키워드}&top_k=3" | jq '.results[] | {source, content}'
```

### 방법 2: hooks 자동화 (추후 검토)

```
Claude Code hooks (PreToolUse) 에서
Edit/Write 도구 호출 전 자동으로 RAG 검색 실행
→ 검색 결과를 컨텍스트에 주입
```

---

## 구현 순서

| 단계 | 작업 | 산출물 |
|---|---|---|
| 1 | Docker Compose + pgvector + init.sql | 인프라 실행 확인 |
| 2 | FastAPI 기본 구조 + DB 연결 + 모델 로딩 | 서버 부팅 확인 |
| 3 | 프로젝트 CRUD API | /projects 동작 확인 |
| 4 | 청킹 + 임베딩 + 색인 API (증분) | /projects/:id/index |
| 5 | 검색 API (E5 프리픽스 + 코사인 유사도) | /projects/:id/search |
| 6 | JH 프로젝트 등록 + 색인 + 검색 테스트 | curl로 검증 |
| 7 | CLAUDE.md 연동 실전 테스트 | 개발 중 활용 |

---

## 필요한 것

- Docker Desktop
- Python 3.11+ (로컬 개발 시)
- API 키 불필요

---

## 검증 반영 사항

| 검증 지적 | 반영 |
|---|---|
| Go+Python 2서버 불필요 | FastAPI 단일 서버로 통합 |
| IVFFlat 초기 데이터 문제 | HNSW로 변경 |
| 전체 삭제 후 재색인 | file_hash 기반 증분 색인 |
| 청킹 AST 파싱 난이도 | 80줄+20줄 오버랩으로 시작 |
| E5 프리픽스 누락 | query:/passage: 프리픽스 명시 |
| 소스 전체 색인 노이즈 | Service/Controller/Composable 위주 |
| CLAUDE.md 자동화 | hooks 방법 2 추후 검토 |

---

## 구현 결과 (v3)

### 해결한 버그

| 버그 | 원인 | 해결 |
|---|---|---|
| UniqueConstraint 충돌 | db.add() 후 autoflush가 delete 전에 발생 | delete 후 db.flush() 명시 |
| SQL `:embedding::vector` 파라미터 충돌 | SQLAlchemy `:param`과 PostgreSQL `::cast` 문법 충돌 | embedding을 문자열로 직접 삽입 |
| `**/*.md`가 node_modules 포함 | glob이 모든 하위 디렉토리 매칭 | EXCLUDE_DIRS 필터 추가 |
| 증분 색인 시 다른 doc_type 삭제 | 같은 doc_type의 모든 파일을 삭제 대상으로 판단 | 자동 삭제 로직 제거 (DELETE API 사용) |
| 프론트 소스 0개 색인 | `src/` 디렉토리가 없고 루트에 바로 위치 | glob 패턴 수정 |

### 현재 색인 현황

```
프로젝트 jh (JH Half):
  총 1,096 청크
  - java: 194 (Service, Controller)
  - vue: 372 (components, pages)
  - typescript: 164 (composables, middleware, stores)
  - markdown: 366 (컨벤션, 아키텍처 문서)

프로젝트 seo (SEO Analysis):
  총 80 청크
  - markdown: 74 (아키텍처, 기능명세)
  - txt: 6 (요구사항, JD)

전체: 1,176 청크, 2 프로젝트
```

### JH 프로젝트 색인 glob 패턴 (실제 사용)

```json
{
  "targets": [
    { "glob": "*/**/*.md", "doc_type": "convention" },
    { "glob": "jh-half-backend/src/**/service/**/*.java", "doc_type": "source" },
    { "glob": "jh-half-backend/src/**/controller/**/*.java", "doc_type": "source" },
    { "glob": "jh-half-frontend/components/**/*.vue", "doc_type": "source" },
    { "glob": "jh-half-frontend/composables/**/*.ts", "doc_type": "source" },
    { "glob": "jh-half-frontend/middleware/**/*.ts", "doc_type": "source" },
    { "glob": "jh-half-frontend/pages/**/*.vue", "doc_type": "source" },
    { "glob": "jh-half-frontend/stores/**/*.ts", "doc_type": "source" }
  ]
}
```

### GitHub

https://github.com/Qmini94/rag-search-server
