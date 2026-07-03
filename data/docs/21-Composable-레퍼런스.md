# Composable 레퍼런스

Q-CMS 프론트엔드(Nuxt 3)의 모든 Composable 함수를 카테고리별로 정리한 레퍼런스 문서.

> **참고**: 관리자(business) 사이트는 Element Plus + Tailwind CSS 사용, 사용자(www) 사이트는 퍼블리싱 CSS 사용.

```
composables/
├── useVersionedCss.ts          CSS 캐시 버스팅
├── api/
│   ├── useAuth.ts              인증 (로그인/로그아웃)
│   ├── render/                 사용자 사이트 렌더링
│   └── admin/                  관리자 페이지 API
└── utils/
    ├── useImeSafeInput.ts      한글 IME 입력 안전 처리
    └── useLegacyGnbJqShim.ts  퍼블리셔 jQuery 호환 레이어
```

---

## 1. 인증/권한 관련

### `useAuth` — `composables/api/useAuth.ts`

로그인·로그아웃 처리. 입력 검증, userStore/renderStore 초기화, 리다이렉트까지 담당.

**파라미터**: 없음 (함수 호출 시 반환된 메서드에 인자 전달)

**반환값**:

| 함수 | 설명 |
|---|---|
| `login(userId, password, redirect?)` | POST /auth/login → userStore 갱신 후 이동 |
| `logout()` | DELETE /auth/logout → userStore/renderStore 초기화 후 페이지 리로드 |

**주요 동작**:
- `login`: 아이디/비밀번호 유효성 검증 → API 호출 → userStore.setUser → renderStore.clear → 안전한 경로로 리다이렉트
- `logout`: 로그아웃 API (실패해도 강제 로그아웃) → 스토어 초기화 → window.location.reload()

**사용 예시**:
```typescript
const { login, logout } = useAuth()
await login('admin', 'password', '/dashboard')
await logout()
```

---

### `usePermissionManager` — `composables/api/admin/usePermissionManager.ts`

메뉴별 권한 매트릭스 관리. `selectedMenuRef`(inject)로 선택 메뉴를 감지하고 권한 체인을 자동 로드.

> 관리자(business) 사이트 전용.

**파라미터**: 없음 (inject로 `selectedMenuRef` 수신)

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `menu` | `Computed<Menu \| null>` | 현재 선택 메뉴 |
| `displayPathString` | `Computed<string>` | 메뉴 경로 (`A > B > C`) |
| `permOrder` | `PermKey[]` | 권한 순서 (MANAGE/ACCESS/VIEW/WRITE/MODIFY/REMOVE) |
| `permLabel` | `Record<PermKey, string>` | 권한 키 → 한글 라벨 |
| `subjectsCurrent` | `Ref<SubjectRowEx[]>` | 현재 메뉴 권한 대상 목록 |
| `subjectsInherited` | `Ref<SubjectRowEx[]>` | 상위 메뉴에서 상속된 대상 목록 |
| `matrixCurrent` | `Reactive<Record<string, PermMap>>` | 현재 메뉴 권한 매트릭스 |
| `matrixInherited` | `Reactive<Record<string, PermMap>>` | 상속 권한 매트릭스 (읽기 전용) |
| `visibleSubjects` | `Computed<SubjectRowEx[]>` | showInherited 토글에 따라 표시할 대상 목록 |
| `saving` | `Ref<boolean>` | 저장 진행 중 여부 |
| `addSubject(input)` | 함수 | 권한 대상 추가 |
| `removeSubject(k)` | 함수 | 권한 대상 제거 |
| `moveUp(k)` / `moveDown(k)` | 함수 | 정렬 순서 이동 |
| `toggleDecision(k, pKey)` | 함수 | 권한 ON/OFF 토글 |
| `loadPermissionChain()` | 함수 | GET /permission/chain → 상태 반영 |
| `savePermission(opts?)` | 함수 | PUT /permission/{menuId}/entries |

**동작**: 메뉴 변경 watch → 자동 `loadPermissionChain()` 호출

**사용 예시**:
```typescript
const {
  visibleSubjects, matrixCurrent, permOrder, permLabel,
  addSubject, toggleDecision, savePermission
} = usePermissionManager()

toggleDecision('LEVEL:10', 'ACCESS')
await savePermission()
```

---

## 2. 게시판/콘텐츠 관련

### `useBoardRenderer` — `composables/api/render/useBoard.ts`

게시판 전체 로직을 조합하는 최상위 Composable. Board.vue에서 호출하여 결과를 provide한다.

**파라미터**: 없음

**반환값**:

| 반환값 | 설명 |
|---|---|
| `core` (`BoardCoreContext`) | 목록/상세/댓글/권한/파일/옵션 등 모든 상태와 함수 |
| `listCtx` (`BoardListContext`) | 리스트 전용 — 카테고리 목록 |
| `gallery` (`BoardGalleryContext`) | 갤러리 전용 — galleryImages, gridCols |
| `flow` (`BoardFlowContext`) | 진행상태 전용 — steps, currentStep, stepStatus |

