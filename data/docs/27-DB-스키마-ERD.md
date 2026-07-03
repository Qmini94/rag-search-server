# DB 스키마 · ERD

> 소스 기준: `jh-half-backend` (Spring Boot 2.7 / JPA / QueryDSL)
> 엔티티 패키지: `kr.co.itid.cms.entity`

---

## 1. 테이블 목록 요약

| 테이블명 | 엔티티 클래스 | 용도 | 관련 문서 |
|---|---|---|---|
| `cms_site` | `Site` | 사이트(멀티사이트) 기본 정보 | — |
| `cms_menu` | `Menu` | 사이트 메뉴 트리 | 메뉴 렌더링 흐름 |
| `cms_member` | `Member` | 회원 정보 (암호화 필드 9개) | 인증/권한 |
| `cms_permission` | `Permission` | 메뉴별 접근·쓰기·관리 권한 | 인증/권한 |
| `cms_board_master` | `BoardMaster` | 게시판 마스터 설정 | 게시판 |
| `cms_board_master_menu` | `BoardMasterMenu` | 게시판 ↔ 메뉴 연결(N:M 조인) | 게시판 |
| `cms_board_types` | `BoardType` | 게시판 타입 코드 테이블 | 게시판 |
| `cms_board_field_definition` | `BoardFieldDefinition` | 게시판 동적 필드 정의 | 게시판 |
| `cms_board_comment` | `BoardComment` | 게시글 댓글 (계층 구조) | 게시판 |
| `cms_board_file` | `BoardFile` | 게시글 첨부파일 | 파일 |
| `cms_content` | `Content` | 단일 콘텐츠 페이지 | 콘텐츠 |
| `cms_content_master_menu` | `ContentMasterMenu` | 콘텐츠 ↔ 메뉴 연결(N:M 조인) | 콘텐츠 |
| `cms_popup` | `Popup` | 팝업 마스터 설정 | 팝업 |
| `cms_popup_image` | `PopupImage` | 팝업 이미지(슬라이드) | 팝업 |
| `cms_login_log` | `LoginLog` | 로그인 성공/실패 감사 로그 | 감사 |
| `cms_apply_request` | `ApplyRequest` | 반값투어 신청 마스터 | 신청 폼 |
| `cms_apply_companion` | `ApplyCompanion` | 신청 동반객 | 신청 폼 |
| `cms_apply_file` | `ApplyFile` | 신청 첨부파일(신분증·영수증 등) | 신청 폼 |
| `visit_site` | (엔티티 없음) | 일별 사이트 방문자 통계 (JdbcTemplate) | 통계 |

---

## 2. ERD 관계도 (텍스트)

```
cms_site 1──N cms_menu
             (site_hostname = cms_site.site_hostname 로 논리적 연결, FK 없음)

cms_menu 1──N cms_board_master_menu
cms_board_master 1──N cms_board_master_menu
  → 게시판(N):메뉴(M) 다대다를 조인 테이블로 표현

cms_menu 1──N cms_content_master_menu
cms_content 1──N cms_content_master_menu
  → 콘텐츠(N):메뉴(M) 다대다를 조인 테이블로 표현

cms_menu 1──N cms_permission
  (menu_id FK)

cms_board_master 1──N cms_board_field_definition
  (board_master_idx FK, ON DELETE CASCADE)

cms_board_master 1──N [동적 게시글 테이블]
  (board_id 로 런타임 동적 테이블 생성·조회)

cms_menu 1──N cms_board_comment
  (menu_id 논리 참조)
cms_board_comment 1──N cms_board_comment
  (parent_idx 자기 참조 → 계층 댓글)

cms_menu 1──N cms_board_file
  (menu_id 논리 참조)

cms_popup 1──N cms_popup_image
  (popup_idx FK, CASCADE ALL)

cms_apply_request 1──N cms_apply_companion
  (request_idx FK, CASCADE ALL)

cms_apply_request 1──N cms_apply_file
  (apply_idx 논리 참조)

[Redis] visitors:daily:{date}:{hostname}:{device}
  → 스케줄러(매일 00:00) → visit_site (JdbcTemplate UPSERT)
```

---

## 3. 각 테이블 상세

### cms_site

