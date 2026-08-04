from src.guardrails import validate_sql


def test_plain_select_passes():
    v = validate_sql("SELECT name FROM categories", row_cap=None)
    assert v.ok
    assert v.tables == ["categories"]


def test_cte_select_passes():
    v = validate_sql(
        "WITH t AS (SELECT category_id FROM transactions) SELECT COUNT(*) FROM t",
        row_cap=None,
    )
    assert v.ok


def test_union_passes():
    v = validate_sql(
        "SELECT name FROM categories UNION SELECT name FROM merchants",
        row_cap=None,
    )
    assert v.ok


def test_writes_rejected():
    for sql in [
        "INSERT INTO categories (name) VALUES ('x')",
        "UPDATE categories SET name='x'",
        "DELETE FROM categories",
        "DROP TABLE categories",
        "CREATE TABLE t (a int)",
    ]:
        v = validate_sql(sql, row_cap=None)
        assert not v.ok, sql


def test_pragma_rejected():
    assert not validate_sql("PRAGMA table_info(categories)", row_cap=None).ok


def test_multi_statement_rejected():
    v = validate_sql("SELECT 1; SELECT 2", row_cap=None)
    assert not v.ok
    assert "one" in v.reason.lower()


def test_garbage_rejected():
    assert not validate_sql("hello world", row_cap=None).ok


def test_limit_appended():
    v = validate_sql("SELECT name FROM categories", row_cap=200)
    assert v.ok
    assert "LIMIT 200" in v.sql


def test_existing_limit_preserved():
    v = validate_sql("SELECT name FROM categories LIMIT 5", row_cap=200)
    assert v.ok
    assert "LIMIT 5" in v.sql
    assert "200" not in v.sql


def test_tables_extracted_across_joins():
    v = validate_sql(
        "SELECT t.amount FROM transactions t JOIN categories c ON t.category_id = c.category_id",
        row_cap=None,
    )
    assert v.tables == ["categories", "transactions"]
