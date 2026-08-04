import json

from src.agent import SingleCallRepairStrategy
from tests.fakes import FakeLLMClient


def _resp(**kwargs):
    return json.dumps(kwargs)


def make(adapter, responses):
    client = FakeLLMClient(responses)
    strategy = SingleCallRepairStrategy(client, adapter, "CARD", row_cap=200)
    return client, strategy


def test_happy_path_one_call(adapter):
    client, strategy = make(
        adapter,
        [_resp(action="sql", sql="SELECT name FROM categories LIMIT 2", confidence="high")],
    )
    turn = strategy.run("list two categories", [])
    assert turn.action == "sql"
    assert turn.result.row_count == 2
    assert turn.attempts == 1
    assert turn.stats.llm_calls == 1
    assert turn.tables == ["categories"]


def test_repair_after_exec_error(adapter):
    client, strategy = make(
        adapter,
        [
            _resp(action="sql", sql="SELECT nme FROM categories", confidence="high"),
            _resp(action="sql", sql="SELECT name FROM categories LIMIT 1", confidence="high"),
        ],
    )
    turn = strategy.run("category names", [])
    assert turn.action == "sql"
    assert turn.attempts == 2
    repair_message = client.calls[1]["messages"][-1]["content"]
    assert "no such column" in repair_message


def test_guardrail_rejection_triggers_repair(adapter):
    _client, strategy = make(
        adapter,
        [
            _resp(action="sql", sql="DROP TABLE categories", confidence="high"),
            _resp(action="sql", sql="SELECT name FROM categories LIMIT 1", confidence="high"),
        ],
    )
    turn = strategy.run("q", [])
    assert turn.action == "sql"
    assert turn.attempts == 2


def test_exhausted_repairs_returns_error(adapter):
    bad = _resp(action="sql", sql="SELECT nme FROM categories", confidence="low")
    _client, strategy = make(adapter, [bad, bad, bad])
    turn = strategy.run("q", [])
    assert turn.action == "error"
    assert turn.attempts == 3
    assert "no such column" in turn.message


def test_clarify_passes_through(adapter):
    _client, strategy = make(
        adapter,
        [_resp(action="clarify", clarification="Which year?", confidence="low")],
    )
    turn = strategy.run("how much revenue", [])
    assert turn.action == "clarify"
    assert turn.message == "Which year?"


def test_history_is_included(adapter):
    history = [
        {"role": "user", "content": "previous question"},
        {"role": "assistant", "content": "previous answer"},
    ]
    client, strategy = make(
        adapter,
        [_resp(action="sql", sql="SELECT 1", confidence="high")],
    )
    strategy.run("follow-up", history)
    sent = client.calls[0]["messages"]
    assert sent[0]["role"] == "system"
    assert sent[1]["content"] == "previous question"
    assert sent[-1]["content"] == "follow-up"
