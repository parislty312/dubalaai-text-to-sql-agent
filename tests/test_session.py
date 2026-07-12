import json

from src.agent import NaiveStrategy, Session, SingleCallRepairStrategy, summarize_result
from src.db import ExecResult
from tests.fakes import FakeLLMClient


def test_session_threads_history(adapter):
    client = FakeLLMClient(
        [
            json.dumps(
                {
                    "action": "sql",
                    "sql": "SELECT Name FROM Artist LIMIT 1",
                    "confidence": "high",
                }
            ),
            json.dumps(
                {
                    "action": "sql",
                    "sql": "SELECT Title FROM Album LIMIT 1",
                    "confidence": "high",
                }
            ),
        ]
    )
    session = Session(SingleCallRepairStrategy(client, adapter, "CARD"))
    t1 = session.ask("first question")
    t2 = session.ask("follow-up")
    assert t1.action == "sql"
    assert t2.action == "sql"
    second_call = client.calls[1]["messages"]
    joined = json.dumps(second_call)
    assert "first question" in joined
    assert "result preview" in joined
    assert t2.wall_s > 0


def test_naive_strategy_no_schema_no_repair(adapter):
    client = FakeLLMClient(["```sql\nSELECT Name FROM Artist LIMIT 1\n```"])
    strategy = NaiveStrategy(client, adapter, "CARD_IGNORED")
    turn = strategy.run("one artist", [])
    assert turn.action == "sql"
    assert turn.result.row_count == 1
    sent = client.calls[0]["messages"]
    assert len(sent) == 1
    assert sent[0]["role"] == "user"
    assert sent[0]["content"] == "Convert this question to SQL: one artist"


def test_naive_strategy_failure_is_error_not_repair(adapter):
    client = FakeLLMClient(["SELECT Nme FROM Artist"])
    turn = NaiveStrategy(client, adapter, "X").run("q", [])
    assert turn.action == "error"
    assert turn.stats.llm_calls == 1


def test_summarize_result():
    client = FakeLLMClient(["There are 275 artists."])
    result = ExecResult(columns=["n"], rows=[(275,)], truncated=False, elapsed_ms=1.0)
    summary = summarize_result(client, "How many artists?", result)
    assert summary == "There are 275 artists."
    assert "275" in client.calls[0]["messages"][0]["content"]
