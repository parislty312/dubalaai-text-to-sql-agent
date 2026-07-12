import json

from src.agent import (
    NaiveStrategy,
    ReActStrategy,
    SelfConsistencyStrategy,
    SingleCallRepairStrategy,
    make_strategy,
)
from tests.fakes import FakeLLMClient


def _sql(sql, confidence="medium"):
    return json.dumps({"action": "sql", "sql": sql, "confidence": confidence})


def test_majority_vote_wins(adapter):
    client = FakeLLMClient(
        [
            _sql("SELECT COUNT(*) FROM Artist"),
            _sql("SELECT 1"),
            _sql("SELECT COUNT(*) AS c FROM Artist"),
        ]
    )
    strategy = SelfConsistencyStrategy(client, adapter, "CARD", n=3)
    turn = strategy.run("how many artists", [])
    assert turn.action == "sql"
    assert turn.result.rows[0][0] == 275
    assert turn.stats.llm_calls == 3
    assert client.calls[0]["temperature"] > 0


def test_failed_candidates_are_excluded(adapter):
    client = FakeLLMClient(
        [
            _sql("SELECT Nme FROM Artist"),
            _sql("SELECT COUNT(*) FROM Artist"),
            _sql("SELECT Nme FROM Artist"),
        ]
    )
    turn = SelfConsistencyStrategy(client, adapter, "CARD", n=3).run("q", [])
    assert turn.action == "sql"
    assert turn.result.rows[0][0] == 275


def test_all_failed_is_error(adapter):
    bad = _sql("SELECT Nme FROM Artist")
    turn = SelfConsistencyStrategy(
        FakeLLMClient([bad, bad, bad]),
        adapter,
        "CARD",
        n=3,
    ).run("q", [])
    assert turn.action == "error"


def test_factory():
    classes = {
        "naive": NaiveStrategy,
        "single": SingleCallRepairStrategy,
        "react": ReActStrategy,
        "sc": SelfConsistencyStrategy,
    }
    for name, cls in classes.items():
        strategy = make_strategy(name, FakeLLMClient([]), None, "CARD")
        assert isinstance(strategy, cls)
        assert strategy.name == name
