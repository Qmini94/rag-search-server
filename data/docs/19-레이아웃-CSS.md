# 레이아웃 & CSS 구조

퍼블리셔/디자이너를 위한 Q-CMS 레이아웃 시스템과 CSS 아키텍처 가이드.

## 1. 레이아웃 시스템

### 레이아웃 파일 목록

```
layouts/
├── www-main.vue        사용자 사이트 메인 페이지
├── www-sub.vue         사용자 사이트 서브 페이지
├── default-main.vue    기본(default) 메인 페이지
├── default-sub.vue     기본(default) 서브 페이지
└── business-sub.vue    관리자 사이트 (main/sub 구분 없이 단일)
```

### 레이아웃 자동 선택 로직

미들웨어 `01b.layout-setting.global.ts`가 URL path를 분석하여 레이아웃을 자동 결정한다.

#### main vs sub 판별 규칙

```
/site         → main 레이아웃  (사이트 루트)
/site/foo/bar → sub 레이아웃   (서브 페이지)
/             → www-main       (루트 접근)
```

#### 레이아웃 이름 조합

```
{sitePrefix}-{main|sub}

예시:
  www 사이트 루트     → www-main
  www 서브 페이지     → www-sub
  business 모든 페이지 → business-sub  (main/sub 구분 없음)
```

- `sitePrefix`는 사이트의 `siteName`을 slugify한 값이다.
- business 사이트는 예외로, main/sub 구분 없이 항상 `business-sub` 레이아웃을 사용한다.

#### fallback 순서

레이아웃 파일이 존재하지 않는 경우 안전하게 폴백한다.

```
main 레이아웃 fallback:
  {prefix}-main → default-main → default

sub 레이아웃 fallback:
  {prefix}-sub → default-sub → default → (빈 문자열)
```

존재 여부는 `import.meta.glob("~/layouts/*.vue")`로 빌드 시점에 수집한 파일 목록(`KNOWN_LAYOUTS`)으로 검사한다.

### 레이아웃별 HTML 구조

#### www-main.vue (사용자 메인)

```html
<div id="skip_nav">...</div>
<div id="wrap" class="main">
  <WwwMainHeader />
  <WwwCommonQuickArea />
  <section id="container">
    <!-- 메인 비주얼, 가이드, 투어, 커뮤니티 등 -->
  </section>
  <WwwMainFooter />
  <WwwCommonTopButton />
</div>
```

#### www-sub.vue (사용자 서브)

```html
<div id="skip_nav">...</div>
<div id="wrap" class="page">
  <WwwMainHeader />
  <WwwCommonQuickArea />
  <section id="container">
    <div class="inner">
      <WwwSubHeader />
      <div class="sub_nav">
        <WwwSubSidebar />
        <WwwSubContentBox />
        <h3 class="tit">{{ breadcrumbTitle }}</h3>
      </div>
      <div class="sub_in">
        <div id="content">
          <slot />
        </div>
      </div>
    </div>
  </section>
  <WwwMainFooter />
  <WwwCommonTopButton />
</div>
```

#### default-sub.vue (기본 서브)

```html
<div id="wrap" class="group">
  <defaultMainHeader />
  <section id="container" class="clear">
    <defaultSubHeader />
    <div class="clear cont_inner">
      <div id="left"><defaultSubSidebar /></div>
      <div id="right">
        <div id="target_cont" class="path"><defaultSubBreadcrumb /></div>
        <div id="content_box">
          <h3>{{ breadcrumbTitle }}</h3>
          <span class="content_line"></span>
          <div id="content"><NuxtPage /></div>
        </div>
      </div>
    </div>
  </section>
  <defaultMainFooter />
</div>
```

#### business-sub.vue (관리자)

```html
<div class="h-screen flex flex-col bg-white dark:bg-gray-900 ...">
  <BusinessHeader />
  <div class="flex flex-1 pt-16 overflow-hidden">
    <BusinessSidebar />
    <main class="flex-1 overflow-auto p-6 ...">
      <div class="max-w-screen-2xl mx-auto px-4 sm:px-6 space-y-6">
        <BusinessBreadcrumb />
        <slot />
      </div>
    </main>
  </div>
</div>
```

## 2. CSS 아키텍처

### 핵심 원칙: 사이트별 CSS 분리

