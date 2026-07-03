# 실전 시나리오 FAQ

신입 개발자/퍼블리셔가 실무에서 바로 마주치는 질문들을 Q&A 형식으로 정리합니다.
각 답변에는 실제 파일 경로와 소스코드 기반 예시를 포함합니다.

---

## 퍼블리셔 시나리오

---

### Q1. 메인 페이지에 새로운 게시판 섹션을 추가하고 싶어요

**핵심 답변:** `layouts/www-main.vue`에 `<WidgetList>` 컴포넌트를 추가하고, `menuId`에 연결할 게시판 ID를 지정합니다.

**수정 파일:**
- `layouts/www-main.vue` — 메인 레이아웃 HTML 구조에 섹션 추가
- `components/common/WidgetList.vue` — 게시판 데이터를 자동으로 가져와 HTML 템플릿으로 렌더링하는 공통 컴포넌트

**menuId 찾는 법:**
관리자 페이지(`/business`) → 홈페이지 → 메뉴관리에서 해당 게시판 메뉴를 선택하면 URL에 `?menuId=숫자` 형태로 확인됩니다. 또는 백엔드 DB의 `cms_menu` 테이블 `id` 컬럼을 직접 조회합니다.

**코드 예시** (`layouts/www-main.vue`에 추가):

```vue
<!-- 공지사항 섹션 추가 예시 -->
<div class="main_notice">
  <div class="inner">
    <h2 class="tit">공지사항</h2>
    <WidgetList
      :menu-id="42"
      :size="5"
      wrapper-tag="ul"
      wrapper-class="notice_list"
      item-template="<li><a href='{%url}'>{%title}</a><span class='date'>{%date}</span></li>"
    />
  </div>
</div>
```

**WidgetList 주요 props:**

| prop | 설명 | 예시 |
|---|---|---|
| `menuId` | 게시판 메뉴 ID (필수) | `:menu-id="42"` |
| `size` | 가져올 게시물 수 | `:size="5"` |
| `itemTemplate` | 각 항목 HTML 템플릿 | `{%title}`, `{%date}`, `{%url}`, `{%img}` |
| `wrapperTag` | 감싸는 태그 | `"ul"`, `"div"` |
| `wrapperClass` | 감싸는 태그의 CSS 클래스 | `"notice_list"` |
| `linkToList` | `true`이면 항목 URL이 목록 페이지로 이동 | `:link-to-list="true"` |

**템플릿 변수:**
- `{%title}` — 제목 (HTML 이스케이프됨)
- `{%url}` — 상세 페이지 URL
- `{%date}` — 등록일 (`2024.01.15` 형식)
- `{%img}` — 대표 이미지 URL
- `{%desc}` — 내용 요약
- `{%newBadge}` — 7일 이내 글이면 `<span class="new">새글</span>` 출력 (raw 변수: `{%raw:newBadge}`)

**관련 문서:** 문서 25 (메인페이지 데이터 연결), 문서 33 (공통 UI 컴포넌트)

---

### Q2. GNB에 4뎁스 메뉴를 추가해야 해요

**핵심 답변:** 현재 GNB는 1~3뎁스(gnbA → gnbB → gnbC)까지 구조가 잡혀 있습니다. 4뎁스를 추가하려면 `GnbMenu.vue`에 gnbD 블록을 추가하고 대응하는 CSS 클래스를 작성해야 합니다.

**수정 파일:**
- `components/default/main/GnbMenu.vue` — Vue 템플릿에 4뎁스 블록 추가
- `public/style/www/module/component.css` (또는 해당 사이트의 CSS 파일) — `.gnbD`, `.gnbD_wrap` CSS 추가

**GnbMenu.vue 현재 구조 (3뎁스까지):**

```html
<!-- 1뎁스: gnbA -->
<li class="gnbA">
  <!-- 2뎁스: gnbB -->
  <ul class="gnbB">
    <li>
      <!-- 3뎁스: gnbC -->
      <div class="gnbC_wrap">
        <ul class="gnbC">
          <li>...</li>  <!-- 여기서 끝 -->
        </ul>
      </div>
    </li>
  </ul>
</li>
```

**4뎁스 추가 위치** (`GnbMenu.vue` 3뎁스 `<li>` 내부에 삽입):

```html
<!-- 3뎁스 li 내부에 4뎁스 블록 추가 -->
<li
  v-for="(child, cIndex) in visibleChildrenOf(sub)"
  :key="child.id"
>
  <NuxtLink :to="getHrefFromMenu(child) || '/'">{{ child.title }}</NuxtLink>

  <!-- 4뎁스 추가 -->
  <div v-if="hasVisibleChildren(child)" class="gnbD_wrap">
    <ul class="gnbD">
      <li
        v-for="(depth4, d4Index) in visibleChildrenOf(child)"
        :key="depth4.id"
      >
        <NuxtLink :to="getHrefFromMenu(depth4) || '/'">{{ depth4.title }}</NuxtLink>
      </li>
    </ul>
  </div>
</li>
```

**CSS 추가 예시:**

```css
/* 4뎁스 GNB */
.gnbD_wrap { display: none; position: absolute; top: 100%; left: 0; }
.gnbA:hover .gnbD_wrap { display: block; }
.gnbD { list-style: none; padding: 0; margin: 0; }
.gnbD li a { display: block; padding: 8px 16px; }
```

