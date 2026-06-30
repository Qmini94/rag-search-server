from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import PROJECT_ID
from db.database import get_db
from models.models import Project, Document
from services.indexer import index_project, index_single_file

router = APIRouter(tags=["index"])


class IndexTarget(BaseModel):
    glob: str
    doc_type: str


class IndexRequest(BaseModel):
    targets: list[IndexTarget]


class FileIndexRequest(BaseModel):
    file_path: str
    doc_type: str


def _get_project(db: Session) -> Project:
    project = db.query(Project).filter(Project.id == PROJECT_ID).first()
    if not project:
        raise HTTPException(404, f"Project '{PROJECT_ID}' not found")
    return project


@router.post("/index")
def do_index(body: IndexRequest, db: Session = Depends(get_db)):
    project = _get_project(db)
    targets = [t.model_dump() for t in body.targets]
    stats = index_project(db, project, targets)
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

    return {
        "project": PROJECT_ID,
        "total_chunks": total,
        "by_type": by_type,
        "by_language": by_language,
    }
