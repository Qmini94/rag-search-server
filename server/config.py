import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dev:dev@localhost:5432/rag")
MODEL_NAME = os.getenv("MODEL_NAME", "intfloat/multilingual-e5-small")
PROJECT_MOUNT_PREFIX = os.getenv("PROJECT_MOUNT_PREFIX", "/project")
