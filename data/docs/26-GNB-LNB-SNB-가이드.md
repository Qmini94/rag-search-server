# GNB · LNB · SNB 네비게이션 가이드

## 1. 네비게이션 컴포넌트 전체 구조

### 사이트별 레이아웃 파일

| 사이트 | 레이아웃 파일 | 적용 CSS |
|---|---|---|
| www (메인) | `layouts/www-main.vue` | `halftour/layout.css`, `halftour/main.css` |
| www (서브) | `layouts/www-sub.vue` | `halftour/layout.css`, `halftour/sub.css` |
| default (메인) | `layouts/default-main.vue` | `yumcorp/layout.css`, `yumcorp/main.css` |
| default (서브) | `layouts/default-sub.vue` | `yumcorp/layout.css`, `yumcorp/sub.css` |
| business (관리자) | `layouts/business-sub.vue` | Tailwind CSS (전용) |

### 사이트별 헤더 / 네비 / 푸터 컴포넌트 목록

| 사이트 | 역할 | 컴포넌트 파일 |
|---|---|---|
| **www** | 메인 헤더 (GNB 포함) | `components/www/main/Header.vue` |
| www | GNB 메뉴 (데스크톱 + 모바일 공용) | `components/www/main/GnbMenu.vue` |
| www | 서브 비주얼 헤더 | `components/www/sub/Header.vue` |
| www | 서브 LNB/SNB 사이드바 | `components/www/sub/Sidebar.vue` |
| www | 브레드크럼 | `components/www/sub/Breadcrumb.vue` |
| www | 콘텐츠 도구 (공유·인쇄) | `components/www/sub/ContentBox.vue` |
| www | 메인 푸터 | `components/www/main/Footer.vue` |
| **default** | 메인 헤더 (GNB 포함) | `components/default/main/Header.vue` |
| default | GNB 메뉴 | `components/default/main/GnbMenu.vue` |
| default | 메인 사이드바 (3뎁스 아코디언) | `components/default/main/Sidebar.vue` |
| default | 서브 사이드바 (3뎁스 아코디언) | `components/default/sub/Sidebar.vue` |
| default | 서브 브레드크럼 | `components/default/sub/Breadcrumb.vue` |
| default | 서브 비주얼 헤더 | `components/default/sub/Header.vue` (미구현, 빈 구조) |
| default | 푸터 | `components/default/main/Footer.vue` |
| **business** | 관리자 헤더 | `components/business/Header.vue` |
| business | 관리자 사이드바 (섹션 + 재귀 아이템) | `components/business/Sidebar.vue` |
| business | 사이드바 아이템 (재귀) | `components/business/SidebarItem.vue` |
| business | 브레드크럼 | `components/business/Breadcrumb.vue` |

---

## 2. GNB (Global Navigation Bar)

### 2-1. 파일 위치

- `components/www/main/GnbMenu.vue` — www 사이트 GNB
- `components/default/main/GnbMenu.vue` — default 사이트 GNB
- 두 파일은 동일한 구조(3뎁스)이며 CSS 클래스 체계가 같음

### 2-2. 마운트 위치

`Header.vue`에서 두 곳에 동일한 컴포넌트를 삽입한다.

```html
<!-- 데스크톱 GNB -->
<div class="gnb_web tpA">
  <WwwMainGnbMenu :dropdown-top="dropdownTop" />
</div>

<!-- 모바일 드로어 안 -->
<div class="gnb_bot">
  <WwwMainGnbMenu :dropdown-top="dropdownTop" />
</div>
```

### 2-3. 3뎁스 HTML 구조

```
ul.gnb (role="menubar")
  li.gnbA.gnbA{N}                    ← 1차 메뉴 (N = 1부터 순서)
    NuxtLink                          ← 1차 링크
    div.gnbB_wrap                     ← 2차 드롭다운 전체 영역
      div.gnbB_area
        p.title
        ul.gnbB.gnbB{N}              ← 2차 목록
          li.gnbBs{N}.gnbBc{M}       ← N=상위 인덱스, M=자신 인덱스
            a / NuxtLink             ← 2차 링크 (link타입이면 a, 아니면 NuxtLink)
            div.gnbC_wrap            ← 3차 영역 (자식 있을 때만)
              ul.gnbC.gnbC{N}
                li.gnbCs{M}.gnbCc{K} ← M=2차 인덱스, K=자신 인덱스
                  a / NuxtLink       ← 3차 링크
```

