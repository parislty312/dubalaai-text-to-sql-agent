from src.config import get_model
from src.providers import Usage, build_response_format, cost_usd


SCHEMA = {"type": "object", "properties": {"a": {"type": "string"}}}


def test_response_format_openai():
    rf = build_response_format("openai", SCHEMA)
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["schema"] == SCHEMA


def test_response_format_fireworks():
    rf = build_response_format("fireworks", SCHEMA)
    assert rf == {"type": "json_object", "schema": SCHEMA}


def test_cost_usd():
    spec = get_model("qwen3p7-plus")
    usage = Usage(input_tokens=1_000_000, output_tokens=100_000)
    assert abs(cost_usd(spec, usage) - (0.50 + 0.30)) < 1e-9
