# loads config from .env, nothing hardcoded
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


@dataclass(frozen=True)
class Config:
    # Vector store
    chroma_path: str = os.getenv("CHROMA_PATH", "./chroma_db")
    chroma_collection: str = os.getenv("CHROMA_COLLECTION", "rag_corpus")

    # Chunking
    chunk_size: int = _int("CHUNK_SIZE", 800)
    chunk_overlap: int = _int("CHUNK_OVERLAP", 120)

    # Embeddings
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embedding_dim: int = _int("EMBEDDING_DIM", 384)

    # Retrieval
    default_top_k: int = _int("DEFAULT_TOP_K", 5)
    no_context_distance_threshold: float = _float("NO_CONTEXT_DISTANCE_THRESHOLD", 0.85)

    # LLM
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Logging
    log_path: str = os.getenv("LOG_PATH", "./logs/query_log.jsonl")


CFG = Config()
