"""Offline execution-accuracy eval harness for text-to-SQL."""
import argparse
import json
import math
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .agent import Session, _result_digest, make_strategy, summarize_result
from .config import DEFAULT_MODEL, MODEL_REGISTRY, get_model
from .context import build_schema_card
from .db import QueryError, SQLiteAdapter
from .providers import LLMClient


def _norm(value: Any):
    if isinstance(value, float):
        return round(value, 2)
    if isinstance(value, str):
        return value.strip()
    return value


def multiset_equal(rows_a, rows_b) -> bool:
    """Order-insensitive row multiset match; column names are intentionally ignored."""
    left = Counter(tuple(_norm(value) for value in row) for row in rows_a)
    right = Counter(tuple(_norm(value) for value in row) for row in rows_b)
    return left == right


def load_questions(paths: list[str]) -> list[dict]:
    questions = []
    for path in paths:
        questions.extend(json.loads(Path(path).read_text()))
    return questions


def evaluate_question(question: dict, strategy, adapter: SQLiteAdapter) -> dict:
    session = Session(strategy)
    turn = session.ask(question["question"])
    mode = question.get("evaluation", "sql_result_match")
    correct = False
    miscalibrated_clarify = False

    if mode == "action_match":
        correct = turn.action == question["expected_action"]
    elif turn.action == "sql" and turn.result is not None:
        try:
            gold = adapter.execute(question["gold_sql"])
            correct = multiset_equal(gold.rows, turn.result.rows)
        except QueryError:
            correct = False
    elif turn.action in ("clarify", "decline"):
        miscalibrated_clarify = True

    record = {
        "id": question["id"],
        "tier": question.get("tier"),
        "mode": mode,
        "question": question["question"],
        "action": turn.action,
        "sql": turn.sql,
        "correct": bool(correct),
        "miscalibrated_clarify": bool(miscalibrated_clarify),
        "attempts": turn.attempts,
        "confidence": turn.confidence,
        "tables": turn.tables,
        "llm_calls": turn.stats.llm_calls,
        "input_tokens": turn.stats.input_tokens,
        "output_tokens": turn.stats.output_tokens,
        "cost_usd": turn.stats.cost_usd,
        "llm_latency_s": turn.stats.llm_latency_s,
        "wall_s": turn.wall_s,
        "error": turn.message if turn.action == "error" else None,
        "result_digest": _result_digest(turn.result) if turn.result else None,
        "turn": turn,
    }
    return record


def percentile(sorted_values: list[float], p: float) -> float:
    """Nearest-rank percentile on an ascending-sorted list."""
    if not sorted_values:
        return 0.0
    return sorted_values[max(0, math.ceil(p * len(sorted_values)) - 1)]


def summarize_records(records: list[dict]) -> dict:
    n = len(records)
    sql_records = [r for r in records if r["mode"] == "sql_result_match"]
    walls = sorted(r["wall_s"] for r in records)

    def avg(values):
        values = list(values)
        return sum(values) / len(values) if values else 0.0

    return {
        "n": n,
        "execution_accuracy": avg(r["correct"] for r in sql_records),
        "overall_accuracy": avg(r["correct"] for r in records),
        "valid_sql_rate": avg(r["action"] == "sql" for r in sql_records),
        "repair_rate": avg(r["attempts"] > 1 for r in records),
        "miscalibrated_clarify_rate": avg(
            r["miscalibrated_clarify"] for r in records
        ),
        "p50_latency_s": statistics.median(walls) if walls else 0.0,
        "p95_latency_s": percentile(walls, 0.95),
        "avg_cost_usd": avg(r["cost_usd"] for r in records),
        "total_cost_usd": sum(r["cost_usd"] for r in records),
        "avg_llm_calls": avg(r["llm_calls"] for r in records),
        "avg_input_tokens": avg(r["input_tokens"] for r in records),
        "avg_output_tokens": avg(r["output_tokens"] for r in records),
    }


def run_eval(
    strategy,
    adapter: SQLiteAdapter,
    question_paths: list[str],
    limit: int | None = None,
    sleep_s: float = 0.0,
) -> dict:
    questions = load_questions(question_paths)
    if limit is not None:
        questions = questions[:limit]
    records = []
    for i, question in enumerate(questions):
        if i and sleep_s:
            time.sleep(sleep_s)  # pace requests for tight serverless rate limits
        records.append(evaluate_question(question, strategy, adapter))
    return {"records": records, "summary": summarize_records(records)}


