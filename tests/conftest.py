import pytest

from src.db import SQLiteAdapter


@pytest.fixture(scope="session")
def adapter():
    return SQLiteAdapter("data/Chinook.db")
