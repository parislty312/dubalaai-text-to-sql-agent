"""Performance measurement: latency distribution and cost projection.

Run with:
    python -m src.perf                          # 3 passes over the dev questions
    python -m src.perf --runs 5 --sleep 7
    python -m src.perf --model gpt-oss-120b --strategy single

Latency is end-to-end wall time per question (generation + validation +
execution + any repair rounds) — the same definition as the customer's
7s-current / 3s-target numbers.

Cost projects the customer's stated load (1,000 users x 30 queries/day =
30,000 queries/day) from the measured average token counts, priced per
registry model so the comparison isolates price-per-token.
"""
import argparse
import json
import statistics
import time
from pathlib import Path

from .agent import Session, make_strategy
from .config import DEFAULT_MODEL, MODEL_REGISTRY, get_model
from .context import build_schema_card
from .db import SQLiteAdapter
from .evals import load_questions, percentile
from .providers import LLMClient

QUERIES_PER_DAY = 30_000  # 1,000 users x 30 queries/day (customer's projection)


def project_cost(model_id: str, avg_in: float, avg_out: float) -> dict:
    spec = MODEL_REGISTRY[model_id]
    per_query = (avg_in * spec.input_price + avg_out * spec.output_price) / 1e6
    return {
        "model": model_id,
        "per_query_usd": round(per_query, 6),
        "per_day_usd": round(per_query * QUERIES_PER_DAY, 2),
        "per_month_usd": round(per_query * QUERIES_PER_DAY * 30, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODEL_REGISTRY))
    parser.add_argument("--strategy", default="single")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--db", default="data/personal_finance.db")
    parser.add_argument("--questions", default="data/finance_questions.json")
    parser.add_argument(
        "--sleep",
        type=float,
        default=6.0,
        help="seconds between queries (free-tier rate limits)",
    )
    parser.add_argument("--out", default=None, help="JSON report path")
    args = parser.parse_args()

    adapter = SQLiteAdapter(args.db)
    schema_card = build_schema_card(adapter)
    client = LLMClient(get_model(args.model))
    questions = [q["question"] for q in load_questions([args.questions])]

    walls, llm_lats, tokens_in, tokens_out = [], [], [], []
    failures = 0
    for run in range(args.runs):
        for question in questions:
            # Fresh session per question: latency must not benefit from history.
            session = Session(
                make_strategy(args.strategy, client, adapter, schema_card)
            )
            turn = session.ask(question)
            walls.append(turn.wall_s)
            llm_lats.append(turn.stats.llm_latency_s)
            tokens_in.append(turn.stats.input_tokens)
            tokens_out.append(turn.stats.output_tokens)
            failures += turn.action not in ("sql", "clarify")
            time.sleep(args.sleep)
        print(f"run {run + 1}/{args.runs} done")

    walls.sort()
    avg_in = statistics.mean(tokens_in)
    avg_out = statistics.mean(tokens_out)

    print(f"\n=== LATENCY ({len(walls)} queries, {args.model}/{args.strategy}) ===")
    print(
        f"P50: {percentile(walls, 0.50):.2f}s   P90: {percentile(walls, 0.90):.2f}s   "
        f"P95: {percentile(walls, 0.95):.2f}s   max: {walls[-1]:.2f}s"
    )
    print(f"mean LLM time: {statistics.mean(llm_lats):.2f}s   failures: {failures}")
    print(f"avg tokens/query: {avg_in:.0f} in / {avg_out:.0f} out")

    print(f"\n=== COST PROJECTION ({QUERIES_PER_DAY:,} queries/day) ===")
    projections = [project_cost(m, avg_in, avg_out) for m in MODEL_REGISTRY]
    print(f"{'model':<22} {'$/query':>10} {'$/day':>10} {'$/month':>10}")
    for row in projections:
        print(
            f"{row['model']:<22} {row['per_query_usd']:>10.6f} "
            f"{row['per_day_usd']:>10.2f} {row['per_month_usd']:>10.2f}"
        )
    print(
        "\nNote: all rows use this run's measured token counts, so the table "
        "isolates price-per-token across models."
    )

    out_path = args.out or f"results/perf_{args.model}_{args.strategy}.json"
    report = {
        "model": args.model,
        "strategy": args.strategy,
        "n_queries": len(walls),
        "p50_s": round(percentile(walls, 0.50), 3),
        "p90_s": round(percentile(walls, 0.90), 3),
        "p95_s": round(percentile(walls, 0.95), 3),
        "max_s": round(walls[-1], 3),
        "failures": failures,
        "avg_tokens_in": round(avg_in),
        "avg_tokens_out": round(avg_out),
        "cost_projection": projections,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