**용도**: 멀티사이트 기본 정보. 호스트명으로 사이트를 구분한다.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Integer` | NOT NULL (PK, AUTO_INCREMENT) | 사이트 고유 번호 |
| `site_name` | `String` | NULL | 사이트 명칭 |
| `site_hostname` | `String` | NULL | 호스트명 (예: `jh`) |
| `site_domain` | `String` | NULL | 실제 도메인 |
| `is_deleted` | `Boolean` | NULL (default `false`) | 삭제 여부 |
| `is_open` | `Boolean` | NOT NULL (default `false`) | 공개 여부 |
| `allow_ip` | `String` (TEXT) | NULL | 허용 IP 목록 (줄바꿈 구분) |
| `deny_ip` | `String` (TEXT) | NULL | 차단 IP 목록 (줄바꿈 구분) |

- **PK**: `idx`
- **특이사항**: 메뉴와 명시적 FK 없음. `site_hostname` 값이 `cms_menu` 조회 시 논리적 필터로 사용된다.

---

### cms_menu

**용도**: 사이트별 메뉴 트리. 자기 참조(`parent_id`)로 계층 구조를 표현한다.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `id` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 메뉴 고유 번호 |
| `parent_id` | `Long` | NULL | 부모 메뉴 ID (루트 메뉴는 NULL) |
| `position` | `int` | NOT NULL | 같은 부모 내 정렬 순서 |
| `level` | `Long` | NOT NULL | 트리 깊이 (루트=1) |
| `title` | `String(255)` | NULL | 메뉴 표시명 |
| `name` | `String(255)` | NULL | 메뉴 슬러그/내부 이름 |
| `type` | `String(255)` | NULL | 메뉴 타입 (`folder` \| `board` \| `content` \| `script` \| `link`) |
| `value` | `String(255)` | NULL | 타입별 구분값 (board_id, content_idx, URL 등) |
| `is_show` | `Boolean` | NOT NULL | GNB 노출 여부 |
| `path_url` | `String(255)` | NULL | 생성된 URL 경로 (예: `/jh/notice`) |
| `path_string` | `String(255)` | NULL | 경로 한글명 (breadcrumb) |
| `path_id` | `String(255)` | NULL | 조상 ID 체인 (예: `1,5,12`) |

- **PK**: `id`
- **자기 참조**: `parent_id → id`
- **특이사항**: `type=script` 이면 pages/ 직접 생성 방식으로 slug 렌더러를 우회한다.

---

### cms_member

**용도**: CMS 회원 정보. 개인정보 9개 필드는 AES-GCM으로 암호화되어 DB에 `VARBINARY`/`BLOB`로 저장된다.

| 컬럼명 | Java 타입 | nullable | 암호화 | 설명 |
|---|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | — | 회원 고유 번호 |
| `user_id` | `String` | NOT NULL | — | 로그인 아이디 |
| `user_name` | `String` | NULL | — | 이름 |
| `user_nick` | `String` | NULL | — | 닉네임 |
| `user_level` | `Integer` | NULL | — | 회원 등급 |
| `user_pin` | `String` | NOT NULL | — | 핀 번호 (해시) |
| `user_password` | `String` | NULL | — | 비밀번호 (해시) |
| `is_del` | `Boolean` | NULL | — | 탈퇴 여부 |
| `group_idx` | `Integer` | NULL | — | 소속 그룹 |
| `dept_code` | `String` | NULL | — | 부서 코드 |
| `dept_id` | `Integer` | NULL | — | 부서 ID |
| `dept_position` | `String` | NULL | — | 직위 |
| `dept_sort` | `Integer` | NULL | — | 부서 정렬 |
| `dept_work` | `String` | NULL | — | 담당 업무 |
| `dept_tel` | `byte[]` | NULL | **AES-GCM** | 부서 전화 |
| `dept_fax` | `byte[]` | NULL | **AES-GCM** | 팩스 번호 |
| `email` | `byte[]` | NULL | **AES-GCM** | 이메일 |
| `tel` | `byte[]` | NULL | **AES-GCM** | 전화번호 |
| `phone` | `byte[]` | NULL | **AES-GCM** | 휴대폰 |
| `zipcode` | `byte[]` | NULL | **AES-GCM** | 우편번호 |
| `address1` | `byte[]` | NULL | **AES-GCM** | 주소 |
| `address2` | `byte[]` | NULL | **AES-GCM** | 상세주소 |
| `pass_hint_question` | `String` | NULL | — | 비밀번호 힌트 질문 |
| `pass_hint_answer` | `byte[]` | NULL | **AES-GCM** | 비밀번호 힌트 답변 |
| `reg_date` | `LocalDateTime` | NULL | — | 가입일 |
| `last_login_date` | `LocalDateTime` | NULL | — | 최근 로그인 일시 |
| `last_login_ip` | `String` | NULL | — | 최근 로그인 IP |
| `recv_sms` | `String` | NULL | — | SMS 수신 여부 |
| `recv_mail` | `String` | NULL | — | 메일 수신 여부 |
| `foreigner` | `String` | NULL | — | 외국인 여부 |
| `staff_id` | `String` | NULL | — | 직원 ID |
| `agree_date` | `LocalDateTime` | NULL | — | 약관 동의 일시 |
| `birthday` | `LocalDate` | NULL | — | 생년월일 |
| `info_update_date` | `LocalDateTime` | NULL | — | 정보 수정 일시 |
| `device_id` | `String` | NULL | — | 기기 ID |
| `auth_token` | `String` | NULL | — | 인증 토큰 |
| `simple_pw` | `String` | NULL | — | 간편 비밀번호 |
| `bookmark` | `String` | NULL | — | 북마크 |
| `is_sync` | `Boolean` | NULL | — | 외부 연동 동기화 여부 |

- **PK**: `idx`
- **암호화 필드 9개**: `dept_tel`, `dept_fax`, `email`, `tel`, `phone`, `zipcode`, `address1`, `address2`, `pass_hint_answer` — `StringCryptoConverter` 적용, DB 컬럼 타입은 `VARBINARY` 또는 `BLOB`.

---

### cms_permission

**용도**: 메뉴별 사용자(id)/레벨(level) 권한 매핑 테이블.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 권한 고유 번호 |
| `menu_id` | `Long` | NOT NULL | 대상 메뉴 ID (FK → cms_menu.id) |
| `type` | `String` ENUM(`'id'`,`'level'`) | NOT NULL | 권한 부여 대상 종류 |
| `value` | `String(30)` | NULL | type=id 이면 user_id, type=level 이면 레벨 숫자 |
| `manage` | `String` ENUM(`'y'`,`'n'`) | NULL (default `'n'`) | 관리 권한 |
| `admin` | `String` ENUM(`'y'`,`'n'`) | NULL (default `'n'`) | 어드민 권한 |
| `access` | `String` ENUM(`'y'`,`'n'`) | NULL (default `'n'`) | 접근 권한 |
| `view` | `String` ENUM(`'y'`,`'n'`) | NULL (default `'n'`) | 열람 권한 |
| `write` | `String` ENUM(`'y'`,`'n'`) | NULL (default `'n'`) | 작성 권한 |
| `modify` | `String` ENUM(`'y'`,`'n'`) | NULL (default `'n'`) | 수정 권한 |
| `reply` | `String` ENUM(`'y'`,`'n'`) | NULL (default `'n'`) | 답글 권한 |
| `remove` | `String` ENUM(`'y'`,`'n'`) | NULL (default `'n'`) | 삭제 권한 |
| `sort` | `Integer` | NULL | 정렬 순서 |
| `reg_user` | `String(30)` | NULL | 등록자 |
| `reg_date` | `LocalDateTime` | NULL | 등록일시 |
| `mod_user` | `String(30)` | NULL | 수정자 |
| `mod_date` | `LocalDateTime` | NULL | 수정일시 |
| `del` | `String` ENUM(`'y'`,`'n'`) | NULL (default `'n'`) | 삭제 여부 |
| `del_user` | `String(30)` | NULL | 삭제자 |
| `del_date` | `LocalDateTime` | NULL | 삭제일시 |

- **PK**: `idx`
- **FK**: `menu_id → cms_menu.id`
- **특이사항**: `view`, `write`, `modify`는 SQL 예약어이므로 엔티티에서 백틱 인용(\`view\` 등)으로 선언. `setType()` 내에서 소문자 정규화·검증 수행.

---

### cms_board_master

**용도**: 게시판 설정 마스터. 게시판 타입·옵션 플래그·파일 정책을 모두 여기서 관리한다.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 게시판 마스터 고유 번호 |
| `board_id` | `String(50)` | NOT NULL, UNIQUE | 게시판 식별 코드 (동적 테이블명 접미사) |
| `board_name` | `String(100)` | NOT NULL | 게시판 명칭 |
| `description` | `String` (TEXT) | NULL | 게시판 설명 |
| `is_use` | `Boolean` TINYINT(1) | NULL (default `1`) | 사용 여부 |
| `board_type` | `String` | NULL | 게시판 타입 코드 (예: `LIST.default`, `GALLERY.default`) |
| `theme` | `String(50)` | NULL (default `'default'`) | 테마 |
| `list_count` | `Integer` | NULL (default `10`) | 목록 페이지당 건수 |
| `is_admin_reply` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션A: 담당자 인라인 답변 |
| `is_thread_reply` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션B: 답변글 계층 |
| `is_private` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션C: 공개/비공개 선택 가능 |
| `is_private_default` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션C-1: 기본 비공개 |
| `is_use_period` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션D: 사용 기간 설정 |
| `is_top_fixed` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션E: 상단 고정 허용 |
| `is_author_only` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션F: 내 글만 보기 |
| `is_mask_author` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션G: 작성자 마스킹 |
| `new_badge_days` | `Integer` | NULL (default `0`) | 옵션H: 새글 뱃지 표시 기간(일) |
| `is_attached` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션I: 첨부파일 허용 |
| `max_file_upload` | `Integer` | NULL (default `0`) | 첨부파일 최대 개수 |
| `max_total_file_size` | `Integer` | NULL (default `0`) | 총 첨부 용량 한도(MB) |
| `max_file_size` | `Integer` | NULL (default `0`) | 개별 파일 크기 한도(MB) |
| `restricted_files` | `String(255)` | NULL | 차단 확장자 목록 |
| `allowed_images` | `String(255)` | NULL | 허용 이미지 확장자 목록 |
| `max_image_size` | `Integer` | NULL (default `0`) | 이미지 크기 한도(MB) |
| `author_display_type` | `String(20)` | NULL (default `'name'`) | 옵션J: 작성자 표시 방식 (`name`/`department`/`both`) |
| `is_admin_approval` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션K: 관리자 승인 후 노출 |
| `is_comment` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션M: 댓글 허용 |
| `is_view_image_display` | `Boolean` TINYINT(1) | NULL (default `0`) | 옵션L: 본문 하단 이미지 자동 출력 |
| `created_date` | `LocalDateTime` | NOT NULL | 생성일시 (JPA Auditing) |
| `updated_date` | `LocalDateTime` | NOT NULL | 수정일시 (JPA Auditing) |

- **PK**: `idx`
- **UK**: `board_id`
- **특이사항**: `board_type` 값은 `cms_board_types.type`을 논리 참조. 실제 게시글은 `board_id`를 이름에 포함한 동적 테이블(`bbs_{board_id}`)에 저장되며 JPA 엔티티가 아닌 QueryDSL/JdbcTemplate로 처리된다.

---

### cms_board_master_menu

**용도**: 게시판(cms_board_master)과 메뉴(cms_menu)의 다대다 조인 테이블.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `id` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 고유 번호 |
| `board_master_idx` | `Long` | NOT NULL (FK) | cms_board_master.idx |
| `menu_id` | `Long` | NOT NULL (FK) | cms_menu.id |
| `created_date` | `LocalDateTime` | NULL (default NOW) | 연결 생성일시 |

- **PK**: `id`
- **UK**: `(board_master_idx, menu_id)` → `uk_master_menu`
- **FK**: `board_master_idx → cms_board_master.idx`, `menu_id → cms_menu.id`

---

### cms_board_types

**용도**: 게시판 타입 코드 테이블. 게시판 타입의 코드값·명칭·설명을 관리한다.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Integer` | NOT NULL (PK, AUTO_INCREMENT) | 고유 번호 |
| `type` | `String(50)` | NOT NULL, UNIQUE | 타입 코드 (예: `LIST.default`) |
| `type_name` | `String(100)` | NOT NULL | 표시명 |
| `description` | `String` (TEXT) | NULL | 설명 |
| `created_date` | `LocalDateTime` | NOT NULL | 생성일시 (JPA Auditing) |
| `updated_date` | `LocalDateTime` | NOT NULL | 수정일시 (JPA Auditing) |