**주의:** `hasVisibleChildren()`과 `visibleChildrenOf()` 함수는 `GnbMenu.vue`에 이미 정의되어 있으므로 그대로 재사용합니다. `GnbMenu.vue`는 `components/default/main/GnbMenu.vue` 위치이므로 `default` 사이트용입니다. `www` 사이트에 별도 GNB가 있다면 해당 컴포넌트를 수정하세요.

**관련 문서:** 문서 26 (GNB-LNB-SNB 가이드)

---

### Q3. 새 사이트(예: tour)의 레이아웃을 만들어야 해요

**핵심 답변:** `layouts/tour-main.vue`와 `layouts/tour-sub.vue`를 생성하면 레이아웃 선택 미들웨어(`01b.layout-setting.global.ts`)가 자동으로 감지해서 적용합니다. CSS는 `useVersionedCss`로 연결합니다.

**생성할 파일:**
- `layouts/tour-main.vue` — 메인 페이지 레이아웃
- `layouts/tour-sub.vue` — 서브 페이지 레이아웃
- `public/style/tour/common/base.css` — 사이트 전용 CSS

**레이아웃 자동 선택 규칙** (`middleware/01b.layout-setting.global.ts`):
- `/tour` (루트) → `tour-main.vue`
- `/tour/...` (서브 페이지) → `tour-sub.vue`
- 파일이 없으면 `default-main.vue` / `default-sub.vue`로 폴백

**`layouts/tour-main.vue` 최소 예시:**

```vue
<template>
  <div id="wrap" class="main">
    <TourMainHeader />

    <section id="container">
      <slot />
    </section>

    <TourMainFooter />

    <ClientOnly>
      <CommonPopupLayer hostname="tour" />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount } from "vue";
import { useLegacyGnbJqShim } from "~/composables/utils/useLegacyGnbJqShim";

onMounted(() => {
  const off = useLegacyGnbJqShim();
  onBeforeUnmount(() => off());
});

useHead({
  link: useVersionedCss([
    "/public/style/tour/common/base.css",
    "/public/style/tour/layout/main.css",
  ]),
});
</script>
```

**`useVersionedCss` 동작:** `css-version.json`의 버전 값을 읽어 `?v=20241201` 형태의 캐시 버스팅 쿼리스트링을 CSS URL에 자동으로 붙여줍니다. CSS 배포 후 캐시가 즉시 갱신되는 원리입니다.

**주의:** `business` 사이트는 관리자 전용으로 Tailwind CSS를 사용합니다. 일반 사이트(www, tour 등)에는 Tailwind를 사용하지 말고 퍼블리싱 CSS만 연결하세요.

**관련 문서:** 문서 19 (레이아웃-CSS), 문서 10 (프론트엔드 구조)

---

### Q4. 게시판 목록 디자인을 바꾸고 싶어요 (특정 메뉴만)

**핵심 답변:** 해당 게시판의 `menuId`로 `overrides/{menuId}.vue` 파일을 생성하면 `Loader.vue`가 자동으로 감지해서 기본 `Ori.vue` 대신 커스텀 컴포넌트를 렌더링합니다.

**수정 파일 (신규 생성):**
- `components/theme/list/default/list/overrides/{menuId}.vue` — 목록 뷰 커스텀
- `components/theme/list/default/view/overrides/{menuId}.vue` — 상세 뷰 커스텀
- `components/theme/list/default/write/overrides/{menuId}.vue` — 작성 뷰 커스텀

**동작 원리** (`components/theme/list/default/list/Loader.vue`):

```vue
<script setup lang="ts">
import Ori from "./Ori.vue";
import { useMenuOverride } from "~/composables/api/render/useMenuOverride";

// overrides/ 폴더의 모든 .vue 파일을 자동 수집
const overrideModules = import.meta.glob("./overrides/*.vue", { eager: true });

// 현재 menuId와 파일명이 일치하면 해당 컴포넌트 사용, 없으면 Ori.vue 사용
const { resolvedComponent } = useMenuOverride(Ori, overrideModules);
</script>

<template>
  <component :is="resolvedComponent" />
</template>
```

**커스텀 컴포넌트 예시** (`overrides/42.vue` — menuId가 42인 게시판만 적용):

```vue
<template>
  <div class="custom_board_42">
    <!-- 기존 board inject에서 데이터를 가져옵니다 -->
    <ul class="card_list">
      <li v-for="item in boardList" :key="item.idx">
        <a :href="`?mode=view&idx=${item.idx}`">
          <img v-if="item.imageUrl" :src="item.imageUrl" :alt="item.title" />
          <p class="tit">{{ item.title }}</p>
          <span class="date">{{ item.createdDate }}</span>
        </a>
      </li>
    </ul>
    <themeCommonListPagination />
  </div>
</template>

<script setup lang="ts">
import { inject } from "vue";
import { boardCoreKey } from "~/composables/api/render/useBoard";

const board = inject(boardCoreKey)!;
const { boardList } = board;
</script>
```

**menuId 확인:** 관리자 메뉴 관리 화면에서 해당 메뉴 선택 시 URL의 `menuId` 파라미터 값입니다.

**관련 문서:** 문서 18 (테마 개발 가이드), 문서 12 (렌더링 시스템)

---

### Q5. Swiper 배너를 새로 하나 더 추가해야 해요

**핵심 답변:** 관리자 팝업 관리에서 새 팝업(팝업 타입: BANNER)을 생성하고 `popupId`를 받아 `VisualBanner` 컴포넌트를 사용하면 됩니다.