**내부 조합 구조**:
```
useBoardRenderer
├── useBoardRoute()          라우트 쿼리 상태 (mode, page, keyword 등)
├── useBoardList(rs)         목록 조회 (fetchBoardList, fetchFieldDefs)
├── useBoardCrud(rs)         상세/저장/삭제 (fetchArticleDetail, saveArticle, deleteArticle)
├── useBoardComment(rs)      댓글 CRUD
├── useBoardPermission(rs)   권한 (canWrite, canModify, canRemove, isOwner)
├── useBoardListContext(rs)  카테고리 목록 추출
├── useBoardGallery(rs)      이미지 파일 추출 (galleryImages)
└── useBoardFlow(rs)         단계별 상태 (steps, currentStep)
```

**SSR/CSR 동작**:
- `onServerPrefetch`에서 `Promise.all`로 목록/상세/댓글 병렬 조회 (Nuxt context 소실 방지)
- CSR에서는 쿼리 변경을 `watch`하여 자동 재조회 (`immediate: true`)

**사용 예시**:
```typescript
// Board.vue
const { core, listCtx, gallery, flow } = useBoardRenderer()
provide(boardCoreKey, core)
provide(boardListKey, listCtx)
provide(boardGalleryKey, gallery)
provide(boardFlowKey, flow)
```
```typescript
// 테마 Ori.vue
const core = inject(boardCoreKey)!
const { boardList, mode, canWrite, saveArticle } = core
```

---

### `useBoardRoute` — `composables/api/render/useBoardRoute.ts`

게시판 라우트 쿼리를 반응형 상태로 변환. `useState`로 SSR ↔ CSR 하이드레이션을 유지하며 게시판 경로별로 상태를 분리한다(`board:{route.path}` 키).

**파라미터**: 없음

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `mode` | `Computed<string>` | `"list"` \| `"view"` \| `"write"` \| `"modify"` |
| `isListPage` / `isViewPage` / `isWritePage` / `isModifyPage` | `Computed<boolean>` | 모드 분기용 |
| `queryPage` / `querySize` / `querySort` | `Computed` | 페이징 파라미터 |
| `queryKeyword` / `queryType` / `queryStartDate` / `queryEndDate` | `Computed` | 검색 파라미터 |
| `boardList` | `useState<BoardListItem[]>` | 목록 데이터 |
| `totalPages` / `totalElements` / `currentPage` | `useState<number>` | 페이징 상태 |
| `viewData` | `useState<BoardViewData \| null>` | 상세 데이터 |
| `formData` | `useState<BoardFormData>` | 작성/수정 폼 데이터 |
| `boardOption` | `Computed<BoardOption \| null>` | renderStore에서 참조한 게시판 설정 |
| `fieldDefs` | `useState<BoardFieldDef[]>` | 필드 정의 목록 |
| `searchableFields` | `Computed<BoardFieldDef[]>` | 검색 가능 필드 목록 |
| `fetchError` / `isLoading` | `useState` | 오류/로딩 상태 |
| `updateQuery(params)` | 함수 | 라우터 쿼리 병합 업데이트 (pidx는 명시 없으면 항상 제거) |

---

### `useBoardList` — `composables/api/render/useBoardList.ts`

게시판 목록 조회 및 필드 정의 조회.

**파라미터**: `rs: BoardRouteState` (useBoardRoute 반환값)

**반환값**:

| 반환값 | 설명 |
|---|---|
| `searchTypeOptions` | `Computed` — fieldDefs 기반 동적 검색 항목 (폴백: 제목/내용/등록자) |
| `fetchFieldDefs()` | GET /board/fields → fieldDefs, searchableFields 갱신 |
| `fetchBoardList()` | GET /board (쿼리 파라미터 포함) → boardList, totalPages, totalElements 갱신 |

---

### `useBoardCrud` — `composables/api/render/useBoardCrud.ts`

게시글 상세 조회, 작성 초기화, 저장, 삭제, 첨부파일 처리.

**파라미터**: `rs: BoardRouteState`

**반환값**:

| 반환값 | 설명 |
|---|---|
| `attachments` | `useState<BoardFile[]>` — 첨부파일 목록 |
| `prevPost` / `nextPost` | `useState<NavItem \| null>` — 이전/다음 글 |
| `fetchArticleDetail()` | GET /board/{idx}/nav → viewData, attachments, prevPost, nextPost 갱신 |
| `initWriteForm()` | 작성 폼 초기화 (pidx 답글 처리 포함) |
| `saveArticle()` | POST/PUT /board → 저장 후 파일 업로드, 성공 시 view/list로 이동 |
| `deleteArticle()` | DELETE /board/{idx} → 확인 후 삭제, list로 이동 |

