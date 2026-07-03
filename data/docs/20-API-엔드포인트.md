# API 엔드포인트 레퍼런스

## 1. API 공통 규칙

### Base URL

모든 API는 `/back-api` 접두사를 사용한다.

### 인증

JWT Bearer Token을 HttpOnly 쿠키(`ACCESS_TOKEN`, `REFRESH_TOKEN`)로 전달한다. `/back-api/auth/*` 경로는 JwtAuthenticationFilter에서 검증 제외된다.

### 응답 형식

```java
ApiResponse<T> {
    int code;       // HTTP 상태 코드 (200, 201, 400, 404 등)
    String message; // 결과 메시지 ("성공", "리소스 생성 성공", 에러 메시지)
    T data;         // 응답 데이터 (null 가능, @JsonInclude NON_NULL)
}
```

팩토리 메서드:

| 메서드 | code | message |
|---|---|---|
| `ApiResponse.success(data)` | 200 | "성공" |
| `ApiResponse.created(data)` | 201 | "리소스 생성 성공" |
| `ApiResponse.error(code, msg)` | code | msg |
| `ApiResponse.redirect(code, location)` | code | "리디렉션" |

### 권한 레벨

`@PreAuthorize("@permService.hasAccess('LEVEL')")` 형태로 메서드 단위 적용:

| 레벨 | 설명 |
|---|---|
| ACCESS | 접근 권한 (목록 조회) |
| VIEW | 상세 조회 |
| WRITE | 생성 |
| MODIFY | 수정 |
| REMOVE | 삭제 |
| REPLY | 댓글 작성 |
| MANAGE | 관리자 기능 |
| ADMIN | 최상위 관리자 |

### 공통 검색/페이징 파라미터

검색 조건 (`SearchOption`, `@ModelAttribute`):

| 파라미터 | 타입 | 설명 |
|---|---|---|
| keyword | String | 검색 키워드 |
| searchType | String | 검색 대상 필드 |

페이징 조건 (`PaginationOption`, `@ModelAttribute`):

| 파라미터 | 타입 | 설명 |
|---|---|---|
| page | int | 페이지 번호 (0-based) |
| size | int | 페이지 크기 |
| sort | String | 정렬 조건 |

---

## 2. AuthController (`/back-api/auth`)

인증(로그인/로그아웃/사용자정보) API. JWT 필터 검증 제외 경로.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| POST | `/back-api/auth/login` | 없음 | 로그인 (JWT 쿠키 발급) |
| GET | `/back-api/auth/me` | 없음 | 현재 로그인 사용자 정보 |
| DELETE | `/back-api/auth/logout` | 없음 | 로그아웃 (세션+쿠키 삭제) |

### 주요 DTO

**LoginRequest** (요청):

| 필드 | 타입 | 설명 |
|---|---|---|
| userId | String | 사용자 ID |
| password | String | 비밀번호 |

**UserInfoResponse** (응답):

로그인 및 `/me` 엔드포인트 공통 응답. JWT Claims 기반 사용자 정보.

**TokenResponse** (내부):

| 필드 | 타입 | 설명 |
|---|---|---|
| accessToken | String | ACCESS JWT |
| refreshToken | String | REFRESH JWT |

---

## 3. SiteController (`/back-api/site`)

사이트 정보 CRUD API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/site/list` | 없음 | 활성 사이트 목록 조회 |
| GET | `/back-api/site/list/all` | 없음 | 전체 사이트 목록 (삭제 포함) |
| POST | `/back-api/site` | MANAGE | 사이트 생성 |
| PUT | `/back-api/site/{idx}` | MANAGE | 사이트 수정 |
| PUT | `/back-api/site/{siteHostName}/restore` | MANAGE | 사이트 소프트 복구 |
| DELETE | `/back-api/site/{siteHostName}` | MANAGE | 사이트 소프트 삭제 |
| DELETE | `/back-api/site/{siteHostName}/hard` | MANAGE | 사이트 완전 삭제 |

### 주요 파라미터

- `idx`: Integer (사이트 PK, @Positive)
- `siteHostName`: String (호스트명, `^[a-zA-Z0-9_-]{3,30}$`)

### 주요 DTO

**SiteRequest** (요청): `@Validated` 적용

**SiteResponse** (응답): 사이트 정보

---

## 4. MenuController (`/back-api/menu`)

메뉴 트리 조회 API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/menu/drive` | 없음 | 모든 드라이브(루트) 메뉴 조회 |
| GET | `/back-api/menu/{name}/lite` | 없음 | 드라이브 하위 메뉴 경량 조회 |
| GET | `/back-api/menu/{name}/tree` | 없음 | 드라이브 하위 메뉴 전체 트리 조회 |