- **PK**: `idx`
- **UK**: `type`

---

### cms_board_field_definition

**용도**: 게시판 동적 필드 정의. 게시판별 커스텀 필드(입력 타입·표시명·암호화 여부 등)를 관리한다.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `id` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 고유 번호 |
| `board_master_idx` | `Long` | NOT NULL (FK) | cms_board_master.idx (ON DELETE CASCADE) |
| `field_name` | `String(100)` | NOT NULL | 필드 식별자 (동적 컬럼명) |
| `display_name` | `String(100)` | NOT NULL | 화면 표시 레이블 |
| `field_type` | `String(50)` | NOT NULL | 입력 타입 (text, textarea, select 등) |
| `is_required` | `Boolean` TINYINT(1) | NULL (default `0`) | 필수 여부 |
| `is_searchable` | `Boolean` TINYINT(1) | NULL (default `0`) | 검색 대상 여부 |
| `is_encrypted` | `Boolean` TINYINT(1) | NULL (default `0`) | 값 암호화 여부 |
| `field_order` | `Integer` | NULL (default `0`) | 필드 표시 순서 |
| `default_value` | `String(255)` | NULL | 기본값 |
| `placeholder` | `String(255)` | NULL | 입력 힌트 |
| `created_date` | `LocalDateTime` | NOT NULL | 생성일시 (JPA Auditing) |
| `updated_date` | `LocalDateTime` | NOT NULL | 수정일시 (JPA Auditing) |

