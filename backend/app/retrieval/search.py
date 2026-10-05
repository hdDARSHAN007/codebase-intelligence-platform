from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.ingestion.embedder import embed_query
from app.retrieval.vectorstore import get_client, COLLECTION_NAME


def vector_search(question: str, limit: int = 5, repo: str | None = None) -> list[dict]:
    """Finds the code chunks whose meaning is closest to the question."""
    vector = embed_query(question)

    query_filter = None
    if repo:
        query_filter = Filter(
            must=[FieldCondition(key="repo", match=MatchValue(value=repo))]
        )

    response = get_client().query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit,
        query_filter=query_filter,
        with_payload=True,
    )

    results = []
    for point in response.points:
        p = point.payload
        results.append({
            "score": round(point.score, 3),
            "symbol": p["symbol_name"],
            "type": p["symbol_type"],
            "parent_class": p["parent_class"],
            "file": p["file_path"],
            "lines": f'{p["start_line"]}-{p["end_line"]}',
            "text": p["text"],
        })
    return results