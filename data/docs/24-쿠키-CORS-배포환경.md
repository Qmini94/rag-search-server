# 쿠키 · CORS · 배포환경

## 1. 쿠키 정책

### 1-1. SecurityConstants.java 상수 전체

`kr.co.itid.cms.constant.SecurityConstants`

| 상수 | 값 | 설명 |
|---|---|---|
| `SAME_SITE_STRICT` | `"Strict"` | 타 도메인으로 쿠키 전송 불가 |
| `SAME_SITE_LAX` | `"Lax"` | GET 요청에 한해 타 도메인 전송 허용 (실제 사용값) |
| `SAME_SITE_NONE` | `"None"` | 타 도메인 전송 허용, Secure 필수 (미사용) |
| `HTTP_ONLY` | `true` | 클라이언트 스크립트 접근 불가 기본값 |
| `SECURE` | `Boolean.parseBoolean(System.getenv().getOrDefault("COOKIE_SECURE", "true"))` | 환경변수 `COOKIE_SECURE`로 제어, **기본값 true** |
| `ACCESS_TOKEN_COOKIE_NAME` | `"accessToken"` | 액세스 토큰 쿠키 이름 |
| `REFRESH_TOKEN_COOKIE_NAME` | `"refreshToken"` | 리프레시 토큰 쿠키 이름 |
| `SESSION_EXPIRES_COOKIE_NAME` | `"sessionExpires"` | 세션 만료 epoch 쿠키 이름 |
| `X_SESSION_EXPIRES_HEADER` | `"X-Session-Expires"` | 세션 만료 응답 헤더 이름 |
| `COOKIE_PATH` | `"/"` | 모든 경로에서 쿠키 유효 |
| `COOKIE_DOMAIN` | `null` | 도메인 미설정 → host-only 쿠키 |

### 1-2. AuthCookieUtil.java — 쿠키 3종 생성/삭제 로직

`kr.co.itid.cms.util.AuthCookieUtil`

모든 쿠키는 내부 `baseCookie()` 헬퍼를 통해 생성된다.

```java
// baseCookie(): 공통 속성 적용
ResponseCookie.from(name, value)
    .path(COOKIE_PATH)          // "/"
    .secure(SECURE)             // 환경변수 COOKIE_SECURE
    .sameSite(SAME_SITE_LAX);   // "Lax"
// domain이 null이면 .domain() 호출 생략 → host-only
```

**setAccessToken**: `httpOnly(true)`, `maxAge(ttl)` (ttl null이면 세션 쿠키)

**setRefreshToken**: `httpOnly(true)`, `maxAge(ttl)` (ttl null이면 세션 쿠키)

**setSessionExpires**: `httpOnly(false)`, `maxAge(남은 초)` + `X-Session-Expires` 헤더도 함께 설정

**clearAll** (로그아웃): 3종 쿠키 모두 `maxAge(Duration.ZERO)`로 삭제 + `X-Session-Expires: 0` 헤더

### 1-3. 쿠키별 속성 비교표

| 쿠키 이름 | HttpOnly | Secure | SameSite | maxAge | 용도 |
|---|---|---|---|---|---|
| `accessToken` | **true** | 환경변수 | Lax | `accessTokenValidity`초 (기본 900초) | JWT 액세스 토큰 |
| `refreshToken` | **true** | 환경변수 | Lax | `refreshTokenValidity`초 (기본 86400초) | JWT 리프레시 토큰 |
| `sessionExpires` | **false** | 환경변수 | Lax | Redis 세션 남은 TTL (기본 3600초) | 프론트 세션 만료 타이머용 |

> `jwt.*` 기본값은 `application.yml`에서 확인:
> - `access-token-validity: 900` (15분)
> - `refresh-token-validity: 86400` (24시간)
> - `session-ttl-seconds: 3600` (1시간, Redis 슬라이딩 TTL)
> - `fallback-token-validity: 3600` (Redis 장애 시 ACCESS 연장 TTL)