- **PK**: `id`
- **FK**: `board_master_idx → cms_board_master.idx` (fk_board_field_definition_board_idx, ON DELETE CASCADE)
- **인덱스**: `idx_board_idx (board_master_idx)`
- **특이사항**: `is_encrypted=true` 인 필드는 서비스 레이어에서 `CryptoUtil.encryptToBase64` / `decryptFromBase64`로 처리한다.

---

### cms_board_comment

**용도**: 게시글 댓글. `parent_idx`로 자기 참조 계층 구조를 지원한다.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 댓글 고유 번호 |
| `menu_id` | `Long` | NOT NULL | 소속 메뉴 ID (논리 참조) |
| `post_idx` | `Long` | NOT NULL | 대상 게시글 IDX |
| `parent_idx` | `Long` | NULL | 부모 댓글 IDX (NULL=최상위 댓글) |
| `content` | `String` (TEXT) | NOT NULL | 댓글 본문 |
| `reg_id` | `String(250)` | NULL | 작성자 ID |
| `reg_name` | `String(30)` | NULL | 작성자 이름 |
| `is_deleted` | `Boolean` TINYINT(1) | NOT NULL (default `0`) | 삭제 여부 (소프트 삭제) |
| `created_date` | `LocalDateTime` | NULL | 작성일시 (JPA Auditing) |
| `updated_date` | `LocalDateTime` | NULL | 수정일시 (JPA Auditing) |

