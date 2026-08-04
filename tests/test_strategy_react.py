import json

from src.agent import ReActStrategy
from src.providers import LLMResponse, Usage
from tests.fakes import FakeLLMClient, tool_call


def _tool_resp(sql):
    return LLMResponse(
        content=None,
        tool_calls=[tool_call("run_sql", json.dumps({"sql": sql}))],
        usage=Usage(100, 20),
        latency_s=0.01,
    )


def test_react_explores_then_answers(adapter):
    client = FakeLLMClient(
        [
            _tool_resp("SELECT name FROM categories LIMIT 3"),
            json.dumps(
                {
                    "action": "sql",
                    "sql": "SELECT COUNT(*) FROM transactions",
                    "confidence": "high",
                }
            ),
        ]
    )
    turn = ReActStrategy(client, adapter, "CARD").run("how many transactions?", [])
    assert turn.action == "sql"
    assert turn.result.rows[0][0] == 40
    assert turn.stats.llm_calls == 2
    roles = [message["role"] for message in client.calls[1]["messages"]]
    assert "tool" in roles


def test_react_tool_error_is_fed_back(adapter):
    client = FakeLLMClient(
        [
            _tool_resp("SELECT nme FROM categories"),
            json.dumps(
                {
                    "action": "sql",
                    "sql": "SELECT name FROM categories LIMIT 1",
                    "confidence": "medium",
                }
            ),
        ]
    )
    turn = ReActStrategy(client, adapter, "CARD").run("q", [])
    assert turn.action == "sql"
    tool_message = [m for m in client.calls[1]["messages"] if m["role"] == "tool"][0]
    assert "no such column" in tool_message["content"]


def test_react_iteration_cap(adapter):
    responses = [_tool_resp("SELECT 1") for _ in range(8)]
    client = FakeLLMClient(responses)
    turn = ReActStrategy(client, adapter, "CARD", max_iters=3).run("q", [])
    assert turn.action == "error"
    assert turn.stats.llm_calls == 3
