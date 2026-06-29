from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from models.models import Project, Document

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    id: str
    name: str
    base_path: str


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    result = []
    for p in projects:
        doc_count = db.query(func.count(Document.id)).filter(Document.project_id == p.id).scalar()
        result.append({
            "id": p.id,
            "name": p.name,
            "base_path": p.base_path,
            "doc_count": doc_count,
        })
    return {"projects": result}


@router.post("", status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    existing = db.query(Project).filter(Project.id == body.id).first()
    if existing:
        raise HTTPException(400, f"Project '{body.id}' already exists")

    project = Project(id=body.id, name=body.name, base_path=body.base_path)
    db.add(project)
    db.commit()
    return {"id": project.id, "name": project.name, "base_path": project.base_path}


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, f"Project '{project_id}' not found")

    db.delete(project)  # CASCADE deletes documents
    db.commit()
    return {"deleted": project_id}