**참고 파일:**
- `components/common/VisualBanner.vue` — 범용 배너 컴포넌트 (슬롯 방식)
- `composables/api/render/useVisualBanner.ts` — 배너 데이터 로딩 + 슬라이드 제어
- `layouts/www-main.vue` — `<WwwMainTourBanner :popup-id="BANNER.mainTour" />` 사용 예시

**새 배너 추가 순서:**

1. 관리자 → 홈페이지 → 팝업/배너 관리에서 새 배너를 생성하고 이미지를 등록합니다.
2. 생성된 팝업의 `idx`(ID) 값을 확인합니다.
3. 새 배너 컴포넌트를 생성합니다.

**새 배너 컴포넌트 예시** (`components/www/main/EventBanner.vue`):

```vue
<template>
  <VisualBanner :popup-id="popupId">
    <template #default="{ items, currentIndex, next, prev, goTo, isPaused, togglePause }">
      <div class="event_banner">
        <ul class="slider_list">
          <li
            v-for="(item, idx) in items"
            :key="item.idx"
            :class="['slide', idx === currentIndex && 'active']"
          >
            <a :href="item.linkUrl || '#'" :target="item.linkTarget">
              <img :src="item.imageUrl" :alt="item.title || '배너'" />
            </a>
          </li>
        </ul>
        <!-- 이전/다음 버튼 -->
        <button type="button" @click="prev">이전</button>
        <button type="button" @click="next">다음</button>
        <!-- 인디케이터 -->
        <ol class="indicator">
          <li
            v-for="(_, i) in items"
            :key="i"
            :class="i === currentIndex && 'on'"
            @click="goTo(i)"
          />
        </ol>
      </div>
    </template>
  </VisualBanner>
</template>

<script setup lang="ts">
defineProps<{ popupId: number }>();
</script>
```

**레이아웃에서 사용:**

```vue
<!-- layouts/www-main.vue -->
<script setup lang="ts">
const BANNER = {
  mainTour: 22,   // 기존 배너 popupId
  event: 35,      // 새로 생성한 배너 popupId
};
</script>

<template>
  <WwwMainEventBanner :popup-id="BANNER.event" />
</template>
```

**`useVisualBanner`가 호출하는 API:** `GET /back-api/popup/{idx}/active-images`
응답 구조: `{ data: { images: [...], autoSlide: true, slideInterval: 3, slideEffect: "fade" } }`

**관련 문서:** 문서 15 (팝업-배너), 문서 25 (메인페이지 데이터 연결)

---

### Q6. 모바일에서만 보이는 요소를 추가하고 싶어요

**핵심 답변:** 퍼블리싱 CSS에 정의된 `.web_only`, `.mob_only` 클래스를 HTML 요소에 추가하면 됩니다.

**사용법:**

```html
<!-- PC에서만 보임 (모바일에서 숨김) -->
<span class="web_only">PC 전용 텍스트</span>
<br class="web_only" />

<!-- 모바일에서만 보임 (PC에서 숨김) -->
<button class="mob_only">모바일 메뉴</button>
```

**실제 사용 예시** (`layouts/www-main.vue` 발췌):

```html
<span class="tit">지금 장흥은<br class="web_only" />즐거움ing</span>
```

**CSS 정의 위치:** `public/style/www/module/component.css` 또는 `base.css`에서 미디어쿼리로 정의됩니다.

```css
/* 퍼블리싱 CSS 예시 구조 */
@media (max-width: 768px) {
  .web_only { display: none !important; }
}
@media (min-width: 769px) {
  .mob_only { display: none !important; }
}
```

**주의:** `business`(관리자) 사이트에서는 Tailwind의 `hidden sm:block` 같은 반응형 유틸리티를 사용합니다. 일반 사이트(www 등)에서는 반드시 퍼블리싱 CSS 클래스(`web_only`, `mob_only`)를 사용하세요.

**관련 문서:** 문서 19 (레이아웃-CSS)

---

## 프론트엔드 개발자 시나리오

---

### Q7. 새 페이지를 만들어야 해요 (slug 라우팅 안 타는)

**핵심 답변:** 관리자에서 메뉴 타입을 `script`로 생성하고, `pages/{site}/페이지명.vue`를 직접 만들면 `[...slug].vue`의 Board/Content 렌더러를 우회합니다.

**동작 원리:** Nuxt의 파일 기반 라우팅에서 구체적인 경로(`/www/half/apply`)가 catch-all(`[...slug]`)보다 우선 매칭됩니다.

**실제 예시** (`pages/www/half/apply.vue` — 신청 폼 페이지):

```vue
<template>
  <ApplyMain />
</template>

<script setup lang="ts">
import ApplyMain from "~/components/render/script/apply/ApplyMain.vue";
</script>
```

**새 페이지 추가 절차:**

1. 관리자 → 메뉴관리 → 새 메뉴 추가, 타입을 `script`로 설정, 경로를 `/www/mypage` 형태로 지정
2. `pages/www/mypage.vue` 파일 생성

```vue
<template>
  <div class="my_page">
    <h1>나의 페이지</h1>
    <!-- 커스텀 UI -->
  </div>
</template>

<script setup lang="ts">
// 레이아웃은 자동으로 www-sub가 적용됨 (미들웨어 01b에서 처리)
// 필요하면 명시적으로 지정 가능
definePageMeta({
  layout: 'www-sub',
})
</script>
```

**주의:** `script` 타입 메뉴는 `[...slug].vue`의 렌더 흐름(Board/Content 렌더러)을 타지 않으므로, `renderStore.fetchRenderData()`도 호출되지 않습니다. 권한 체크 등이 필요하면 컴포넌트에서 직접 처리해야 합니다.