### 주요 파라미터

- `name`: String (드라이브/메뉴 이름, `^[a-zA-Z0-9_-]{3,30}$`)

### 주요 DTO

**MenuResponse**: 메뉴 정보 (드라이브 목록용)

**MenuTreeLiteResponse**: 트리 경량 응답

**MenuTreeResponse**: 트리 전체 응답

---

## 5. BoardMasterController (`/back-api/boardMaster`)

게시판 마스터(모듈) 관리 API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/boardMaster` | MANAGE | 게시판 모듈 목록 (검색+페이징) |
| GET | `/back-api/boardMaster/{idx}` | MANAGE | 게시판 모듈 단건 조회 |
| GET | `/back-api/boardMaster/{boardId}/checkBoardId` | MANAGE | 게시판 ID 중복 체크 |
| POST | `/back-api/boardMaster` | MANAGE | 게시판 생성 (메타+필드+테이블) |
| PUT | `/back-api/boardMaster/{idx}` | MANAGE | 게시판 수정 (메타+필드+동기화) |
| DELETE | `/back-api/boardMaster/{idx}` | MANAGE | 게시판 삭제 (defs+master+DROP) |
| GET | `/back-api/boardMaster/{idx}/linked-menus` | MANAGE | 연결된 메뉴 목록 조회 |
| GET | `/back-api/boardMaster/{idx}/fields` | MANAGE | 필드 목록 조회 (default 제외) |
| GET | `/back-api/boardMaster/{type}/default-fields` | MANAGE | 타입별 기본 필드 조회 |
| GET | `/back-api/boardMaster/{idx}/all-fields` | ACCESS | 전체 필드 조회 (default 포함) |
| PUT | `/back-api/boardMaster/{idx}/fields` | MANAGE | 필드 업서트 + 테이블 동기화 |
| POST | `/back-api/boardMaster/{idx}/sync` | MANAGE | 물리 테이블 강제 동기화 |

### 주요 파라미터

- `idx`: Long (@Positive, 게시판 마스터 PK)
- `boardId`: String (게시판 식별자)
- `type`: String (게시판 타입)
- `SearchOption`, `PaginationOption`: 검색+페이징 (공통)

### 주요 DTO

**BoardCreateRequest** (요청): 메타+필드 동시 생성

**BoardUpdateRequest** (요청): 메타+필드 동시 수정, `idx` setter 포함

**BoardFieldDefinitionsUpsertRequest** (요청): `boardMasterIdx` + 필드 목록

**BoardMasterListResponse** (응답): 목록용 경량 응답

**BoardMasterResponse** (응답): 상세 응답

**BoardFieldDefinitionResponse** (응답): 필드 정의 응답

**FieldMeta** (응답): 기본 필드 메타 정보

---

## 6. DynamicBoardController (`/back-api/board`)

동적 게시판 데이터 CRUD API. 데이터는 `Map<String, Object>` 형태.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/board` | ACCESS | 게시글 목록 (검색+페이징) |
| GET | `/back-api/board/{idx}` | VIEW | 게시글 상세 조회 |
| POST | `/back-api/board` | WRITE | 게시글 생성 |
| PUT | `/back-api/board/{idx}` | MODIFY | 게시글 수정 |
| DELETE | `/back-api/board/{idx}` | REMOVE | 게시글 삭제 |
| GET | `/back-api/board/{idx}/nav` | VIEW | 이전/다음 글 네비게이션 |
| GET | `/back-api/board/fields` | 없음 | 현재 게시판 필드 정의 조회 |
| PUT | `/back-api/board/{idx}/admin-comment` | MODIFY | 담당자 인라인 답변 저장 |
| PUT | `/back-api/board/{idx}/approval` | MODIFY | 관리자 승인 처리 |