- **PK**: `idx`
- **자기 참조**: `parent_idx → idx` (논리적, DB FK 없음)
- **계층 구조**: `parent_idx IS NULL` = 루트 댓글, `parent_idx IS NOT NULL` = 대댓글. 소프트 삭제 처리(`is_deleted=true`)로 트리 구조 유지.

---

### cms_board_file

**용도**: 게시글 첨부파일. 이미지 여부·크기 메타 포함.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 파일 고유 번호 |
| `menu_id` | `Long` | NOT NULL | 소속 메뉴 ID (논리 참조) |
| `post_idx` | `Long` | NOT NULL | 대상 게시글 IDX |
| `seq` | `Integer` | NOT NULL | 파일 순서 |
| `orig_name` | `String(255)` | NOT NULL | 원본 파일명 |
| `stored_name` | `String(255)` | NOT NULL | 저장 파일명 (UUID 등) |
| `content_type` | `String(100)` | NULL | MIME 타입 |
| `size_bytes` | `Long` | NOT NULL | 파일 크기(bytes) |
| `file_path` | `String(500)` | NOT NULL | 서버 저장 경로 |
| `is_image` | `Boolean` | NOT NULL (default `false`) | 이미지 파일 여부 |
| `width` | `Integer` | NULL | 이미지 너비(px) |
| `height` | `Integer` | NULL | 이미지 높이(px) |
| `description` | `String` (LOB) | NULL | 파일 설명 |

- **PK**: `idx`
- **특이사항**: `is_image=true` 인 경우 `width`, `height` 값이 채워진다. 동적 게시글 테이블과 `menu_id + post_idx`로 논리 연결.

---

### cms_content

**용도**: 단일 콘텐츠 페이지(HTML 에디터 입력). 버전 관리를 위해 `parent_id`로 계층화 가능.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 콘텐츠 고유 번호 |
| `parent_id` | `Long` | NULL | 부모 콘텐츠 ID (버전 그룹) |
| `is_use` | `Boolean` TINYINT(1) | NOT NULL (default `0`) | 사용(활성) 여부 |
| `is_main` | `Boolean` TINYINT(1) | NOT NULL (default `0`) | 메인 콘텐츠 여부 |
| `is_draft` | `Boolean` TINYINT(1) | NOT NULL (default `0`) | 임시저장 여부 |
| `title` | `String(200)` | NULL | 콘텐츠 제목 |
| `content` | `String` (LOB) | NOT NULL | 본문 HTML |
| `hostname` | `String(30)` | NOT NULL | 소속 사이트 호스트명 |
| `updated_by` | `String(30)` | NULL | 최종 수정자 |
| `created_by` | `String(30)` | NULL | 최초 등록자 |
| `updated_date` | `LocalDateTime` | NULL | 수정일시 (JPA Auditing) |
| `created_date` | `LocalDateTime` | NULL | 생성일시 (JPA Auditing) |

- **PK**: `idx`
- **특이사항**: `content` 컬럼은 `@Lob`으로 선언되어 MEDIUMTEXT/LONGTEXT에 매핑된다.

---

### cms_content_master_menu

**용도**: 콘텐츠(cms_content)와 메뉴(cms_menu)의 다대다 조인 테이블.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `id` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 고유 번호 |
| `content_idx` | `Long` | NOT NULL (FK) | cms_content.idx |
| `menu_id` | `Long` | NOT NULL (FK) | cms_menu.id |
| `created_date` | `LocalDateTime` | NULL (default NOW) | 연결 생성일시 |

