from fastapi import APIRouter
from pydantic import BaseModel
from app.retrieval.hybrid_search import hybrid_search

router = APIRouter()

class SearchRequest(BaseModel):
    question: str
    repo: str
    limit: int = 5

@router.post("/search")
def search(req: SearchRequest):
    return hybrid_search(req.question, repo=req.repo, limit=req.limit)