### 주요 파라미터

- `idx`: Long (게시글 PK)
- `SearchOption`, `PaginationOption`: 검색+페이징 (공통)
- Body: `Map<String, Object>` (동적 필드)

### 주요 DTO

**BoardNavResponse** (응답): 이전/다음 글 정보

**FieldDefinitionResponse** (응답): 필드 정의

**관리자 답변 Body**: `{ "adminComment": "..." }`

**승인 처리 Body**: `{ "approved": true/false }`

---

## 7. BoardCommentController (`/back-api/board/{postIdx}/comments`)

게시판 댓글 CRUD API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/board/{postIdx}/comments` | ACCESS | 댓글 목록 조회 |
| POST | `/back-api/board/{postIdx}/comments` | REPLY | 댓글 생성 |
| PUT | `/back-api/board/{postIdx}/comments/{commentIdx}` | 없음(본인) | 댓글 수정 |
| DELETE | `/back-api/board/{postIdx}/comments/{commentIdx}` | 없음(본인) | 댓글 삭제 |

### 주요 파라미터

- `postIdx`: Long (게시글 PK)
- `commentIdx`: Long (댓글 PK)

### 주요 DTO

**BoardCommentRequest** (요청): `@Valid` 적용

**BoardCommentResponse** (응답): 댓글 정보

---

## 8. BoardFileController (`/back-api/board/{postIdx}/files`)

게시판 첨부파일 CRUD API. 다운로드는 FileController에서 처리.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/board/{postIdx}/files` | ACCESS | 첨부파일 목록 조회 |
| POST | `/back-api/board/{postIdx}/files` | WRITE | 파일 업로드 (multipart) |
| DELETE | `/back-api/board/{postIdx}/files/{fileIdx}` | MODIFY | 파일 개별 삭제 |

### 주요 파라미터

- `postIdx`: Long (게시글 PK)
- `fileIdx`: Long (파일 PK)
- `files`: `List<MultipartFile>` (@RequestPart, optional)
- `meta`: `List<BoardFileRequest>` (@RequestPart, optional)

### 주요 DTO

**BoardFileRequest** (요청): 파일 메타 정보

**BoardFileResponse** (응답): 파일 정보

---

## 9. ContentController (`/back-api/content`)

콘텐츠 CRUD API. Draft 워크플로우 지원.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/content` | ACCESS | 콘텐츠 목록 (검색+페이징) |
| GET | `/back-api/content/group/{idx}` | ACCESS | 그룹 콘텐츠 목록 |
| GET | `/back-api/content/{idx}/view` | ACCESS | 메인 콘텐츠 상세 조회 |
| POST | `/back-api/content/draft` | WRITE | Draft 생성 (parentId 확보) |
| PUT | `/back-api/content/draft/{parentId}` | WRITE | Draft를 콘텐츠로 발행 |
| DELETE | `/back-api/content/draft/{parentId}` | REMOVE | Draft 삭제 (취소) |
| POST | `/back-api/content` | WRITE | 대표(루트) 콘텐츠 등록 |
| POST | `/back-api/content/{idx}` | WRITE | 하위 콘텐츠 등록 |
| PUT | `/back-api/content/{idx}` | MODIFY | 콘텐츠 수정 |
| PUT | `/back-api/content/{idx}/active` | MODIFY | 콘텐츠 활성화 |
| DELETE | `/back-api/content/{idx}` | REMOVE | 단일 콘텐츠 삭제 |
| DELETE | `/back-api/content/group/{idx}` | REMOVE | 그룹 전체 삭제 |

### 주요 파라미터

- `idx`: Long (@Positive, 콘텐츠 PK)
- `parentId`: Long (@Positive, 부모 콘텐츠 ID)
- `hostname`: String (Draft 생성 시 사이트명, 기본값 "www")
- `SearchOption`, `PaginationOption`: 검색+페이징 (공통)

### 주요 DTO

**ContentRequest** (요청): `@Valid` 적용

**ContentResponse** (응답): 콘텐츠 정보

---

## 10. ContentFileController (`/back-api/content` - 파일)

콘텐츠 파일 관리 API. 저장 경로: `{base-path}/{parentId}/{fileName}`.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/content/files?parentId={id}` | ACCESS | 파일 목록 조회 |
| POST | `/back-api/content/upload?parentId={id}` | WRITE | 파일 업로드 (multipart) |
| DELETE | `/back-api/content/files?parentId={id}&filename={name}` | REMOVE | 파일 삭제 |

