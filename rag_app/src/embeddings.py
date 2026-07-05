"""
Embedding wrapper. Local sentence-transformers model -> zero per-call cost,
no external API dependency for the ingestion path (only generation calls a
paid LLM). Model + dimensionality are recorded explicitly for the eval report.
"""
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from src.config import CFG


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(CFG.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = _model().encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
