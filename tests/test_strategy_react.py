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
            _tool_resp("SELECT Name FROM Artist LIMIT 3"),
            json.dumps(
                {
                    "action": "sql",
                    "sql": "SELECT COUNT(*) FROM Artist",
                    "confidence": "high",
                }
            ),
        ]
    )
    turn = ReActStrategy(client, adapter, "CARD").run("how many artists?", [])
    assert turn.action == "sql"
    assert turn.result.rows[0][0] == 275
    assert turn.stats.llm_calls == 2
    roles = [message["role"] for message in client.calls[1]["messages"]]
    assert "tool" in roles


def test_react_tool_error_is_fed_back(adapter):
    client = FakeLLMClient(
        [
            _tool_resp("SELECT Nme FROM Artist"),
            json.dumps(
                {
                    "action": "sql",
                    "sql": "SELECT Name FROM Artist LIMIT 1",
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
