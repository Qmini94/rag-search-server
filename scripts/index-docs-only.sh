#!/bin/bash
# ============================================
# RAG 문서(md)만 인덱싱 (소스코드 제외)
# 문서 수정 후 빠르게 반영할 때 사용
# 운영: bash scripts/index-docs-only.sh
# 로컬: bash scripts/index-docs-only.sh local
# ============================================

RAG_URL="${RAG_URL:-http://localhost:3200}"
ENV="${1:-prod}"

if [ "$ENV" = "local" ]; then
  GLOB="../../RAG/data/docs/*.md"
else
  GLOB="docs/*.md"
fi

echo "=== RAG 문서 인덱싱 [${ENV}] ==="

RESULT=$(curl -s -X POST "${RAG_URL}/index" \
  -H "Content-Type: application/json" \
  -d "{\"targets\": [{\"glob\": \"${GLOB}\", \"doc_type\": \"convention\"}]}")

echo "${RESULT}" | python3 -m json.tool 2>/dev/null || echo "${RESULT}"
