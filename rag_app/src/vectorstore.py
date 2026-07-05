# chroma wrapper. picked chroma because it's embedded (no separate server
# to run) and has upsert + metadata filtering built in.
import hashlib
import chromadb
from src.config import CFG


def _client():
    return chromadb.PersistentClient(path=CFG.chroma_path)


def get_collection():
    client = _client()
    return client.get_or_create_collection(
        name=CFG.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )


def chunk_id(source: str, index: int, text: str) -> str:
    # id = hash(source + index + text), so re-ingesting the same file
    # gives the same ids and upsert just overwrites instead of duplicating
    h = hashlib.sha256(f"{source}:{index}:{text}".encode("utf-8")).hexdigest()[:24]
    safe_source = source.replace("/", "_").replace(" ", "_")
    return f"{safe_source}_{index}_{h}"


def upsert_chunks(ids, embeddings, documents, metadatas):
    col = get_collection()
    col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def count() -> int:
    return get_collection().count()


def query(embedding, top_k: int, where: dict | None = None):
    col = get_collection()
    return col.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
