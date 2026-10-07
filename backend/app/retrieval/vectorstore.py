import os
import hashlib
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, FilterSelector,
)
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "code_chunks"
EMBEDDING_DIM = 1536  # gemini-embedding-001 with output_dimensionality=1536

_client = None

def get_client() -> QdrantClient:
    global _client
    if _client is None:
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if qdrant_url:
            # Qdrant Cloud (deployed)
            _client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            # Local Docker (fallback, e.g. for quick local testing)
            _client = QdrantClient(host="localhost", port=6333)
    return _client

def ensure_collection():
    """Creates the code_chunks collection if it doesn't exist yet, and
    makes sure the 'repo' field has an index so it can be filtered on."""
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )

    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="repo",
        field_schema="keyword",
    )

def chunk_to_point_id(repo_name: str, chunk) -> str:
    """
    Same repo + file + line range always gives the same ID, so storing
    the same chunk again overwrites it instead of duplicating it.
    """
    key = f"{repo_name}:{chunk.file_path}:{chunk.start_line}:{chunk.end_line}"
    return hashlib.md5(key.encode()).hexdigest()

def delete_repo_chunks(repo_name: str):
    """Removes every stored chunk of one repo (used before re-ingesting it)."""
    get_client().delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="repo", match=MatchValue(value=repo_name))]
            )
        ),
    )

def store_chunks(repo_name: str, chunks, embeddings) -> int:
    """Stores chunks + their embeddings in Qdrant. Returns how many were stored."""
    client = get_client()
    points = []

    for chunk, vector in zip(chunks, embeddings):
        points.append(PointStruct(
            id=chunk_to_point_id(repo_name, chunk),
            vector=vector,
            payload={
                "repo": repo_name,
                "text": chunk.text,
                "symbol_name": chunk.symbol_name,
                "symbol_type": chunk.symbol_type,
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "language": chunk.language,
                "parent_class": chunk.parent_class,
                "imports": chunk.imports,
            },
        ))

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)