### 2-4. CSS 클래스 패턴 정리

| 클래스 | 의미 | 예시 |
|---|---|---|
| `gnbA` | 1차 메뉴 공통 | - |
| `gnbA{N}` | 1차 메뉴 N번째 | `gnbA1`, `gnbA2` |
| `.on` | 현재 경로가 해당 섹션에 속할 때 | `isCurrentGnb()` 반환값 |
| `.now` | 마우스 호버/포커스로 열린 상태 | `openIndex === index` |
| `gnbB{N}` | N번째 1차 메뉴의 2차 목록 | `gnbB1` |
| `gnbBs{N}` | 상위 1차 메뉴가 N번째인 2차 항목 | `gnbBs1` |
| `gnbBc{M}` | 2차 메뉴 중 M번째 항목 | `gnbBc1`, `gnbBc2` |
| `gnbC{N}` | N번째 1차 메뉴 산하 3차 목록 | `gnbC1` |
| `gnbCs{M}` | 상위 2차 메뉴가 M번째인 3차 항목 | `gnbCs1` |
| `gnbCc{K}` | 3차 메뉴 중 K번째 항목 | `gnbCc1`, `gnbCc2` |
| `gnb_dim` | `#wrap`에 붙는 딤 처리 클래스 | hover 시 배경 어둡게 |
| `newwin` | 외부 링크(`link` 타입) 항목 | `target="_blank"` |

### 2-5. 드롭다운 동작 로직

```
mouseenter(li.gnbA)
  → clearClose()           타이머 취소
  → openIndex = i          해당 인덱스 열기
  → setDim(true)           #wrap에 gnb_dim 클래스 추가

mouseleave(li.gnbA)
  → scheduleClose()        120ms 뒤 닫힘 예약

focusin / focusout         키보드 접근성 동일 처리

ESC 키 (keydown.esc)
  → blurActive()           현재 포커스 blur
```

- `gnbB_wrap`은 `display: block / none` 인라인 스타일로 제어 (CSS transition은 CSS 파일에서)
- www 사이트: dim 효과 있음 (`setDim` 호출), default 사이트: dim 없음

### 2-6. 스크롤 시 자동 닫힘

```typescript
function onWindowScroll() {
  const y = window.scrollY || 0;
  if (openIndex.value !== null && Math.abs(y - lastScrollY) > 1) {
    clearClose();
    openIndex.value = null;
    setDim(false);       // www만 해당
  }
  lastScrollY = y;
}
```

`onMounted`에서 `window.addEventListener('scroll', onWindowScroll, { passive: true })` 등록,
`onBeforeUnmount`에서 제거.

### 2-7. 모바일 드로어 (www Header.vue)

모바일에서는 `gnb_mob` 영역이 오른쪽에서 슬라이드 인/아웃한다.

```typescript
// 열기
function openMobileMenu() {
  document.body.classList.add('noscroll');
  gnbWrap.style.display = 'block';
  gnbArea.style.right = '0';
  document.getElementById('wrap')?.classList.add('gnb_dim');
}

// 닫기
function closeMobileMenu() {
  gnbArea.style.right = '-100%';
  setTimeout(() => gnbWrap.style.display = 'none', 300);  // transition 대기
  document.body.classList.remove('noscroll');
  document.getElementById('wrap')?.classList.remove('gnb_dim');
}
```

- 브레이크포인트: `window.innerWidth <= 1400` 이면 모바일
- 라우트 변경 시 `watch(route.fullPath)` 로 자동 닫힘
- 트리거: `.gnb_open` 버튼(모바일), `.gnb_close` 버튼

### 2-8. 4뎁스 추가하는 방법

현재 3뎁스(`gnbC`)까지 구현되어 있다. 4뎁스를 추가하려면 아래 절차를 따른다.

#### 수정 파일