**주요 동작**:
- 접근 차단 체크 (code 4030 → 목록으로 리다이렉트)
- 제목(50자)/내용 검증, 기간 논리 검증(시작일 ≤ 종료일) 수행
- 첨부파일: 게시글 저장 성공 후 별도 POST /board/{idx}/files 업로드
- 수정 모드: 유지할 기존 파일 목록을 `meta` JSON으로 전달

---

### `useBoardComment` — `composables/api/render/useBoardComment.ts`

게시글 댓글 CRUD.

**파라미터**: `rs: BoardRouteState`

**반환값**:

| 반환값 | 설명 |
|---|---|
| `comments` | `useState<BoardComment[]>` — 댓글 목록 |
| `fetchComments()` | GET /board/{idx}/comments |
| `submitComment(content, parentIdx?)` | POST /board/{idx}/comments (대댓글 지원) |
| `updateComment(commentIdx, content)` | PUT /board/{idx}/comments/{commentIdx} |
| `deleteComment(commentIdx)` | DELETE /board/{idx}/comments/{commentIdx} |

---

### `useBoardPermission` — `composables/api/render/useBoardPermission.ts`

현재 사용자의 게시판 권한 판단.

**파라미터**: `rs: BoardRouteState`

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `isOwner` | `Computed<boolean>` | 작성자 본인 여부 (regId === currentUserId) |
| `canWrite(permission?)` | 함수 | 쓰기 가능 여부 (permission.write AND (isOwner OR manage OR isAdmin)) |
| `canModify(permission?)` | 함수 | 수정 가능 여부 |
| `canRemove(permission?)` | 함수 | 삭제 가능 여부 |

---

### `useBoardListContext` — `composables/api/render/useBoardListContext.ts`

리스트/썸네일 타입 전용. boardList에서 카테고리 고유값을 추출. list/thumb 타입일 때만 Board.vue에서 provide된다.

**파라미터**: `rs: BoardRouteState`

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `categories` | `Computed<string[]>` | boardList의 category_1 고유값 정렬 목록 |

---

### `useBoardGallery` — `composables/api/render/useBoardGallery.ts`

갤러리 타입 전용. boardList 항목에서 이미지 파일만 추출. gallery 타입일 때만 Board.vue에서 provide된다.

**파라미터**: `rs: BoardRouteState`

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `galleryImages` | `Computed<GalleryImage[]>` | isImage=true인 첨부파일 목록 |
| `gridCols` | `Ref<number>` | 그리드 컬럼 수 (기본 4) |

---

### `useBoardFlow` — `composables/api/render/useBoardFlow.ts`

진행상태(Flow) 타입 전용. flow 타입일 때만 Board.vue에서 provide된다.

**파라미터**: `rs: BoardRouteState` (미사용, 확장 예비)

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `steps` | `Ref<FlowStep[]>` | 단계 정의 목록 (Ori.vue에서 주입) |
| `currentStep` | `Ref<number>` | 현재 단계 인덱스 (0-based) |
| `stepStatus` | `Computed<StepState[]>` | 각 단계 상태 (`"end"` \| `"ing"` \| `"future"`) |

---

### `useBoardOptionHelpers` — `composables/api/render/useBoardOptionHelpers.ts`

게시판 옵션(BoardOption)과 필드 정의(BoardFieldDef) 기반의 UI 헬퍼 함수 모음.

**파라미터**:
- `boardOption: ComputedRef<BoardOption | null> | Ref<BoardOption | null>`
- `fieldDefs: Ref<BoardFieldDef[]>`

**반환값**:

| 반환값 | 설명 |
|---|---|
| `isNewPost(createdDate)` | 새글 여부 판단 (boardOption.newBadgeDays 기준) |
| `formatAuthor(item)` | 작성자 표시 형식 (name / department / both) |
| `splitTopFixed(list)` | `{ topFixed, normal }` — 상단고정/일반 분리 |
| `opt(field)` | boardOption 특정 필드 ON/OFF 체크 |
| `isFieldRequired(fieldName)` | 필드 필수 여부 |
| `customFields` | `Computed` — 기본 필드 제외 커스텀 필드 목록 |
| `validateRequiredFields(formData)` | 필수 필드 일괄 검증 (`{ valid, errors }` 반환) |
| `searchOptions` | `Computed` — 검색 가능 필드 드롭다운 목록 |

---

### `useContentRenderer` — `composables/api/render/useContent.ts`

콘텐츠 타입 메뉴의 HTML 조회. renderStore의 contentsId를 기준으로 SSR/CSR 공용 데이터 관리.

**파라미터**: 없음

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `contentsHtml` | `useState<string>` | GET /content/{id}/view 결과 HTML |
| `fetchContent()` | 함수 | 수동 재조회 (라우트/contentsId 변경 시 자동 호출됨) |

**동작**:
- SSR: `onServerPrefetch`에서 최초 조회, 결과를 `useState`로 하이드레이션
- CSR: 최초 진입 시 SSR 데이터 재사용(스킵), 이후 라우트/contentsId 변경 시 재조회