### 주요 파라미터

- `parentId`: Long (@Positive, 콘텐츠 부모 ID, @RequestParam)
- `filename`: String (@NotBlank, 파일명, @RequestParam)
- `files`: `List<MultipartFile>` (@RequestPart)

### 주요 DTO

**UploadedFileResponse** (응답): 업로드된 파일 정보

---

## 11. MemberController (`/back-api/member`)

회원 관리 API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/member` | MANAGE | 회원 목록 (검색+페이징) |
| GET | `/back-api/member/{idx}` | MANAGE | 회원 단건 조회 |
| GET | `/back-api/member/{userId}/exist` | MANAGE | 아이디 중복 확인 |
| POST | `/back-api/member` | MANAGE | 회원 생성 |
| PUT | `/back-api/member/{idx}` | MANAGE | 회원 정보 수정 |
| PUT | `/back-api/member/{idx}/password` | MANAGE | 비밀번호 변경 |
| PUT | `/back-api/member/{idx}/recovery` | MANAGE | 회원 복원 |
| PUT | `/back-api/member/{idx}/soft-delete` | MANAGE | 회원 탈퇴 처리 (소프트) |
| GET | `/back-api/member/search?q={keyword}&size={n}` | MANAGE | 자동완성 검색 |

### 주요 파라미터

- `idx`: Long (@Positive, 회원 PK)
- `userId`: String (사용자 ID)
- `q`: String (검색 키워드, optional)
- `size`: int (결과 수, 기본값 10, @Positive)

### 주요 DTO

**MemberCreateRequest** (요청): userId, userName, password 등

**MemberUpdateRequest** (요청): 일반 정보 수정

**MemberUpdatePwRequest** (요청): 비밀번호 변경

**MemberListResponse** (응답): 목록/자동완성용

**MemberResponse** (응답): 상세 정보

---

## 12. PermissionController (`/back-api/permission`)

메뉴/게시판 권한 관리 API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/permission/chain?menuId={id}&pathId={pid}` | MANAGE | 권한 체인(현재+상속) 조회 |
| PUT | `/back-api/permission/{menuId}/entries` | MANAGE | 메뉴 권한 일괄 업서트 |

### 주요 파라미터

- `menuId`: Long (@Positive, 메뉴 ID, @RequestParam 또는 @PathVariable)
- `pathId`: String (메뉴 경로 ID, optional, `^[0-9]+(\.[0-9]+)*$`)

### 주요 DTO

**PermissionSaveRequest** (요청): menuId + entries 목록

**PermissionChainResponse** (응답): 현재 권한 + 상속 권한 체인

---

## 13. PopupController (`/back-api/popup`)

