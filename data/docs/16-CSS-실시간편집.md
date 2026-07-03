# CSS 실시간 편집

## 개요

Q-CMS는 관리자 UI에서 사이트 CSS를 실시간으로 편집할 수 있다. CodeMirror 6 기반 에디터, 파일 잠금(lock), 자동 백업, 버전 관리를 제공한다.

## 핵심 파일

### 백엔드

| 파일 | 역할 |
|---|---|
| `controller/cms/core/css/CssEditorController.java` | CSS 편집 API |
| `service/cms/core/css/CssEditorService.java` | 파일 CRUD + 잠금 |

### 프론트엔드

| 파일 | 역할 |
|---|---|
| `pages/business/homepage/style.vue` | CSS 편집기 페이지 |
| `components/business/css/` | 에디터 컴포넌트 |
| `composables/api/admin/css/` | CSS API composable |
| `composables/useVersionedCss.ts` | CSS 캐시 버스팅 |

## API

모든 엔드포인트는 MANAGE 권한 필요.

```
GET    /back-api/admin/css/list?path=...    → 디렉토리 탐색 (폴더 + .css만)
GET    /back-api/admin/css/read?path=...    → CSS 파일 읽기 + 잠금 정보
PUT    /back-api/admin/css/save             → 저장 (잠금 확인 + 백업)
POST   /back-api/admin/css/file             → 새 .css 파일 생성
DELETE /back-api/admin/css/file             → .css 파일 삭제
POST   /back-api/admin/css/folder           → 폴더 생성
DELETE /back-api/admin/css/folder           → 빈 폴더 삭제
GET    /back-api/admin/css/version          → CSS 버전 조회
POST   /back-api/admin/css/lock             → 잠금 획득
DELETE /back-api/admin/css/lock             → 잠금 해제
POST   /back-api/admin/css/unlock           → 잠금 해제 (sendBeacon용)
```

## 파일 저장 구조

```
{paths.shared-root}/public/style/
├── global/
│   ├── common.css
│   └── theme.css
├── pages/
│   └── home.css
└── components/
    ├── header.css
    └── footer.css
```

Nginx에서 `/public/` 경로로 직접 서빙된다.

## 잠금 (Lock) 메커니즘

동시 편집 충돌을 방지하기 위한 비관적(pessimistic) 잠금.

```
잠금 획득 (acquireLock):
  ├─ 기존 잠금 없음 → 잠금 생성 (사용자명, 시간)
  ├─ 같은 사용자 잠금 → 갱신
  └─ 다른 사용자 잠금:
      ├─ 타임아웃 만료 → 잠금 탈취
      └─ 유효 → 실패 (잠금 소유자 정보 반환)

잠금 해제 (releaseLock):
  └─ 잠금 소유자만 해제 가능
```

### 구현 방식 (CssEditorServiceImpl)

```java
// 인메모리 잠금 저장소
private final ConcurrentHashMap<String, LockInfo> locks = new ConcurrentHashMap<>();

// LockInfo 레코드
record LockInfo(String user, Instant acquiredAt) {}
```

- **저장소:** `ConcurrentHashMap<String, LockInfo>` — 키는 파일 상대 경로
- **타임아웃:** `css.lock-timeout-minutes` (기본 30분). acquireLock 시 만료 검사
- **잠금 탈취:** 타임아웃 만료된 잠금은 새 사용자가 자동 탈취
- **삭제 시 잠금 체크:** deleteFile 전에 다른 사용자 잠금 확인, 잠금 있으면 거부
- **제한:** 단일 JVM 인스턴스만 지원 (분산 잠금 아님, 서버 재시작 시 잠금 초기화)

### sendBeacon 해제

브라우저 닫기/이동 시 `navigator.sendBeacon()`으로 잠금 해제. POST 방식이므로 별도 `/unlock` 엔드포인트 제공.

## 저장 흐름

```
1. 잠금 소유 확인 (다른 사용자 잠금 시 거부)
2. 기존 파일 .bak 백업 생성
3. UTF-8로 파일 쓰기 (truncate 모드)
4. css-version.json 업데이트
```

## 버전 관리

### css-version.json

```json
{
  "version": "20260630143015",
  "updatedBy": "admin",
  "updatedAt": "2026-06-30T14:30:15+09:00"
}
```

- 파일 저장 시마다 자동 업데이트
- 버전 형식: `yyyyMMddHHmmss` 타임스탬프

### 프론트엔드 캐시 버스팅

`composables/useVersionedCss.ts`가 CSS `<link>` 태그에 `?v={version}` 쿼리 파라미터를 추가하여 브라우저 캐시를 무효화한다.

```html
<link rel="stylesheet" href="/public/style/global/common.css?v=20260630143015" />
```

## 파일 생성

새 .css 파일 생성 시 초기 내용:
```css
/* filename.css */
```

## 경로 보안

- `..` (경로 순회) 차단
- 절대 경로 차단
- 콜론 차단
- URL 디코딩 후 검증
- 해석된 경로가 cssBasePath 내인지 검증

## 응답 DTO

### CssFileContentResponse

```
path          : 파일 상대 경로
content       : 파일 전체 내용
lastModified  : ISO 8601 수정 시간
lockedBy      : 잠금 소유자 (없으면 null)
```

### CssFileItem

```
path          : 상대 경로
name          : 파일/폴더명
directory     : 폴더 여부
lockedBy      : 잠금 소유자
lockedAt      : 잠금 시간 (ISO 8601)
```

### CssLockResponse

```
success       : 잠금 성공 여부
lockedBy      : 사용자명
lockedAt      : 시간
message       : 실패 시 에러 메시지
```

## 설정

```yaml
css:
  base-path: ${paths.shared-root}/public/style
  version-file: ${paths.shared-root}/public/css-version.json
  lock-timeout-minutes: 30
```