### 1-4. sessionExpires만 HttpOnly=false인 이유

`sessionExpires` 쿠키는 Redis 세션의 만료 시각(Unix epoch 초)을 저장한다. 프론트엔드(`safeFetch.ts`)가 이 값을 `document.cookie`로 직접 읽어 자동 로그아웃 타이머(`scheduleAutoLogoutFrom`)를 설정해야 하므로 `httpOnly(false)`로 설정한다.

```typescript
// utils/safeFetch.ts — 폴백 로직
const v = getCookie("sessionExpires");   // JS에서 document.cookie 직접 읽음
if (v && /^\d+$/.test(v)) {
    scheduleAutoLogoutFrom(Number(v));
}
```

우선순위: `X-Session-Expires` 응답 헤더 → `sessionExpires` 쿠키(폴백).

`accessToken` / `refreshToken`은 JS에서 읽을 필요가 없으므로 `httpOnly(true)`로 XSS 탈취를 방지한다.

### 1-5. COOKIE_DOMAIN=null — host-only 쿠키 의미

`COOKIE_DOMAIN = null`이면 `baseCookie()`에서 `.domain()` 호출 자체를 생략한다.

```java
if (domain != null && !domain.isEmpty()) {
    b.domain(domain);   // null이면 이 줄 실행 안 됨
}
```

브라우저는 `Domain` 속성이 없는 쿠키를 **host-only 쿠키**로 처리한다. 즉, 쿠키를 발급한 정확한 호스트(`example.com`)에서만 전송되며, 서브도메인(`api.example.com`)에는 전송되지 않는다. 도메인을 명시하면(`domain=example.com`) 서브도메인 포함 전체에 전송된다.

운영 환경에서 서브도메인을 공유해야 할 경우 `COOKIE_DOMAIN=itid.co.kr`처럼 환경변수로 주입하거나 상수 주석(`예: "itid.co.kr"`)을 수정한다.

---

## 2. 개발 vs 운영 로그인 안 되는 원인

### 2-1. COOKIE_SECURE 기본값 문제

```java
// SecurityConstants.java
public static final boolean SECURE = Boolean.parseBoolean(
    System.getenv().getOrDefault("COOKIE_SECURE", "true"));
```

`COOKIE_SECURE` 환경변수를 설정하지 않으면 기본값이 `true`다. `Secure` 속성이 붙은 쿠키는 **HTTPS 연결에서만 브라우저가 서버로 전송**한다.

- **개발 환경(HTTP)**: `COOKIE_SECURE` 환경변수를 `false`로 설정하지 않으면 쿠키가 응답에 Set-Cookie로 내려와도 브라우저가 이후 요청 시 전송하지 않아 로그인이 유지되지 않는다.
- **운영 환경(HTTPS)**: `COOKIE_SECURE=true`(기본) 그대로 사용.

```bash
# 개발 환경 (docker-compose 또는 IDE 실행 시)
COOKIE_SECURE=false
```

### 2-2. HTTPS + Secure 쿠키 필수 조건 정리

| 환경 | 프로토콜 | COOKIE_SECURE 설정 | 쿠키 전송 여부 |
|---|---|---|---|
| 로컬 개발 | HTTP | `false` | 정상 전송 |
| 로컬 개발 | HTTP | `true` (기본) | **전송 안 됨 → 로그인 실패** |
| 운영 서버 | HTTPS | `true` (기본) | 정상 전송 |
| 운영 서버 | HTTP (잘못된 설정) | `true` | **전송 안 됨** |

### 2-3. Nginx 프록시 헤더 누락 시 문제

Nginx 리버스 프록시 뒤에 배포할 경우 다음 헤더가 백엔드로 전달되어야 한다.

```nginx
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Host              $host;
```