**관련 문서:** 문서 08 (메뉴-콘텐츠), 문서 12 (렌더링 시스템)

---

### Q8. 게시판 데이터를 API로 가져와서 커스텀 UI를 만들고 싶어요

**핵심 답변:** `safeFetch`와 `menuOverride` 옵션을 사용하면 어떤 메뉴의 게시판 데이터든 가져올 수 있습니다.

**참고 파일:**
- `components/common/WidgetList.vue` — `safeFetch` + `menuOverride` 사용 실제 예시

**코드 예시:**

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { safeFetch } from "~/utils/safeFetch";
import { useSiteStore } from "~/stores/siteStore";

const siteStore = useSiteStore();
const items = ref([]);

onMounted(async () => {
  const res = await safeFetch("/board", {
    query: {
      page: 0,
      size: 10,
      sort: "regDate,desc",
    },
    credentials: "include",
    timeout: 2000,
    defaultValue: { code: 500, message: "조회 실패", data: {} },
    // menuOverride: 어떤 메뉴(게시판)의 데이터를 가져올지 지정
    menuOverride: { id: 42, site: siteStore.site },
    cacheScope: "url+menu",
  });

  // 응답 구조: { code, message, data: { content: [...], totalPages, totalElements } }
  items.value = res?.data?.content ?? res?.data ?? [];
});
</script>
```

**응답 구조:**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "content": [
      { "idx": 1, "title": "제목", "createdDate": "2024-01-15", ... }
    ],
    "totalPages": 5,
    "totalElements": 48,
    "number": 0
  }
}
```

**`safeFetch` 주요 옵션:**

| 옵션 | 설명 |
|---|---|
| `menuOverride.id` | 타겟 게시판 menuId |
| `menuOverride.site` | 사이트명 (`siteStore.site`) |
| `credentials: "include"` | 로그인 쿠키 전송 (로그인 필요 게시판에 필수) |
| `timeout` | 밀리초 단위 타임아웃 (기본 2000) |
| `defaultValue` | 실패 시 반환할 기본값 |
| `cacheScope` | 클라이언트 캐시 범위 (`"url+menu"` 권장) |

**관련 문서:** 문서 21 (Composable 레퍼런스), 문서 20 (API 엔드포인트)

---

### Q9. 로그인 상태를 확인하고 싶어요

**핵심 답변:** `useUserStore()`의 `isGuest` / `isAdmin` computed를 사용합니다. 로그인/로그아웃 액션은 `useAuth()` composable을 사용합니다.

**참고 파일:**
- `stores/userStore.ts` — 사용자 상태 관리
- `composables/api/useAuth.ts` — 로그인/로그아웃 액션

**로그인 상태 확인:**

```vue
<script setup lang="ts">
import { useUserStore } from "~/stores/userStore";

const userStore = useUserStore();

// 비로그인 여부 (idx === -1이면 게스트)
console.log(userStore.isGuest);      // true/false

// 관리자 여부 (level === 1)
console.log(userStore.isAdmin);      // true/false

// 사용자 정보 접근
console.log(userStore.user?.userId);
console.log(userStore.user?.userName);
console.log(userStore.user?.level);  // 1=관리자, 99=게스트
</script>

<template>
  <!-- 로그인 상태에 따른 조건부 렌더링 -->
  <div v-if="!userStore.isGuest">
    <p>안녕하세요, {{ userStore.user?.userName }}님</p>
  </div>
  <div v-else>
    <a href="/common/login">로그인</a>
  </div>
</template>
```

**로그인/로그아웃 처리:**

```vue
<script setup lang="ts">
import { useAuth } from "~/composables/api/useAuth";

const { login, logout } = useAuth();

// 로그인: 성공 시 자동으로 userStore 갱신 + 메인 페이지로 이동
async function handleLogin() {
  await login("userId", "password", "/www");
}

// 로그아웃: 서버 세션 삭제 + 쿠키 제거 + 페이지 리로드
async function handleLogout() {
  await logout();
}
</script>
```

**초기화 타이밍 주의:** `userStore.initialized`가 `false`인 상태에서 `isGuest`를 읽으면 잘못된 값이 나올 수 있습니다. 미들웨어 `02.authentication.global.ts`에서 `await userStore.initUser()`를 이미 호출하므로 페이지/컴포넌트에서는 별도 초기화 없이 바로 사용 가능합니다.

**관련 문서:** 문서 06 (인증-권한), 문서 13 (Store-Composable)

---

### Q10. 새 composable을 만들어야 해요

**핵심 답변:** `composables/api/render/` (렌더링 관련) 또는 `composables/api/admin/` (관리자 관련) 위치에 `use{기능명}.ts` 형태로 생성합니다.

**디렉터리 규칙:**

```
composables/
  api/
    render/          # 공개 사이트 렌더링용 composable
      useBoardList.ts
      useContent.ts
      useVisualBanner.ts
    admin/           # 관리자 페이지용 composable
      useBoardMasterApi.ts
      useMenuManage.ts
  utils/             # 범용 유틸리티
    useImeSafeInput.ts
  useVersionedCss.ts # 최상위 공통
```

**네이밍 규칙:** 파일명은 반드시 `use`로 시작, camelCase. 예: `useMyFeature.ts`

**기본 패턴 (렌더링 composable):**