---

### `useContentManager` — `composables/api/admin/useContentManager.ts`

콘텐츠 관리 화면의 전체 로직. 5개 하위 composable을 조합.

> 관리자(business) 사이트 전용.

**내부 조합 구조**:
```
useContentManager
├── useContentList()      목록/삭제
├── useContentEditor()    에디터/생성/수정
├── useContentPreview()   미리보기
├── useContentHistory()   히스토리/버전 활성화
└── useContentFiles()     파일 관리
```

**반환값** (주요 그룹):

| 그룹 | 주요 반환값 |
|---|---|
| 목록 | `contents`, `loading`, `totalPages`, `fetchContents`, `deleteContent`, `updateQuery` |
| 에디터 | `showCreateModal`, `modalMode`, `newContent`, `openCreateModal`, `createContent`, `editContent` |
| 미리보기 | `showPreviewModal`, `previewHtml`, `previewContent`, `closePreview`, `openWindowPreview` |
| 히스토리 | `historyModal`, `showHistory`, `activateHistory`, `editHistoryVersion` |
| 파일 | `fileList`, `fileLoading`, `uploadFiles`, `deleteFile`, `copyImgTag` |

---

### `useBoardMasterManager` — `composables/api/admin/useBoardMasterManager.ts`

게시판 마스터(BoardMaster) 관리. 목록 조회, CRUD, 필드 정의, 물리 테이블 동기화.

> 관리자(business) 사이트 전용.

**파라미터**: 없음

**반환값**:

| 반환값 | 설명 |
|---|---|
| `boardMasters` / `loading` / `totalPages` / `totalElements` / `currentPage` | 목록/페이징 상태 |
| `fetchBoardMasters(override?)` | GET /board-master (쿼리 연동, watch 자동 실행) |
| `fetchBoardMaster(idx)` | GET /board-master/{idx} |
| `checkBoardId(boardId)` | 게시판 ID 중복 확인 |
| `createBoardMaster(master, fields)` | POST /board-master (CREATE TABLE + sync 포함) |
| `updateBoardMaster(idx, master, fields)` | PUT /board-master/{idx} (fields replace + ALTER) |
| `deleteBoardMaster(idx)` | DELETE /board-master/{idx} (defs + DROP TABLE) |
| `fetchAllFieldDefinitions(boardMasterIdx)` | 전체 필드 목록 조회 |
| `fetchFieldDefinitions(boardMasterIdx)` | 커스텀 필드 목록 조회 |
| `fetchDefaultFieldMetas(type)` | 기본 필드 메타 조회 |
| `upsertFieldDefinitionsAndSync(idx, fields)` | 필드 업서트 + 테이블 동기화 |
| `fetchLinkedMenus(idx)` | 연결된 메뉴 목록 조회 |
| `forceSyncPhysicalTable(idx)` | 물리 테이블 강제 동기화 |
| `updateQuery(params)` | 쿼리 파라미터 업데이트 |

---

## 3. 메뉴 관련

### `useMenuManageTree` — `composables/api/admin/useMenuManage.ts`

메뉴 트리 관리 화면의 최상위 Composable. 데이터/조작/버전/드래그앤드롭을 조합.

> 관리자(business) 사이트 전용.

**내부 조합 구조**:
```
useMenuManageTree
├── useMenuDataManager()       메뉴 트리 데이터 로드 (API)
├── useMenuTreeOperations()    노드 추가/수정/삭제/클릭
├── useMenuVersionManager()    버전 저장/조회/활성화/삭제
└── useMenuDragDrop()          드래그앤드롭 + 순서 재배치
```

**반환값**:

| 그룹 | 주요 반환값 |
|---|---|
| 데이터 | `menuData`, `selectedNode`, `hasChanges`, `movedGroups`, `fetchMenuTree`, `fetchDriveMenu` |
| 트리 조작 | `handleNodeClick`, `handleDrop`, `addNode`, `updateMenuNode`, `removeNode` |
| 버전 관리 | `fetchVersionList`, `readVersion`, `activateVersion`, `saveTree`, `deleteVersion`, `loadMenuTreeFromVersion` |

---

### `useMenuDataManager` — `composables/api/admin/menu/useMenuDataManager.ts`

메뉴 트리 데이터를 API에서 로드하고 drive 노드로 감싸는 처리.

**파라미터**: 없음

**반환값**:

| 반환값 | 설명 |
|---|---|
| `menuData` | `Ref<TreeMenu[]>` — drive 노드를 루트로 하는 트리 데이터 |
| `selectedNode` | `Ref<TreeMenu \| null>` — 현재 선택 노드 |
| `hasChanges` | `Ref<boolean>` — 미저장 변경 여부 |
| `movedGroups` | `Ref` — 이동된 그룹 목록 |
| `driveNode` | `Ref<TreeMenu \| null>` — drive 루트 노드 참조 |
| `fetchMenuTree(siteHostName)` | GET /menu/{site}/tree → menuData 갱신, 경로 정규화 |
| `fetchDriveMenu(siteHostName)` | drive 노드만 조회 (버전 복원 시 사용) |
| `loadMenuTreeFromVersion(domain, fileName, readVersion)` | 버전 파일 JSON 파싱 후 menuData 교체 |

