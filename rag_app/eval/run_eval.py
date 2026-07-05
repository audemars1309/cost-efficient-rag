# runs the questions in questions.json through the pipeline and computes
# retrieval metrics (recall@k, mrr, ndcg, context precision - based on
# whether the retrieved chunk's source doc matches the gold source doc)
# and answer metrics (llm judge for faithfulness/relevance, f1/em vs gold answer)
# usage: python -m eval.run_eval --top-k 5 --out eval/results.json
import argparse
import json
import math
import re
import statistics
import time
from pathlib import Path

from src.embeddings import embed_query
from src.vectorstore import query as vs_query
from src.llm import complete
from src.config import CFG

SYSTEM_PROMPT = (
    "Answer using only the context given below. Cite the chunk you used "
    "like [chunk:0]. If the context doesn't have the answer, just say "
    "'I don't have enough context to answer that.' Don't make anything up."
)

JUDGE_SYSTEM_PROMPT = (
    "Score this answer on two things, 0 to 1:\n"
    "faithfulness - is everything in the answer actually backed by the context?\n"
    "relevance - does it answer the question?\n"
    "Reply with just JSON: {\"faithfulness\": <float>, \"relevance\": <float>, "
    "\"rationale\": \"<one line>\"}"
)


def _normalize(s: str) -> list[str]:
    return re.findall(r"\w+", s.lower())


def f1_em(pred: str, gold: str):
    pred_tokens = _normalize(pred)
    gold_tokens = _normalize(gold)
    # loose EM - just checking if gold answer is a substring, since these
    # aren't extractive spans
    em = 1.0 if gold.lower() in pred.lower() else 0.0
    common = set(pred_tokens) & set(gold_tokens)
    if not pred_tokens or not gold_tokens:
        return 0.0, em
    if not common:
        return 0.0, em
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gold_tokens)
    f1 = 2 * precision * recall / (precision + recall)
    return f1, em


def retrieve(question: str, top_k: int):
    emb = embed_query(question)
    res = vs_query(emb, top_k=top_k)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    distances = res["distances"][0]
    return docs, metas, distances


def generate_answer(question: str, docs, metas, distances):
    if not docs or min(distances) > CFG.no_context_distance_threshold:
        return "I don't have enough context to answer that.", {"input_tokens": 0, "output_tokens": 0}
    context_block = "\n\n".join(
        f"[chunk:{i}] (source: {m['source']})\n{d}" for i, (d, m) in enumerate(zip(docs, metas))
    )
    return complete(SYSTEM_PROMPT, f"Context:\n{context_block}\n\nQuestion: {question}")


def judge_answer(question: str, docs, answer: str):
    context_block = "\n\n".join(docs) if docs else "(no context retrieved)"
    prompt = f"Question: {question}\n\nContext:\n{context_block}\n\nAnswer:\n{answer}"
    raw, _ = complete(JUDGE_SYSTEM_PROMPT, prompt, max_tokens=200)
    try:
        parsed = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        return float(parsed.get("faithfulness", 0)), float(parsed.get("relevance", 0))
    except Exception:
        return None, None  # malformed judge output -- surfaced as null, not silently zeroed


def dcg(relevances):
    return sum(r / math.log2(i + 2) for i, r in enumerate(relevances))


def ndcg_at_k(relevances):
    ideal = sorted(relevances, reverse=True)
    idcg = dcg(ideal)
    return dcg(relevances) / idcg if idcg > 0 else 0.0


def run(top_k: int, out_path: str):
    questions = json.loads(Path("eval/questions.json").read_text())
    per_case = []
    latencies = []

    for q in questions:
        t0 = time.time()
        docs, metas, distances = retrieve(q["question"], top_k)
        answer, usage = generate_answer(q["question"], docs, metas, distances)
        latency_ms = (time.time() - t0) * 1000
        latencies.append(latency_ms)

        sources_hit = [m["source"] for m in metas]
        gold = q.get("gold_source")
        relevances = [1 if s == gold else 0 for s in sources_hit] if gold else []

        recall_at_k = 1.0 if gold and gold in sources_hit else (1.0 if not gold and not docs else (0.0 if gold else None))
        rr = 0.0
        if gold:
            for rank, s in enumerate(sources_hit, start=1):
                if s == gold:
                    rr = 1.0 / rank
                    break
        ndcg = ndcg_at_k(relevances) if relevances else None
        context_precision = (sum(relevances) / len(relevances)) if relevances else None

        faithfulness, relevance = judge_answer(q["question"], docs, answer)

        f1 = em = None
        if q.get("gold_answer"):
            f1, em = f1_em(answer, q["gold_answer"])

        no_context_expected = q.get("expect_no_context", False)
        correctly_refused = (
            no_context_expected and answer.strip() == "I don't have enough context to answer that."
        ) if no_context_expected else None

        per_case.append({
            "id": q["id"],
            "question": q["question"],
            "answer": answer,
            "sources_hit": sources_hit,
            "gold_source": gold,
            "recall_at_k": recall_at_k,
            "mrr": rr if gold else None,
            "ndcg_at_k": ndcg,
            "context_precision": context_precision,
            "faithfulness": faithfulness,
            "relevance": relevance,
            "f1": f1,
            "em": em,
            "correctly_refused_no_context": correctly_refused,
            "latency_ms": round(latency_ms, 1),
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
        })
        print(f"  [{q['id']}] {latency_ms:6.0f} ms  recall={recall_at_k}  faithfulness={faithfulness}")

    def _avg(key, filt=None):
        vals = [c[key] for c in per_case if c[key] is not None and (filt is None or filt(c))]
        return round(statistics.mean(vals), 3) if vals else None

    grounded_cases = [c for c in per_case if not q.get("expect_no_context")]
    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[len(latencies_sorted) // 2]
    p95 = latencies_sorted[min(len(latencies_sorted) - 1, int(len(latencies_sorted) * 0.95))]

    summary = {
        "n_questions": len(questions),
        "top_k": top_k,
        "recall_at_k": _avg("recall_at_k"),
        "mrr": _avg("mrr"),
        "ndcg_at_k": _avg("ndcg_at_k"),
        "context_precision": _avg("context_precision"),
        "faithfulness_mean": _avg("faithfulness"),
        "relevance_mean": _avg("relevance"),
        "f1_mean": _avg("f1"),
        "em_mean": _avg("em"),
        "no_context_refusal_accuracy": _avg("correctly_refused_no_context"),
        "latency_p50_ms": round(p50, 1),
        "latency_p95_ms": round(p95, 1),
        "total_input_tokens": sum(c["input_tokens"] for c in per_case),
        "total_output_tokens": sum(c["output_tokens"] for c in per_case),
    }

    result = {"summary": summary, "per_case": per_case}
    Path(out_path).write_text(json.dumps(result, indent=2))
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"\nFull results written to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out", default="eval/results.json")
    args = parser.parse_args()
    run(args.top_k, args.out)
