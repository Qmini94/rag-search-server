from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.database import get_db
from models.models import Project
from services.embedder import embed_for_query

router = APIRouter(prefix="/projects/{project_id}", tags=["search"])


@router.get("/search")
def search(
    project_id: str,
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, f"Project '{project_id}' not found")

    query_embedding = embed_for_query(q)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    type_filter = ""
    params = {"project_id": project_id, "top_k": top_k}

    if type:
        type_filter = "AND doc_type = :doc_type"
        params["doc_type"] = type

    # embedding을 직접 문자열로 삽입 (숫자 배열이라 SQL injection 위험 없음)
    sql = text(f"""
        SELECT content, source, doc_type, language,
               1 - (embedding <=> '{embedding_str}'::vector) AS similarity
        FROM documents
        WHERE project_id = :project_id {type_filter}
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT :top_k
    """)

    rows = db.execute(sql, params).fetchall()

    results = [
        {
            "content": row.content,
            "source": row.source,
            "doc_type": row.doc_type,
            "language": row.language,
            "similarity": round(float(row.similarity), 4),
        }
        for row in rows
    ]

    return {"project": project_id, "query": q, "results": results}