| 구분 | 사용자 사이트 (www, default) | 관리자 사이트 (business) |
|---|---|---|
| CSS 방식 | 전통 CSS 클래스 | Tailwind CSS |
| UI 라이브러리 | 자체 CSS | Element Plus + Tailwind |
| 다크 모드 | 미지원 (light 강제) | 지원 (dark: 접두사) |

**왜 분리했는가?** 사용자 사이트는 퍼블리싱된 HTML/CSS를 그대로 사용해야 하고, Tailwind의 reset/utility가 기존 퍼블리싱 CSS와 충돌할 수 있기 때문이다. 관리자 사이트는 새로 구축하므로 Tailwind를 자유롭게 사용한다.

### nuxt.config.ts 글로벌 CSS

```typescript
css: [
  "@/assets/css/fonts/pretendardGov.css",   // PretendardGOV 웹폰트
  "~/assets/css/common/common.css",          // 공통 CSS (트랜지션, 사이드바 등)
]
```

이 두 파일은 모든 사이트에 공통으로 적용된다.

### 사이트별 CSS 로딩

각 레이아웃 파일이 `useVersionedCss()`를 통해 사이트 전용 CSS를 `<head>`에 주입한다.

#### www-main.vue CSS 로딩 순서

```
1. /public/style/www/plugin/swiper-8.4.7.min.css   (슬라이더 플러그인)
2. /public/style/www/common/base.css                (기본 리셋/타이포)
3. /public/style/www/module/component.css            (공통 컴포넌트)
4. /public/style/www/module/codingmap.css             (코딩맵)
5. /public/style/www/halftour/layout.css             (레이아웃)
6. /public/style/www/halftour/main.css               (메인 전용)
```

#### www-sub.vue CSS 로딩 순서

```
1. /public/style/www/common/base.css
2. /public/style/www/module/component.css
3. /public/style/www/module/codingmap.css
4. /public/style/www/halftour/layout.css
5. /public/style/www/halftour/sub.css                (서브 전용)
```

#### default-main.vue CSS 로딩 순서

```
1. /public/style/default/common/base.css
2. /public/style/default/common/component.css
3. /public/style/default/yumcorp/layout.css
4. /public/style/default/yumcorp/main.css
```

#### default-sub.vue CSS 로딩 순서

```
1. /public/style/default/common/base.css
2. /public/style/default/common/component.css
3. /public/style/default/yumcorp/layout.css
4. /public/style/default/yumcorp/sub.css
5. /public/style/default/yumcorp/sub_content.css
```

### CSS 파일 디렉토리 구조

```
{shared-root}/public/style/
├── www/                         사용자 사이트 (www)
│   ├── plugin/                  외부 플러그인 CSS
│   │   └── swiper-8.4.7.min.css
│   ├── common/                  공통 베이스
│   │   └── base.css
│   ├── module/                  공통 모듈
│   │   ├── component.css
│   │   └── codingmap.css
│   └── halftour/                사이트별 스타일
│       ├── layout.css
│       ├── main.css
│       └── sub.css
└── default/                     기본 사이트
    ├── common/
    │   ├── base.css
    │   └── component.css
    └── yumcorp/
        ├── layout.css
        ├── main.css
        ├── sub.css
        └── sub_content.css
```

이 CSS 파일들은 Nginx에서 `/public/` 경로로 정적 서빙된다.

## 3. 사용자 사이트 CSS 클래스 체계

사용자 사이트(www, default)에서 사용하는 전통 CSS 클래스 규칙.

### 버튼 시스템

```
기본 구조: c_btn_base + 용도별 클래스

<a class="c_btn_base">기본 버튼</a>
<a class="c_btn_base btn_event">이벤트 버튼</a>
<a class="c_btn_base btn_map">지도 버튼</a>
```

HTML 퍼블리싱에서 정의된 btn_base 계열 클래스를 사용한다.

### 입력 필드

```
input_base 계열 클래스로 통일
```

### 레이아웃 클래스

```
.write_box     폼 작성 영역 컨테이너
.w_tit         폼 라벨(제목) 영역
.w_cnt         폼 입력(콘텐츠) 영역
```

### 테이블/리스트

```
.table_list    테이블 형태 리스트
```

### 아이콘

