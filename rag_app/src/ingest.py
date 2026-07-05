# usage: python -m src.ingest --path ./data/sample_docs
# run it twice on the same folder and check count() didn't grow - that's
# the idempotency check
import argparse
import time
from pathlib import Path

from src.config import CFG
from src.loaders import discover_corpus, load_file
from src.chunking import chunk_text
from src.embeddings import embed_texts
from src.vectorstore import upsert_chunks, chunk_id, count


def ingest(path: str, chunk_size: int | None = None, overlap: int | None = None):
    chunk_size = chunk_size or CFG.chunk_size
    overlap = overlap or CFG.chunk_overlap

    files = list(discover_corpus(path))
    if not files:
        print(f"No ingestible files found under {path}")
        return

    t0 = time.time()
    total_chunks = 0

    for f in files:
        text = load_file(f)
        if not text.strip():
            print(f"  [skip empty] {f}")
            continue
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            continue

        ids = [chunk_id(str(f), c.index, c.text) for c in chunks]
        docs = [c.text for c in chunks]
        embeddings = embed_texts(docs)
        metadatas = [
            {"source": str(f), "chunk_index": c.index, "n_chunks": len(chunks)}
            for c in chunks
        ]
        upsert_chunks(ids=ids, embeddings=embeddings, documents=docs, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"  ingested {len(chunks):>3} chunks  <-  {f}")

    dt = time.time() - t0
    print(
        f"\nDone. {len(files)} files -> {total_chunks} chunks upserted in {dt:.1f}s. "
        f"Collection size now: {count()} vectors."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Folder to recursively ingest")
    parser.add_argument("--chunk-size", type=int, default=None)
    parser.add_argument("--overlap", type=int, default=None)
    args = parser.parse_args()
    ingest(args.path, args.chunk_size, args.overlap)