- **PK**: `id`
- **UK**: `(content_idx, menu_id)` → `uk_content_menu`
- **FK**: `content_idx → cms_content.idx`, `menu_id → cms_menu.id`

---

### cms_popup

**용도**: 팝업 마스터. 레이어/윈도우 타입, 슬라이드 설정, 노출 기간 등 관리.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 팝업 고유 번호 |
| `type` | `String(10)` ENUM | NOT NULL (default `LAYER`) | 팝업 유형 (`LAYER`, `WINDOW`) |
| `hostname` | `String(50)` | NOT NULL | 소속 사이트 호스트명 |
| `title` | `String(100)` | NOT NULL | 팝업 제목 |
| `left_px` | `Integer` | NULL (default `30`) | 좌측 위치(px) |
| `top_px` | `Integer` | NULL (default `30`) | 상단 위치(px) |
| `width` | `Integer` | NULL (default `450`) | 너비(px) |
| `height` | `Integer` | NULL (default `500`) | 높이(px) |
| `sort_order` | `Integer` | NOT NULL (default `0`) | 노출 순서 |
| `start_date` | `LocalDateTime` | NULL | 노출 시작일시 |
| `end_date` | `LocalDateTime` | NULL | 노출 종료일시 |
| `use_today_hide` | `Boolean` TINYINT(1) | NOT NULL (default `1`) | 오늘 하루 안보기 사용 여부 |
| `is_use` | `Boolean` TINYINT(1) | NOT NULL (default `1`) | 팝업 활성 여부 |
| `auto_slide` | `Boolean` TINYINT(1) | NOT NULL (default `1`) | 이미지 자동 슬라이드 여부 |
| `slide_interval` | `Integer` | NOT NULL (default `3`) | 슬라이드 간격(초) |
| `slide_effect` | `String(20)` | NOT NULL (default `'fade'`) | 슬라이드 효과 |
| `created_by` | `String(50)` | NULL | 등록자 |
| `created_date` | `LocalDateTime` | NULL | 생성일시 (JPA Auditing) |
| `modified_date` | `LocalDateTime` | NULL | 수정일시 (JPA Auditing) |

- **PK**: `idx`
- **연관**: `images` → `cms_popup_image` (OneToMany, CascadeType.ALL, orphanRemoval)

---

### cms_popup_image

**용도**: 팝업 슬라이드 이미지 목록. 팝업 1개에 이미지 N개.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 이미지 고유 번호 |
| `popup_idx` | `Long` | NOT NULL (FK) | cms_popup.idx |
| `image_url` | `String(500)` | NOT NULL | 이미지 URL |
| `title` | `String(100)` | NULL | 이미지 제목 (alt 텍스트) |
| `link_url` | `String(500)` | NULL | 클릭 시 이동 URL |
| `link_target` | `String(10)` | NOT NULL (default `'_blank'`) | 링크 대상 (`_blank`, `_self`) |
| `sort_order` | `Integer` | NOT NULL (default `0`) | 슬라이드 순서 |
| `start_date` | `LocalDateTime` | NULL | 노출 시작일시 |
| `end_date` | `LocalDateTime` | NULL | 노출 종료일시 |
| `is_use` | `Boolean` TINYINT(1) | NOT NULL (default `1`) | 사용 여부 |

- **PK**: `idx`
- **FK**: `popup_idx → cms_popup.idx`

---

### cms_login_log

**용도**: 로그인 시도 감사 로그. 성공/실패 모두 기록한다.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `id` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 로그 고유 번호 |
| `user_id` | `String(100)` | NULL | 시도한 사용자 ID |
| `user_name` | `String(100)` | NULL | 사용자 이름 |
| `is_success` | `Boolean` | NOT NULL | 로그인 성공 여부 |
| `fail_reason` | `String(255)` | NULL | 실패 사유 |
| `ip` | `String(45)` | NOT NULL | 클라이언트 IP (IPv6 포함) |
| `user_agent` | `String(255)` | NULL | 브라우저 User-Agent |
| `hostname` | `String(100)` | NULL | 접속 사이트 호스트명 |
| `request_uri` | `String(255)` | NULL | 요청 URI |
| `session_id` | `String(100)` | NULL | 세션 ID |
| `created_date` | `LocalDateTime` | NOT NULL | 로그 생성일시 (DB default: `CURRENT_TIMESTAMP(3)`) |

- **PK**: `id`
- **인덱스**:
  - `idx_login_log_user_ts (user_id, created_date)`
  - `idx_login_log_success_ts (is_success, created_date)`
