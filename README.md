# Codebase Intelligence Platform

Paste a GitHub repository link, and ask natural-language questions about its code.
Answers are grounded in the actual source and cite exact files and line numbers.

## How it works

GitHub repo -> clone -> filter -> tree-sitter parsing -> AST-based chunking ->
embeddings -> Qdrant vector store -> hybrid search (vector + keyword + RRF fusion)
-> Cohere reranking -> an LLM agent (with search/read-file tools) -> cited answer.

## Stack

- Backend: FastAPI (Python 3.11)
- Frontend: Next.js (React, TypeScript)
- Parsing: tree-sitter (Python, JavaScript, TypeScript)
- Embeddings: Google Gemini (gemini-embedding-001)
- Vector DB: Qdrant (Docker)
- Keyword search: BM25 (rank_bm25)
- Reranking: Cohere rerank-v3.5
- LLM: Google Gemini (gemini-3.5-flash-lite)

## Setup

1. Start Qdrant: `docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage --name codebase-intel-qdrant qdrant/qdrant`
2. Backend:

3. Create `backend/.env` with:

4. Run the backend: `uvicorn app.main:app --port 8001`
5. Frontend:

6. Open `http://localhost:3000`, paste a repo URL, click Ingest, then ask a question.

## Status

All core phases complete: ingestion, chunking, embeddings, hybrid retrieval,
reranking, an agent with tool-calling, a working frontend, and a retrieval
evaluation (precision@5 on a 9-question hand-labeled set).