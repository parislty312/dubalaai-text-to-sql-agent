"""AST-level SQL validation: SELECT-only, one statement, row cap, table extraction."""
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp


_FORBIDDEN = tuple(
    getattr(exp, name)
    for name in ("Insert", "Update", "Delete", "Create", "Drop", "Alter", "Pragma", "Command")
    if hasattr(exp, name)
)
_SELECT_ROOTS = (exp.Select, exp.Union, exp.Intersect, exp.Except)


@dataclass
class ValidationResult:
    ok: bool
    reason: str | None
    sql: str
    tables: list = field(default_factory=list)


def _walk_nodes(tree):
    for item in tree.walk():
        if isinstance(item, tuple):
            yield item[0]
        else:
            yield item


def validate_sql(sql: str, row_cap: int | None = 200) -> ValidationResult:
    try:
        statements = [stmt for stmt in sqlglot.parse(sql or "", read="sqlite") if stmt]
    except sqlglot.errors.ParseError as exc:
        return ValidationResult(False, f"SQL parse error: {exc}", sql)

    if len(statements) != 1:
        return ValidationResult(
            False,
            f"Exactly one SQL statement is required (got {len(statements)}).",
            sql,
        )

    tree = statements[0]
    if not isinstance(tree, _SELECT_ROOTS):
        return ValidationResult(
            False,
            f"Only read-only SELECT queries are allowed (got {tree.key.upper()}).",
            sql,
        )

    for node in _walk_nodes(tree):
        if isinstance(node, _FORBIDDEN):
            return ValidationResult(
                False,
                f"Forbidden operation in query: {node.key.upper()}.",
                sql,
            )

    tables = sorted({table.name for table in tree.find_all(exp.Table) if table.name})
    if row_cap is not None and tree.args.get("limit") is None:
        final_sql = tree.copy().limit(row_cap).sql(dialect="sqlite")
    else:
        final_sql = sql.strip().rstrip(";")
    return ValidationResult(True, None, final_sql, tables)
