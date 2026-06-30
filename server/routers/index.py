import json
import os
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import PROJECT_ID, CONFIG_FILE, DOCS_DIR, SOURCES_DIR
from db.database import get_db
from models.models import Project, Document
from services.indexer import index_project, index_single_file

router = APIRouter(tags=["index"])

KST = timezone(timedelta(hours=9))

# --- 기본 수집 설정 ---
DEFAULT_CONFIG = {
    "targets": [
        {"glob": "docs/*.md", "doc_type": "convention"},
        {"glob": "sources/backend/**/*.java", "doc_type": "source"},
        {"glob": "sources/frontend/**/*.vue", "doc_type": "source"},
        {"glob": "sources/frontend/**/*.ts", "doc_type": "source"},
    ],
    "last_indexed_at": None,
    "last_stats": None,
}


def _load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        return json.loads(open(CONFIG_FILE, encoding="utf-8").read())
    return DEFAULT_CONFIG.copy()


def _save_config(config: dict):
    os.makedirs(os.path.dirname(CONFIG_FILE) or ".", exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# --- 수집 설정 API ---

class IndexTarget(BaseModel):
    glob: str
    doc_type: str


class ConfigUpdateRequest(BaseModel):
    targets: list[IndexTarget]


@router.get("/config")
def get_config():
    return _load_config()


@router.put("/config")
def update_config(body: ConfigUpdateRequest):
    config = _load_config()
    config["targets"] = [t.model_dump() for t in body.targets]
    _save_config(config)
    return config


# --- 인덱싱 API ---

class IndexRequest(BaseModel):
    targets: list[IndexTarget] | None = None


class FileIndexRequest(BaseModel):
    file_path: str
    doc_type: str


def _get_project(db: Session) -> Project:
    project = db.query(Project).filter(Project.id == PROJECT_ID).first()
    if not project:
        raise HTTPException(404, f"Project '{PROJECT_ID}' not found")
    return project


@router.post("/index")
def do_index(body: IndexRequest = None, db: Session = Depends(get_db)):
    project = _get_project(db)

    # targets 지정 없으면 설정 파일에서 로드
    if body and body.targets:
        targets = [t.model_dump() for t in body.targets]
    else:
        config = _load_config()
        targets = config.get("targets", DEFAULT_CONFIG["targets"])

    stats = index_project(db, project, targets)

    # 설정 파일에 마지막 실행 정보 저장
    config = _load_config()
    config["last_indexed_at"] = datetime.now(KST).isoformat()
    config["last_stats"] = stats
    _save_config(config)

    return {"project": PROJECT_ID, **stats}


@router.post("/file")
def do_file_index(body: FileIndexRequest, db: Session = Depends(get_db)):
    project = _get_project(db)
    result = index_single_file(db, project, body.file_path, body.doc_type)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return {"project": PROJECT_ID, **result}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    _get_project(db)

    total = db.query(func.count(Document.id)).filter(
        Document.project_id == PROJECT_ID
    ).scalar()

    by_type = dict(
        db.query(Document.doc_type, func.count(Document.id))
        .filter(Document.project_id == PROJECT_ID)
        .group_by(Document.doc_type)
        .all()
    )

    by_language = dict(
        db.query(Document.language, func.count(Document.id))
        .filter(Document.project_id == PROJECT_ID, Document.language.isnot(None))
        .group_by(Document.language)
        .all()
    )

    config = _load_config()

    return {
        "project": PROJECT_ID,
        "total_chunks": total,
        "by_type": by_type,
        "by_language": by_language,
        "last_indexed_at": config.get("last_indexed_at"),
    }