팝업/배너 관리 API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/popup` | ACCESS | 팝업 목록 (검색+페이징+타입) |
| GET | `/back-api/popup/{idx}` | ACCESS | 팝업 단건 조회 |
| POST | `/back-api/popup` | WRITE | 팝업 생성 |
| PUT | `/back-api/popup/{idx}` | MODIFY | 팝업 수정 |
| DELETE | `/back-api/popup/{idx}` | REMOVE | 팝업 삭제 |
| GET | `/back-api/popup/active?hostname={host}` | 없음(공개) | 활성 레이어 팝업 목록 |
| GET | `/back-api/popup/{idx}/active-images` | 없음(공개) | 배너 활성 이미지 목록 |
| POST | `/back-api/popup/{idx}/images` | WRITE | 이미지 업로드 (다중) |
| DELETE | `/back-api/popup/{idx}/images/{imageIdx}` | REMOVE | 이미지 개별 삭제 |
| PUT | `/back-api/popup/{idx}/images/order` | MODIFY | 이미지 순서 변경 |
| PUT | `/back-api/popup/images/{imageIdx}/link` | MODIFY | 이미지 링크 수정 |
| PUT | `/back-api/popup/images/{imageIdx}` | MODIFY | 이미지 개별 수정 |

### 주요 파라미터

- `idx`: Long (@Positive, 팝업 PK)
- `imageIdx`: Long (@Positive, 이미지 PK)
- `type`: PopupType (enum, optional 필터)
- `hostname`: String (사이트 호스트명)
- `files`: `MultipartFile[]` (@RequestParam)

### 주요 DTO

**PopupRequest** (요청): 팝업 생성/수정

**PopupImageOrderRequest** (요청): 이미지 순서 변경

**PopupImageUpdateRequest** (요청): 이미지 제목, 기간, 링크, 사용여부

**PopupResponse** (응답): 팝업 정보 (이미지 포함)

**PopupImageResponse** (응답): 이미지 정보

**이미지 링크 Body**: `{ "linkUrl": "...", "linkTarget": "..." }`

---

## 14. AssetController (`/back-api/asset`)

에셋 디렉토리/파일 관리 API. 클래스 레벨 `@PreAuthorize("@permService.hasAccess('MANAGE')")`.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/asset/list?path={path}` | MANAGE | 파일/폴더 목록 조회 |
| POST | `/back-api/asset/upload?path={path}` | MANAGE | 파일 업로드 (다중) |
| DELETE | `/back-api/asset/delete` | MANAGE | 파일 삭제 |
| POST | `/back-api/asset/folder` | MANAGE | 폴더 생성 |
| DELETE | `/back-api/asset/folder` | MANAGE | 폴더 삭제 |

### 주요 파라미터

- `path`: String (상대 경로, 기본값 "")
- `files`: `List<MultipartFile>` (@RequestParam)
- Body (삭제/폴더): `{ "path": "..." }`

### 주요 DTO

**AssetListResponse** (응답): 파일/폴더 목록

---

## 15. CssEditorController (`/back-api/admin/css`)

CSS 실시간 편집 API. 클래스 레벨 `@PreAuthorize("@permService.hasAccess('MANAGE')")`. Lock 메커니즘 포함.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/admin/css/list?path={path}` | MANAGE | 파일/폴더 목록 (단일 레벨) |
| GET | `/back-api/admin/css/read?path={path}` | MANAGE | CSS 파일 읽기 |
| PUT | `/back-api/admin/css/save` | MANAGE | CSS 파일 저장 |
| POST | `/back-api/admin/css/file` | MANAGE | CSS 파일 생성 |
| DELETE | `/back-api/admin/css/file` | MANAGE | CSS 파일 삭제 |
| POST | `/back-api/admin/css/folder` | MANAGE | 폴더 생성 |
| DELETE | `/back-api/admin/css/folder` | MANAGE | 폴더 삭제 |
| GET | `/back-api/admin/css/version` | MANAGE | CSS 버전 조회 |
| POST | `/back-api/admin/css/lock` | MANAGE | Lock 획득 |
| DELETE | `/back-api/admin/css/lock` | MANAGE | Lock 해제 |
| POST | `/back-api/admin/css/unlock` | MANAGE | Lock 해제 (sendBeacon용) |

### 주요 파라미터

- `path`: String (파일/폴더 경로)
- 저장 Body: `{ "path": "...", "content": "..." }`
- 기타 Body: `{ "path": "..." }`

### 주요 DTO

**CssFileItem** (응답): 파일/폴더 항목 정보

**CssFileContentResponse** (응답): 파일 내용

**CssLockResponse** (응답): Lock 정보

---

## 16. FileController (`/back-api/file`)

게시판 파일 다운로드 API. 302 리다이렉트 방식.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/file/download/{menuId}/{fileId}` | 없음 | 파일 다운로드 (302 리다이렉트) |

### 주요 파라미터

- `menuId`: long (메뉴 ID)
- `fileId`: long (파일 ID)

### 동작 방식

1. `fileId`로 파일 메타 조회
2. 메타의 `menuId`와 경로의 `menuId` 일치 확인 (불일치 시 404)
3. 정적/CDN 경로로 302 리다이렉트

---

## 17. JsonVersionController (`/back-api/json-version`)

