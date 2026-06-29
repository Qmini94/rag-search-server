from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from models.models import Project, Document
from services.indexer import index_project, index_single_file

router = APIRouter(prefix="/projects/{project_id}", tags=["index"])


class IndexTarget(BaseModel):
    glob: str
    doc_type: str


class IndexRequest(BaseModel):
    targets: list[IndexTarget]


class FileIndexRequest(BaseModel):
    file_path: str
    doc_type: str


def _get_project(project_id: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, f"Project '{project_id}' not found")
    return project


@router.post("/index")
def do_index(project_id: str, body: IndexRequest, db: Session = Depends(get_db)):
    project = _get_project(project_id, db)
    targets = [t.model_dump() for t in body.targets]
    stats = index_project(db, project, targets)
    return {"project": project_id, **stats}


@router.post("/file")
def do_file_index(project_id: str, body: FileIndexRequest, db: Session = Depends(get_db)):
    project = _get_project(project_id, db)
    result = index_single_file(db, project, body.file_path, body.doc_type)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return {"project": project_id, **result}


@router.get("/stats")
def get_stats(project_id: str, db: Session = Depends(get_db)):
    _get_project(project_id, db)

    total = db.query(func.count(Document.id)).filter(Document.project_id == project_id).scalar()

    by_type = dict(
        db.query(Document.doc_type, func.count(Document.id))
        .filter(Document.project_id == project_id)
        .group_by(Document.doc_type)
        .all()
    )

    by_language = dict(
        db.query(Document.language, func.count(Document.id))
        .filter(Document.project_id == project_id, Document.language.isnot(None))
        .group_by(Document.language)
        .all()
    )

    return {
        "project": project_id,
        "total_chunks": total,
        "by_type": by_type,
        "by_language": by_language,
    }
