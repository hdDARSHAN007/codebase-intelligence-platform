from app.retrieval.vectorstore import ensure_collection, get_client, COLLECTION_NAME

ensure_collection()
client = get_client()
info = client.get_collection(COLLECTION_NAME)
print(f"Connected to Qdrant Cloud")
print(f"Vector size: {info.config.params.vectors.size}")
print(f"Points count: {info.points_count}")