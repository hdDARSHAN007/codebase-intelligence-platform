import os
import cohere
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        _client = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))
    return _client


def _format_for_rerank(chunk: dict) -> str:
    """
    Adds the symbol name and type as a heading before the code, so the
    reranker can tell a real implementation apart from a test that
    happens to mention the same words.
    """
    kind = chunk["type"]
    name = chunk["symbol"]
    where = f'in class {chunk["parent_class"]}' if chunk.get("parent_class") else ""
    header = f"{kind.upper()} {name} {where} ({chunk['file']})".strip()
    return f"{header}\n{chunk['text']}"


def rerank(question: str, chunks: list[dict], top_n: int = 5) -> list[dict]:
    """
    Re-scores candidate chunks by how well each one actually answers the
    question, using Cohere's rerank model. Returns the top_n in the new
    order, each with a rerank_score added.
    """
    if not chunks:
        return []

    client = get_client()
    documents = [_format_for_rerank(c) for c in chunks]

    response = client.rerank(
        model="rerank-v3.5",
        query=question,
        documents=documents,
        top_n=min(top_n, len(chunks)),
    )

    results = []
    for r in response.results:
        chunk = chunks[r.index]
        chunk["rerank_score"] = round(r.relevance_score, 4)
        results.append(chunk)

    return results