- `X-Forwarded-Proto` 누락: 백엔드가 실제 요청이 HTTPS인지 HTTP인지 판단 불가. Spring Security의 HSTS, CSRF, 리다이렉트 로직에 영향.
- `X-Forwarded-For` 누락: IP 기반 접근 제어(`cms.allowed-ips`) 오작동. 모든 요청이 Nginx 내부 IP로 보여 차단되거나 허용될 수 있다.
- Spring Boot 설정에서 프록시 신뢰를 활성화해야 헤더가 적용된다(`server.forward-headers-strategy: native` 또는 `framework`).

### 2-4. CORS origin 불일치 시 쿠키 전송 실패

프론트엔드가 `withCredentials: true`(쿠키 포함 요청)로 백엔드를 호출할 때, 백엔드 CORS 응답에 `Access-Control-Allow-Origin`이 요청 Origin과 정확히 일치해야 한다. `*`(와일드카드)는 `credentials: true`와 함께 사용 불가.

현재 백엔드는 `allowedOriginPatterns("*")`을 사용하므로 실제 Origin을 패턴 매칭해 동적으로 반환한다. 이 설정이 잘못되거나 CORS 필터 적용 순서가 틀리면 브라우저가 preflight(OPTIONS)를 실패 처리해 쿠키가 포함된 본 요청 자체를 보내지 않는다.

---

## 3. CORS 설정

`kr.co.itid.cms.config.security.JwtSecurityConfig`

### 3-1. corsConfigurationSource()

```java
CorsConfiguration config = new CorsConfiguration();
config.setAllowedOriginPatterns(List.of("*"));                          // 모든 Origin 패턴 허용
config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
config.setAllowedHeaders(List.of("*"));                                 // 모든 요청 헤더 허용
config.setAllowCredentials(true);                                       // 쿠키/인증 헤더 포함 허용
config.setMaxAge(3600L);                                                // preflight 캐시 1시간

// 모든 경로에 적용
source.registerCorsConfiguration("/**", config);
```

`allowedOriginPatterns("*")` + `allowCredentials(true)` 조합은 Spring이 내부적으로 요청 `Origin` 헤더 값을 그대로 `Access-Control-Allow-Origin`으로 반환하기 때문에 와일드카드 제한 없이 자격 증명 포함 요청이 허용된다.

### 3-2. CSRF 설정

```java
.csrf(csrf -> csrf
    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
    .ignoringRequestMatchers(
        request -> request.getRequestURI().equals("/back-api/auth/login"))
)
```

- `CookieCsrfTokenRepository.withHttpOnlyFalse()`: CSRF 토큰을 `XSRF-TOKEN` 쿠키(HttpOnly=false)로 발급. JS에서 읽어 `X-XSRF-TOKEN` 헤더로 전송.
- 프론트엔드(`safeFetch.ts`)는 매 요청 전 `getCookie("XSRF-TOKEN")`으로 읽어 `X-XSRF-TOKEN` 헤더에 포함한다.
- **로그인(`/back-api/auth/login`)만 CSRF 예외**: 로그인 시점에는 아직 CSRF 토큰을 보유하지 않으므로 예외 처리.
- 로그아웃(`/back-api/auth/logout`)은 CSRF 보호 대상이므로 `X-XSRF-TOKEN` 헤더 포함 필요.

---

## 4. 인증 흐름 요약

### 4-1. 로그인 (`POST /back-api/auth/login`)

```
1. AuthServiceImpl.login()
   ├─ 사용자 조회 + 비밀번호 검증
   ├─ SessionManagerImpl.createSession() → Redis에 SessionData 저장 (TTL: sessionTtlSeconds=3600초)
   ├─ JwtTokenProvider.createToken()     → ACCESS JWT 발급
   │   └─ Redis 장애 시(isRedisDown=true) fallbackTokenValidity(3600초) 적용
   └─ JwtTokenProvider.createRefreshToken() → REFRESH JWT 발급

2. AuthController.login()
   ├─ AuthCookieUtil.setAccessToken(response, token, Duration.ofSeconds(900))
   ├─ AuthCookieUtil.setRefreshToken(response, token, Duration.ofSeconds(86400))
   └─ AuthCookieUtil.setSessionExpires(response, now + 3600)
       └─ sessionExpires 쿠키 + X-Session-Expires 헤더 동시 설정
```