---

## 4. 신청 관련

### `useApplyFlow` — `composables/api/render/useApplyFlow.ts`

장흥반값 신청 폼 멀티스텝 (Step1 동의 → Step2 폼 → Step3 완료).

**파라미터**: 없음

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `step` | `Ref<number>` | 현재 단계 (1~3) |
| `steps` | `ApplyStepDef[]` | 단계 정의 목록 (agree / form / complete) |
| `stepStatus` | `Computed<ApplyStepState[]>` | 각 단계 상태 (`"end"` \| `"ing"` \| `"future"`) |
| `agreePrivacy` | `Ref<boolean>` | Step1 개인정보 동의 여부 |
| `formData` | `Ref<ApplyFormData>` | Step2 신청서 데이터 |
| `addCompanion()` | 함수 | 동반객 추가 (companions + idCards 슬롯 동시 추가) |
| `removeCompanion(index)` | 함수 | 동반객 제거 |
| `nextStep()` | 함수 | 다음 단계 이동 (Step1: 동의 미체크 시 차단) |
| `prevStep()` | 함수 | 이전 단계 이동 |
| `submitting` | `Ref<boolean>` | 제출 중 여부 |
| `submitApply()` | 함수 | POST /apply → 신분증 파일 업로드 → step=3 |
| `completeData` | `Ref<ApplyResponse \| null>` | 제출 완료 응답 데이터 |
| `resetForm()` | 함수 | 폼 전체 초기화 |

**사용 예시**:
```typescript
// pages/{site}/apply.vue (script 타입 메뉴 — slug 우회)
const {
  step, stepStatus, agreePrivacy, formData,
  addCompanion, removeCompanion,
  nextStep, prevStep,
  submitting, submitApply, completeData
} = useApplyFlow()
```

---

### `useApplyList` / `useApplyDetail` — `composables/api/render/useApplyDetail.ts`

신청자 본인의 신청 내역 조회 및 상세 관리.

**`useApplyList` 반환값**:

| 반환값 | 설명 |
|---|---|
| `loading` | `Ref<boolean>` |
| `list` | `Ref<ApplyListResponse[]>` — 내 신청 목록 |
| `totalPages` / `totalElements` / `currentPage` | 페이징 상태 |
| `fetchMyList(page?, size?)` | GET /apply/my |

**`useApplyDetail` 반환값**:

| 반환값 | 설명 |
|---|---|
| `loading` / `uploading` | 로딩/업로드 중 여부 |
| `detail` | `Ref<ApplyResponse \| null>` — 신청 상세 |
| `files` | `Ref<ApplyFileInfo[]>` — 첨부파일 목록 |
| `fetchDetail(idx)` | GET /apply/{idx} + /apply/{idx}/files 병렬 조회 |
| `uploadEvidence(idx, photos, receipts)` | POST /apply/{idx}/evidence — 증빙자료 업로드 |
| `cancelApply(idx)` | DELETE /apply/{idx} — 신청 취소 |

---

### `useAdminApplyList` / `useAdminApplyDetail` — `composables/api/render/useAdminApply.ts`

관리자 신청 관리 (전체 목록 조회, 상태 변경, 메모 저장).

> 관리자(business) 사이트 전용.

**`useAdminApplyList` 반환값**:

| 반환값 | 설명 |
|---|---|
| `loading` / `list` / `totalPages` / `totalElements` / `currentPage` | 목록/페이징 상태 |
| `fetchList(menuId, page?, size?)` | GET /apply/admin?menuId={menuId} |

**`useAdminApplyDetail` 반환값**:

| 반환값 | 설명 |
|---|---|
| `loading` / `detail` / `files` | 상태 |
| `fetchDetail(idx)` | GET /apply/{idx} + files 병렬 조회 |
| `changeStatus(idx, status, rejectReason?)` | PUT /apply/{idx}/status |
| `saveMemo(idx, adminMemo)` | PUT /apply/{idx}/memo |

---

## 5. 관리자 API 관련

### `useSiteManager` — `composables/api/admin/useSiteManager.ts`

사이트 CRUD 관리.

> 관리자(business) 사이트 전용.

**파라미터**: 없음

**반환값**:

| 함수 | 설명 |
|---|---|
| `createSite(site)` | POST /site |
| `updateSite(site)` | PUT /site/{idx} |
| `restoreSite(siteHostName)` | PUT /site/{hostname}/restore — 소프트 복구 (is_deleted=false) |
| `softDeleteSite(siteHostName)` | DELETE /site/{hostname} — 소프트 삭제 (is_deleted=true) |
| `hardDeleteSite(siteHostName)` | DELETE /site/{hostname}/hard — DB 완전 삭제 |

