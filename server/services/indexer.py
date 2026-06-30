import hashlib
import glob as glob_module
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

EXCLUDE_DIRS = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__",
    "build", "dist", "out", ".gradle", ".nuxt", ".next",
    "target", ".output", "vendor",
}

from sqlalchemy.orm import Session

from models.models import Project, Document
from services.chunker import chunk_file, detect_language
from services.embedder import embed_for_indexing


def compute_file_hash(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def index_project(db: Session, project: Project, targets: list[dict]) -> dict:
    base = Path(project.base_path).resolve()
    stats = {"indexed": 0, "skipped": 0, "deleted": 0, "errors": 0}

    all_sources = set()

    for target in targets:
        pattern = os.path.normpath(str(base / target["glob"]))
        doc_type = target["doc_type"]

        matched_files = glob_module.glob(pattern, recursive=True)

        for file_path in matched_files:
            file_path = str(Path(file_path).resolve())
            rel_path = os.path.relpath(file_path, base)

            # node_modules 등 제외
            if any(part in EXCLUDE_DIRS for part in Path(rel_path).parts):
                continue
            all_sources.add(rel_path)

            try:
                file_hash = compute_file_hash(file_path)
            except (OSError, PermissionError):
                stats["errors"] += 1
                continue

            # hash 비교로 변경 여부 확인
            existing = (
                db.query(Document.file_hash)
                .filter(Document.project_id == project.id, Document.source == rel_path)
                .first()
            )

            if existing and existing.file_hash == file_hash:
                stats["skipped"] += 1
                continue

            # 변경된 파일: 기존 청크 삭제 + flush
            db.query(Document).filter(
                Document.project_id == project.id, Document.source == rel_path
            ).delete(synchronize_session="fetch")
            db.flush()

            # 청킹 + 임베딩 + 저장
            chunks = chunk_file(file_path)
            language = detect_language(file_path)

            for chunk in chunks:
                try:
                    embedding = embed_for_indexing(chunk["content"])
                except Exception:
                    stats["errors"] += 1
                    continue

                doc = Document(
                    project_id=project.id,
                    content=chunk["content"],
                    embedding=embedding,
                    source=rel_path,
                    file_hash=file_hash,
                    doc_type=doc_type,
                    language=language,
                    chunk_index=chunk["chunk_index"],
                )
                db.add(doc)

            db.flush()
            stats["indexed"] += 1
            logger.info(f"Indexed: {rel_path} ({len(chunks)} chunks)")

    db.commit()
    return stats


def index_single_file(
    db: Session, project: Project, file_path: str, doc_type: str
) -> dict:
    base = Path(project.base_path)
    full_path = str((base / file_path).resolve())
    rel_path = file_path

    if not Path(full_path).exists():
        return {"error": f"File not found: {full_path}"}

    file_hash = compute_file_hash(full_path)

    db.query(Document).filter(
        Document.project_id == project.id, Document.source == rel_path
    ).delete(synchronize_session="fetch")
    db.flush()

    chunks = chunk_file(full_path)
    language = detect_language(full_path)
    count = 0

    for chunk in chunks:
        embedding = embed_for_indexing(chunk["content"])
        doc = Document(
            project_id=project.id,
            content=chunk["content"],
            embedding=embedding,
            source=rel_path,
            file_hash=file_hash,
            doc_type=doc_type,
            language=language,
            chunk_index=chunk["chunk_index"],
        )
        db.add(doc)
        count += 1

    db.commit()
    return {"file": rel_path, "chunks": count}
