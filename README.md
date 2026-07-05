Cost-Efficient RAG App
QA service over a document corpus, using ChromaDB instead of a managed vector DB (Pinecone etc) to avoid paying for always-on infra when the corpus isn't queried that often.

Why Chroma
It's embedded - no separate DB server to run, no docker-compose. Has metadata filtering and upsert built in, which the assignment needed anyway. Downside: doesn't scale/shard the way Qdrant or pgvector can at really large sizes, so this wouldn't be the pick past maybe 10M+ vectors.

How it works
PDF/HTML/MD -> loaders.py -> chunking.py (800 char chunks, 120 overlap)
            -> embeddings.py (local sentence-transformers, 384-dim, free)
            -> vectorstore.py (chroma upsert, id = hash of source+index+text)

query -> embed -> chroma top-k -> if best match too far, say "no context"
      -> else build context block -> call llm -> answer + citations
      -> log latency/tokens to logs/query_log.jsonl
Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# add your ANTHROPIC_API_KEY (or OPENAI_API_KEY + set LLM_PROVIDER=openai)
Ingest the sample docs (fictional product "Nimbus Cloud Storage" so the eval questions have real gold answers to check against):

python -m src.ingest --path ./data/sample_docs
Run the server:

uvicorn src.app:app --reload --port 8000

curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy for the Pro plan?", "top_k": 5}'
Run the eval:

python -m eval.run_eval --top-k 5 --out eval/results.json
python -m eval.cost_model
Cost model output
This part doesn't call an LLM so it's real, reproducible right now:

   Vectors |  Self-hosted ($/mo) |  Pinecone ($/mo) | Savings
-----------------------------------------------------------------
   100,000 |               12.00 |            50.00 | $38.00 (76%)
 1,000,000 |               12.00 |            50.00 | $38.00 (76%)
10,000,000 |               48.00 |            50.00 | $2.00 (4%)
Assumptions (see eval/cost_model.py for the full list): Pinecone Standard $50/mo minimum + usage pricing checked July 2026, self-hosted is just a small VM cost. Basically the $50 minimum is what makes self-hosting look good at low/mid scale - the gap closes once you're at real scale (10M+ vectors), which is when switching back to managed starts to make sense.

Notes / limitations
Chunk size 800/overlap 120 - tried a few values on the sample docs, this gave decent results. Smaller chunks lost context, bigger ones sometimes mixed unrelated info together.
No-hallucination check is just a distance threshold (0.85) on the closest retrieved chunk - if nothing's close enough, it skips the LLM call entirely and returns a fixed refusal.
If you change CHUNK_SIZE/OVERLAP and re-ingest, old chunk IDs won't match the new ones and become orphans in the DB. Would need a full wipe if you change chunking params.
Real eval numbers (retrieval/answer scores, actual latency) need to come from an actual run with your API key - didn't fake these, run eval/run_eval.py yourself and use eval/results.json.