---

### `useMemberManager` — `composables/api/admin/useMemberManager.ts`

회원 목록 조회, 생성/수정/삭제, 비밀번호 변경, 자동완성. 내부적으로 `useMemberApi` + `useMemberModal` + `useMemberAutocomplete`를 조합.

> 관리자(business) 사이트 전용.

**파라미터**: 없음

**반환값** (주요):

| 그룹 | 주요 반환값 |
|---|---|
| 목록 | `members`, `loading`, `totalPages`, `totalElements`, `currentPage`, `searchTypeOptions` |
| 조회/페이징 | `fetchMembers(override?)`, `updateQuery`, `onSearch`, `onPageChange`, `onPageSizeChange` |
| 모달 | `showCreateModal`, `modalMode`, `form`, `openCreateModal`, `openEditModal`, `openPwEditModal`, `closeCreateModal`, `submitForm` |
| 상세 | `showViewModal`, `viewItem`, `openViewModal`, `closeViewModal` |
| ID 검증 | `checkDuplicateId()` — 아이디 중복 확인 |
| 상태 변경 | `recoveryMember(idx)`, `softDeleteMember(idx)` |
| 자동완성 | `memberSuggest`, `memberSuggestLoading`, `searchMemberSuggestions`, `clearMemberSuggestions` |

**동작**: 쿼리 파라미터 watch → 자동 `fetchMembers()` 호출

---

### `useAuditAccessManager` — `composables/api/admin/useAuditManager.ts`

접근 로그 조회 (관리자 감사 로그).

> 관리자(business) 사이트 전용.

**파라미터**: 없음

**반환값**:

| 반환값 | 설명 |
|---|---|
| `logs` | `Ref<AuditAccess[]>` |
| `loading` / `totalPages` / `totalElements` / `currentPage` | 상태 |
| `searchTypeOptions` | 아이디/이름/IP/성공여부 검색 옵션 |
| `successOptions` | 전체/성공/실패 필터 옵션 |
| `fetchAccessLogs(override?)` | GET /audit/access (쿼리 연동, watch 자동 실행) |
| `updateQuery(params)` | 쿼리 파라미터 업데이트 |

---

### `usePopupManager` — `composables/api/admin/popup/usePopupManager.ts`

팝업(LAYER/VISUAL 배너) 관리. 목록, 생성(드래프트 방식), 수정, 삭제, 이미지 CRUD.

> 관리자(business) 사이트 전용.

**파라미터**: 없음

**반환값** (주요):

| 그룹 | 주요 반환값 |
|---|---|
| 탭 | `activeTab`, `switchTab(tab)` |
| 목록 | `popups`, `loading`, `totalPages`, `fetchPopups()`, `updateQuery`, `searchTypeOptions` |
| 모달 | `showModal`, `modalMode`, `form`, `modalImages`, `openCreateModal()`, `openEditModal(item)`, `closeModal()`, `savePopup()`, `deletePopup(idx)` |
| 이미지 | `uploadImages(files)`, `deleteImage(imageIdx)`, `reorderImages(from, to)`, `updateImageLink(imageIdx, url, target)`, `updateImageDetail(imageIdx, data)` |
| 경고 | `overlapWarnings` — LAYER 타입 기간 겹침 팝업 목록 |
| 상수 | `POSITION_PRESETS` — 위치 프리셋 (좌상단/우상단/중앙 등) |

**주요 동작**:
- 생성 시 드래프트 패턴: 즉시 서버에 임시 팝업 생성 → idx 확보 → 이미지 바로 업로드 가능
- 모달 취소 시: 드래프트면 팝업 삭제, 편집 중 추가 이미지가 있으면 롤백

---

### `useCssEditor` — `composables/api/admin/css/useCssEditor.ts`

CSS 파일 실시간 편집. Lock 기반으로 동시 편집 충돌을 방지.

> 관리자(business) 사이트 전용.

**파라미터**: 없음

**반환값**:

| 반환값 | 설명 |
|---|---|
| `items` | `Ref<CssFileItem[]>` — 현재 경로의 파일/폴더 목록 |
| `currentPath` | `Ref<string>` — 현재 탐색 경로 |
| `currentFile` | `Ref<CssFileContent \| null>` — 현재 열린 파일 내용 |
| `loading` / `saving` | 로딩/저장 중 여부 |
| `lockedByOther` | `Ref<boolean>` — 다른 사용자가 편집 중인 경우 true |
| `fetchList(path?)` | GET /admin/css/list |
| `navigateTo(path)` | 폴더 이동 |
| `openFile(path)` | POST /admin/css/lock 후 GET /admin/css/read |
| `saveFile(path, content)` | PUT /admin/css/save |
| `createFile(path)` | POST /admin/css/file |
| `deleteFile(path)` | DELETE /admin/css/file |
| `createFolder(name)` | POST /admin/css/folder |
| `deleteFolder(path)` | DELETE /admin/css/folder |
| `releaseLock(path)` | DELETE /admin/css/lock |
| `closeFile()` | Lock 해제 + 상태 초기화 |

