from fastapi import APIRouter
from pydantic import BaseModel
from app.agent.pipeline import ask

router = APIRouter()

class AskRequest(BaseModel):
    question: str
    repo: str
    limit: int = 5

@router.post("/ask")
def ask_question(req: AskRequest):
    return ask(req.question, repo=req.repo, limit=req.limit)