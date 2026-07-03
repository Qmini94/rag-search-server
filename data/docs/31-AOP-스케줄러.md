# AOP · 스케줄러 · 횡단 관심사

## 1. AOP 개요

백엔드에는 3개의 `@Aspect` 컴포넌트가 등록되어 있다. 모두 `kr.co.itid.cms.aop` 패키지에 위치한다.

| 클래스 | 트리거 어노테이션 | 포인트컷 | 동작 |
|---|---|---|---|
| `ExecutionTimeAspect` | `@ExecutionTime` | `@annotation(executionTime)` — 메서드 단위 | `@Around`: 메서드 실행 전후 나노초 측정 후 로그 출력 |
| `HtmlSanitizerAspect` | `@SanitizeHtml` (필드) | `execution(* kr.co.itid.cms.service.cms..*(..)) && @annotation(Transactional)` | `@Around`: cms 서비스 레이어 `@Transactional` 메서드 진입 시 파라미터 객체의 `@SanitizeHtml` String 필드 새니타이징 |
| `LoginLogAspect` | — | `execution(* kr.co.itid.cms.service..AuthService.login(..))` | `@AfterReturning` / `@AfterThrowing`: 로그인 성공/실패 감지 후 비동기 로그 저장 |

---

## 2. ExecutionTimeAspect

**파일**: `aop/ExecutionTimeAspect.java`

### 커스텀 어노테이션 `@ExecutionTime`

```java
@ExecutionTime                            // 기본: INFO 레벨, MILLISECONDS
@ExecutionTime(description = "사이트 생성") // 설명 지정
@ExecutionTime(level = LogLevel.DEBUG, unit = TimeUnit.MICROSECONDS)
```

속성:

| 속성 | 기본값 | 설명 |
|---|---|---|
| `description` | `""` (→ `클래스명.메서드명`) | 로그에 출력될 설명 문자열 |
| `level` | `LogLevel.INFO` | DEBUG / INFO / WARN / ERROR |
| `unit` | `TimeUnit.MILLISECONDS` | NANOSECONDS / MICROSECONDS / MILLISECONDS / SECONDS |

### 실행시간 측정 로직

`@Around` 어드바이스로 `System.nanoTime()`을 사용해 메서드 실행 전후를 측정한다. 예외가 발생하더라도 실행시간을 측정한 뒤 예외를 재발생시킨다.

### 출력 형식

```
[EXECUTION_TIME] {description}: {time:.2f} {unit}
[EXECUTION_TIME] BoardService.getBoardList: 12.34 ms
[EXECUTION_TIME] BoardService.getBoardList [EXCEPTION]: 5.67 ms
```

로그 레벨은 `@ExecutionTime(level = ...)` 속성으로 제어되며 기본값은 `INFO`다.

---

## 3. HtmlSanitizerAspect

**파일**: `aop/HtmlSanitizerAspect.java`

### 동작 방식

- **포인트컷**: `kr.co.itid.cms.service.cms` 하위 패키지의 `@Transactional` 메서드 진입 시에만 동작한다.
- `@Around` 어드바이스에서 메서드 파라미터 객체들을 순회하고, 각 객체의 `DeclaredFields` 중 `String` 타입이면서 `@SanitizeHtml`이 붙은 필드만 선별하여 `HtmlSanitizerUtil.sanitize()`를 호출한다.

### `@SanitizeHtml` 사용 대상

```java
public class BoardSaveRequest {
    @SanitizeHtml
    private String content;   // 게시판 본문, 에디터 HTML 필드에만 사용

    // 아래는 사용 금지
    private String title;
    private String writerEmail;
    private String password;
}
```

권장 대상: 게시판 본문, 페이지/콘텐츠 에디터 HTML 필드
사용 금지 대상: 이메일, 아이디, 전화번호, 비밀번호 등 순수 텍스트

### `HtmlSanitizerUtil` 새니타이징 단계

`HtmlSanitizerUtil.sanitize()`는 4단계로 위험 패턴을 제거한다.

| 단계 | 처리 내용 |
|---|---|
| 1 | `<script>...</script>` 블록 제거, `javascript:` / `vbscript:` 프로토콜 제거 |
| 2 | `on\w+=` 형태의 이벤트 핸들러 속성 제거 (`onload=`, `onclick=` 등) |
| 3 | CSS `expression()` 제거 |
| 4 | 위험 태그 통째로 제거: `script`, `object`, `embed`, `link`, `meta`, `iframe`, `frame`, `frameset`, `form`, `input`, `button`, `textarea`, `select`, `option` |

허용되지 않는 HTML 패턴이 감지되면 `IllegalArgumentException`을 던지며, 처리 오류 시 폴백으로 모든 HTML 태그를 제거하고 텍스트만 반환한다.

---

## 4. LoginLogAspect

**파일**: `aop/LoginLogAspect.java`

### 포인트컷

```java
@Pointcut("execution(* kr.co.itid.cms.service..AuthService.login(..))")
public void loginPointcut() {}
```

`AuthService.login()` 메서드 하나만 타겟으로 삼는다.

### @AfterReturning — 로그인 성공

로그인 성공 후 `SecurityUtil.getCurrentUser()`로 인증된 사용자 정보(`userId`, `userName`, `hostname`, `sessionId`)를 가져오고, `RequestInfoUtil`로 `clientIp`, `userAgent`를 추출하여 `LoginLogRecord`를 구성한다.

### @AfterThrowing — 로그인 실패

예외를 받아 `resolveReason()` 헬퍼로 실패 사유를 추출한다. 우선순위:

1. `EgovBizException.getWrappedException()`의 `messageKey`
2. 바깥 `EgovBizException.messageKey`
3. `EgovBizException.getMessage()`
4. 일반 `Exception.getMessage()`
5. 폴백: 예외 클래스명

실패 사유는 DB 컬럼 보호를 위해 240자로 잘린다(`truncate`).

### 비동기 저장

```java
loginLogService.writeAsync(rec);
```

성공/실패 모두 `writeAsync()`를 통해 비동기로 저장하므로 로그인 응답 지연에 영향을 주지 않는다. 실행자는 아래 섹션의 `logExecutor` 스레드풀을 사용한다.

---

## 5. VisitorInterceptor

**파일**: `config/common/interceptor/VisitorInterceptor.java`

```java
@Override
public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
    visitorService.checkAndCountVisitor(request);
    return true;
}
```

### WebMvcConfig 등록 경로

```java
registry.addInterceptor(visitorInterceptor)
        .addPathPatterns("/back-api/auth/me");
```

`/back-api/auth/me` 단 하나의 경로에만 등록한 이유: 프론트엔드(Nuxt)는 페이지 진입 시마다 `/auth/me`를 호출하여 세션을 확인한다. 이 단일 엔드포인트에만 인터셉터를 걸면 별도의 방문자 추적 API 없이 모든 페이지 방문을 자연스럽게 캡처할 수 있다.

### Redis 키 구조

| 키 패턴 | TTL | 용도 |
|---|---|---|
| `visitor:{ip}:{date}:{hostname}` | `PERMISSION_TTL` (상수) | 중복 방문 방지용 — `setIfAbsent()`로 이미 카운트된 IP 체크 |
| `visitors:daily:{date}:{hostname}:{device}` | — (스케줄러가 삭제) | 일일 방문자 수 카운터 (`device` = `web` or `mobile`) |

### 동작 흐름

1. `X-Forwarded-For` 헤더 우선으로 클라이언트 IP 추출
2. `User-Agent`로 모바일 여부 판별 (`iphone|android|mobile` 패턴)
3. JWT 인증 컨텍스트에서 `hostname` 추출
4. `hostname`이 `common` 또는 `unknown`이면 카운트 없이 즉시 반환
5. `visitor:{ip}:{date}:{hostname}` 키로 `setIfAbsent()` 호출 — 새 방문자인 경우에만 `visitors:daily:...` 카운터 증가

---

## 6. 방문자 스케줄러

**파일**: `service/scheduler/visitor/impl/VisitorMigrationServiceImpl.java`

### 실행 시점

```java
@Scheduled(cron = "0 0 0 * * *") // 매일 00시 정각
public void migrateDailyVisitorStats()
```

### Redis → DB 마이그레이션 흐름

```
1. redisTemplate.keys("visitors:daily:*") 로 전체 키 스캔
2. 각 키를 ":" 기준으로 파싱 → parts[2]=date, parts[3]=hostname, parts[4]=deviceType
3. compoundKey = "date|hostname" 단위로 web/mobile 카운트를 Map에 집계
4. compoundKey 순회:
   - hostname == "common" 이면 스킵
   - jdbcTemplate으로 visit_site 테이블 UPSERT
     INSERT INTO visit_site (visit_date, hostname, web_cnt, mobile_cnt)
     VALUES (?, ?, ?, ?)
     ON DUPLICATE KEY UPDATE
         web_cnt = web_cnt + VALUES(web_cnt),
         mobile_cnt = mobile_cnt + VALUES(mobile_cnt)
5. DB 저장 성공 시에만 해당 Redis 키를 삭제 목록에 추가
6. 성공 키들을 일괄 삭제 (redisTemplate.delete(keysToDelete))
```

### 실패 처리 전략

- 키 파싱 오류(parts 개수 불일치 등): 해당 키만 건너뛰고 나머지 진행
- DB 저장 실패(`DataAccessException`): 로그만 남기고 해당 키는 **Redis에 잔류** — 다음 날 스케줄러 실행 시 재처리 가능
- 전체 예외: `processException("error.visitor.migration_fail", ...)` 호출 후 예외 전파

`hostname == "common"` 키는 파싱은 하되 DB 저장을 건너뛰고 Redis 키도 삭제하지 않는다.

---

## 7. AsyncConfig

**파일**: `config/common/async/AsyncConfig.java`

```java
@Bean(name = "logExecutor")
public Executor logExecutor() {
    ThreadPoolTaskExecutor ex = new ThreadPoolTaskExecutor();
    ex.setCorePoolSize(2);
    ex.setMaxPoolSize(8);
    ex.setQueueCapacity(1000);
    ex.setThreadNamePrefix("audit-");
    ex.initialize();
    return ex;
}
```

### 스레드풀 설정

| 설정 | 값 | 의미 |
|---|---|---|
| `corePoolSize` | 2 | 상시 유지 스레드 수 |
| `maxPoolSize` | 8 | 큐 포화 시 최대 확장 스레드 수 |
| `queueCapacity` | 1000 | 대기 작업 큐 크기 |
| `threadNamePrefix` | `audit-` | 스레드 이름 접두사 (로그 추적용) |

### 사용처

`LoginLogService.writeAsync()`에서 `@Async("logExecutor")`로 지정하여 로그인 로그를 비동기로 저장한다.

### 주의사항

큐 용량(1000)을 초과하면 Spring의 기본 `AbortPolicy`에 의해 `TaskRejectedException`이 발생하고 **로그가 유실**된다. 대용량 동시 로그인 트래픽이 예상될 경우 `RejectedExecutionHandler`를 커스텀하거나 `queueCapacity`를 증가시켜야 한다.
