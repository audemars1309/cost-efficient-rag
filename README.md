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
