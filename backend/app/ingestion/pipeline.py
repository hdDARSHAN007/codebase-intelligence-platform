import time
from app.ingestion.cloner import clone_repo
from app.ingestion.filters import collect_files
from app.ingestion.language_detect import detect_language
from app.ingestion.parser import parse_file, LANGUAGES
from app.ingestion.chunker import extract_chunks
from app.ingestion.embedder import embed_texts
from app.retrieval.vectorstore import ensure_collection, store_chunks, delete_repo_chunks

# The embedding model reads about 2000 tokens. Very long chunks (like a whole
# class) are cut to this many characters for embedding only. The full text is
# still stored.
MAX_EMBED_CHARS = 6000

# Embed and save in groups, so progress is saved as we go.
CHUNKS_PER_GROUP = 40


def repo_name_from_url(repo_url: str) -> str:
    """https://github.com/pallets/flask(.git) -> pallets/flask"""
    parts = repo_url.rstrip("/").removesuffix(".git").split("/")
    return "/".join(parts[-2:])


def ingest_repository(repo_url: str, github_token: str | None = None) -> dict:
    started = time.time()
    repo_name = repo_name_from_url(repo_url)

    ensure_collection()

    # 1. Download the repo and list the files worth reading
    local_path = clone_repo(repo_url, github_token)
    files = collect_files(local_path)
    code_files = [f for f in files if f["kind"] == "code"]
    parseable = [f for f in code_files if detect_language(f["extension"]) in LANGUAGES]
    print(f"[ingest] {repo_name}: {len(files)} files found, {len(parseable)} can be parsed")

    # 2. Remove old chunks of this repo, so re-ingesting never leaves duplicates
    delete_repo_chunks(repo_name)

    # 3. Cut every parseable file into chunks
    all_chunks = []
    skipped = 0
    for f in parseable:
        language = detect_language(f["extension"])
        rel_path = f["relative_path"].replace("\\", "/")
        try:
            parsed = parse_file(f["path"], language)
            if parsed is None:
                skipped += 1
                continue
            tree, source_bytes = parsed
            all_chunks.extend(extract_chunks(tree, source_bytes, rel_path, language))
        except Exception as e:
            print(f"[ingest] skipped {rel_path}: {e}")
            skipped += 1

    print(f"[ingest] {len(all_chunks)} chunks created")

    # 4. Embed and store, group by group
    stored = 0
    for i in range(0, len(all_chunks), CHUNKS_PER_GROUP):
        group = all_chunks[i:i + CHUNKS_PER_GROUP]
        embeddings = embed_texts([c.text[:MAX_EMBED_CHARS] for c in group])
        stored += store_chunks(repo_name, group, embeddings)
        print(f"[ingest] stored {stored}/{len(all_chunks)} chunks")

    return {
        "status": "done",
        "repo": repo_name,
        "files_found": len(files),
        "files_parsed": len(parseable) - skipped,
        "files_skipped": skipped,
        "chunks_stored": stored,
        "seconds": round(time.time() - started, 1),
        "local_path": local_path,
    }