- **특이사항**: `created_date`는 `insertable=false, updatable=false`로 선언되어 DB 기본값(`CURRENT_TIMESTAMP(3)`, 밀리초 정밀도)이 그대로 사용된다.

---

### cms_apply_request

**용도**: 반값투어 신청 마스터. 신청인 정보·여행 정보·동의·상태를 한 테이블에서 관리한다.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 신청 고유 번호 |
| `receipt_no` | `String(30)` | NULL, UNIQUE | 접수 번호 (발번 후 세팅) |
| `menu_id` | `Long` | NOT NULL | 신청 메뉴 ID (논리 참조) |
| `applicant_name` | `String(50)` | NOT NULL | 신청인 이름 |
| `birth_date` | `String(6)` | NOT NULL | 생년월일 6자리 (예: `900101`) |
| `phone` | `String(20)` | NOT NULL | 연락처 |
| `zipcode` | `String(10)` | NULL | 우편번호 |
| `address1` | `String(200)` | NULL | 주소 |
| `address2` | `String(200)` | NULL | 상세주소 |
| `tourist_verified` | `Boolean` TINYINT(1) | NULL (default `0`) | 장흥군민 인증 여부 |
| `chak_card_no` | `String(30)` | NULL | 착카드 번호 |
| `travel_start` | `LocalDate` | NOT NULL | 여행 시작일 |
| `travel_end` | `LocalDate` | NOT NULL | 여행 종료일 |
| `travel_place` | `String(100)` | NULL | 여행지 |
| `agree_privacy` | `Boolean` TINYINT(1) | NULL (default `0`) | 개인정보 수집 동의 여부 |
| `agree_final` | `Boolean` TINYINT(1) | NULL (default `0`) | 최종 확인 동의 여부 |
| `status` | `String(20)` | NOT NULL (default `'RECEIVED'`) | 처리 상태 (`RECEIVED`, `APPROVED`, `REJECTED` 등) |
| `reject_reason` | `String` (TEXT) | NULL | 반려 사유 |
| `admin_memo` | `String` (TEXT) | NULL | 관리자 메모 |
| `reg_id` | `String(50)` | NULL | 등록자 ID |
| `reg_name` | `String(50)` | NULL | 등록자 이름 |
| `reg_ip` | `String(50)` | NULL | 등록 IP |
| `created_date` | `LocalDateTime` | NOT NULL | 생성일시 (JPA Auditing) |
| `updated_date` | `LocalDateTime` | NOT NULL | 수정일시 (JPA Auditing) |

- **PK**: `idx`
- **UK**: `receipt_no`
- **연관**: `companions` → `cms_apply_companion` (OneToMany, CascadeType.ALL, orphanRemoval)

---

### cms_apply_companion

**용도**: 신청 동반객 정보. 신청 1건에 동반객 N명.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 동반객 고유 번호 |
| `request_idx` | `Long` | NOT NULL (FK) | cms_apply_request.idx |
| `comp_name` | `String(50)` | NOT NULL | 동반객 이름 |
| `comp_birth` | `String(6)` | NOT NULL | 동반객 생년월일 6자리 |
| `delegation_yn` | `String(1)` | NOT NULL (default `'N'`) | 대리 신청 여부 (`Y`/`N`) |
| `tourist_verified` | `Boolean` TINYINT(1) | NULL (default `0`) | 장흥군민 인증 여부 |

- **PK**: `idx`
- **FK**: `request_idx → cms_apply_request.idx`

---

### cms_apply_file

**용도**: 신청 첨부파일(신분증 앞/뒷면, 관광지 방문사진, 영수증). 인원 인덱스로 신청인/동반객을 구분한다.

| 컬럼명 | Java 타입 | nullable | 설명 |
|---|---|---|---|
| `idx` | `Long` | NOT NULL (PK, AUTO_INCREMENT) | 파일 고유 번호 |
| `apply_idx` | `Long` | NOT NULL | cms_apply_request.idx (논리 참조) |
| `file_type` | `String(30)` | NOT NULL | 파일 유형: `ID_FRONT`, `ID_BACK`, `EVIDENCE_PHOTO`, `EVIDENCE_RECEIPT` |
| `person_index` | `Integer` | NULL | 인원 인덱스 (0=신청인, 1~=동반객 순서) |
| `orig_name` | `String(500)` | NOT NULL | 원본 파일명 |
| `stored_name` | `String(500)` | NOT NULL | 저장 파일명 |
| `content_type` | `String(100)` | NULL | MIME 타입 |
| `file_size` | `Long` | NULL | 파일 크기(bytes) |
| `created_date` | `LocalDateTime` | NOT NULL | 업로드 일시 (JPA Auditing) |

