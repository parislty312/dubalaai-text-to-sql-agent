"""Full-schema card builder with samples, join paths, known values, and glossary."""
from pathlib import Path

from .db import SQLiteAdapter


DEFAULT_GLOSSARY = "data/glossary.md"
_TEXT_TYPES = ("CHAR", "TEXT", "CLOB", "STRING")


def _is_text(declared_type: str) -> bool:
    text = (declared_type or "").upper()
    return any(kind in text for kind in _TEXT_TYPES)


def _fmt(value) -> str:
    if value is None:
        return "NULL"
    text = str(value)
    return text if len(text) <= 40 else text[:37] + "..."


def build_schema_card(
    adapter: SQLiteAdapter,
    sample_n: int = 3,
    enum_cap: int = 25,
    glossary_path: str = DEFAULT_GLOSSARY,
) -> str:
    parts = [f"### Database schema ({adapter.dialect})\n"]
    creates = adapter.create_statements()
    for ddl in creates.values():
        parts.append(ddl.strip().rstrip(";") + ";")

    parts.append("\n### Foreign keys (join paths)")
    for table, column, ref_table, ref_column in adapter.foreign_keys():
        parts.append(f"- {table}.{column} -> {ref_table}.{ref_column}")

    parts.append("\n### Sample rows (value formats are authoritative)")
    for table in creates:
        res = adapter.sample_rows(table, sample_n)
        header = ", ".join(res.columns)
        rows = " | ".join(
            "(" + ", ".join(_fmt(value) for value in row) + ")" for row in res.rows
        )
        parts.append(f"-- {table} ({header}): {rows}")

    parts.append(
        "\n### Known values (complete lists for small text columns; "
        "use these exact spellings in filters)"
    )
    for table in creates:
        for column, declared_type in adapter.columns(table):
            if not _is_text(declared_type):
                continue
            values = adapter.distinct_values(table, column, cap=enum_cap)
            if values and len(values) > 1:
                joined = ", ".join(f"'{value}'" for value in values)
                parts.append(f"- {table}.{column}: {joined}")

    glossary = Path(glossary_path)
    if glossary.exists():
        parts.append("\n### Business glossary (authoritative metric definitions)")
        parts.append(glossary.read_text().strip())

    return "\n".join(parts)