1. `components/www/main/GnbMenu.vue` (그리고 동일하게 `components/default/main/GnbMenu.vue`)
2. www CSS: `/public/style/www/halftour/layout.css` (또는 별도 `gnb.css`)
3. default CSS: `/public/style/default/yumcorp/layout.css`

#### GnbMenu.vue 수정 — gnbC `<li>` 내부에 gnbD 블록 추가

```html
<!-- 3차 메뉴 li 내부 끝에 추가 -->
<li
  v-for="(child, cIndex) in visibleChildrenOf(sub)"
  :key="child.id"
  :class="['gnbCs' + (sIndex + 1), 'gnbCc' + (cIndex + 1)]"
>
  <!-- 기존 3차 링크 -->
  <NuxtLink :to="getHrefFromMenu(child) || '/'">{{ child.title }}</NuxtLink>

  <!-- 4차 메뉴 (신규 추가) -->
  <div v-if="hasVisibleChildren(child)" class="gnbD_wrap">
    <ul :class="['gnbD', 'gnbD' + (index + 1)]">
      <li
        v-for="(d, dIndex) in visibleChildrenOf(child)"
        :key="d.id"
        :class="['gnbDs' + (cIndex + 1), 'gnbDc' + (dIndex + 1)]"
      >
        <template v-if="isLinkType(d)">
          <a :href="linkHref(d)" target="_blank" title="새창" class="newwin">
            {{ d.title }}<span>새창</span>
          </a>
        </template>
        <template v-else>
          <NuxtLink :to="getHrefFromMenu(d) || '/'">{{ d.title }}</NuxtLink>
        </template>
      </li>
    </ul>
  </div>
</li>
```

#### CSS 추가 (layout.css)

```css
/* 4차 메뉴 기본 스타일 — 퍼블리셔가 디자인에 맞게 수정 */
.gnbD_wrap { display: none; position: absolute; }
.gnbCs1:hover .gnbD_wrap,
.gnbCs1:focus-within .gnbD_wrap { display: block; }
.gnbD { list-style: none; padding: 0; margin: 0; }
.gnbD li a { display: block; padding: 6px 12px; }
```

---

## 3. LNB/SNB (서브 페이지 사이드바)

### 3-1. www 서브 사이드바: `components/www/sub/Sidebar.vue`

서브 페이지에서 좌측에 마운트되는 네비. `layouts/www-sub.vue`의 `div.sub_nav` 안에 위치.

#### HTML 구조

```
div.lnb.tpB
  ul.snb
    li.home                         ← HOME 링크
    li.snb_level.snb_level1[.on]    ← 1차 메뉴 셀렉터 (전체 GNB 목록 드롭다운)
      a (토글)
      ul.sectionB.sectionB1
        li.sectionBs1.sectionBc{N}  ← N번째 1차 메뉴 항목
    li.snb_level.snb_level2[.on]    ← 2차 메뉴 셀렉터 (현재 섹션 하위 목록)
      a (토글)
      ul.sectionB.sectionB2
        li.sectionBs2.sectionBc{M}  ← M번째 2차 메뉴 항목
```

#### 동작 방식

- `openLevel`: `1` 또는 `2` (숫자) 또는 `null`. 한 번에 하나만 열림.
- `toggleLevel(level)`: 같은 레벨 재클릭 시 닫힘.
- 외부 클릭 감지: `onClickOutside` 핸들러가 `sidebarEl.value.contains(e.target)` 확인.
- 라우트 변경 시 `watch(route.fullPath)` → `openLevel = null` 자동 닫힘.

#### `useTopMenu()` 활용

```typescript
const menuStore = useMenuStore();
const menuTree = menuStore.menuTree;
const { topMenu, secondDepthMenu } = useTopMenu(menuTree);
```

- `topMenu`: 현재 경로와 가장 긴 prefix로 매칭된 1차 메뉴 (`MenuItem`)
- `secondDepthMenu`: `topMenu.children` 중 `isShow === true`인 항목 배열

### 3-2. SNB CSS 클래스 패턴

