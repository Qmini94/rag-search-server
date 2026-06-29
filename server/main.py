from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import func, text

from db.database import SessionLocal
from models.models import Document
from routers import project, index, search
from services.embedder import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading embedding model...")
    get_model()
    print("Model loaded.")
    yield


app = FastAPI(title="RAG Search Server", version="1.0.0", lifespan=lifespan)

app.include_router(project.router)
app.include_router(index.router)
app.include_router(search.router)


@app.get("/health")
def health():
    db = SessionLocal()
    try:
        total_docs = db.query(func.count(Document.id)).scalar()
        project_count = db.execute(
            text("SELECT COUNT(DISTINCT project_id) FROM documents")
        ).scalar()
        return {"status": "ok", "projects": project_count or 0, "total_docs": total_docs or 0}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3200, reload=True)
