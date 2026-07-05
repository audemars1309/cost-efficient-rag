# run with: uvicorn src.app:app --reload --port 8000
# POST /query with {"question": "...", "top_k": 5}
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from src.config import CFG
from src.embeddings import embed_query
from src.vectorstore import query as vs_query
from src.llm import complete

app = FastAPI(title="Cost-Efficient RAG Service")

SYSTEM_PROMPT = (
    "Answer using only the context given below. Cite the chunk you used "
    "like [chunk:0]. If the context doesn't have the answer, just say "
    "'I don't have enough context to answer that.' Don't make anything up."
)


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None
    filter: dict | None = None


def _log(entry: dict):
    Path(CFG.log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(CFG.log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


@app.post("/query")
def query_endpoint(req: QueryRequest):
    t0 = time.time()
    top_k = req.top_k or CFG.default_top_k

    q_embedding = embed_query(req.question)
    results = vs_query(q_embedding, top_k=top_k, where=req.filter)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieval_ms = (time.time() - t0) * 1000

    # if the closest chunk is too far off, don't bother calling the llm
    if not docs or min(distances) > CFG.no_context_distance_threshold:
        answer = "I don't have enough context to answer that."
        usage = {"input_tokens": 0, "output_tokens": 0}
        gen_ms = 0.0
    else:
        context_block = "\n\n".join(
            f"[chunk:{i}] (source: {m['source']})\n{d}"
            for i, (d, m) in enumerate(zip(docs, metas))
        )
        user_prompt = f"Context:\n{context_block}\n\nQuestion: {req.question}"
        t1 = time.time()
        answer, usage = complete(SYSTEM_PROMPT, user_prompt)
        gen_ms = (time.time() - t1) * 1000

    total_ms = (time.time() - t0) * 1000

    log_entry = {
        "timestamp": time.time(),
        "question": req.question,
        "top_k": top_k,
        "chunk_count": len(docs),
        "distances": distances,
        "retrieval_ms": round(retrieval_ms, 2),
        "generation_ms": round(gen_ms, 2),
        "total_ms": round(total_ms, 2),
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "llm_model": CFG.llm_model,
    }
    _log(log_entry)

    return {
        "answer": answer,
        "citations": [
            {"chunk_ref": f"chunk:{i}", "source": m["source"], "distance": distances[i]}
            for i, m in enumerate(metas)
        ],
        "latency_ms": round(total_ms, 2),
        "chunk_count": len(docs),
        "tokens": usage,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