def serializable_report(report: dict) -> dict:
    records = []
    for record in report["records"]:
        clean = dict(record)
        clean.pop("turn", None)
        records.append(clean)
    return {"summary": report["summary"], "records": records}


def write_markdown_report(report: dict, path: str, meta: dict | None = None) -> None:
    meta = meta or {}
    summary = report["summary"]
    lines = [
        "# Text-to-SQL Evaluation Report",
        "",
        f"- Model: `{meta.get('model', 'unknown')}`",
        f"- Strategy: `{meta.get('strategy', 'unknown')}`",
        f"- Questions: `{', '.join(meta.get('questions', []))}`",
        f"- Timestamp: `{meta.get('timestamp', '')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in summary.items():
        rendered = f"{value:.6f}" if isinstance(value, float) else str(value)
        lines.append(f"| {key} | {rendered} |")

    lines.extend(
        [
            "",
            "## Per-Question Results",
            "",
            "| ID | Correct | Action | Attempts | Latency (s) | SQL |",
            "|---|---:|---|---:|---:|---|",
        ]
    )
    for record in report["records"]:
        sql = (record.get("sql") or "").replace("|", "\\|").replace("\n", " ")
        if len(sql) > 140:
            sql = sql[:137] + "..."
        lines.append(
            "| {id} | {correct} | {action} | {attempts} | {wall:.3f} | `{sql}` |".format(
                id=record["id"],
                correct="yes" if record["correct"] else "no",
                action=record["action"],
                attempts=record["attempts"],
                wall=record["wall_s"],
                sql=sql,
            )
        )

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")


def result_answer_text(turn) -> str:
    if not turn.result:
        return turn.message or "No answer."
    if not turn.result.rows:
        return "No rows returned."
    preview = []
    for row in turn.result.rows[:10]:
        if len(row) == 1:
            preview.append(str(row[0]))
        else:
            preview.append(", ".join(str(value) for value in row))
    suffix = "" if turn.result.row_count <= 10 else f" ... ({turn.result.row_count} rows)"
    return "; ".join(preview) + suffix


def write_answers(report: dict, path: str, client=None) -> None:
    answers = {}
    for record in report["records"]:
        if not record["id"].startswith("q_"):
            continue
        turn = record["turn"]
        if client is not None and turn.action == "sql" and turn.result is not None:
            answer = summarize_result(client, record["question"], turn.result)
        else:
            answer = result_answer_text(turn)
        answers[record["id"]] = {"sql": turn.sql or "", "answer": answer}

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(answers, indent=2, default=str) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run offline text-to-SQL eval")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODEL_REGISTRY))
    parser.add_argument(
        "--strategy",
        default="single",
        choices=["naive", "single", "react", "sc"],
    )
    parser.add_argument(
        "--questions",
        nargs="+",
        default=["data/finance_questions_with_answers.json"],
    )
    parser.add_argument("--db", default="data/personal_finance.db")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="seconds to pause between questions (free-tier rate limits)",
    )
    parser.add_argument("--out", default="results/eval_report.json")
    parser.add_argument("--markdown", default="results/eval_report.md")
    parser.add_argument("--write-answers", default=None)
    parser.add_argument(
        "--llm-answer-summary",
        action="store_true",
        help="use an extra LLM call per answer when writing the answers JSON",
    )
    args = parser.parse_args()

    adapter = SQLiteAdapter(args.db)
    client = LLMClient(get_model(args.model))
    strategy = make_strategy(
        args.strategy,
        client,
        adapter,
        build_schema_card(adapter),
        row_cap=None,
    )
    report = run_eval(
        strategy, adapter, args.questions, limit=args.limit, sleep_s=args.sleep
    )

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    meta = {
        "model": args.model,
        "strategy": args.strategy,
        "questions": args.questions,
        "timestamp": timestamp,
    }

    output = {"meta": meta, **serializable_report(report)}
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(output, indent=2, default=str) + "\n")
    if args.markdown:
        write_markdown_report(serializable_report(report), args.markdown, meta=meta)
    if args.write_answers:
        answer_client = client if args.llm_answer_summary else None
        write_answers(report, args.write_answers, client=answer_client)

    print(f"\n== {args.model} / {args.strategy} ==")
    for key, value in report["summary"].items():
        print(f"{key}: {value:.6f}" if isinstance(value, float) else f"{key}: {value}")
    if args.out:
        print(f"wrote {args.out}")
    if args.markdown:
        print(f"wrote {args.markdown}")
    if args.write_answers:
        print(f"wrote {args.write_answers}")


if __name__ == "__main__":
    main()