### 4-2. 로그아웃 (`DELETE /back-api/auth/logout`)

```
1. AuthServiceImpl.logout()
   └─ SessionManagerImpl.deleteSession(sid) → Redis에서 세션 삭제

2. AuthController.logout()
   └─ AuthCookieUtil.clearAll(response)
       ├─ accessToken      → maxAge=0 (삭제)
       ├─ refreshToken     → maxAge=0 (삭제)
       ├─ sessionExpires   → maxAge=0 (삭제)
       └─ X-Session-Expires: 0 헤더
```

### 4-3. Redis 장애 시 fallback TTL

```java
// JwtTokenProvider.createToken()
boolean isRedisDown = !sessionManager.isRedisHealthy();
long validity = isRedisDown
    ? props.getFallbackTokenValidity()   // 3600초 (Redis 장애 fallback)
    : props.getAccessTokenValidity();    // 900초 (정상)
```

Redis 장애 시:
- `isRedisHealthy()` → `false`
- ACCESS 토큰 유효기간을 `fallbackTokenValidity`(3600초)로 연장해 Redis 없이도 일정 시간 인증 유지
- `getSession()` / `touchSession()`은 `Optional.empty()` / 조용히 패스 처리로 요청 흐름을 막지 않음

---

## 5. 개발 → 운영 전환 체크리스트

### 환경변수

- [ ] `COOKIE_SECURE=true` 설정 (또는 생략, 기본값이 true)
- [ ] `SPRING_PROFILES_ACTIVE=prod` 설정
- [ ] `JWT_SECRET` 운영용 강력한 키(32자 이상)로 교체
- [ ] `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` 운영 DB로 설정
- [ ] `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` 운영 Redis로 설정
- [ ] `DOMAIN_URL` 실제 운영 도메인으로 설정
- [ ] `CMS_ALLOWED_IPS` 허용 IP 목록 운영 환경에 맞게 설정

### HTTPS / Nginx

- [ ] 운영 서버 HTTPS 인증서 설치 및 적용
- [ ] Nginx에 `proxy_set_header X-Forwarded-Proto $scheme;` 설정
- [ ] Nginx에 `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;` 설정
- [ ] Nginx에 `proxy_set_header Host $host;` 설정
- [ ] Spring Boot `server.forward-headers-strategy: native` (또는 `framework`) 설정 확인

### 쿠키 / CORS

- [ ] 운영 도메인이 단일 호스트면 `COOKIE_DOMAIN=null`(기본) 유지, 서브도메인 공유 필요 시 `COOKIE_DOMAIN=example.com` 설정
- [ ] 프론트엔드 `apiBase` URL이 운영 백엔드를 정확히 가리키는지 확인
- [ ] 브라우저 DevTools → Application → Cookies에서 `accessToken`, `refreshToken`, `sessionExpires`, `XSRF-TOKEN` 쿠키 존재 여부 확인
- [ ] 로그인 후 `Secure` 속성 표시 확인 (HTTPS 환경에서 체크 표시 있어야 함)

### CSRF

- [ ] 프론트엔드가 모든 POST/PUT/DELETE 요청에 `X-XSRF-TOKEN` 헤더를 포함하는지 확인 (`safeFetch.ts`의 `getCookie("XSRF-TOKEN")` 로직)
- [ ] 로그인 요청은 CSRF 헤더 불필요(예외 처리됨) — 다른 API는 필수

### 보안 헤더

- [ ] HSTS (`Strict-Transport-Security`) 헤더 응답에 포함 여부 확인 (백엔드에서 자동 추가)
- [ ] `X-Frame-Options: DENY` 확인
- [ ] CSP(`Content-Security-Policy`) 헤더가 운영 정적 리소스 도메인을 모두 허용하는지 검토
