# RAG Search Server

Claude Code 개발 환경에서 프로젝트 소스/문서를 시맨틱 검색하는 로컬 RAG 서버.

코드 작성 전 기존 패턴을 검색하여 일관된 코드를 생성하도록 지원.

## 기술 스택

- **FastAPI** — 검색 + 색인 API
- **PostgreSQL + pgvector** — 벡터 DB
- **sentence-transformers (multilingual-e5-small)** — 로컬 임베딩 (무료, API 키 불필요)
- **Docker Compose** — 원클릭 실행

## 빠른 시작

```bash
# 1. 실행
docker compose up -d

# 2. 프로젝트 등록
curl -s -X POST http://localhost:3200/projects \
  -H "Content-Type: application/json" \
  -d '{"id":"jh","name":"JH Half","base_path":"/project/JH/half"}'

# 3. 색인
curl -s -X POST http://localhost:3200/projects/jh/index \
  -H "Content-Type: application/json" \
  -d '{"targets":[{"glob":"*/**/*.md","doc_type":"convention"}]}'

# 4. 검색
curl -s "http://localhost:3200/projects/jh/search?q=게시판+목록&top_k=3"
```

## API

### 프로젝트 관리

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/projects` | 프로젝트 목록 |
| POST | `/projects` | 프로젝트 등록 |
| DELETE | `/projects/:id` | 프로젝트 삭제 (문서 포함) |

### 색인

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/projects/:id/index` | 전체 색인 (증분: 변경 파일만) |
| POST | `/projects/:id/file` | 단일 파일 색인 |
| GET | `/projects/:id/stats` | 색인 통계 |

### 검색

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/projects/:id/search?q=&top_k=&type=` | 시맨틱 검색 |
| GET | `/health` | 서버 상태 |

## 색인 가이드

### 프로젝트 등록

```bash
curl -s -X POST http://localhost:3200/projects \
  -H "Content-Type: application/json" \
  -d '{"id":"프로젝트ID","name":"프로젝트명","base_path":"/project/경로"}'
```

`base_path`는 Docker 컨테이너 내부 경로. `docker-compose.yml`에서 호스트의 `C:\Users\user\Desktop\Project`가 `/project`로 마운트됨.

### 전체 색인

```bash
curl -s -X POST http://localhost:3200/projects/jh/index \
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

증분 색인: 파일 SHA-256 hash를 비교하여 **변경된 파일만** 재색인. 동일하면 skip.

### doc_type 분류

| doc_type | 용도 |
|---|---|
| `convention` | 컨벤션, 코드 규칙 |
| `architecture` | 아키텍처, 설계 문서 |
| `source` | 소스 코드 (Service, Controller, Composable 등) |
| `policy` | 비즈니스 정책 |
| `deploy` | 배포, 인프라 설정 |

### 단일 파일 색인

```bash
curl -s -X POST http://localhost:3200/projects/jh/file \
  -H "Content-Type: application/json" \
  -d '{"file_path":"장흥반값/게시판_전체_Render_흐름.md","doc_type":"convention"}'
```

### 자동 제외 디렉토리

`node_modules`, `.git`, `.idea`, `build`, `dist`, `.nuxt`, `.next`, `target`, `vendor` 등은 자동 제외.

## 검색 가이드

### 기본 검색

```bash
curl -s "http://localhost:3200/projects/jh/search?q=게시판+목록+조회&top_k=3"
```

### doc_type 필터

```bash
# 소스 코드에서만 검색
curl -s "http://localhost:3200/projects/jh/search?q=board+service&type=source&top_k=3"

# 문서에서만 검색
curl -s "http://localhost:3200/projects/jh/search?q=미들웨어+렌더&type=convention&top_k=3"
```

### 응답 형식

```json
{
  "project": "jh",
  "query": "게시판 목록 조회",
  "results": [
    {
      "content": "...",
      "source": "jh-half-frontend/components/theme/flow/default/list/Ori.vue",
      "doc_type": "source",
      "language": "vue",
      "similarity": 0.882
    }
  ]
}
```

### jq로 보기 좋게 출력

```bash
# content만
curl -s "http://localhost:3200/projects/jh/search?q=JWT+인증&top_k=3" | jq '.results[].content'

# source + content
curl -s "http://localhost:3200/projects/jh/search?q=JWT+인증&top_k=3" | jq '.results[] | {source, content}'
```

## 문서 업데이트 반영

### 수동

```bash
# 변경된 파일이 있는 범위만 다시 실행 (변경 없으면 skip)
curl -s -X POST http://localhost:3200/projects/jh/index \
  -H "Content-Type: application/json" \
  -d '{"targets":[{"glob":"*/**/*.md","doc_type":"convention"}]}'
```

### git hook 자동화 (선택)

```bash
# .git/hooks/post-commit
#!/bin/bash
curl -s -X POST http://localhost:3200/projects/jh/index \
  -H "Content-Type: application/json" \
  -d '{"targets":[{"glob":"*/**/*.md","doc_type":"convention"}]}' > /dev/null 2>&1 &
```

## Claude Code 연동

프로젝트의 `CLAUDE.md`에 아래 규칙 추가:

```markdown
## RAG 검색 규칙
코드를 작성하거나 수정하기 전에 반드시 관련 패턴을 검색하세요.

curl -s "http://localhost:3200/projects/jh/search?q={키워드}&top_k=3" | jq '.results[] | {source, content}'
```

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
