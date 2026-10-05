from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ingestion.cloner import CloneError
from app.ingestion.pipeline import ingest_repository

router = APIRouter()

class IngestRequest(BaseModel):
    repo_url: str
    github_token: str | None = None

@router.post("/ingest")
def ingest_repo(req: IngestRequest):
    try:
        return ingest_repository(req.repo_url, req.github_token)
    except CloneError as e:
        raise HTTPException(status_code=400, detail=str(e))