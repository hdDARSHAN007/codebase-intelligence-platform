from app.retrieval.search import vector_search
from app.retrieval.keyword_search import keyword_search
from app.retrieval.query_analyzer import analyze_query
from app.retrieval.reranker import rerank

RRF_K = 60
CANDIDATE_POOL = 15  # how many go into reranking


def _chunk_key(r: dict) -> str:
    return f'{r["file"]}:{r["lines"]}'


def hybrid_search(question: str, repo: str, limit: int = 5) -> dict:
    """
    Runs vector search and keyword search, fuses them by rank, then
    reranks the top candidates for the final, more accurate order.
    """
    analysis = analyze_query(question)

    vector_results = vector_search(question, limit=analysis["vector_pool"], repo=repo)
    keyword_results = keyword_search(question, repo=repo, limit=analysis["keyword_pool"])

    fused_scores: dict = {}
    chunk_data: dict = {}

    for rank, r in enumerate(vector_results):
        key = _chunk_key(r)
        fused_scores[key] = fused_scores.get(key, 0) + 1 / (RRF_K + rank)
        chunk_data[key] = r

    for rank, r in enumerate(keyword_results):
        key = _chunk_key(r)
        fused_scores[key] = fused_scores.get(key, 0) + 1 / (RRF_K + rank)
        chunk_data[key] = r

    candidate_keys = sorted(fused_scores, key=lambda k: fused_scores[k], reverse=True)[:CANDIDATE_POOL]
    candidates = [chunk_data[k] for k in candidate_keys]

    final_results = rerank(question, candidates, top_n=limit)

    return {"query_type": analysis["query_type"], "results": final_results}