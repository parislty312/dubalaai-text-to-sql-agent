import json

from src.agent import SingleCallRepairStrategy
from src.evals import evaluate_question, percentile, run_eval, serializable_report
from tests.fakes import FakeLLMClient


def test_percentile_nearest_rank():
    walls = [1.0, 1.5, 2.0, 2.5, 9.0]
    assert percentile(walls, 0.95) == 9.0  # regression: used to return 2.5
    assert percentile(walls, 0.50) == 2.0
    assert percentile([4.2], 0.95) == 4.2
    assert percentile([], 0.95) == 0.0
    assert percentile([1.0, 9.0], 0.95) == 9.0


Q_MATCH = {
    "id": "t1",
    "question": "How many artists are there?",
    "tier": 1,
    "gold_sql": "SELECT COUNT(*) FROM Artist",
    "evaluation": "sql_result_match",
}
Q_DECLINE = {
    "id": "t2",
    "question": "What's the weather?",
    "tier": 1,
    "evaluation": "action_match",
    "expected_action": "decline",
}


def _sql(sql):
    return json.dumps({"action": "sql", "sql": sql, "confidence": "high"})


def _strategy(adapter, responses):
    return SingleCallRepairStrategy(FakeLLMClient(responses), adapter, "CARD")


def test_correct_answer_scores(adapter):
    strategy = _strategy(adapter, [_sql("SELECT COUNT(ArtistId) FROM Artist")])
    record = evaluate_question(Q_MATCH, strategy, adapter)
    assert record["correct"] is True
    assert record["action"] == "sql"


def test_wrong_answer_fails(adapter):
    strategy = _strategy(adapter, [_sql("SELECT COUNT(*) FROM Album")])
    record = evaluate_question(Q_MATCH, strategy, adapter)
    assert record["correct"] is False


def test_clarify_on_answerable_counts_as_failure(adapter):
    strategy = _strategy(
        adapter,
        [
            json.dumps(
                {
                    "action": "clarify",
                    "clarification": "which?",
                    "confidence": "low",
                }
            )
        ],
    )
    record = evaluate_question(Q_MATCH, strategy, adapter)
    assert record["correct"] is False
    assert record["miscalibrated_clarify"] is True


def test_action_match_mode(adapter):
    strategy = _strategy(adapter, [json.dumps({"action": "decline", "confidence": "high"})])
    record = evaluate_question(Q_DECLINE, strategy, adapter)
    assert record["correct"] is True


def test_run_eval_summary(adapter, tmp_path):
    qfile = tmp_path / "questions.json"
    qfile.write_text(json.dumps([Q_MATCH, Q_DECLINE]))
    strategy = _strategy(
        adapter,
        [_sql("SELECT COUNT(*) FROM Artist"), json.dumps({"action": "decline", "confidence": "high"})],
    )
    report = run_eval(strategy, adapter, [str(qfile)])
    assert report["summary"]["n"] == 2
    assert report["summary"]["execution_accuracy"] == 1.0
    assert report["summary"]["valid_sql_rate"] == 1.0
    assert "turn" not in serializable_report(report)["records"][0]
