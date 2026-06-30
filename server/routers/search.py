from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import PROJECT_ID
from db.database import get_db
from services.embedder import embed_for_query

router = APIRouter(tags=["search"])


@router.get("/search")
def search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query_embedding = embed_for_query(q)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    type_filter = ""
    params = {"project_id": PROJECT_ID, "top_k": top_k}

    if type:
        type_filter = "AND doc_type = :doc_type"
        params["doc_type"] = type

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

    return {"project": PROJECT_ID, "query": q, "results": results}