```typescript
// composables/api/render/useMyFeature.ts
import { ref, computed } from "vue";
import { safeFetch } from "~/utils/safeFetch";

export function useMyFeature(menuId: number) {
  const data = ref<any[]>([]);
  const isLoading = ref(false);

  const fetchData = async () => {
    isLoading.value = true;
    try {
      const res = await safeFetch("/my-endpoint", {
        query: { menuId },
        credentials: "include",
        timeout: 3000,
        defaultValue: { code: 500, data: [] },
      });
      data.value = res?.data ?? [];
    } finally {
      isLoading.value = false;
    }
  };

  const isEmpty = computed(() => data.value.length === 0);

  return { data, isLoading, isEmpty, fetchData };
}
```

**Board 렌더러에서 provide/inject로 데이터 공유하는 패턴:**

```typescript
// composables/api/render/useBoard.ts에서 provide
import type { InjectionKey } from "vue";
export const boardCoreKey = Symbol() as InjectionKey<BoardCore>;
provide(boardCoreKey, boardCore);

// 자식 컴포넌트(Ori.vue 등)에서 inject
import { inject } from "vue";
import { boardCoreKey } from "~/composables/api/render/useBoard";
const board = inject(boardCoreKey)!;
const { boardList, boardOption } = board;
```

**관련 문서:** 문서 13 (Store-Composable), 문서 21 (Composable 레퍼런스)

---

### Q11. SSR에서 동작하는 코드를 작성할 때 주의할 점은?

**핵심 답변:** `window`, `document`, `localStorage` 등 브라우저 전용 API는 `import.meta.client` 가드 안에서만 사용하고, 서버/클라이언트 공통 상태는 `useState`로 전달합니다.

**주요 패턴:**

**1) 브라우저 API 가드:**

```typescript
// 잘못된 예 - SSR에서 window가 없어서 에러
const width = window.innerWidth;

// 올바른 예
if (import.meta.client) {
  const width = window.innerWidth;
}

// 또는 onMounted 안에서 (클라이언트 전용)
onMounted(() => {
  const width = window.innerWidth;
});
```

**2) 서버/클라이언트 분기 실행:**

```typescript
if (import.meta.server) {
  // SSR에서만 실행 (예: 서버 리소스 접근, 응답 헤더 설정)
}

if (import.meta.client) {
  // CSR에서만 실행 (예: DOM 조작, localStorage)
}
```

**3) SSR → CSR 하이드레이션 안전 상태 공유** (`useState` 사용):

```typescript
// composables/useVersionedCss.ts에서 실제 사용 예
export function useVersionedCss(paths: string[]) {
  const config = useRuntimeConfig();
  // useState는 SSR에서 설정된 값을 CSR에서 재사용 (하이드레이션 불일치 방지)
  const cssVersion = useState("cssVersion", () => config.public.cssVersion as string);

  if (import.meta.server) {
    const nuxtApp = useNuxtApp();
    const dynamicVersion = nuxtApp.ssrContext?.event?.context?.cssVersion;
    if (dynamicVersion && dynamicVersion !== "0") {
      cssVersion.value = dynamicVersion;
    }
  }
  // ...
}
```

**4) SSR에서 redirect 1회 제한** (미들웨어 패턴):

```typescript
// middleware 안에서 SSR redirect가 중복 실행되는 것을 방지
if (import.meta.server) {
  const once = useState("__ssr_redirect__", () => false);
  if (once.value) return;  // 이미 redirect 했으면 스킵
  once.value = true;

  return navigateTo("/target", { redirectCode: 302 });
}
```

**5) 서버에서만 실행되는 유저 초기화:**

```typescript
// userStore.ts의 fetchUser에서 타임아웃을 SSR/CSR별로 다르게 설정
timeout: import.meta.server ? 7000 : 2500,
```

**관련 문서:** 문서 11 (미들웨어 체인), 문서 30 (플러그인-서버미들웨어)

---

## 백엔드 개발자 시나리오

---

### Q12. 새 API 엔드포인트를 추가해야 해요

**핵심 답변:** `controller/cms/core/` 하위에 Controller를 생성하고, `@PreAuthorize("@permService.hasAccess('ACCESS')")`로 권한을 설정하고, `ApiResponse<T>` 형식으로 응답합니다.

**참고 파일:** `controller/cms/core/board/DynamicBoardController.java`

**Controller 생성 예시:**

```java
package kr.co.itid.cms.controller.cms.core.myfeature;

import kr.co.itid.cms.dto.common.ApiResponse;
import kr.co.itid.cms.service.cms.core.myfeature.MyFeatureService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/back-api/my-feature")
@RequiredArgsConstructor
public class MyFeatureController {

    private final MyFeatureService myFeatureService;

    // ACCESS 권한: 목록 조회 (비로그인 포함 허용 시 @PreAuthorize 제거)
    @PreAuthorize("@permService.hasAccess('ACCESS')")
    @GetMapping
    public ResponseEntity<ApiResponse<Page<MyDto>>> getList() throws Exception {
        return ResponseEntity.ok(ApiResponse.success(myFeatureService.getList()));
    }

    // VIEW 권한: 상세 조회
    @PreAuthorize("@permService.hasAccess('VIEW')")
    @GetMapping("/{idx}")
    public ResponseEntity<ApiResponse<MyDto>> getOne(@PathVariable Long idx) throws Exception {
        return ResponseEntity.ok(ApiResponse.success(myFeatureService.getOne(idx)));
    }

    // WRITE 권한: 생성
    @PreAuthorize("@permService.hasAccess('WRITE')")
    @PostMapping
    public ResponseEntity<ApiResponse<MyDto>> create(@RequestBody MyRequest req) throws Exception {
        MyDto result = myFeatureService.create(req);
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(result));
    }

    // MODIFY 권한: 수정 (작성자 본인 or 관리자)
    @PreAuthorize("@permService.hasAccess('MODIFY', #idx)")
    @PutMapping("/{idx}")
    public ResponseEntity<ApiResponse<Void>> update(
            @PathVariable Long idx,
            @RequestBody MyRequest req) throws Exception {
        myFeatureService.update(idx, req);
        return ResponseEntity.ok(ApiResponse.success(null));
    }
}
```

