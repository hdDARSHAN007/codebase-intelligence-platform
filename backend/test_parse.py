from app.retrieval.search import vector_search
from app.retrieval.keyword_search import keyword_search
from app.retrieval.query_analyzer import analyze_query
from app.retrieval.hybrid_search import _chunk_key, RRF_K, CANDIDATE_POOL

question = "how does Flask register a URL route?"
repo = "pallets/flask"

analysis = analyze_query(question)
vector_results = vector_search(question, limit=analysis["vector_pool"], repo=repo)
keyword_results = keyword_search(question, repo=repo, limit=analysis["keyword_pool"])

fused_scores = {}
chunk_data = {}
for rank, r in enumerate(vector_results):
    key = _chunk_key(r)
    fused_scores[key] = fused_scores.get(key, 0) + 1 / (RRF_K + rank)
    chunk_data[key] = r
for rank, r in enumerate(keyword_results):
    key = _chunk_key(r)
    fused_scores[key] = fused_scores.get(key, 0) + 1 / (RRF_K + rank)
    chunk_data[key] = r

candidate_keys = sorted(fused_scores, key=lambda k: fused_scores[k], reverse=True)[:CANDIDATE_POOL]

print(f"Candidates going into reranking ({len(candidate_keys)}):")
for k in candidate_keys:
    r = chunk_data[k]
    print(f'  {r["symbol"]} ({r["type"]}) - {r["file"]} lines {r["lines"]}')