| 클래스 | 의미 |
|---|---|
| `snb_level1` | 1차 메뉴 선택 드롭다운 |
| `snb_level2` | 2차 메뉴 선택 드롭다운 |
| `.on` | 현재 열려 있는 레벨 |
| `sectionB1` | 1차 메뉴 전체 목록 ul |
| `sectionB2` | 2차 메뉴 목록 ul |
| `sectionBs1` / `sectionBs2` | 상위 레벨 인덱스 표시 |
| `sectionBc{N}` | N번째 항목 |

### 3-3. 3뎁스 이상 추가하는 방법

현재 www 서브 사이드바는 2뎁스(1차 선택 + 2차 목록)만 지원한다. 3뎁스를 추가하려면:

**수정 파일**: `components/www/sub/Sidebar.vue`

1. `openLevel`을 숫자가 아닌 배열로 변경하거나 `openLevel3` ref를 추가
2. `useTopMenu()`가 반환하는 `secondDepthMenu`에서 현재 활성 2차 메뉴 선택
3. 해당 2차 메뉴의 `children`을 3차 목록으로 렌더링

```html
<!-- snb_level3 추가 예시 -->
<li v-if="thirdDepthMenu?.length" :class="['snb_level snb_level3', openLevel === 3 && 'on']">
  <a href="#none" @click.prevent="toggleLevel(3)">
    <span>{{ activeThirdTitle }}</span>
    <span class="more">{{ openLevel === 3 ? '닫기' : '열기' }}</span>
  </a>
  <ul class="sectionB sectionB3" :style="openLevel === 3 ? 'display:block' : ''">
    <li
      v-for="(menu, index) in thirdDepthMenu"
      :key="menu.id"
      :class="['sectionBs3', `sectionBc${index + 1}`, isActiveMenu(menu) && 'on']"
    >
      <NuxtLink :to="getHrefFromMenu(menu) || '/'">
        <span>{{ menu.title }}</span>
      </NuxtLink>
    </li>
  </ul>
</li>
```

```typescript
// script에 추가
const activeSecondMenu = computed(() =>
  secondDepthMenu.value?.find(m => isActiveMenu(m)) ?? secondDepthMenu.value?.[0]
);
const thirdDepthMenu = computed(() =>
  (activeSecondMenu.value?.children ?? []).filter(c => c.isShow === true)
);
```

---

## 4. default 사이트 네비게이션

### 4-1. default GNB: `components/default/main/GnbMenu.vue`

www GNB와 동일한 3뎁스 구조. 차이점:

| 항목 | www | default |
|---|---|---|
| dim 효과 | 있음 (`setDim()`) | 없음 |
| `gnbB_wrap` 내부 구조 | `gnbB_area` 단일 | `gnb_wrap > gnb_inner > title_box + gnbB_wrap` |
| 2차 링크 텍스트 감싸는 span | 없음 | `span.gnbB_txt` |
| `newWinId` 속성 | 없음 | `aria-describedby` 적용 |

default GNB 드롭다운 HTML:

```
div.gnb_wrap
  div.gnb_inner.inner
    div.title_box
      h2 (1차 메뉴 제목)
    div.gnbB_wrap
      ul.gnbB.gnbB{N}
        li.gnbBs{N}.gnbBc{M}
          NuxtLink > span.gnbB_txt
          div.gnbC_wrap
            ul.gnbC.gnbC{N}
              li.gnbCs{M}.gnbCc{K}
```

### 4-2. default 메인 사이드바: `components/default/main/Sidebar.vue`

메인 레이아웃(main 화면)에서 쓰는 사이드바. Tailwind 없이 custom CSS로 작동.

- 1차 메뉴: `div.primary-menu > ul > li.menu-item[.active]` — 클릭 시 `setActiveFirstMenu(menu)` 호출
- 2차 메뉴: `div.secondary-content > ul.secondary-menu > li.secondary-menu-item[.active]`
  - 자식 없는 리프: `NuxtLink.secondary-menu-header.tertiary-menu-link`
  - 자식 있는 폴더: `button.secondary-menu-header` + 아코디언
