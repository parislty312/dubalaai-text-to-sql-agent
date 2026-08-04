import shutil
import sqlite3

from scripts.sync_finance_data import sync


def write(path, text):
    path.write_text(text.strip() + "\n")


def count_rows(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, args).fetchone()[0]
    finally:
        conn.close()


def test_sync_transactions_is_idempotent(tmp_path):
    db = tmp_path / "finance.db"
    shutil.copy2("data/personal_finance.db", db)
    imports = tmp_path / "imports"
    imports.mkdir()
    write(
        imports / "transactions.csv",
        """
transaction_id,txn_date,account,merchant,category,amount,direction,description,payment_method,recurring
,2026-08-11,Travel Credit Card,Trader Joes,Groceries,42.50,expense,Extra groceries,credit,0
""",
    )

    first = sync(imports, db, make_backup=False)
    second = sync(imports, db, make_backup=False)

    assert first["transactions"].inserted == 1
    assert second["transactions"].updated == 1
    assert count_rows(
        db,
        "SELECT COUNT(*) FROM transactions WHERE txn_date = ? AND description = ?",
        ("2026-08-11", "Extra groceries"),
    ) == 1


def test_sync_updates_budget_by_month_and_category(tmp_path):
    db = tmp_path / "finance.db"
    shutil.copy2("data/personal_finance.db", db)
    imports = tmp_path / "imports"
    imports.mkdir()
    write(
        imports / "budgets.csv",
        """
budget_id,month,category,amount_limit
,2026-08,Groceries,500.00
""",
    )

    result = sync(imports, db, make_backup=False)

    assert result["budgets"].updated == 1
    assert count_rows(
        db,
        """
        SELECT amount_limit
        FROM budgets b
        JOIN categories c ON b.category_id = c.category_id
        WHERE b.month = ? AND c.name = ?
        """,
        ("2026-08", "Groceries"),
    ) == 500.00
