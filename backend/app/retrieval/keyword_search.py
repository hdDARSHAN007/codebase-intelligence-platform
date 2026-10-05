import re
from rank_bm25 import BM25Okapi
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.retrieval.vectorstore import get_client, COLLECTION_NAME

# One keyword index per repo, built the first time it is needed and kept in
# memory. Restart the program after re-ingesting a repo to refresh it.
_indexes: dict = {}


def tokenize(text: str) -> list[str]:
    """
    Splits code into lowercase words.
    'add_url_rule' -> add_url_rule, add, url, rule
    'BlueprintSetupState' -> blueprintsetupstate, blueprint, setup, state
    The whole name is kept too, so exact-name searches match strongly.
    """
    tokens = []
    for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
        tokens.append(word.lower())
        spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", word).replace("_", " ")
        parts = spaced.lower().split()
        if len(parts) > 1:
            tokens.extend(parts)
    return tokens


def _load_repo_chunks(repo: str) -> list[dict]:
    """Reads every stored chunk of one repo out of Qdrant."""
    client = get_client()
    payloads = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="repo", match=MatchValue(value=repo))]
            ),
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        payloads.extend(p.payload for p in points)
        if offset is None:
            break
    return payloads


def _get_index(repo: str):
    if repo not in _indexes:
        payloads = _load_repo_chunks(repo)
        documents = []
        for p in payloads:
            # The function name counts 3x, the file path once, then the code itself
            tokens = (
                tokenize(p["symbol_name"]) * 3
                + tokenize(p["file_path"])
                + tokenize(p["text"])
            )
            documents.append(tokens)
        _indexes[repo] = (BM25Okapi(documents), payloads)
    return _indexes[repo]


def keyword_search(question: str, repo: str, limit: int = 5) -> list[dict]:
    """Finds the chunks that contain the words of the question."""
    bm25, payloads = _get_index(repo)
    scores = bm25.get_scores(tokenize(question))

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]

    results = []
    for i in ranked:
        if scores[i] <= 0:
            continue
        p = payloads[i]
        results.append({
            "score": round(float(scores[i]), 2),
            "symbol": p["symbol_name"],
            "type": p["symbol_type"],
            "parent_class": p["parent_class"],
            "file": p["file_path"],
            "lines": f'{p["start_line"]}-{p["end_line"]}',
            "text": p["text"],
        })
    return results