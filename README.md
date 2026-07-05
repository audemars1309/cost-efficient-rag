# Cost-Efficient RAG App

QA service over a document corpus using ChromaDB instead of a managed
vector DB, to avoid always-on infra costs on a lightly-queried corpus.

## Stack

- ChromaDB (embedded, no server, has upsert + metadata filtering built in)
- Local sentence-transformers embeddings (384-dim, free)
- Configurable LLM (Anthropic/OpenAI) for generation

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY
python -m src.ingest --path ./data/sample_docs
uvicorn src.app:app --reload --port 8000
```

Query:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy for the Pro plan?", "top_k": 5}'
```

Eval:
```bash
python -m eval.run_eval --top-k 5 --out eval/results.json
python -m eval.cost_model
```

## Cost comparison (100K / 1M / 10M vectors)

Vectors | Self-hosted | Pinecone | Savings
100,000 |    $12/mo   |  $50/mo  | 76%
1,000,000 |    $12/mo   |  $50/mo  | 76%
10,000,000 |    $48/mo   |  $50/mo  | 4%

Pinecone's $50/mo minimum is what makes self-hosting win at low/mid scale —
gap closes at real scale (10M+), which is when managed starts making sense.

## Known limits

- No-hallucination check = distance threshold (0.85), not a real classifier
- Changing CHUNK_SIZE/OVERLAP orphans old vector IDs, needs a full re-index
