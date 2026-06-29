CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE projects (
    id          VARCHAR(50) PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    base_path   VARCHAR(500) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE documents (
    id           BIGSERIAL PRIMARY KEY,
    project_id   VARCHAR(50) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    content      TEXT NOT NULL,
    embedding    vector(384) NOT NULL,
    source       VARCHAR(500) NOT NULL,
    file_hash    VARCHAR(64) NOT NULL,
    doc_type     VARCHAR(50) NOT NULL,
    language     VARCHAR(20),
    chunk_index  INT NOT NULL DEFAULT 0,
    updated_at   TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_project_source_chunk UNIQUE(project_id, source, chunk_index)
);

CREATE INDEX idx_documents_embedding
    ON documents USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_documents_project_type ON documents(project_id, doc_type);

CREATE INDEX idx_documents_source ON documents(project_id, source);
