from app.retrieval.hybrid_search import hybrid_search
from app.agent.answerer import answer_question

def ask(question: str, repo: str, limit: int = 5) -> dict:
    search_result = hybrid_search(question, repo=repo, limit=limit)
    chunks = search_result["results"]

    answer = answer_question(question, chunks, repo=repo)

    return {
        "query_type": search_result["query_type"],
        "answer": answer["answer"],
        "sources": answer["sources"],
    }