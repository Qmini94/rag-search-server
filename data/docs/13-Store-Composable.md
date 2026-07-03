# Store 및 Composable 패턴

## 개요

Q-CMS 프론트엔드는 **Pinia 스토어**로 전역 상태를, **Composable**로 페이지/컴포넌트 로직을 관리한다.

```
Store (전역 상태)          Composable (로직 캡슐화)
├── siteStore             ├── api/admin/    관리자 API
├── menuStore             ├── api/render/   렌더링 API
├── renderStore           └── utils/        유틸리티
├── userStore
└── uiStore
```

## Composable 패턴

### 렌더링 API (composables/api/render/)

게시판 렌더링에서 사용하는 composable 체계.

#### useBoard.ts (useBoardRenderer) — 핵심

모든 게시판 로직을 조합하는 최상위 composable.

```typescript
const { core, listCtx, gallery, flow } = useBoardRenderer()
```

내부에서 하위 composable을 조합:

```
useBoardRenderer
├── useBoardRoute()          쿼리 파라미터 (mode, idx, page, keyword 등)
├── useBoardList()           목록 조회 (fetchBoardList, fetchFieldDefs)
├── useBoardCrud()           상세/저장/삭제 (fetchArticleDetail, saveArticle)
├── useBoardComment()        댓글 CRUD
├── useBoardPermission()     권한 (canWrite, canModify, isOwner)
├── useBoardGallery()        갤러리 전용 (선택적)
└── useBoardFlow()           진행상태 전용 (선택적)
```

#### useBoardRoute.ts — 라우트 상태

```typescript
// 반환값 (ref)
mode           // "list" | "view" | "write" | "modify"
queryPage      // 현재 페이지
querySize      // 페이지 크기
queryKeyword   // 검색 키워드
queryType      // 검색 타입
queryStartDate // 시작일
queryEndDate   // 종료일
queryIdx       // 게시글 idx (view/modify 시)
```

#### useBoardList.ts — 목록 데이터

```typescript
fetchBoardList()    // GET /board/list → boardList, totalPages, totalElements
fetchFieldDefs()    // GET /board/fields → fieldDefinitions, searchableFields
```

#### useBoardCrud.ts — CRUD

```typescript
fetchArticleDetail()  // GET /board/{idx} → viewData, formData
saveArticle()         // POST /board → 저장 (create/update)
deleteArticle()       // DELETE /board/{idx}
// prevPost, nextPost: 이전/다음 글
```

#### useBoardComment.ts — 댓글

```typescript
fetchComments()   // 댓글 목록
submitComment()   // 댓글 작성
updateComment()   // 댓글 수정
deleteComment()   // 댓글 삭제
```

#### useBoardPermission.ts — 권한

```typescript
canWrite      // 글쓰기 가능
canModify     // 수정 가능
canRemove     // 삭제 가능
isOwner       // 작성자 여부
```

#### useBoardOptionHelpers.ts — 옵션 헬퍼

게시판 옵션(상단고정, 비공개, 기간 등)에 따른 UI 분기 헬퍼.

### 기타 렌더링 Composable

| Composable | 용도 |
|---|---|
| useContent.ts | 콘텐츠 조회 (parentId로 공개 버전) |
| usePopup.ts | 팝업 목록 조회 (active 필터) |
| useVisualBanner.ts | 비주얼 배너 캐러셀 |
| useApplyFlow.ts | 신청 폼 멀티스텝 (step1→step2→step3) |
| useMenuOverride.ts | 메뉴 오버라이드 |

### 관리자 API (composables/api/admin/)

관리자 페이지에서 사용하는 API composable.

| Composable | 용도 |
|---|---|
| useBoardMasterManager.ts | 게시판 마스터 CRUD |
| useContentManager.ts | 콘텐츠 관리 |
| useSiteManager.ts | 사이트 관리 |
| usePermissionManager.ts | 권한 관리 |
| useMemberManager.ts | 회원 관리 |
| useAuditManager.ts | 감사 로그 |

하위 디렉토리별:

```
composables/api/admin/
├── asset/     에셋 관리 API
├── board/     게시판 관리 API
├── content/   콘텐츠 관리 API
├── css/       CSS 편집 API
├── menu/      메뉴 관리 API
├── popup/     팝업 관리 API
├── member/    회원 관리 API
└── audit/     감사 로그 API
```

### 인증 (composables/api/useAuth.ts)

```typescript
login(userId, password)    // POST /auth/login
logout()                   // DELETE /auth/logout
verifySession()           // 세션 유효성 확인
```

## safeFetch 패턴

모든 API 호출은 `utils/safeFetch.ts`를 통한다.

```typescript
// SSR/CSR 안전한 fetch
safeFetch(url, options)

기능:
- SSR: 서버에서 백엔드 직접 호출 (NUXT_API_BASE)
- CSR: 브라우저에서 Nginx 경유 (NUXT_PUBLIC_API_BASE)
- 요청 캐싱 (동일 URL 중복 방지)
- 타임아웃
- 인증 에러 처리 (401 → 로그인 리다이렉트)
- 세션 만료 처리 (X-Session-Expires 헤더)
- 쿠키 포워딩 (SSR 시 cookie, user-agent, accept-language만)
- XSRF 토큰 자동 포함 (X-XSRF-TOKEN 헤더)
```

## Provide/Inject 패턴

Board.vue에서 컨텍스트를 provide하고 테마 컴포넌트에서 inject한다.

```typescript
// types/site/boardKeys.ts — 인젝션 키

export const boardCoreKey: InjectionKey<BoardCoreContext>
export const boardListKey: InjectionKey<BoardListContext>
export const boardGalleryKey: InjectionKey<BoardGalleryContext>
export const boardFlowKey: InjectionKey<BoardFlowContext>
```

```typescript
// Board.vue
const { core, listCtx } = useBoardRenderer()
provide(boardCoreKey, core)
provide(boardListKey, listCtx)

// 테마 Ori.vue
const core = inject(boardCoreKey)!
const { boardList, currentPage } = core
```

## Cross-Tab 인증 (authBus)

`utils/authBus.ts`로 탭 간 인증 이벤트를 동기화한다.

```typescript
// 이벤트 타입
LOGIN            // 로그인 완료
LOGOUT           // 로그아웃
PROFILE_UPDATED  // 프로필 변경

// userStore에서 watch
authBus.on('LOGIN', () => fetchUser())
authBus.on('LOGOUT', () => clearUser())
```

## TanStack Query 사용

`@tanstack/vue-query`로 일부 API 호출에 캐싱/재시도를 적용한다.

```typescript
// plugins/vue-query.client.ts (클라이언트 전용)
nuxtApp.vueApp.use(VueQueryPlugin, {
  queryClientConfig: {
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,   // 탭 포커스 복귀시 재요청 금지
        refetchOnReconnect: false,     // 네트워크 복구시 재요청 금지
        refetchOnMount: false,         // 마운트시 자동 재요청 금지
        staleTime: Infinity,           // 항상 '신선' 취급 → 자동 재검증 안 함
        retry: 0,                      // 재시도 없음
        gcTime: 5 * 60 * 1000          // 5분 후 가비지 컬렉션
      }
    }
  }
})
```