```
.ico_*         아이콘 공통 접두사
.ico_step      단계 아이콘
.ico_guide_01  가이드 아이콘 (번호별)
.ico_mascoat   마스코트 아이콘
.ico_mascoat_01 마스코트 변형

용도 수식어:
  .main        메인 페이지용
  .icon        아이콘 전용

출처 체계: krds / itid 디자인 시스템 기반
```

### 반응형 유틸리티

```
.web_only      PC에서만 표시 (모바일 숨김)
.mob_only      모바일에서만 표시 (PC 숨김)
.sr_only       스크린리더 전용 (시각적 숨김)
```

### 상태 클래스

```
.on            활성 상태
.notice        공지 강조
.badge_*       배지 계열
```

### 주요 ID 구조

```
#skip_nav      스킵 네비게이션
#wrap          최상위 래퍼 (.main = 메인, .page = 서브)
#container     콘텐츠 컨테이너
#content       본문 콘텐츠 영역
#left          좌측 사이드바 (default-sub)
#right         우측 본문 (default-sub)
#content_box   콘텐츠 박스 (default-sub)
```

## 4. 관리자 사이트 CSS

### 기술 스택

- **Tailwind CSS**: 유틸리티 클래스 기반 레이아웃/스타일링
- **Element Plus**: UI 컴포넌트 라이브러리 (테이블, 폼, 다이얼로그 등)

### Tailwind 사용 예시 (business-sub.vue)

```html
<div class="h-screen flex flex-col bg-white dark:bg-gray-900">
<main class="flex-1 overflow-auto p-6 bg-gray-50 dark:bg-gray-900">
<div class="max-w-screen-2xl mx-auto px-4 sm:px-6 space-y-6">
```

### 공통 CSS (common.css)

`assets/css/common/common.css`에는 관리자 사이드바 스타일이 정의되어 있다.

```css
.sidebar-container { ... }
.sidebar-container .primary-menu { ... }
.sidebar-container .primary-menu .menu-item { ... }
.sidebar-container .primary-menu .menu-item.active { ... }
.sidebar-container .secondary-menu { ... }
```

트랜지션 애니메이션도 이 파일에 정의되어 있다.

```css
.slide-left-enter-active, .slide-left-leave-active { ... }
.expand-enter-active, .expand-leave-active { ... }
```

### 왜 분리했는가

사용자 사이트(www)는 퍼블리셔가 만든 완성된 HTML/CSS를 사용하므로, Tailwind의 기본 리셋(preflight)이 기존 스타일을 깨뜨릴 수 있다. 관리자 사이트(business)는 자체 구축이므로 Tailwind를 전면 적용하여 빠르게 개발한다.

## 5. 색상 모드 (다크/라이트)

### 설정 (nuxt.config.ts)

```typescript
colorMode: {
  classSuffix: "",        // 접미사 없음 → html 태그에 "dark" 클래스 직접 적용
  preference: "light",    // 기본값 light
  fallback: "light",      // 시스템 감지 실패 시 light
  storageKey: "nuxt-color-mode",  // localStorage 키
}
```

### 동작 방식

`plugins/color-mode-www.client.ts` 플러그인이 레이아웃에 따라 색상 모드를 제어한다.

```typescript
// business 레이아웃만 다크모드 허용, 나머지는 light 강제
watch(
  () => route.meta.layout,
  (layout) => {
    if (!layout?.startsWith("business")) {
      colorMode.preference = "light";
    }
  },
  { immediate: true },
);
```

- **business 사이트**: 사용자가 다크/라이트 모드를 선택할 수 있다.
- **그 외 사이트**: 항상 light 모드가 강제된다.

추가로, default-main.vue와 default-sub.vue는 `useHead({ htmlAttrs: { "data-color-mode-forced": "light" } })`를 설정하여 HTML 속성으로도 light를 명시한다.

### CSS에서 다크 모드 적용

Tailwind의 `dark:` 접두사를 사용한다 (`classSuffix: ""`이므로 `html.dark` 선택자).

```css
/* business-sub.vue 내부 <style> */
html.dark {
  background-color: #111827;
  --el-bg-color: #1f2937;
  --el-text-color-primary: #f3f4f6;
  --el-border-color: #374151;
  /* ... Element Plus CSS 변수 오버라이드 */
}
```

## 6. CSS 실시간 편집

### 개요

관리자 UI(business 사이트)에서 CssEditor를 통해 `/public/style/` 아래의 CSS 파일을 실시간으로 편집할 수 있다. 자세한 API 및 잠금 메커니즘은 `16-CSS-실시간편집.md` 참조.

