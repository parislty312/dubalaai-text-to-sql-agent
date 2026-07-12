import pytest

from src.db import QueryError


def test_execute_select(adapter):
    res = adapter.execute("SELECT Name FROM Artist ORDER BY ArtistId LIMIT 2")
    assert res.columns == ["Name"]
    assert res.row_count == 2
    assert res.rows[0] == ("AC/DC",)


def test_writes_are_blocked(adapter):
    with pytest.raises(QueryError):
        adapter.execute("INSERT INTO Artist (Name) VALUES ('Evil')")


def test_row_cap_truncates(adapter):
    res = adapter.execute("SELECT TrackId FROM Track", row_cap=10)
    assert res.row_count == 10
    assert res.truncated


def test_timeout(adapter):
    with pytest.raises(QueryError, match="interrupt"):
        adapter.execute("SELECT count(*) FROM Track a, Track b, Track c", timeout_s=0.2)


def test_bad_sql_raises_query_error(adapter):
    with pytest.raises(QueryError):
        adapter.execute("SELECT * FROM NoSuchTable")


def test_create_statements_cover_all_tables(adapter):
    creates = adapter.create_statements()
    assert len(creates) == 11
    assert "Album" in creates
    assert "CREATE TABLE" in creates["Album"]


def test_foreign_keys(adapter):
    fks = adapter.foreign_keys()
    assert ("Album", "ArtistId", "Artist", "ArtistId") in fks


def test_distinct_values_small_column(adapter):
    genres = adapter.distinct_values("Genre", "Name", cap=25)
    assert genres is not None
    assert "Rock" in genres


def test_distinct_values_large_column_returns_none(adapter):
    assert adapter.distinct_values("Track", "Name", cap=25) is None
