#!/bin/bash
# ============================================
# RAG 문서 인덱싱 스크립트
# 운영: bash scripts/index-docs.sh
# 로컬: bash scripts/index-docs.sh local
# ============================================

RAG_URL="${RAG_URL:-http://localhost:3200}"
ENV="${1:-prod}"

echo "=== RAG 인덱싱 [${ENV}] ==="
echo "서버: ${RAG_URL}"

# 환경별 glob 경로 설정
if [ "$ENV" = "local" ]; then
  DOCS_GLOB="../../RAG/data/docs/*.md"
  SOURCE_GLOBS='
    {"glob": "jh-half-backend/src/**/*.java", "doc_type": "source"},
    {"glob": "jh-half-frontend/components/**/*.vue", "doc_type": "source"},
    {"glob": "jh-half-frontend/composables/**/*.ts", "doc_type": "source"},
    {"glob": "jh-half-frontend/middleware/**/*.ts", "doc_type": "source"},
    {"glob": "jh-half-frontend/stores/**/*.ts", "doc_type": "source"},
    {"glob": "jh-half-frontend/utils/**/*.ts", "doc_type": "source"},
    {"glob": "jh-half-frontend/server/**/*.ts", "doc_type": "source"}
  '
else
  DOCS_GLOB="docs/*.md"
  SOURCE_GLOBS='
    {"glob": "source/jh-half-backend/src/**/*.java", "doc_type": "source"},
    {"glob": "source/jh-half-frontend/components/**/*.vue", "doc_type": "source"},
    {"glob": "source/jh-half-frontend/composables/**/*.ts", "doc_type": "source"},
    {"glob": "source/jh-half-frontend/middleware/**/*.ts", "doc_type": "source"},
    {"glob": "source/jh-half-frontend/stores/**/*.ts", "doc_type": "source"},
    {"glob": "source/jh-half-frontend/utils/**/*.ts", "doc_type": "source"},
    {"glob": "source/jh-half-frontend/server/**/*.ts", "doc_type": "source"}
  '
fi

# 헬스 체크
echo ""
echo "[1/3] 서버 상태 확인..."
curl -s "${RAG_URL}/health" | python3 -m json.tool 2>/dev/null

# 인덱싱 실행
echo ""
echo "[2/3] 인덱싱 실행..."
RESULT=$(curl -s -X POST "${RAG_URL}/index" \
  -H "Content-Type: application/json" \
  -d "{
    \"targets\": [
      {\"glob\": \"${DOCS_GLOB}\", \"doc_type\": \"convention\"},
      ${SOURCE_GLOBS}
    ]
  }")
echo "${RESULT}" | python3 -m json.tool 2>/dev/null || echo "${RESULT}"

# 통계 확인
echo ""
echo "[3/3] 인덱스 통계..."
curl -s "${RAG_URL}/stats" | python3 -m json.tool 2>/dev/null

echo ""
echo "=== 완료 ==="