**권한 레벨 (`@permService.hasAccess`):**

| 권한 | 의미 |
|---|---|
| `ACCESS` | 접근 (목록 진입) |
| `VIEW` | 상세 조회 |
| `WRITE` | 새 글 작성 |
| `MODIFY` | 수정 (본인 글 or 관리자) |
| `REMOVE` | 삭제 |
| `MANAGE` | 관리자급 조작 |

**`ApiResponse<T>` 응답 형식:**

```json
{ "code": 200, "message": "success", "data": { ... } }
{ "code": 201, "message": "created", "data": { ... } }
{ "code": 400, "message": "에러 메시지", "data": null }
```

**관련 문서:** 문서 05 (백엔드 구조), 문서 20 (API 엔드포인트), 문서 06 (인증-권한)

---

### Q13. 게시판에 커스텀 필드를 추가해야 해요

**핵심 답변:** `BoardFieldDefinition` 엔티티를 통해 게시판 마스터에 커스텀 필드를 추가합니다. 관리자 UI에서 추가하거나 API로 직접 등록합니다.

**참고 파일:**
- `mapper/cms/core/board/BoardFieldDefinitionMapper.java` — 프리셋/커스텀 필드 매핑
- `service/cms/core/board/impl/BoardMasterCacheService.java` — 필드 정의 조회 (캐시 적용)
- `service/cms/core/board/preset/PresetField.java` — 기본 제공 프리셋 필드 목록

**필드 타입 구분:**
- **프리셋 필드:** `BoardType`별로 기본 제공되는 고정 필드 (`title`, `content`, `author` 등). DB 저장 불필요.
- **커스텀 필드:** `cms_board_field_definition` 테이블에 `boardMasterIdx`로 연결하여 저장.

**API로 커스텀 필드 추가 (관리자 권한 필요):**

```
POST /back-api/board-master/{boardMasterIdx}/fields
Content-Type: application/json

{
  "fieldName": "region",
  "displayName": "지역",
  "fieldType": "TEXT",
  "isRequired": false,
  "isSearchable": true,
  "fieldOrder": 10
}
```

**필드 조회 API (프론트엔드에서 호출):**

```typescript
// 커스텀 필드만 조회
GET /back-api/board/fields
// → BoardMasterCacheService.getFieldDefinitions() 호출
// 프리셋 필드 이름과 겹치는 건 제외하고 커스텀만 반환

// 전체 필드 조회 (프리셋 + 커스텀)
GET /back-api/board/fields/all
// → BoardMasterCacheService.getAllFieldDefinitions() 호출
```

**캐시 주의:** 필드 정의는 `boardFieldDefinitions` 캐시에 저장됩니다. 필드를 추가/수정한 뒤 캐시가 갱신되지 않으면 `BoardMasterCacheService.evictAllBoardMasterCache()`를 호출해야 합니다.

```java
// 캐시 전체 무효화
@CacheEvict(
  value = {"boardMasters", "boardMaster", "boardFieldDefinitions",
           "boardFieldDefinitionsFull", "activeBoardMasters"},
  allEntries = true
)
public void evictAllBoardMasterCache() {}
```

**관련 문서:** 문서 07 (게시판-시스템), 문서 27 (DB-스키마-ERD)

---

### Q14. 특정 사이트에만 접근 가능하게 IP를 제한하고 싶어요

**핵심 답변:** 백엔드 `cms_site` 테이블의 `allow_ip` / `deny_ip` 컬럼을 설정하거나, 전역 허용 IP는 `cms.allowed-ips` 설정을 사용합니다.

**참고 파일:**
- `service/cms/core/site/impl/SiteAccessCheckerImpl.java` — 백엔드 IP 체크 로직
- `middleware/01.site-init.global.ts` — 프론트엔드 IP 차단 처리
- `resources/application-local.yml` — 전역 허용 IP 설정

**관리자 UI에서 설정:**
관리자 → 사이트 관리 → 해당 사이트 선택 → IP 설정 탭에서 `allowIp` / `denyIp` 입력.

**IP 설정 형식:**
```
# 단일 IP
1.2.3.4

# CIDR 표기
10.0.0.0/8

# 여러 개 (쉼표 또는 줄바꿈 구분)
1.2.3.4, 5.6.7.8

# 전체 차단
all
```

**동작 우선순위:**
1. `allow_ip`에 포함 → **무조건 허용**
2. `deny_ip`가 `all` → **전체 차단** (allow 제외)
3. `deny_ip`에 포함 → **차단**
4. 해당 없음 → **기본 허용**

**전역 허용 IP (`application-local.yml`):**

```yaml
cms:
  allowed-ips:
    - 49.254.140.62   # 프론트엔드 서버 IP
    - 127.0.0.1
    - 172.16.0.0/12   # Docker 내부 네트워크
    - 192.168.0.0/16
```

`cms.allowed-ips`에 등록된 IP는 모든 사이트에서 항상 허용됩니다 (프론트엔드 서버 → 백엔드 통신 경로).