### useVersionedCss composable

CSS 파일에 캐시 버스팅 쿼리스트링을 붙여주는 핵심 유틸이다.

```typescript
export function useVersionedCss(paths: string[]) {
  const config = useRuntimeConfig();
  const cssVersion = useState("cssVersion", () => config.public.cssVersion);

  // SSR: 서버 미들웨어가 주입한 동적 버전 사용
  if (import.meta.server) {
    const nuxtApp = useNuxtApp();
    const dynamicVersion = nuxtApp.ssrContext?.event?.context?.cssVersion;
    if (dynamicVersion && dynamicVersion !== "0") {
      cssVersion.value = dynamicVersion;
    }
  }

  return paths.map((href) => ({
    key: href,
    rel: "stylesheet",
    href: `${base}${href}?v=${cssVersion.value}`,
  }));
}
```

### 캐시 버스팅 메커니즘

```
1. 관리자가 CssEditor에서 CSS 저장
2. 백엔드가 css-version.json 업데이트 (타임스탬프 버전)
3. 다음 SSR 요청 시 서버 미들웨어가 css-version.json 읽음
4. useVersionedCss가 ?v={새버전} 쿼리스트링 생성
5. 브라우저가 새 URL로 CSS 재요청 → 캐시 무효화
```

빌드 시점 기본 버전은 nuxt.config.ts에서 생성한다.

```typescript
// nuxt.config.ts
cssVersion: (() => {
  const now = new Date();
  return `${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}${pad(now.getHours())}${pad(now.getMinutes())}`;
})(),
```

## 7. 새 사이트용 레이아웃 만들기

### 절차

1. **레이아웃 파일 생성**

```
layouts/{site}-main.vue    메인 페이지 레이아웃
layouts/{site}-sub.vue     서브 페이지 레이아웃
```

2. **기존 레이아웃 복사**

사용자 사이트라면 `www-main.vue` / `www-sub.vue`를 복사하여 시작한다.

3. **CSS 파일 준비**

```
{shared-root}/public/style/{site}/
├── common/
│   └── base.css
├── module/
│   └── component.css
└── {site}/
    ├── layout.css
    ├── main.css
    └── sub.css
```

4. **useVersionedCss 경로 수정**

복사한 레이아웃 파일 내 `useVersionedCss()` 호출에서 CSS 경로를 새 사이트에 맞게 변경한다.

```typescript
useHead({
  link: useVersionedCss([
    "/public/style/{site}/common/base.css",
    "/public/style/{site}/module/component.css",
    "/public/style/{site}/{site}/layout.css",
    "/public/style/{site}/{site}/main.css",   // main 레이아웃
    // 또는
    "/public/style/{site}/{site}/sub.css",     // sub 레이아웃
  ]),
});
```

5. **헤더/푸터 컴포넌트 생성**

레이아웃 내에서 사용하는 Header, Footer, Sidebar 등의 컴포넌트를 새로 만들거나 기존 것을 재사용한다.

6. **자동 인식**

`01b.layout-setting.global.ts` 미들웨어는 `import.meta.glob("~/layouts/*.vue")`로 파일을 자동 수집하므로, 파일을 추가하면 미들웨어 수정 없이 자동으로 인식된다.

### 주의사항

- 레이아웃 파일명은 반드시 `{site}-main.vue` 또는 `{site}-sub.vue` 형식을 따른다.
- business 사이트가 아닌 경우 `useHead({ htmlAttrs: { "data-color-mode-forced": "light" } })`를 설정하여 다크모드를 비활성화한다.
- 웹 접근성을 위해 `#skip_nav`(스킵 네비게이션)을 포함한다.
- `useLegacyGnbJqShim()`은 기존 jQuery 기반 GNB 호환 shim이므로, 레거시 헤더를 사용하는 경우 `onMounted`에서 호출한다.

## 8. 폰트

### PretendardGOV

`assets/css/fonts/pretendardGov.css`에 정의된 시스템 기본 폰트.

```
font-family: 'PretendardGOV'
font-weight: 100 ~ 900 (9단계)
format: woff2, woff
font-display: swap (로딩 중 시스템 폰트 대체 표시)
```

폰트 파일은 `/fonts/pretendard-gov/` 경로에서 서빙된다.
