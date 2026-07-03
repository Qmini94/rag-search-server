# Git 워크플로우 및 CI/CD

## Git 저장소

Q-CMS는 Gitea(사내 Git 서버)에서 프론트엔드/백엔드를 분리 관리한다.

| 저장소 | URL | 브랜치 |
|---|---|---|
| 프론트엔드 | `http://49.254.140.64:4000/yubi/jh-half-frontend.git` | main |
| 백엔드 | `http://49.254.140.64:4000/yubi/jh-half-backend.git` | main |

## 브랜치 전략

현재 `main` 단일 브랜치로 운영한다.

```
main ──●──●──●──●──●──  (모든 커밋이 여기에)
       ↑
     Jenkins 자동 감지 → 빌드 → 배포
```

## 커밋 → 배포 흐름

```
1. 로컬에서 코드 수정
2. git add → git commit → git push (Gitea main 브랜치)
3. Jenkins가 push 감지 (또는 수동 Build Now)
4. Docker 이미지 빌드
5. 기존 컨테이너 중지 → 새 컨테이너 실행
6. Health Check (컨테이너 running 확인)
7. Docker 이미지 tar.gz로 저장 (운영 이관용)
8. 이전 이미지 정리
```

## Jenkins 파이프라인

### 백엔드 Jenkinsfile

파일: `jh-half-backend/Jenkinsfile`

```
5단계: Checkout → Build Docker Image → Deploy → Health Check → Export Image
```

**주요 환경변수** (새 프로젝트 투입 시 여기만 수정):

```groovy
IMAGE_NAME     = 'jh-half-backend'
SHARED_DIR     = '/data/jh_half/shared'
INSTALL_DIR    = '/data/jh_half/install'
SPRING_PROFILE = 'prod'
DOMAIN_URL     = 'jhhalf.mx.co.kr'
DB_HOST        = 'jh-mysql'        // Docker 네트워크 내 컨테이너명
DB_PORT        = '3306'
DB_NAME        = 'jh_half_q_cms'
DB_USER        = 'root'
DB_PASSWORD    = 'Yubi!!@@##64'
REDIS_HOST     = 'jh-redis'
REDIS_PORT     = '6379'
REDIS_PASSWORD = 'Yubi!!@@##64'
CMS_ALLOWED_IPS = '49.254.140.64,127.0.0.1'
COOKIE_SECURE  = 'false'           // HTTPS 적용 시 true
```

**Deploy 단계 핵심**:
```bash
docker stop jh-half-backend || true
docker rm jh-half-backend || true
docker run -d \
  --name jh-half-backend \
  --network docker_jh-net \
  --restart unless-stopped \
  -p 8080:8080 \
  -v ${SHARED_DIR}:${SHARED_DIR} \
  -v ${INSTALL_DIR}:${INSTALL_DIR}:ro \
  -e SPRING_PROFILES_ACTIVE=prod \
  -e SHARED_DIR=${SHARED_DIR} \
  ... (환경변수 전달)
  jh-half-backend:${BUILD_NUMBER}
```

**Export 단계**: 이미지를 tar.gz로 저장하여 운영 서버 이관에 사용한다.
```bash
docker save jh-half-backend:latest | gzip > /data/jh_half/deploy/backend/jh-half-backend.tar.gz
echo "$(date +%s) ${GIT_COMMIT}" > /data/jh_half/deploy/backend/VERSION
```

### 프론트엔드 Jenkinsfile

파일: `jh-half-frontend/Jenkinsfile`

동일한 5단계 구조. 차이점:

```groovy
IMAGE_NAME     = 'jh-half-frontend'
SITE_URL       = 'http://jhhalf.mx.co.kr'
BACKEND_URL    = 'http://jh-half-backend:8080/back-api'  // Docker 내부 통신
CMS_ALLOWED_IPS = '49.254.140.64,127.0.0.1,172.16.0.0/12,192.168.0.0/16'
```