**프론트엔드 쿠키 기반 차단:** SSR에서 차단된 경우 `__ipBlock=1` 쿠키가 내려져 CSR에서도 동일하게 차단이 유지됩니다.

**관련 문서:** 문서 24 (쿠키-CORS-배포환경), 문서 28 (보안-에러처리)

---

### Q15. 캐시가 갱신이 안 되는 것 같아요

**핵심 답변:** `BoardMasterCacheService`의 캐시는 **TTL이 없는 로컬 메모리 캐시**입니다. 게시판 마스터 정보를 변경한 후 `evictAllBoardMasterCache()`를 명시적으로 호출해야 갱신됩니다.

**참고 파일:** `service/cms/core/board/impl/BoardMasterCacheService.java`

**캐시 이름 목록:**

| 캐시 이름 | 대상 |
|---|---|
| `boardMasters` | 게시판 목록 (`searchBoardMasters`) |
| `boardMaster` | 게시판 단건 (`getBoardByIdx`) |
| `boardFieldDefinitions` | 커스텀 필드 정의 목록 |
| `boardFieldDefinitionsFull` | 전체 필드 정의 (프리셋 포함) |
| `activeBoardMasters` | 활성 게시판 목록 |

**캐시 무효화 전체 API 호출 (관리자):**

```
DELETE /back-api/board-master/cache
```

또는 서비스 레이어에서 직접 호출:

```java
@Autowired
private BoardMasterCacheService boardMasterCacheService;

// 게시판 수정 후 캐시 무효화
boardMasterCacheService.evictAllBoardMasterCache();
```

**Redis 캐시(권한)와 구분:** 권한 정보는 Redis에 저장됩니다. 권한 변경 시에는 `PermissionServiceImpl.invalidateMenuPermission(menuId)`가 자동으로 Redis 키를 삭제합니다.

**캐시 갱신이 안 되는 주요 원인:**

1. 게시판 마스터 수정 후 캐시 evict 누락 → `evictAllBoardMasterCache()` 호출
2. Redis가 다운된 상태에서 권한을 변경한 경우 → Redis 복구 후 권한 재저장
3. 프론트엔드에서 `cacheScope: "url+menu"` 사용 시 브라우저 메모리 캐시도 존재 → 페이지 새로고침으로 해결

**관련 문서:** 문서 29 (캐싱-세션-전략)

---

## 운영/배포 시나리오

---

### Q16. 로컬에서 로그인 되는데 서버에서 안 돼요

**핵심 답변:** JWT 토큰을 HttpOnly 쿠키로 내려주는데, 서버 환경에서 `COOKIE_SECURE=true`(HTTPS 전용)이거나 Nginx의 `X-Forwarded-*` 헤더 설정이 누락된 경우 쿠키가 전달되지 않습니다.

**참고 파일:**
- `controller/auth/AuthController.java` — 로그인 시 쿠키 설정
- `resources/application-prod.yml` — 운영 환경 설정

**체크리스트:**

**1) 쿠키 Secure 속성 확인:**

로컬은 HTTP이므로 `Secure` 쿠키가 전달되지 않습니다. 운영에서도 HTTPS가 아닌데 `Secure=true`로 설정되어 있으면 쿠키가 브라우저에서 저장되지 않습니다.

```yaml
# application-prod.yml에서 확인
jwt:
  cookie-secure: true   # HTTPS 환경에서만 true
```

**2) Nginx `X-Forwarded-For` 헤더 설정:**

백엔드의 IP 체크(`SiteAccessCheckerImpl`)는 `X-Forwarded-For` 헤더로 실제 클라이언트 IP를 확인합니다. Nginx에서 이 헤더를 전달하지 않으면 IP 차단 정책이 잘못 적용됩니다.

```nginx
# Nginx 설정 필수 항목
location /back-api/ {
    proxy_pass http://backend:8080/;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $host;
}
```

**3) CORS 설정 확인:**

프론트엔드 도메인이 백엔드의 허용 Origin 목록에 없으면 쿠키를 포함한 요청이 차단됩니다.

```yaml
# application-prod.yml
cors:
  allowed-origins:
    - https://www.yourdomain.com
    - https://jhhalf.mx.co.kr
```

**4) 로그인 API 경로 IP 체크 예외:**

`/back-api/auth/*` 경로는 `JwtAuthenticationFilter`에서 검증을 제외하지만, IP 차단 정책은 여전히 적용될 수 있습니다. `cms.allowed-ips`에 서버 IP를 추가하세요.

**관련 문서:** 문서 24 (쿠키-CORS-배포환경), 문서 04 (배포 가이드)

---

### Q17. 서버 배포 후 CSS가 안 바뀌어요

**핵심 답변:** CSS 파일을 배포한 후 `css-version.json`의 버전 값을 갱신해야 합니다. 이 값이 변경되어야 `useVersionedCss`가 새로운 쿼리스트링(`?v=새값`)을 만들어 브라우저 캐시를 무효화합니다.

**참고 파일:**
- `server/utils/cssVersion.ts` — 버전 파일 읽기 (10초 메모리 캐시)
- `composables/useVersionedCss.ts` — CSS URL에 버전 쿼리스트링 부착
- `server/middleware/css-version.ts` — SSR 요청마다 버전을 이벤트 컨텍스트에 주입

**`css-version.json` 위치:** `{shared-root}/public/css-version.json`

```json
{
  "version": "20241215143022"
}
```

**CSS 배포 후 버전 갱신 방법:**

```bash
# 배포 스크립트에서 타임스탬프로 버전 갱신
echo "{\"version\": \"$(date +%Y%m%d%H%M%S)\"}" > /data/shared/public/css-version.json
```

