from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes.ingest import router as ingest_router
from app.api.routes.search import router as search_router
from app.api.routes.ask import router as ask_router

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(ingest_router)
app.include_router(ask_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.env}