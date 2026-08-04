"""Sync Google Sheets/CSV finance data into the SQLite database.

Export each Google Sheets tab as a CSV named after the target table, then run:

    uv run python scripts/sync_finance_data.py --import-dir data/imports

Supported CSV files:
accounts.csv, categories.csv, merchants.csv, transactions.csv, budgets.csv,
subscriptions.csv, savings_goals.csv.
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "personal_finance.db"
DEFAULT_IMPORT_DIR = ROOT / "data" / "imports"

TABLE_ORDER = [
    "accounts",
    "categories",
    "merchants",
    "transactions",
    "budgets",
    "subscriptions",
    "savings_goals",
]


class SyncError(Exception):
    """Raised when an import file has invalid or unresolved data."""


@dataclass
class SyncStats:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0

    def add(self, other: "SyncStats") -> None:
        self.inserted += other.inserted
        self.updated += other.updated
        self.skipped += other.skipped


def count(stats: SyncStats, action: str) -> None:
    if action == "inserted":
        stats.inserted += 1
    elif action == "updated":
        stats.updated += 1
    elif action == "skipped":
        stats.skipped += 1
    else:
        raise SyncError(f"Unknown sync action: {action}")


def clean(value: str | None) -> str:
    return (value or "").strip()


def required(row: dict, key: str, table: str, row_num: int) -> str:
    value = clean(row.get(key))
    if not value:
        raise SyncError(f"{table}.csv row {row_num}: missing required column '{key}'")
    return value


def maybe_int(value: str | None, default: int | None = None) -> int | None:
    value = clean(value)
    return int(value) if value else default


def money(value: str | None, table: str, row_num: int, key: str = "amount") -> float:
    raw = required({key: value}, key, table, row_num).replace("$", "").replace(",", "")
    return float(raw)


def bool_int(value: str | None, default: int = 0) -> int:
    value = clean(value).lower()
    if not value:
        return default
    if value in {"1", "true", "yes", "y"}:
        return 1
    if value in {"0", "false", "no", "n"}:
        return 0
    raise SyncError(f"Invalid boolean value: {value!r}")


def validate_date(value: str, table: str, row_num: int, key: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SyncError(
            f"{table}.csv row {row_num}: '{key}' must be YYYY-MM-DD, got {value!r}"
        ) from exc
    return value


def validate_month(value: str, table: str, row_num: int) -> str:
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise SyncError(
            f"{table}.csv row {row_num}: 'month' must be YYYY-MM, got {value!r}"
        ) from exc
    return value


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def table_id(conn: sqlite3.Connection, table: str, id_col: str, name: str) -> int:
    row = conn.execute(f"SELECT {id_col} FROM {table} WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise SyncError(f"Could not find {table} row named {name!r}")
    return int(row[0])


def upsert_by_id_or_key(
    conn: sqlite3.Connection,
    table: str,
    id_col: str,
    values: dict,
    key_where: str,
    key_args: tuple,
) -> str:
    record_id = values.get(id_col)
    columns = [c for c in values if c != id_col]

    if record_id:
        assignments = ", ".join(f"{c} = ?" for c in columns)
        args = [values[c] for c in columns] + [record_id]
        cur = conn.execute(f"UPDATE {table} SET {assignments} WHERE {id_col} = ?", args)
        if cur.rowcount:
            return "updated"

    existing = conn.execute(
        f"SELECT {id_col} FROM {table} WHERE {key_where}",
        key_args,
    ).fetchone()
    if existing:
        assignments = ", ".join(f"{c} = ?" for c in columns)
        args = [values[c] for c in columns] + [existing[0]]
        conn.execute(f"UPDATE {table} SET {assignments} WHERE {id_col} = ?", args)
        return "updated"

    insert_columns = [c for c in values if values[c] is not None]
    placeholders = ", ".join("?" for _ in insert_columns)
    conn.execute(
        f"INSERT INTO {table} ({', '.join(insert_columns)}) VALUES ({placeholders})",
        [values[c] for c in insert_columns],
    )
    return "inserted"


def sync_accounts(conn: sqlite3.Connection, rows: Iterable[dict]) -> SyncStats:
    stats = SyncStats()
    for row_num, row in enumerate(rows, start=2):
        name = required(row, "name", "accounts", row_num)
        values = {
            "account_id": maybe_int(row.get("account_id")),
            "name": name,
            "account_type": required(row, "account_type", "accounts", row_num),
            "institution": required(row, "institution", "accounts", row_num),
            "currency": clean(row.get("currency")) or "USD",
            "active": bool_int(row.get("active"), default=1),
        }
        count(stats, upsert_by_id_or_key(conn, "accounts", "account_id", values, "name = ?", (name,)))
    return stats


def sync_categories(conn: sqlite3.Connection, rows: Iterable[dict]) -> SyncStats:
    stats = SyncStats()
    valid_kinds = {"income", "expense", "transfer", "savings"}
    for row_num, row in enumerate(rows, start=2):
        name = required(row, "name", "categories", row_num)
        kind = required(row, "kind", "categories", row_num).lower()
        if kind not in valid_kinds:
            raise SyncError(f"categories.csv row {row_num}: invalid kind {kind!r}")
        values = {
            "category_id": maybe_int(row.get("category_id")),
            "name": name,
            "parent_category": clean(row.get("parent_category")) or None,
            "kind": kind,
            "is_essential": bool_int(row.get("is_essential"), default=0),
        }
        count(stats, upsert_by_id_or_key(conn, "categories", "category_id", values, "name = ?", (name,)))
    return stats


def sync_merchants(conn: sqlite3.Connection, rows: Iterable[dict]) -> SyncStats:
    stats = SyncStats()
    for row_num, row in enumerate(rows, start=2):
        name = required(row, "name", "merchants", row_num)
        category = clean(row.get("default_category"))
        values = {
            "merchant_id": maybe_int(row.get("merchant_id")),
            "name": name,
            "merchant_type": required(row, "merchant_type", "merchants", row_num),
            "default_category_id": table_id(conn, "categories", "category_id", category) if category else None,
        }
        count(stats, upsert_by_id_or_key(conn, "merchants", "merchant_id", values, "name = ?", (name,)))
    return stats


def sync_transactions(conn: sqlite3.Connection, rows: Iterable[dict]) -> SyncStats:
    stats = SyncStats()
    valid_directions = {"income", "expense", "transfer"}
    for row_num, row in enumerate(rows, start=2):
        txn_date = validate_date(required(row, "txn_date", "transactions", row_num), "transactions", row_num, "txn_date")
        account_id = table_id(conn, "accounts", "account_id", required(row, "account", "transactions", row_num))
        merchant_name = clean(row.get("merchant"))
        merchant_id = table_id(conn, "merchants", "merchant_id", merchant_name) if merchant_name else None
        category_id = table_id(conn, "categories", "category_id", required(row, "category", "transactions", row_num))
        direction = required(row, "direction", "transactions", row_num).lower()
        if direction not in valid_directions:
            raise SyncError(f"transactions.csv row {row_num}: invalid direction {direction!r}")
        values = {
            "transaction_id": maybe_int(row.get("transaction_id")),
            "account_id": account_id,
            "merchant_id": merchant_id,
            "category_id": category_id,
            "txn_date": txn_date,
            "amount": money(row.get("amount"), "transactions", row_num),
            "direction": direction,
            "description": clean(row.get("description")) or None,
            "payment_method": required(row, "payment_method", "transactions", row_num),
            "recurring": bool_int(row.get("recurring"), default=0),
        }
        key_where = (
            "account_id = ? AND COALESCE(merchant_id, -1) = COALESCE(?, -1) "
            "AND category_id = ? AND txn_date = ? AND amount = ? AND direction = ? "
            "AND COALESCE(description, '') = COALESCE(?, '') AND payment_method = ?"
        )
        key_args = (
            account_id,
            merchant_id,
            category_id,
            txn_date,
            values["amount"],
            direction,
            values["description"],
            values["payment_method"],
        )
        count(stats, upsert_by_id_or_key(conn, "transactions", "transaction_id", values, key_where, key_args))
    return stats


def sync_budgets(conn: sqlite3.Connection, rows: Iterable[dict]) -> SyncStats:
    stats = SyncStats()
    for row_num, row in enumerate(rows, start=2):
        month = validate_month(required(row, "month", "budgets", row_num), "budgets", row_num)
        category_id = table_id(conn, "categories", "category_id", required(row, "category", "budgets", row_num))
        values = {
            "budget_id": maybe_int(row.get("budget_id")),
            "category_id": category_id,
            "month": month,
            "amount_limit": money(row.get("amount_limit"), "budgets", row_num, key="amount_limit"),
        }
        count(stats, upsert_by_id_or_key(conn, "budgets", "budget_id", values, "category_id = ? AND month = ?", (category_id, month)))
    return stats


def sync_subscriptions(conn: sqlite3.Connection, rows: Iterable[dict]) -> SyncStats:
    stats = SyncStats()
    valid_cycles = {"monthly", "annual"}
    valid_statuses = {"active", "paused", "cancelled"}
    for row_num, row in enumerate(rows, start=2):
        merchant_id = table_id(conn, "merchants", "merchant_id", required(row, "merchant", "subscriptions", row_num))
        plan_name = required(row, "plan_name", "subscriptions", row_num)
        cycle = required(row, "billing_cycle", "subscriptions", row_num).lower()
        status = required(row, "status", "subscriptions", row_num).lower()
        if cycle not in valid_cycles:
            raise SyncError(f"subscriptions.csv row {row_num}: invalid billing_cycle {cycle!r}")
        if status not in valid_statuses:
            raise SyncError(f"subscriptions.csv row {row_num}: invalid status {status!r}")
        values = {
            "subscription_id": maybe_int(row.get("subscription_id")),
            "merchant_id": merchant_id,
            "category_id": table_id(conn, "categories", "category_id", required(row, "category", "subscriptions", row_num)),
            "account_id": table_id(conn, "accounts", "account_id", required(row, "account", "subscriptions", row_num)),
            "plan_name": plan_name,
            "amount": money(row.get("amount"), "subscriptions", row_num),
            "billing_cycle": cycle,
            "next_renewal_date": validate_date(required(row, "next_renewal_date", "subscriptions", row_num), "subscriptions", row_num, "next_renewal_date"),
            "status": status,
            "started_on": validate_date(required(row, "started_on", "subscriptions", row_num), "subscriptions", row_num, "started_on"),
        }
        count(stats, upsert_by_id_or_key(conn, "subscriptions", "subscription_id", values, "merchant_id = ? AND plan_name = ?", (merchant_id, plan_name)))
    return stats


def sync_savings_goals(conn: sqlite3.Connection, rows: Iterable[dict]) -> SyncStats:
    stats = SyncStats()
    valid_priorities = {"low", "medium", "high"}
    for row_num, row in enumerate(rows, start=2):
        name = required(row, "name", "savings_goals", row_num)
        priority = required(row, "priority", "savings_goals", row_num).lower()
        if priority not in valid_priorities:
            raise SyncError(f"savings_goals.csv row {row_num}: invalid priority {priority!r}")
        values = {
            "goal_id": maybe_int(row.get("goal_id")),
            "name": name,
            "target_amount": money(row.get("target_amount"), "savings_goals", row_num, key="target_amount"),
            "current_amount": money(row.get("current_amount"), "savings_goals", row_num, key="current_amount"),
            "target_date": validate_date(required(row, "target_date", "savings_goals", row_num), "savings_goals", row_num, "target_date"),
            "priority": priority,
        }
        count(stats, upsert_by_id_or_key(conn, "savings_goals", "goal_id", values, "name = ?", (name,)))
    return stats


SYNCERS = {
    "accounts": sync_accounts,
    "categories": sync_categories,
    "merchants": sync_merchants,
    "transactions": sync_transactions,
    "budgets": sync_budgets,
    "subscriptions": sync_subscriptions,
    "savings_goals": sync_savings_goals,
}


def backup_db(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = db_path.with_suffix(f".{stamp}.bak")
    shutil.copy2(db_path, backup)
    return backup


def sync(import_dir: Path, db_path: Path, make_backup: bool = True) -> dict[str, SyncStats]:
    if not db_path.exists():
        raise SyncError(f"Database not found: {db_path}")
    if not import_dir.exists():
        raise SyncError(f"Import directory not found: {import_dir}")

    if make_backup:
        backup_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    results: dict[str, SyncStats] = {}
    try:
        for table in TABLE_ORDER:
            path = import_dir / f"{table}.csv"
            if not path.exists():
                continue
            stats = SYNCERS[table](conn, read_rows(path))
            results[table] = stats
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync finance CSV exports into SQLite")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--import-dir", default=str(DEFAULT_IMPORT_DIR))
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    results = sync(Path(args.import_dir), Path(args.db), make_backup=not args.no_backup)
    if not results:
        print("No CSV files found to sync.")
        return
    for table, stats in results.items():
        print(
            f"{table}: inserted={stats.inserted} updated={stats.updated} skipped={stats.skipped}"
        )


if __name__ == "__main__":
    main()
