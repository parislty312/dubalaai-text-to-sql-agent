"""Read-only SQLite adapter with timeout, row cap, and introspection."""
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


class QueryError(Exception):
    """Any SQL execution failure: syntax, missing object, blocked write, timeout."""


@dataclass
class ExecResult:
    columns: list
    rows: list
    truncated: bool
    elapsed_ms: float

    @property
    def row_count(self) -> int:
        return len(self.rows)


_ALLOWED_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
    sqlite3.SQLITE_PRAGMA,
}


class SQLiteAdapter:
    dialect = "sqlite"

    def __init__(self, db_path: str = "data/personal_finance.db"):
        p = Path(db_path)
        if not p.exists():
            raise FileNotFoundError(f"{db_path} not found. Run ./setup.sh first.")
        uri = p.resolve().as_uri() + "?mode=ro"
        self.conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self.conn.set_authorizer(self._authorize)

    @staticmethod
    def _authorize(action, *_args):
        if action in _ALLOWED_ACTIONS:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    def execute(
        self,
        sql: str,
        timeout_s: float = 5.0,
        row_cap: int | None = None,
    ) -> ExecResult:
        deadline = time.perf_counter() + timeout_s
        self.conn.set_progress_handler(
            lambda: 1 if time.perf_counter() > deadline else 0,
            50_000,
        )
        t0 = time.perf_counter()
        try:
            cur = self.conn.execute(sql)
            rows = cur.fetchmany(row_cap + 1) if row_cap is not None else cur.fetchall()
            columns = [d[0] for d in cur.description] if cur.description else []
        except sqlite3.Error as exc:
            raise QueryError(str(exc)) from exc
        finally:
            self.conn.set_progress_handler(None, 0)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        truncated = row_cap is not None and len(rows) > row_cap
        if truncated:
            rows = rows[:row_cap]
        return ExecResult(columns, [tuple(r) for r in rows], truncated, elapsed_ms)

    def tables(self) -> list:
        res = self.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in res.rows]

    def create_statements(self) -> dict:
        res = self.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return {name: ddl for name, ddl in res.rows}

    def foreign_keys(self) -> list:
        fks = []
        for table in self.tables():
            res = self.execute(f'PRAGMA foreign_key_list("{table}")')
            cols = {column: idx for idx, column in enumerate(res.columns)}
            for row in res.rows:
                fks.append(
                    (table, row[cols["from"]], row[cols["table"]], row[cols["to"]])
                )
        return fks

    def columns(self, table: str) -> list:
        """Return (column_name, declared_type) pairs for a table."""
        res = self.execute(f'PRAGMA table_info("{table}")')
        cols = {column: idx for idx, column in enumerate(res.columns)}
        return [(row[cols["name"]], row[cols["type"]]) for row in res.rows]

    def sample_rows(self, table: str, n: int = 3) -> ExecResult:
        return self.execute(f'SELECT * FROM "{table}" LIMIT {int(n)}')

    def distinct_values(self, table: str, column: str, cap: int = 25):
        res = self.execute(
            f'SELECT DISTINCT "{column}" FROM "{table}" '
            f'WHERE "{column}" IS NOT NULL ORDER BY 1 LIMIT {int(cap) + 1}'
        )
        if res.row_count > cap:
            return None
        return [row[0] for row in res.rows]
