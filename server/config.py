import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dev:dev@localhost:5432/rag")
MODEL_NAME = os.getenv("MODEL_NAME", "intfloat/multilingual-e5-small")

# 프로젝트 설정
PROJECT_ID = os.getenv("PROJECT_ID", "qcms")
PROJECT_NAME = os.getenv("PROJECT_NAME", "Q-CMS")
PROJECT_BASE_PATH = os.getenv("PROJECT_BASE_PATH", "/data")

# 데이터 디렉토리
DOCS_DIR = os.getenv("DOCS_DIR", os.path.join(PROJECT_BASE_PATH, "docs"))
SOURCES_DIR = os.getenv("SOURCES_DIR", os.path.join(PROJECT_BASE_PATH, "sources"))
CONFIG_FILE = os.getenv("CONFIG_FILE", os.path.join(PROJECT_BASE_PATH, "index-config.json"))

# VLLM (OpenAI-compatible API)
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:7100/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "google/gemma-4-E4B-it")
