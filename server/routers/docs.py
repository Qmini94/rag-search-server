import os
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import PROJECT_ID, DOCS_DIR
from db.database import get_db
from models.models import Document
from services.chunker import chunk_file, detect_language
from services.embedder import embed_for_indexing

router = APIRouter(prefix="/documents", tags=["documents"])

KST = timezone(timedelta(hours=9))


def _ensure_dir():
    os.makedirs(DOCS_DIR, exist_ok=True)


def _safe_name(filename: str) -> str:
    """경로 순회 방지"""
    name = Path(filename).name
    if not name or name.startswith("."):
        raise HTTPException(400, "Invalid filename")
    if not name.endswith(".md"):
        raise HTTPException(400, "Only .md files allowed")
    return name


def _file_info(filepath: str) -> dict:
    stat = os.stat(filepath)
    return {
        "name": Path(filepath).name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=KST).isoformat(),
    }


def _reindex_file(db: Session, filepath: str, source: str):
    """단일 파일 재인덱싱 (기존 청크 삭제 → 새로 생성)"""
    db.query(Document).filter(
        Document.project_id == PROJECT_ID,
        Document.source == source,
    ).delete(synchronize_session="fetch")
    db.flush()

    chunks = chunk_file(filepath)
    language = detect_language(filepath)
    from services.indexer import compute_file_hash
    file_hash = compute_file_hash(filepath)

    for chunk in chunks:
        embedding = embed_for_indexing(chunk["content"])
        doc = Document(
            project_id=PROJECT_ID,
            content=chunk["content"],
            embedding=embedding,
            source=source,
            file_hash=file_hash,
            doc_type="convention",
            language=language,
            chunk_index=chunk["chunk_index"],
        )
        db.add(doc)

    db.commit()
    return len(chunks)


def _remove_from_index(db: Session, source: str) -> int:
    """인덱스에서 해당 소스 삭제"""
    count = db.query(Document).filter(
        Document.project_id == PROJECT_ID,
        Document.source == source,
    ).delete(synchronize_session="fetch")
    db.commit()
    return count


def _doc_source(filename: str) -> str:
    """DB에 저장할 source 경로"""
    return f"docs/{filename}"


@router.get("")
def list_docs():
    _ensure_dir()
    files = []
    for f in sorted(os.listdir(DOCS_DIR)):
        if f.endswith(".md"):
            filepath = os.path.join(DOCS_DIR, f)
            files.append(_file_info(filepath))
    return {"docs": files}


@router.get("/{filename}")
def read_doc(filename: str):
    name = _safe_name(filename)
    filepath = os.path.join(DOCS_DIR, name)
    if not os.path.isfile(filepath):
        raise HTTPException(404, f"File not found: {name}")
    content = Path(filepath).read_text(encoding="utf-8")
    return {"name": name, "content": content, **_file_info(filepath)}


class DocSaveRequest(BaseModel):
    content: str


@router.put("/{filename}")
def save_doc(filename: str, body: DocSaveRequest, db: Session = Depends(get_db)):
    name = _safe_name(filename)
    _ensure_dir()
    filepath = os.path.join(DOCS_DIR, name)

    Path(filepath).write_text(body.content, encoding="utf-8")

    source = _doc_source(name)
    chunks = _reindex_file(db, filepath, source)
    return {"name": name, "chunks": chunks, "message": "Saved and re-indexed"}


@router.post("/upload")
def upload_doc(file: UploadFile = File(...), db: Session = Depends(get_db)):
    name = _safe_name(file.filename)
    _ensure_dir()
    filepath = os.path.join(DOCS_DIR, name)

    if os.path.exists(filepath):
        raise HTTPException(409, f"File already exists: {name}. Use PUT to update.")

    content = file.file.read()
    Path(filepath).write_bytes(content)

    source = _doc_source(name)
    chunks = _reindex_file(db, filepath, source)
    return {"name": name, "chunks": chunks, "message": "Uploaded and indexed"}


@router.delete("/{filename}")
def delete_doc(filename: str, db: Session = Depends(get_db)):
    name = _safe_name(filename)
    filepath = os.path.join(DOCS_DIR, name)

    if not os.path.isfile(filepath):
        raise HTTPException(404, f"File not found: {name}")

    os.remove(filepath)

    source = _doc_source(name)
    removed = _remove_from_index(db, source)
    return {"name": name, "removed_chunks": removed, "message": "Deleted"}
