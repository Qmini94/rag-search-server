from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, text

from config import PROJECT_ID, PROJECT_NAME, PROJECT_BASE_PATH
from db.database import SessionLocal
from models.models import Project, Document
from routers import index, search, chat
from services.embedder import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading embedding model...")
    get_model()
    print("Model loaded.")

    # Q-CMS 프로젝트 자동 등록
    db = SessionLocal()
    try:
        existing = db.query(Project).filter(Project.id == PROJECT_ID).first()
        if not existing:
            db.add(Project(id=PROJECT_ID, name=PROJECT_NAME, base_path=PROJECT_BASE_PATH))
            db.commit()
            print(f"Project '{PROJECT_ID}' registered.")
    finally:
        db.close()

    yield


app = FastAPI(title="Q-CMS RAG Chatbot", version="2.0.0", lifespan=lifespan)

app.include_router(index.router)
app.include_router(search.router)
app.include_router(chat.router)

app.mount("/ui", StaticFiles(directory="static", html=True), name="static")


@app.get("/health")
def health():
    db = SessionLocal()
    try:
        total_docs = db.query(func.count(Document.id)).filter(
            Document.project_id == PROJECT_ID
        ).scalar()
        return {"status": "ok", "project": PROJECT_ID, "total_docs": total_docs or 0}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3200, reload=True)