- 3차 메뉴: `ul.tertiary-menu > li.tertiary-menu-item` (expand transition 적용)
- 외부 link 타입: `LinkIcon` (heroicons) 아이콘 표시 + `newWinId` aria 처리
- 상태: `hoveredFirst` (현재 선택 1차), `expandedSecondId` (열린 2차 id)
- 라우트 변경 시 `watch([route.path, firstLevelMenus])` 로 자동 갱신

### 4-3. default 서브 사이드바: `components/default/sub/Sidebar.vue`

서브 레이아웃(`layouts/default-sub.vue`)의 `#left`에 마운트.

- `useTopMenu()` 로 현재 1차 메뉴(`topMenu`)와 2차 메뉴 목록(`secondDepthMenu`) 획득
- 2차 항목에 자식이 있으면 토글 버튼 + 3차 아코디언 (`snbB.snbB{N}`)
- 2차 항목에 자식 없으면 직접 링크 또는 외부 링크

```
h2 (topMenu.title)
ul.snb
  li.snbA.snbA{N}[.on][.open]
    NuxtLink (토글, has_child)   ← 자식 있을 때
    ul.snbB.snbB{N}              ← 3차 목록 (display:block/none)
      li.snbBs{N}.snbBc{M}[.on]
        a (link 타입)
        NuxtLink (내부)
    a / NuxtLink                 ← 자식 없을 때 (리프)
```

`www/sub/Sidebar.vue`와 코드가 거의 동일하며 같은 클래스 네이밍을 공유한다.

---

## 5. business (관리자) 사이드바

### 5-1. `components/business/Sidebar.vue`

Tailwind CSS 전용. 사이드바 전체 래퍼.

**주요 동작:**

| 상태 | 조건 | 결과 |
|---|---|---|
| 데스크톱 확장 | `!ui.isSidebarCollapsed` | `w-64`, 텍스트 표시 |
| 데스크톱 축소 | `ui.isSidebarCollapsed` | `w-20`, 아이콘만 표시 |
| 모바일 | `ui.isMobile` | `fixed top-16 left-0 w-64`, translate로 슬라이드 |
| 호버 임시 확장 | `mouseenter` (축소 상태) | 임시로 펼침 → `wasCollapsedOnHover = true` |
| 호버 복원 | `mouseleave` | `wasCollapsedOnHover`이면 다시 축소 |

**메뉴 구조:**

```
aside
  div.h-16 (로고)
  nav
    div (섹션, type='folder'인 최상위 항목)
      h6 (섹션 제목)
      BusinessSidebarItem (자식 목록, 재귀)
```

- `visibleSections`: `menuTree.filter(s => s.type === 'folder' && s.isShow === true)`
- 각 섹션의 자식은 `getVisibleChildren(section)` → `children.filter(c => c.isShow)`

### 5-2. `components/business/SidebarItem.vue`

재귀 컴포넌트. 자식이 있으면 토글, 없으면 `NuxtLink` 직접 링크.

**아이콘 매핑** (메뉴 title → heroicons):

| 메뉴 title | 아이콘 |
|---|---|
| 사이트관리 | `Cog6ToothIcon` |
| 메뉴관리 | `ListBulletIcon` |
| 회원관리 | `UserIcon` |
| 권한관리 | `KeyIcon` |
| 콘텐츠관리 | `WindowIcon` |
| 게시판관리 | `DocumentTextIcon` |
| 팝업관리 | `Square2StackIcon` |
| 접속로그 | `ClockIcon` |
| 이미지관리 | `PhotoIcon` |
| 스타일관리 | `PaintBrushIcon` |
| (기타) | `DocumentIcon` (기본값) |

**활성 상태 판단:**

```typescript
const isActive = computed(() => route.path === getHrefFromMenu(props.item.pathUrl))
const isActiveParent = computed(() => {
  if (isActive.value) return true
  return children.some(child =>
    route.path === childPath || route.path.startsWith(childPath + '/')
  )
})
// 라우트 변경 시 isActiveParent이면 자동으로 open = true
```

---

## 6. 메뉴 데이터 흐름

### 6-1. 데이터 소스

```
menuStore.menuTree  ← API /api/cms/menu/tree (미들웨어 02에서 fetch)
menuStore.breadcrumb
menuStore.breadcrumbTitle
```

