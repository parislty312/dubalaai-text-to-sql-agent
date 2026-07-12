import json

from src.agent import build_system_prompt, extract_sql, parse_response


def test_parse_clean_json():
    data = parse_response(
        json.dumps({"action": "sql", "sql": "SELECT 1", "confidence": "high"})
    )
    assert data["action"] == "sql"
    assert data["sql"] == "SELECT 1"


def test_parse_json_inside_prose():
    data = parse_response(
        'Sure! {"action": "sql", "sql": "SELECT 1", "confidence": "low"} done'
    )
    assert data["action"] == "sql"


def test_parse_infers_sql_action_when_missing():
    data = parse_response('{"sql": "SELECT 1"}')
    assert data["action"] == "sql"
    assert data["confidence"] == "medium"


def test_parse_garbage_is_error():
    assert parse_response("no json here")["action"] == "error"


def test_extract_sql_strips_fences():
    assert extract_sql("```sql\nSELECT 1\n```") == "SELECT 1"
    assert extract_sql("SELECT 2") == "SELECT 2"


def test_system_prompt_contains_card_date_and_rules():
    prompt = build_system_prompt("MY_SCHEMA_CARD", today="2026-06-12")
    assert "MY_SCHEMA_CARD" in prompt
    assert "2026-06-12" in prompt
    assert "Never invent" in prompt
    assert "single" in prompt.lower()