---

### `useAssetManager` — `composables/api/admin/asset/useAssetManager.ts`

정적 파일 에셋 관리 (이미지 업로드/삭제, 폴더 관리, 경로 복사).

> 관리자(business) 사이트 전용.

**파라미터**: 없음

**반환값**:

| 반환값 | 설명 |
|---|---|
| `items` | `Ref<AssetItem[]>` — 파일/폴더 목록 |
| `currentPath` | `Ref<string>` — 현재 경로 |
| `loading` | `Ref<boolean>` |
| `fetchList(path?)` | GET /asset/list |
| `uploadFiles(path, files)` | POST /asset/upload (IMAGE 프리셋, 최대 50MB 검증) |
| `deleteFile(path)` | DELETE /asset/delete |
| `createFolder(path)` | POST /asset/folder |
| `deleteFolder(path)` | DELETE /asset/folder |
| `copyPath(url)` | 클립보드에 URL 복사 |

---

## 6. UI/유틸리티 관련

### `usePopup` — `composables/api/render/usePopup.ts`

사용자 사이트의 활성 레이어 팝업 조회. '오늘 하루 보지 않기'를 localStorage로 관리.

**파라미터**: `hostname: string`

**반환값**:

| 반환값 | 설명 |
|---|---|
| `popups` | `Ref<ActivePopup[]>` — 전체 활성 팝업 |
| `visiblePopups` | `Ref<ActivePopup[]>` — 오늘 숨김 처리 제외 후 표시할 팝업 |
| `loading` | `Ref<boolean>` |
| `hideToday(popupIdx)` | localStorage에 기록 후 해당 팝업 숨김 |
| `closePopup(popupIdx)` | 즉시 숨김 (localStorage 저장 없음) |

**동작**: `onMounted`에서 GET /popup/active?hostname={hostname} 자동 호출

**사용 예시**:
```typescript
// 레이아웃 컴포넌트
const { visiblePopups, hideToday, closePopup } = usePopup('www.example.com')
// onMounted 자동 실행됨
```

---

### `useVisualBanner` — `composables/api/render/useVisualBanner.ts`

비주얼 배너(VISUAL 팝업) 캐러셀 제어. SSR/CSR 겸용이며 자동 슬라이드 타이머를 관리. `async` 함수이므로 반드시 `await`하여 사용.

**파라미터**: `popupIdx: number | Ref<number>`

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `items` | `Computed<VisualBannerItem[]>` | 배너 이미지 목록 (sortOrder 정렬) |
| `current` | `Computed<VisualBannerItem \| null>` | 현재 표시 이미지 |
| `currentIndex` / `prevIndex` | `Ref<number>` | 현재/이전 인덱스 |
| `total` | `Computed<number>` | 전체 개수 |
| `slideEffect` | `Computed<string>` | 슬라이드 효과 (fade 등) |
| `effectClass` | `Computed<string>` | CSS 클래스 (`vis_slider--fade`) |
| `next()` / `prev()` / `goTo(index)` | 함수 | 슬라이드 이동 |
| `pause()` / `resume()` / `togglePause()` | 함수 | 자동 슬라이드 제어 |
| `isPaused` | `Ref<boolean>` | 일시정지 여부 |

**사용 예시**:
```typescript
const banner = await useVisualBanner(popupIdx)
const { items, current, next, prev, togglePause } = banner
```

---

### `useMenuOverride` — `composables/api/render/useMenuOverride.ts`

현재 menuId에 맞는 override 컴포넌트를 동적으로 선택. Loader.vue에서 사용.

**파라미터**:
- `defaultComp: Component` — 기본 Ori.vue
- `overrideModules: Record<string, any>` — `import.meta.glob()` 결과

**반환값**:

| 반환값 | 타입 | 설명 |
|---|---|---|
| `resolvedComponent` | `Computed<Component>` | menuId 파일명과 일치하는 override 컴포넌트, 없으면 defaultComp |

**사용 예시**:
```typescript
// Loader.vue
const overrideModules = import.meta.glob('./overrides/*.vue', { eager: true })
const { resolvedComponent } = useMenuOverride(Ori, overrideModules)
```

---

## 7. 기타

### `useImeSafeInput` — `composables/utils/useImeSafeInput.ts`

한글 IME 조합 중 포커스 전환 시 클릭이 씹히는 Chrome/Edge 버그 대응.

**문제**: 한글 입력 중 다른 요소 클릭 시 `compositionend` → Vue `:value` 패치 → 브라우저 포커스 전환 방해 순서로 버그 발생.

**해결**: 조합 중 formData 업데이트 차단 + `compositionend` 시 RAF 지연 + `blur` 시 setTimeout(0)으로 보정.