`menuTree`는 `MenuItem[]` 트리 구조. 각 노드:

```typescript
interface MenuItem {
  id: number
  title: string
  type: 'folder' | 'board' | 'content' | 'script' | 'link'
  isShow: boolean
  pathUrl: string           // "menuId|site|seg1|seg2" 형식
  routePath: string | null  // 실제 라우트 경로 (백엔드 계산)
  value: string | null      // link 타입의 외부 URL
  children: MenuItem[]
}
```

### 6-2. `utils/menu.ts` 주요 함수

| 함수 | 역할 |
|---|---|
| `initRouteContext(route)` | SSR 대비: `setup()` 첫 줄에서 반드시 호출 |
| `getHrefFromMenu(menu, opts?)` | 메뉴 타입에 따라 이동 경로 반환 |
| `visibleChildrenOf(node)` | `isShow === true`인 자식만 필터링 |
| `isCurrentGnb(pathUrl)` | 현재 경로가 해당 GNB 섹션에 속하는지 (prefix 매칭) |
| `isCurrentSnb(pathUrl)` | 현재 경로가 pathUrl과 정확히 일치하는지 (SNB용) |
| `isActiveMenu(menu)` | 현재 메뉴 또는 자식 메뉴가 활성 경로인지 재귀 판별 |
| `useTopMenu(menuTree)` | `topMenu`, `secondDepthMenu` computed 반환 |
| `findTopMenu(path, menuTree)` | 현재 경로와 가장 긴 prefix 매칭 1차 메뉴 탐색 |
| `findMenuByPath(path, menuList)` | 경로로 특정 MenuItem 탐색 |
| `getEffectiveRoutePath(menu, opts?)` | folder/link는 자식 중 첫 콘텐츠 경로 반환 |

### 6-3. `getHrefFromMenu()` 타입별 경로 규칙

| 메뉴 type | 경로 계산 방식 |
|---|---|
| `link` | `menu.value` (외부 URL). `preferChild: true`이면 자식 콘텐츠 경로 우선 탐색 |
| `folder` | 자식 중 첫 번째 `isShow && type !== 'folder'`의 `routePath` 재귀 탐색 |
| `board` / `content` / `script` | `menu.routePath` 또는 `pathUrl` 파싱 → `/{site}/{seg1}/{seg2}` |

`pathUrl` 파싱 규칙 (`buildInternalFromPathUrl`):

```
"123|www|notify|view"  →  "/www/notify/view"
"456|www"              →  "/www"
"789|default|about"   →  "/default/about"
```

### 6-4. `utils/link.ts` 주요 함수

| 함수 | 역할 |
|---|---|
| `isLinkType(menu)` | `menu.type === 'link'` 여부 |
| `linkHref(menu)` | link 타입의 외부 URL 정규화 (도메인만 오면 `http://` 보정) |
| `newWinId(menu)` | 스크린리더용 "새 창에서 열림" 안내 element id 생성 |
| `normalizeLinkValue(raw)` | `javascript:`, `data:` 차단; `//`, `http:`, `/` 그대로 |

외부 링크 렌더링 패턴 (GNB/SNB 공통):

```html
<template v-if="isLinkType(menu)">
  <a :href="linkHref(menu)" target="_blank" title="새창" class="newwin">
    {{ menu.title }}<span>새창</span>
  </a>
</template>
<template v-else>
  <NuxtLink :to="getHrefFromMenu(menu) || '/'">{{ menu.title }}</NuxtLink>
</template>
```

---

## 7. HTML 수정 포인트 요약

퍼블리셔가 네비 디자인을 변경할 때 건드려야 하는 파일과 클래스 매핑표.

### www 사이트