- **PK**: `idx`
- **논리 FK**: `apply_idx → cms_apply_request.idx` (엔티티에 FK 어노테이션 없음)

---

### visit_site (JdbcTemplate 전용)

**용도**: 일별·사이트별·기기별 방문자 수 집계. JPA 엔티티 없이 `VisitorMigrationServiceImpl`이 JdbcTemplate로 직접 UPSERT한다.

스케줄러(`@Scheduled cron="0 0 0 * * *"`)가 매일 00:00에 Redis 카운터를 읽어 이 테이블로 이관한다.

| 컬럼명 | 추정 타입 | nullable | 설명 |
|---|---|---|---|
| `visit_date` | `DATE` | NOT NULL (PK 추정) | 방문 날짜 |
| `hostname` | `VARCHAR` | NOT NULL (PK 추정) | 사이트 호스트명 |
| `web_cnt` | `INT` | NOT NULL | PC 방문자 수 |
| `mobile_cnt` | `INT` | NOT NULL | 모바일 방문자 수 |

- **PK(추정)**: `(visit_date, hostname)` — UPSERT SQL의 `ON DUPLICATE KEY UPDATE` 조건으로 유추
- **Redis 키 패턴**: `visitors:daily:{date}:{hostname}:{device}` (`device` = `web` | `mobile`)
- **방문자 중복 제거**: `visitor:{ip}:{date}:{hostname}` 키를 `setIfAbsent`로 TTL 설정하여 당일 IP별 1회만 카운트
- **특이사항**: `hostname='common'`은 집계에서 제외된다.

---

## 4. JPA 암호화 컨버터

### StringCryptoConverter 동작 원리

```
kr.co.itid.cms.config.jpa.StringCryptoConverter
  implements AttributeConverter<String, byte[]>
```

| 방향 | 메서드 | 처리 |
|---|---|---|
| Java → DB | `convertToDatabaseColumn(String)` | `CryptoUtil.encryptToBytes(plaintext)` → `byte[]` |
| DB → Java | `convertToEntityAttribute(byte[])` | `CryptoUtil.decryptToString(bytes)` → `String` |

**암호화 알고리즘**: AES/GCM/NoPadding (인증 태그 128bit)

**바이트 레이아웃** (암호문 포맷):
```
[ 1byte version=0x01 | 12byte IV (랜덤) | N byte ciphertext+GCM tag ]
```

**키 관리**:
- 키 파일 경로 우선순위: `crypto.key.path` (yml) → `-Dcrypto.key.path` (시스템 프로퍼티) → `CRYPTO_KEY_PATH` (환경변수) → `/data/egovframe-cms/install/crypto_key/crypto.key` (기본값)
- 키 포맷: HEX 문자열, 16/24/32 bytes (AES-128/192/256)
- 키는 JVM 기동 시 최초 1회 로드 후 `volatile` 변수에 캐싱 (DCL 패턴)

**레거시 안전처리**: 복호화 시 첫 바이트가 version(0x01)이 아니면 원본 바이트를 UTF-8 문자열로 반환하여 구버전 데이터와의 호환성을 유지한다.

**동적 필드 암호화**: `cms_board_field_definition.is_encrypted=true`인 필드는 `StringCryptoConverter` 대신 `CryptoUtil.encryptToBase64` / `decryptFromBase64`를 서비스 레이어에서 직접 호출하여 Base64 문자열로 DB에 저장한다(동적 테이블은 JPA 엔티티가 아니므로 컨버터 적용 불가).

### 암호화 적용 필드 목록

| 테이블 | 컬럼명 | 엔티티 필드 | 컨버터 방식 |
|---|---|---|---|
| `cms_member` | `dept_tel` | `Member.deptTel` | `@Convert(StringCryptoConverter)` |
| `cms_member` | `dept_fax` | `Member.deptFax` | `@Convert(StringCryptoConverter)` |
| `cms_member` | `email` | `Member.email` | `@Convert(StringCryptoConverter)` |
| `cms_member` | `tel` | `Member.tel` | `@Convert(StringCryptoConverter)` |
| `cms_member` | `phone` | `Member.phone` | `@Convert(StringCryptoConverter)` |
| `cms_member` | `zipcode` | `Member.zipcode` | `@Convert(StringCryptoConverter)` |
| `cms_member` | `address1` | `Member.address1` | `@Convert(StringCryptoConverter)` |
| `cms_member` | `address2` | `Member.address2` | `@Convert(StringCryptoConverter)` |
| `cms_member` | `pass_hint_answer` | `Member.passHintAnswer` | `@Convert(StringCryptoConverter)` |
| `bbs_{board_id}` | `{field_name}` | (동적 컬럼) | `CryptoUtil.encryptToBase64` (서비스 레이어 직접 처리) |
