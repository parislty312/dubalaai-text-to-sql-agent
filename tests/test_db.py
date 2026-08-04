import pytest

from src.db import QueryError


def test_execute_select(adapter):
    res = adapter.execute("SELECT name FROM categories ORDER BY category_id LIMIT 2")
    assert res.columns == ["name"]
    assert res.row_count == 2
    assert res.rows[0] == ("Salary",)


def test_writes_are_blocked(adapter):
    with pytest.raises(QueryError):
        adapter.execute("INSERT INTO categories (name, kind) VALUES ('Evil', 'expense')")


def test_row_cap_truncates(adapter):
    res = adapter.execute("SELECT transaction_id FROM transactions", row_cap=10)
    assert res.row_count == 10
    assert res.truncated


def test_timeout(adapter):
    with pytest.raises(QueryError, match="interrupt"):
        adapter.execute(
            "SELECT count(*) FROM transactions a, transactions b, transactions c, transactions d, transactions e",
            timeout_s=0.2,
        )


def test_bad_sql_raises_query_error(adapter):
    with pytest.raises(QueryError):
        adapter.execute("SELECT * FROM NoSuchTable")


def test_create_statements_cover_all_tables(adapter):
    creates = adapter.create_statements()
    assert len(creates) == 7
    assert "transactions" in creates
    assert "CREATE TABLE" in creates["transactions"]


def test_foreign_keys(adapter):
    fks = adapter.foreign_keys()
    assert ("transactions", "category_id", "categories", "category_id") in fks


def test_distinct_values_small_column(adapter):
    categories = adapter.distinct_values("categories", "name", cap=25)
    assert categories is not None
    assert "Groceries" in categories


def test_distinct_values_large_column_returns_none(adapter):
    assert adapter.distinct_values("transactions", "description", cap=5) is None