| 수정 내용 | Vue 컴포넌트 | CSS 파일 | 주요 클래스 |
|---|---|---|---|
| GNB 1차 메뉴 스타일 | `www/main/GnbMenu.vue` | `halftour/layout.css` | `.gnbA`, `.gnbA{N}`, `.on`, `.now` |
| GNB 2차 드롭다운 영역 | `www/main/GnbMenu.vue` | `halftour/layout.css` | `.gnbB_wrap`, `.gnbB_area`, `.gnbB{N}` |
| GNB 3차 메뉴 | `www/main/GnbMenu.vue` | `halftour/layout.css` | `.gnbC_wrap`, `.gnbC{N}`, `.gnbCs{M}`, `.gnbCc{K}` |
| GNB 배경 dim | `www/main/GnbMenu.vue` | `halftour/layout.css` | `#wrap.gnb_dim` |
| 헤더 전체 구조 | `www/main/Header.vue` | `halftour/layout.css` | `#header.tpA`, `.gnb_web`, `.util` |
| 모바일 드로어 | `www/main/Header.vue` | `halftour/layout.css` | `.gnb_mob`, `.gnb_wrap`, `.gnb_area`, `.gnb_top`, `.gnb_mid`, `.gnb_bot` |
| 모바일 열기/닫기 버튼 | `www/main/Header.vue` | `halftour/layout.css` | `.gnb_open`, `.gnb_close` |
| 서브 비주얼 | `www/sub/Header.vue` | `halftour/sub.css` | `.sub_vis`, `.tit` |
| LNB/SNB 사이드바 | `www/sub/Sidebar.vue` | `halftour/sub.css` | `.lnb.tpB`, `.snb`, `.snb_level`, `.snb_level1`, `.snb_level2` |
| SNB 드롭다운 목록 | `www/sub/Sidebar.vue` | `halftour/sub.css` | `.sectionB`, `.sectionB1`, `.sectionB2`, `.sectionBs{N}`, `.sectionBc{N}` |
| 브레드크럼 | `www/sub/Breadcrumb.vue` | `halftour/sub.css` | `.path` |
| 서브 레이아웃 구조 | `layouts/www-sub.vue` | `halftour/sub.css` | `#container`, `.inner`, `.sub_nav`, `.sub_in`, `#content` |

### default 사이트

| 수정 내용 | Vue 컴포넌트 | CSS 파일 | 주요 클래스 |
|---|---|---|---|
| GNB 헤더 | `default/main/Header.vue` | `yumcorp/layout.css` | `#header.header`, `#top_menu.gnb_box`, `.loginout` |
| GNB 드롭다운 | `default/main/GnbMenu.vue` | `yumcorp/layout.css` | `.gnb_wrap`, `.gnb_inner`, `.title_box`, `.gnbB_wrap` |
| GNB 2·3차 메뉴 | `default/main/GnbMenu.vue` | `yumcorp/layout.css` | `.gnbB{N}`, `.gnbBs{N}`, `.gnbBc{M}`, `.gnbC_wrap`, `.gnbC{N}` |
| 메인 사이드바 | `default/main/Sidebar.vue` | `yumcorp/layout.css` | `.sidebar-container`, `.primary-menu`, `.secondary-content`, `.secondary-menu`, `.tertiary-menu` |
| 서브 사이드바 | `default/sub/Sidebar.vue` | `yumcorp/sub.css` | `.snb`, `.snbA`, `.snbA{N}`, `.snbB`, `.snbB{N}`, `.snbBs{N}`, `.snbBc{M}` |
| 서브 레이아웃 | `layouts/default-sub.vue` | `yumcorp/sub.css` | `#container`, `.cont_inner`, `#left`, `#right`, `#content_box` |

### business (관리자)

| 수정 내용 | Vue 컴포넌트 | 방식 | 주요 Tailwind 클래스 |
|---|---|---|---|
| 사이드바 너비/전환 | `business/Sidebar.vue` | Tailwind | `w-64` / `w-20`, `translate-x-0` / `-translate-x-full` |
| 섹션 제목 | `business/Sidebar.vue` | Tailwind | `text-xs text-gray-400 uppercase` |
| 메뉴 아이템 링크 | `business/SidebarItem.vue` | Tailwind | `bg-sky-100 dark:bg-gray-800` (활성), `hover:bg-gray-100` |
| 아이콘 컬러 | `business/SidebarItem.vue` | Tailwind | `text-indigo-500 dark:text-indigo-400` (활성) |
| 아이콘 매핑 추가 | `business/SidebarItem.vue` | TypeScript | `titleToIconMap` 객체에 항목 추가 |
