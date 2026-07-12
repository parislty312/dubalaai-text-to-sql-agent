from src.config import get_model
from src.providers import Usage, build_response_format, cost_usd


SCHEMA = {"type": "object", "properties": {"a": {"type": "string"}}}


def test_response_format_openai():
    rf = build_response_format("openai", SCHEMA)
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["schema"] == SCHEMA


def test_response_format_dubalaai():
    rf = build_response_format("dubalaai", SCHEMA)
    assert rf == {"type": "json_object", "schema": SCHEMA}


def test_cost_usd():
    spec = get_model("gpt-5.4")
    usage = Usage(input_tokens=1_000_000, output_tokens=100_000)
    assert abs(cost_usd(spec, usage) - (2.50 + 1.50)) < 1e-9
