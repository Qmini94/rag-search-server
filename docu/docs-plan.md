# Q-CMS RAG 문서 작성 계획

## 목적

Q-CMS 솔루션을 처음 접하는 개발자가 RAG 챗봇으로 질문했을 때 정확한 답변을 받을 수 있도록, 체계적이고 구체적인 문서를 작성한다.

---

## 문서 목록 (작성 순서)

### Part 1. 환경 셋업

| # | 파일명 | 주제 | 내용 |
|---|---|---|---|
| 01 | `01-프로젝트-개요.md` | Q-CMS 솔루션 소개 | 기술 스택, 디렉토리 구조, 멀티사이트 개념, 주요 기능 목록 |
| 02 | `02-개발환경-셋업.md` | 로컬 개발 환경 구축 | Docker Compose(MySQL/Redis/Gitea/Jenkins), 백엔드/프론트엔드 실행, 환경변수 설정 |
| 03 | `03-Git-워크플로우.md` | Git + CI/CD | Gitea 저장소 구조, 브랜치 전략, Jenkins 파이프라인, 빌드/배포 흐름 |
| 04 | `04-배포-가이드.md` | 서버 구축 및 배포 | Rocky Linux 서버 셋업, Docker 오프라인 설치, Nginx, relay→운영 이관, 환경별 설정 |

### Part 2. 백엔드 아키텍처

| # | 파일명 | 주제 | 내용 |
|---|---|---|---|
| 05 | `05-백엔드-구조.md` | 패키지 구조 및 레이어 | controller/service/repository/entity/dto 레이어, MapStruct, QueryDSL, 네이밍 규칙 |
| 06 | `06-인증-권한.md` | JWT + 세션 + 권한 | JWT 쿠키 기반 인증, Redis 세션, PermissionService, IP 제어, XSS 보호 |
| 07 | `07-게시판-시스템.md` | 동적 게시판 핵심 로직 | BoardMaster, DynamicBoard, 동적 DDL/SQL, 필드정의, 옵션 프로세서(관리자답변/비공개/기간 등) |
| 08 | `08-메뉴-콘텐츠.md` | 메뉴 트리 + 콘텐츠 | Menu 계층 구조, 메뉴 타입(folder/board/content/script/link), Content CRUD, 버전 관리 |
| 09 | `09-파일-에셋.md` | 파일 업로드 + 에셋 관리 | BoardFile, 이미지 리사이즈, 에셋 디렉토리 탐색, 보안(path traversal 방지) |

### Part 3. 프론트엔드 아키텍처

| # | 파일명 | 주제 | 내용 |
|---|---|---|---|
| 10 | `10-프론트엔드-구조.md` | Nuxt 3 프로젝트 구조 | 디렉토리 구성, nuxt.config, SSR 설정, 주요 의존성, auto-import |
| 11 | `11-미들웨어-체인.md` | 미들웨어 01~06 | 사이트초기화 → 레이아웃 → 인증 → 메뉴 → 권한체크 → 컬러모드, SSR/CSR 분기 처리 |
| 12 | `12-렌더링-시스템.md` | 게시판/콘텐츠 렌더링 | [...slug].vue catch-all, renderStore, Board.vue/Content.vue, 테마 시스템(Loader/Ori/overrides) |
| 13 | `13-Store-Composable.md` | 상태관리 + API 패턴 | Pinia 스토어(site/menu/render/user/ui), composable 패턴(useXxxApi/useXxxManager), safeFetch |
| 14 | `14-관리자-UI.md` | business 페이지 구조 | 관리자 대시보드, 사이트/메뉴/게시판/콘텐츠/팝업/에셋/CSS 관리 화면 구조 |

### Part 4. 주요 기능

| # | 파일명 | 주제 | 내용 |
|---|---|---|---|
| 15 | `15-팝업-배너.md` | 팝업 + 비주얼배너 | LAYER(모달)/VISUAL(인라인) 타입, 이미지별 기간, 관리자 설정, composable 패턴 |
| 16 | `16-CSS-실시간편집.md` | CSS 에디터 | CodeMirror, 잠금 메커니즘, 버전관리, SHARED_DIR 구조, 캐시 버스팅 |
| 17 | `17-개발-컨벤션.md` | 코딩 규칙 | 프론트(Vue/TS 컨벤션, Tailwind, Element Plus), 백엔드(레이어 규칙, 에러처리), API 네이밍 |

---

## 작성 원칙

1. **RAG 검색에 최적화** — `##` 헤딩 단위로 의미 있는 청크가 되도록 구성
2. **코드 예시 포함** — 실제 파일 경로와 핵심 코드 스니펫 포함
3. **파일 경로 명시** — 관련 소스 파일 경로를 항상 기재
4. **Q&A 친화적** — "~는 어떻게 동작하는가?" 질문에 답할 수 있는 구조
5. **독립적 문서** — 각 문서가 독립적으로 읽힐 수 있도록 최소한의 컨텍스트 포함

## 작성 방법

1. 관련 소스코드 분석 (Agent로 코드 탐색)
2. 기존 문서 내용 반영 (장흥반값/ 기존 MD 참고)
3. 문서 작성 → `data/docs/`에 저장
4. RAG 색인 → 챗봇 테스트

---

## 기존 문서 → 신규 문서 매핑

| 기존 (장흥반값/) | 신규 문서 | 비고 |
|---|---|---|
| Git_가이드.md | 03-Git-워크플로우.md | 내용 흡수 + CI/CD 추가 |
| 서버구축-진행순서.md | 04-배포-가이드.md | 내용 흡수 + 정리 |
| DEPLOYMENT_GUIDE.md | 04-배포-가이드.md | 병합 |
| 게시판_전체_Render_흐름.md | 07, 11, 12에 분산 | 백엔드/프론트 분리 |
| 개발_컨벤션_가이드.md | 17-개발-컨벤션.md | 내용 흡수 + 보완 |
| sprint-popup-management.md | 15-팝업-배너.md | 구현 결과 반영 |
| sprint-visual-banner.md | 15-팝업-배너.md | 병합 |
| 관리자_CSS_실시간편집_Sprint.md | 16-CSS-실시간편집.md | 구현 결과 반영 |
| make-theme_스킬_전략.md | 12-렌더링-시스템.md | 테마 변환 규칙 포함 |
| 콘텐츠관리_트리기반_리팩토링_Sprint.md | 08-메뉴-콘텐츠.md | 트리 구조 반영 |
| 이미지관리_스프린트.md | 09-파일-에셋.md | 에셋 관리 반영 |
| sprint_plan.md (신청) | 제외 | 프로젝트 특화 (솔루션 공통 아님) |
