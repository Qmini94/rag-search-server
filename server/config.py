import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dev:dev@localhost:5432/rag")
MODEL_NAME = os.getenv("MODEL_NAME", "intfloat/multilingual-e5-small")
PROJECT_MOUNT_PREFIX = os.getenv("PROJECT_MOUNT_PREFIX", "/project")

# Q-CMS 프로젝트 고정
PROJECT_ID = os.getenv("PROJECT_ID", "qcms")
PROJECT_NAME = os.getenv("PROJECT_NAME", "Q-CMS")
PROJECT_BASE_PATH = os.getenv("PROJECT_BASE_PATH", "/project/JH/half")

# VLLM (OpenAI-compatible API)
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:7100/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "google/gemma-4-E4B-it")