**파라미터**: `formData: Ref<Record<string, any>>`

**반환값**:

| 반환값 | 설명 |
|---|---|
| `onCompositionStart()` | `@compositionstart` 이벤트 핸들러 |
| `onSafeInput(e, field)` | `@input` 이벤트 핸들러 — IME 조합 중에는 formData 업데이트 차단 |
| `onCompositionEnd(e, field)` | `@compositionend` 핸들러 — RAF로 지연 업데이트 |
| `onBlurSync(e, field)` | `@blur` 핸들러 — setTimeout(0)으로 잘린 값 보정 |
| `flush()` | 저장 직전 호출 — latestVal을 즉시 formData에 반영 |

**사용 예시**:
```vue
<input
  :value="formData.title"
  @compositionstart="onCompositionStart"
  @compositionend="onCompositionEnd($event, 'title')"
  @input="onSafeInput($event, 'title')"
  @blur="onBlurSync($event, 'title')"
/>
```

---

### `useLegacyGnbJqShim` — `composables/utils/useLegacyGnbJqShim.ts`

퍼블리셔 jQuery 기반 UI를 바닐라 JS로 재현하는 shim. 사용자 사이트 레이아웃에서 `onMounted` 후 실행. base.js + layout.js + sub.js 통합.

**파라미터**: 없음

**반환값**: `Unbind` 함수 — 컴포넌트 언마운트 시 이벤트 리스너 일괄 해제

**처리 항목**:
- `.select_box` — 커스텀 셀렉트박스
- `.drop_area` — 드롭다운 영역 (포커스 trap + Tab 키 닫기)
- `.search_wrap` — 통합검색 입력/초기화 버튼
- `.modal` / `.modal_close` — 모달 열기/닫기 (접근성: Tab trap, Escape 닫기, 포커스 복원)
- `.search_filter` — 모바일 검색 필터 토글
- `.flicking` — 모바일 수평 스크롤 래핑
- resize 핸들러 (debounce 150ms): searchPlaceholder, applyFlickingUI, bindFilter

**사용 예시**:
```typescript
// 레이아웃 컴포넌트
onMounted(() => {
  const unbind = useLegacyGnbJqShim()
  onUnmounted(unbind)
})
```

---

### `useVersionedCss` — `composables/useVersionedCss.ts`

정적 CSS 파일에 캐시 버스팅 쿼리스트링(`?v=...`)을 붙여주는 유틸.

**파라미터**: `paths: string[]` — CSS 파일 경로 배열

**반환값**: `Array<{ key, rel, href }>` — `useHead`의 link 옵션 형식

**동작**:
- SSR: 서버 미들웨어가 주입한 동적 버전(`ssrContext.event.context.cssVersion`) 우선 사용
- CSR: `useState("cssVersion")`에서 SSR 버전 재사용 (hydration 시 덮어쓰기 방지)

**사용 예시**:
```typescript
// 레이아웃 컴포넌트
const links = useVersionedCss(['/css/common.css', '/css/layout.css'])
useHead({ link: links })
```

---

## 부록: Composable 계층 구조 요약

```
인증
└── useAuth

게시판 렌더링 (사용자 사이트)
└── useBoardRenderer (useBoard.ts)
    ├── useBoardRoute
    ├── useBoardList
    ├── useBoardCrud
    ├── useBoardComment
    ├── useBoardPermission
    ├── useBoardListContext
    ├── useBoardGallery
    └── useBoardFlow

콘텐츠 렌더링 (사용자 사이트)
└── useContentRenderer (useContent.ts)

신청 (장흥반값)
├── useApplyFlow                          사용자 신청 멀티스텝
├── useApplyList / useApplyDetail         사용자 내역 조회
└── useAdminApplyList / useAdminApplyDetail  관리자 신청 관리

관리자 API (admin/*)
├── useMenuManageTree
│   ├── useMenuDataManager
│   ├── useMenuTreeOperations
│   ├── useMenuVersionManager
│   └── useMenuDragDrop
├── useContentManager
│   ├── useContentList / useContentEditor
│   ├── useContentPreview / useContentHistory
│   └── useContentFiles
├── useBoardMasterManager → useBoardMasterApi
├── useSiteManager
├── usePermissionManager
├── useMemberManager
│   ├── useMemberApi
│   ├── useMemberModal
│   └── useMemberAutocomplete
├── useAuditAccessManager → useAuditApi
├── usePopupManager
├── useCssEditor
└── useAssetManager

UI/팝업 (사용자 사이트)
├── usePopup              레이어 팝업 조회
├── useVisualBanner       비주얼 배너 캐러셀
└── useMenuOverride       테마 override 컴포넌트 선택

유틸리티
├── useImeSafeInput       한글 IME 버그 대응
├── useLegacyGnbJqShim   퍼블리셔 jQuery shim
└── useVersionedCss       CSS 캐시 버스팅
```