**동작 흐름:**

```
1. CSS 파일 배포 (/data/shared/public/style/...)
2. css-version.json 버전 값 갱신
3. 다음 SSR 요청 시 server/utils/cssVersion.ts가 JSON 읽음 (10초 캐시)
4. useVersionedCss가 CSS URL에 ?v=새버전 붙임
5. 브라우저가 새 URL로 CSS 재요청 → 캐시 무효화
```

**`useVersionedCss` 사용 예** (`layouts/www-main.vue`):

```typescript
useHead({
  link: useVersionedCss([
    "/public/style/www/common/base.css",
    "/public/style/www/halftour/layout.css",
  ]),
});
// 출력: <link rel="stylesheet" href="/public/style/www/common/base.css?v=20241215143022">
```

**주의:** `server/utils/cssVersion.ts`는 10초 메모리 캐시를 가지고 있으므로, 버전 파일 갱신 후 최대 10초 뒤에 SSR에서 새 버전이 반영됩니다.

**관련 문서:** 문서 16 (CSS-실시간편집), 문서 30 (플러그인-서버미들웨어)

---

### Q18. Redis가 죽으면 어떻게 되나요?

**핵심 답변:** Redis 장애 시 세션 조회가 불가능해지고, 권한은 매 요청마다 DB에서 직접 조회합니다. 토큰 자체(JWT)는 유효하므로 요청은 처리되지만 세션 기반 기능(만료 추적 등)은 동작하지 않습니다.

**참고 파일:**
- `service/auth/impl/SessionManagerImpl.java` — Redis 장애 감지 및 Degraded 모드
- `service/auth/impl/PermissionServiceImpl.java` — Redis 권한 캐시 + DB 폴백

**Redis 장애 시 동작:**

**세션 관리:**

```java
// SessionManagerImpl.getSession()
@Override
public Optional<SessionData> getSession(String sid) {
    if (!redisHealthChecker.isCachedRedisHealthy()) {
        // Redis 장애 시 세션 조회 생략 → Optional.empty() 반환
        return Optional.empty();
    }
    // ...
}
```

Redis가 죽으면 세션 조회가 빈 값을 반환합니다. JWT 토큰이 유효 기간 내라면 `fallback-token-validity`(기본 3600초) 동안 토큰 자체의 클레임으로 사용자를 인증합니다.

**권한 조회:**

Redis에 권한 캐시가 없으면 `PermissionResolverService`가 DB(`cms_permission` 테이블)에서 직접 조회합니다. Redis 장애 중에는 모든 권한 확인 요청이 DB 쿼리를 발생시키므로 DB 부하가 증가합니다.

**로그인 시:**

```java
// AuthServiceImpl.login()
boolean isRedisDown = !sessionManager.isRedisHealthy();
// isRedisDown = true이면 JWT 유효기간을 fallback-token-validity로 연장
String accessToken = jwtTokenProvider.createToken(userId, claims, isRedisDown);
```

**`application.yml` 관련 설정:**

```yaml
jwt:
  access-token-validity: 900         # 정상 시 15분
  fallback-token-validity: 3600      # Redis 장애 시 1시간
  refresh-token-validity: 86400      # Refresh 토큰 24시간
  session-ttl-seconds: 3600          # Redis 세션 TTL
```

**Redis 복구 후:** `RedisHealthChecker`가 헬스 상태를 자동으로 갱신합니다. 이후 새 로그인 요청부터 정상 세션이 생성됩니다. 장애 중 로그인한 사용자는 다시 로그인하거나 토큰이 만료될 때까지 fallback 모드로 동작합니다.

**영향 없는 기능:** 게시판 목록/상세 조회, 컨텐츠 조회, 공개 API 등 권한 체크가 없는 엔드포인트.

**관련 문서:** 문서 29 (캐싱-세션-전략), 문서 06 (인증-권한)

---

## 빠른 참조

| 상황 | 파일/방법 |
|---|---|
| 메인 게시판 섹션 추가 | `layouts/www-main.vue` + `<WidgetList :menu-id="N">` |
| GNB 4뎁스 추가 | `components/default/main/GnbMenu.vue` + CSS |
| 새 사이트 레이아웃 | `layouts/{site}-main.vue` 생성 (자동 감지) |
| 특정 메뉴 게시판 디자인 변경 | `components/theme/.../overrides/{menuId}.vue` 생성 |
| 새 배너 | 관리자에서 팝업 생성 → `<VisualBanner :popup-id="N">` |
| slug 안 타는 페이지 | `pages/{site}/page.vue` 직접 생성 |
| 로그인 상태 확인 | `useUserStore().isGuest` / `isAdmin` |
| 새 composable | `composables/api/render/use기능명.ts` |
| 새 API 엔드포인트 | Controller + `@PreAuthorize("@permService.hasAccess('ACCESS')")` + `ApiResponse<T>` |
| 게시판 커스텀 필드 | 관리자 UI 또는 `BoardFieldDefinition` API |
| IP 제한 | 관리자 사이트 설정 `allowIp`/`denyIp` |
| 캐시 강제 갱신 | `evictAllBoardMasterCache()` 호출 |
| CSS 배포 후 캐시 | `css-version.json` 버전 값 갱신 |
| 서버 로그인 안 됨 | `COOKIE_SECURE`, Nginx `X-Forwarded-For` 헤더 확인 |
| Redis 장애 | Fallback TTL 동작, DB 직접 권한 조회 |
