from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import PROJECT_ID
from db.database import get_db
from models.models import Project
from services.embedder import embed_for_query
from services.llm import ask_llm

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    top_k: int = 5
    doc_type: str | None = None


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == PROJECT_ID).first()
    if not project:
        raise HTTPException(404, f"Project '{PROJECT_ID}' not found. Run /setup first.")

    query_embedding = embed_for_query(req.question)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    type_filter = ""
    params = {"project_id": PROJECT_ID, "top_k": req.top_k}
    if req.doc_type:
        type_filter = "AND doc_type = :doc_type"
        params["doc_type"] = req.doc_type

    sql = text(f"""
        SELECT content, source, doc_type, language,
               1 - (embedding <=> '{embedding_str}'::vector) AS similarity
        FROM documents
        WHERE project_id = :project_id {type_filter}
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT :top_k
    """)
    rows = db.execute(sql, params).fetchall()

    contexts = []
    sources = []
    for row in rows:
        contexts.append(f"[{row.source}]\n{row.content}")
        sources.append({
            "source": row.source,
            "doc_type": row.doc_type,
            "similarity": round(float(row.similarity), 4),
        })

    context_text = "\n\n---\n\n".join(contexts)
    try:
        answer = ask_llm(req.question, context_text)
    except Exception as e:
        answer = f"LLM 서버 연결 실패: {str(e)}\n\n관련 문서는 아래 참고 문서를 확인하세요."

    return {
        "question": req.question,
        "answer": answer,
        "sources": sources,
    }
