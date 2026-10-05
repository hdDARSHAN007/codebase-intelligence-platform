import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-embedding-001"
DIMENSIONS = 1536   # matches the Qdrant collection
BATCH_SIZE = 20
MAX_RETRIES = 8
WAIT_SECONDS = 30

_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

def _embed_batch(batch: list[str], task_type: str) -> list[list[float]]:
    """Embeds one batch. If a request fails (for example a rate limit), waits and retries."""
    client = get_client()
    for attempt in range(MAX_RETRIES):
        try:
            result = client.models.embed_content(
                model=MODEL,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=DIMENSIONS,
                ),
            )
            return [e.values for e in result.embeddings]
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"[embed] request failed ({e}); waiting {WAIT_SECONDS}s and retrying...")
            time.sleep(WAIT_SECONDS)

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeds code chunks (used when ingesting a repo)."""
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        all_embeddings.extend(_embed_batch(texts[i:i + BATCH_SIZE], "RETRIEVAL_DOCUMENT"))
    return all_embeddings

def embed_query(text: str) -> list[float]:
    """Embeds a user's question (used when searching)."""
    return _embed_batch([text], "RETRIEVAL_QUERY")[0]