from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.retrieval.vectorstore import get_client, COLLECTION_NAME


def get_file_chunks(repo: str, file_path: str) -> list[dict]:
    """Returns every stored chunk belonging to one exact file in one repo."""
    client = get_client()
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="repo", match=MatchValue(value=repo)),
                FieldCondition(key="file_path", match=MatchValue(value=file_path)),
            ]
        ),
        limit=100,
        with_payload=True,
        with_vectors=False,
    )

    results = []
    for p in points:
        payload = p.payload
        results.append({
            "symbol": payload["symbol_name"],
            "type": payload["symbol_type"],
            "parent_class": payload["parent_class"],
            "file": payload["file_path"],
            "lines": f'{payload["start_line"]}-{payload["end_line"]}',
            "text": payload["text"],
        })
    return results