**Deploy 환경변수**:
```bash
-e NUXT_API_BASE=${BACKEND_URL}             # SSR에서 백엔드 호출 (Docker 내부)
-e NUXT_PUBLIC_BASE_URL=${SITE_URL}         # 클라이언트 기본 URL
-e NUXT_PUBLIC_API_BASE=${SITE_URL}/back-api  # CSR에서 백엔드 호출 (Nginx 경유)
-e CMS_JSON_ROOT=${SHARED_DIR}/json
-e CMS_BASE_URL=${SITE_URL}
-e CMS_ALLOWED_IPS=${CMS_ALLOWED_IPS}
```

> SSR(서버사이드)에서는 `NUXT_API_BASE`로 Docker 네트워크 내부 직접 호출하고, CSR(브라우저)에서는 `NUXT_PUBLIC_API_BASE`로 Nginx를 경유하여 호출한다.

## Docker 빌드

### 백엔드 Dockerfile

파일: `jh-half-backend/Dockerfile`

```dockerfile
# Stage 1: 빌드
FROM eclipse-temurin:17-jdk AS build
WORKDIR /app
COPY gradlew .
COPY gradle gradle
COPY build.gradle* settings.gradle* ./
RUN chmod +x ./gradlew
RUN ./gradlew dependencies -q || true   # 의존성 캐싱 레이어
COPY src src
RUN ./gradlew clean bootJar -x test

# Stage 2: 실행
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /app/build/libs/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java","-jar","/app/app.jar"]
```

### 프론트엔드 Dockerfile

파일: `jh-half-frontend/Dockerfile`

```dockerfile
# Stage 1: 빌드
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: 실행
FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/.output ./.output
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./
EXPOSE 3000
ENV HOST=0.0.0.0
ENV PORT=3000
CMD ["node", ".output/server/index.mjs"]
```

## 새 프로젝트 투입 시 변경 사항

Q-CMS를 새 프로젝트에 적용할 때 Jenkinsfile에서 환경변수만 수정하면 된다.

| 변경 항목 | 백엔드 | 프론트엔드 |
|---|---|---|
| 이미지/컨테이너명 | `IMAGE_NAME`, `CONTAINER_NAME` | 동일 |
| 도메인 | `DOMAIN_URL` | `SITE_URL` |
| DB | `DB_HOST`, `DB_NAME`, `DB_PASSWORD` | - |
| Redis | `REDIS_HOST`, `REDIS_PASSWORD` | - |
| 공유 디렉토리 | `SHARED_DIR`, `INSTALL_DIR` | `SHARED_DIR` |
| IP 제어 | `CMS_ALLOWED_IPS` | `CMS_ALLOWED_IPS` |
| 네트워크 | `NETWORK_NAME` | `NETWORK_NAME` |

## 운영 서버 이관

중계 서버(Jenkins)에서 빌드한 이미지를 운영 서버로 전송하는 방식이다.

```bash
# 중계 서버에서 이미지 저장됨 (Jenkins Export 단계)
/data/jh_half/deploy/
├── backend/
│   ├── jh-half-backend.tar.gz
│   └── VERSION
└── frontend/
    ├── jh-half-frontend.tar.gz
    └── VERSION

# 운영 서버로 전송 (rsync 또는 scp)
rsync -avz /data/jh_half/deploy/ user@운영서버:/data/jh_half/deploy/

# 운영 서버에서 로드 + 실행
gunzip -c jh-half-backend.tar.gz | docker load
docker stop jh-half-backend && docker rm jh-half-backend
docker run -d --name jh-half-backend ... jh-half-backend:latest
```

## Jenkins 접속 정보

| 항목 | 값 |
|---|---|
| URL | http://49.254.140.64:9090 |
| ID | yubi |
| PW | Yubi!!@@##5630 |

수동 빌드: Jenkins → 프로젝트 선택 → Build Now → 약 5분 소요
