# Q-CMS RAG Chatbot

Q-CMS 솔루션의 소스/문서를 시맨틱 검색하고 LLM으로 답변하는 RAG 챗봇.

## 기술 스택

- **FastAPI** — 검색 + 색인 + 채팅 API
- **PostgreSQL + pgvector** — 벡터 DB
- **sentence-transformers (multilingual-e5-small)** — 로컬 임베딩 (무료, API 키 불필요)
- **VLLM (gemma-4-E4B-it)** — LLM 서버 (OpenAI-compatible API)
- **Docker Compose** — 원클릭 실행

## 빠른 시작

```bash
# 1. 실행
docker compose up -d

# 2. 색인
curl -s -X POST http://localhost:3200/index \
  -H "Content-Type: application/json" \
  -d '{"targets":[{"glob":"*/**/*.md","doc_type":"convention"}]}'

# 3. 검색
curl -s "http://localhost:3200/search?q=게시판+목록&top_k=3"

# 4. 채팅 UI
# http://localhost:3200/ui/
```

## API

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/chat` | RAG 검색 + LLM 답변 |
| GET | `/search?q=&top_k=&type=` | 시맨틱 검색 |
| POST | `/index` | 전체 색인 (증분: 변경 파일만) |
| POST | `/file` | 단일 파일 색인 |
| GET | `/stats` | 색인 통계 |
| GET | `/health` | 서버 상태 |
| GET | `/ui/` | 채팅 웹 UI |

## 색인

```bash
curl -s -X POST http://localhost:3200/index \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

증분 색인: 파일 SHA-256 hash를 비교하여 **변경된 파일만** 재색인.

### doc_type 분류

| doc_type | 용도 |
|---|---|
| `convention` | 컨벤션, 코드 규칙 |
| `architecture` | 아키텍처, 설계 문서 |
| `source` | 소스 코드 (Service, Controller, Composable 등) |
| `policy` | 비즈니스 정책 |

## 채팅

### API

```bash
curl -s -X POST http://localhost:3200/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"게시판 목록 조회 방법","top_k":5}'
```

### 웹 UI

`http://localhost:3200/ui/` 에서 브라우저로 채팅.

## 운영

```bash
# 시작
docker compose up -d

# 중지
docker compose down

# 로그 확인
docker logs rag-server-1

# 데이터 초기화 (볼륨 삭제)
docker compose down -v
```

## 회사 서버 배포

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

VLLM (gemma-4-E4B-it, port 7100)과 자동 연동.