JSON 기반 메뉴 버전 관리 API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/json-version/{domain}/list` | 없음 | 도메인 내 버전 목록 |
| GET | `/back-api/json-version/{domain}/read?fileName={name}` | 없음 | 버전 파일 내용 조회 |
| POST | `/back-api/json-version/{domain}/activate?fileName={name}` | MODIFY | 버전 활성화 (active.json 갱신) |
| POST | `/back-api/json-version/{domain}/save` | MODIFY | 새 버전 저장 |
| PUT | `/back-api/json-version/{domain}/node/{menuId}/value` | MODIFY | 활성 메뉴 노드 value 업데이트 |
| DELETE | `/back-api/json-version/{domain}/delete?fileName={name}` | REMOVE | 버전 파일 삭제 |

### 주요 파라미터

- `domain`: String (`^[a-zA-Z0-9_-]{2,30}$`)
- `fileName`: String (`^[a-zA-Z0-9._-]+\.json$`)
- `menuId`: Long (@Positive)
- Body (save): `List<MenuRequest>` (메뉴 트리)

### 주요 DTO

**VersionListResponse** (응답): 버전 파일 목록

**MenuRequest** (요청): 메뉴 트리 노드

**UpdateNodeValueRequest** (요청): value 값

---

## 18. RenderController (`/back-api/render`)

프론트엔드 렌더링 데이터 API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/render` | 없음 | 현재 컨텍스트 기반 렌더 데이터 |

### 주요 DTO

**RenderResponse** (응답): JWT 내 menuId 등 컨텍스트 기반 렌더링 데이터

---

## 19. ApplyController (`/back-api/apply`)

신청(반값 관광 등) 관리 API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| POST | `/back-api/apply` | ACCESS | 신청 등록 |
| GET | `/back-api/apply/{idx}` | ACCESS | 신청 상세 조회 |
| GET | `/back-api/apply/my?page={p}&size={s}` | ACCESS | 내 신청 목록 |
| GET | `/back-api/apply/admin?menuId={id}&page={p}&size={s}` | MANAGE | 관리자: 메뉴별 신청 목록 |
| DELETE | `/back-api/apply/{idx}` | ACCESS | 신청 취소 (RECEIVED 상태만) |
| POST | `/back-api/apply/{idx}/files` | ACCESS | 신분증 파일 업로드 |
| POST | `/back-api/apply/{idx}/evidence` | ACCESS | 증빙자료 업로드 |
| GET | `/back-api/apply/{idx}/files` | ACCESS | 첨부+증빙 파일 목록 |
| PUT | `/back-api/apply/{idx}/status` | MANAGE | 관리자: 상태 변경 |
| PUT | `/back-api/apply/{idx}/memo` | MANAGE | 관리자: 메모 저장 |
| POST | `/back-api/apply/verify-tourist` | ACCESS | 관광객(비거주자) 확인 |

### 주요 파라미터

- `idx`: Long (@Positive, 신청 PK)
- `menuId`: Long (메뉴 ID)
- `page`: int (기본값 0)
- `size`: int (기본값 10)
- `fronts`, `backs`: `List<MultipartFile>` (신분증 앞/뒷면)
- `photos`, `receipts`: `List<MultipartFile>` (관광사진/영수증)

### 주요 DTO

**ApplyCreateRequest** (요청): 신청 등록 정보

**ApplyStatusChangeRequest** (요청): status, rejectReason

**ApplyMemoRequest** (요청): adminMemo

**TouristVerifyRequest** (요청): name, birthDate

**ApplyResponse** (응답): 신청 상세

**ApplyListResponse** (응답): 목록용

**ApplyFileResponse** (응답): 첨부파일 정보

**TouristVerifyResponse** (응답): 관광객 확인 결과

---

## 20. AuditController (`/back-api/audit`)

감사 로그 조회 API.

### 엔드포인트

| 메서드 | URL | 권한 | 설명 |
|---|---|---|---|
| GET | `/back-api/audit/access` | MANAGE | 로그인 로그 조회 (검색+페이징) |

### 주요 파라미터

- `SearchOption`, `PaginationOption`: 검색+페이징 (공통)

### 주요 DTO

**AuditAccessListResponse** (응답): 로그인 로그 목록
