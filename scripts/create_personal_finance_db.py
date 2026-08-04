"""Create the sample personal finance SQLite database and eval questions."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB_PATH = DATA / "personal_finance.db"


SCHEMA = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS budgets;
DROP TABLE IF EXISTS savings_goals;
DROP TABLE IF EXISTS merchants;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    institution TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    parent_category TEXT,
    kind TEXT NOT NULL CHECK (kind IN ('income', 'expense', 'transfer', 'savings')),
    is_essential INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE merchants (
    merchant_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    merchant_type TEXT NOT NULL,
    default_category_id INTEGER,
    FOREIGN KEY (default_category_id) REFERENCES categories(category_id)
);

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    merchant_id INTEGER,
    category_id INTEGER NOT NULL,
    txn_date TEXT NOT NULL,
    amount REAL NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('income', 'expense', 'transfer')),
    description TEXT,
    payment_method TEXT NOT NULL,
    recurring INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE budgets (
    budget_id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    month TEXT NOT NULL,
    amount_limit REAL NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE subscriptions (
    subscription_id INTEGER PRIMARY KEY,
    merchant_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    plan_name TEXT NOT NULL,
    amount REAL NOT NULL,
    billing_cycle TEXT NOT NULL CHECK (billing_cycle IN ('monthly', 'annual')),
    next_renewal_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'paused', 'cancelled')),
    started_on TEXT NOT NULL,
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE savings_goals (
    goal_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL NOT NULL,
    target_date TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high'))
);
"""


ACCOUNTS = [
    (1, "Everyday Checking", "checking", "Mock National Bank", "USD", 1),
    (2, "Travel Credit Card", "credit_card", "Mock Rewards Bank", "USD", 1),
    (3, "High Yield Savings", "savings", "Mock Online Bank", "USD", 1),
]

CATEGORIES = [
    (1, "Salary", "Income", "income", 1),
    (2, "Rent", "Housing", "expense", 1),
    (3, "Groceries", "Food", "expense", 1),
    (4, "Dining", "Food", "expense", 0),
    (5, "Coffee", "Food", "expense", 0),
    (6, "Transportation", "Mobility", "expense", 1),
    (7, "Utilities", "Home", "expense", 1),
    (8, "Phone", "Home", "expense", 1),
    (9, "Streaming", "Subscriptions", "expense", 0),
    (10, "Software", "Subscriptions", "expense", 0),
    (11, "Cloud", "Subscriptions", "expense", 0),
    (12, "Fitness", "Health", "expense", 0),
    (13, "Shopping", "Lifestyle", "expense", 0),
    (14, "Travel", "Lifestyle", "expense", 0),
    (15, "Healthcare", "Health", "expense", 1),
    (16, "Savings Transfer", "Savings", "transfer", 1),
]

MERCHANTS = [
    (1, "Employer Payroll", "payroll", 1),
    (2, "Oak Street Apartments", "landlord", 2),
    (3, "Trader Joes", "grocery", 3),
    (4, "Whole Foods", "grocery", 3),
    (5, "Sweetgreen", "restaurant", 4),
    (6, "Blue Bottle Coffee", "cafe", 5),
    (7, "Muni Mobile", "transit", 6),
    (8, "PG&E", "utility", 7),
    (9, "Verizon", "telecom", 8),
    (10, "Netflix", "subscription", 9),
    (11, "Spotify", "subscription", 9),
    (12, "Notion", "subscription", 10),
    (13, "GitHub", "subscription", 10),
    (14, "iCloud", "subscription", 11),
    (15, "OpenAI API", "cloud", 11),
    (16, "ClassPass", "fitness", 12),
    (17, "Amazon", "retail", 13),
    (18, "United Airlines", "travel", 14),
    (19, "One Medical", "healthcare", 15),
    (20, "Mock Online Bank", "bank", 16),
]

TRANSACTIONS = [
    (1, 1, 1, 1, "2026-06-01", 6400.00, "income", "June salary", "direct_deposit", 1),
    (2, 1, 2, 2, "2026-06-02", 2450.00, "expense", "June rent", "ach", 1),
    (3, 1, 3, 3, "2026-06-03", 86.42, "expense", "Weekly groceries", "debit", 0),
    (4, 2, 5, 4, "2026-06-04", 18.73, "expense", "Lunch", "credit", 0),
    (5, 2, 6, 5, "2026-06-05", 6.25, "expense", "Coffee", "credit", 0),
    (6, 1, 7, 6, "2026-06-07", 81.00, "expense", "Monthly transit pass", "debit", 1),
    (7, 1, 8, 7, "2026-06-10", 72.18, "expense", "Electric bill", "ach", 1),
    (8, 1, 9, 8, "2026-06-12", 65.00, "expense", "Phone bill", "ach", 1),
    (9, 2, 10, 9, "2026-06-15", 15.49, "expense", "Netflix subscription", "credit", 1),
    (10, 2, 11, 9, "2026-06-17", 10.99, "expense", "Spotify subscription", "credit", 1),
    (11, 2, 12, 10, "2026-06-19", 12.00, "expense", "Notion subscription", "credit", 1),
    (12, 2, 17, 13, "2026-06-22", 142.37, "expense", "Desk accessories", "credit", 0),
    (13, 1, 20, 16, "2026-06-25", 900.00, "transfer", "Savings transfer", "ach", 1),
    (14, 2, 4, 3, "2026-06-26", 118.92, "expense", "Groceries", "credit", 0),
    (15, 2, 16, 12, "2026-06-28", 59.00, "expense", "Fitness membership", "credit", 1),
    (16, 1, 1, 1, "2026-07-01", 6400.00, "income", "July salary", "direct_deposit", 1),
    (17, 1, 2, 2, "2026-07-02", 2450.00, "expense", "July rent", "ach", 1),
    (18, 2, 3, 3, "2026-07-03", 94.31, "expense", "Groceries", "credit", 0),
    (19, 2, 5, 4, "2026-07-04", 24.56, "expense", "Dinner", "credit", 0),
    (20, 2, 6, 5, "2026-07-05", 7.10, "expense", "Coffee", "credit", 0),
    (21, 1, 7, 6, "2026-07-07", 81.00, "expense", "Monthly transit pass", "debit", 1),
    (22, 1, 8, 7, "2026-07-10", 88.46, "expense", "Electric bill", "ach", 1),
    (23, 1, 9, 8, "2026-07-12", 65.00, "expense", "Phone bill", "ach", 1),
    (24, 2, 10, 9, "2026-07-15", 15.49, "expense", "Netflix subscription", "credit", 1),
    (25, 2, 11, 9, "2026-07-17", 10.99, "expense", "Spotify subscription", "credit", 1),
    (26, 2, 12, 10, "2026-07-19", 12.00, "expense", "Notion subscription", "credit", 1),
    (27, 2, 13, 10, "2026-07-20", 4.00, "expense", "GitHub Pro", "credit", 1),
    (28, 2, 15, 11, "2026-07-21", 38.44, "expense", "API usage", "credit", 0),
    (29, 2, 17, 13, "2026-07-22", 210.18, "expense", "Household items", "credit", 0),
    (30, 1, 20, 16, "2026-07-25", 1000.00, "transfer", "Savings transfer", "ach", 1),
    (31, 2, 4, 3, "2026-07-26", 126.77, "expense", "Groceries", "credit", 0),
    (32, 2, 16, 12, "2026-07-28", 59.00, "expense", "Fitness membership", "credit", 1),
    (33, 2, 18, 14, "2026-07-29", 480.20, "expense", "Flight to Seattle", "credit", 0),
    (34, 2, 19, 15, "2026-07-30", 35.00, "expense", "Clinic copay", "credit", 0),
    (35, 1, 1, 1, "2026-08-01", 6400.00, "income", "August salary", "direct_deposit", 1),
    (36, 1, 2, 2, "2026-08-02", 2450.00, "expense", "August rent", "ach", 1),
    (37, 2, 3, 3, "2026-08-03", 101.54, "expense", "Groceries", "credit", 0),
    (38, 2, 5, 4, "2026-08-04", 21.35, "expense", "Lunch", "credit", 0),
    (39, 2, 6, 5, "2026-08-05", 6.80, "expense", "Coffee", "credit", 0),
    (40, 1, 8, 7, "2026-08-10", 91.12, "expense", "Electric bill", "ach", 1),
]

BUDGETS = [
    (1, 2, "2026-07", 2450.00),
    (2, 3, "2026-07", 450.00),
    (3, 4, "2026-07", 180.00),
    (4, 5, "2026-07", 60.00),
    (5, 6, "2026-07", 100.00),
    (6, 7, "2026-07", 90.00),
    (7, 9, "2026-07", 35.00),
    (8, 10, "2026-07", 30.00),
    (9, 11, "2026-07", 75.00),
    (10, 12, "2026-07", 80.00),
    (11, 13, "2026-07", 200.00),
    (12, 14, "2026-07", 300.00),
    (13, 3, "2026-08", 450.00),
    (14, 4, "2026-08", 180.00),
    (15, 5, "2026-08", 60.00),
]

SUBSCRIPTIONS = [
    (1, 10, 9, 2, "Standard", 15.49, "monthly", "2026-08-15", "active", "2024-01-15"),
    (2, 11, 9, 2, "Individual", 10.99, "monthly", "2026-08-17", "active", "2023-10-17"),
    (3, 12, 10, 2, "Plus", 12.00, "monthly", "2026-08-19", "active", "2025-02-19"),
    (4, 13, 10, 2, "Pro", 4.00, "monthly", "2026-08-20", "active", "2024-08-20"),
    (5, 14, 11, 2, "200GB", 2.99, "monthly", "2026-08-23", "active", "2022-03-23"),
    (6, 16, 12, 2, "Base", 59.00, "monthly", "2026-08-28", "active", "2026-01-28"),
]

SAVINGS_GOALS = [
    (1, "Emergency Fund", 15000.00, 8400.00, "2026-12-31", "high"),
    (2, "Japan Trip", 3500.00, 1250.00, "2027-04-01", "medium"),
    (3, "New Laptop", 2800.00, 900.00, "2026-11-15", "medium"),
]

QUESTIONS = [
    {
        "id": "q_001",
        "tier": 1,
        "question": "How much did I spend in July 2026 by category?",
        "gold_sql": "SELECT c.name AS category, ROUND(SUM(t.amount), 2) AS total_spent FROM transactions t JOIN categories c ON t.category_id = c.category_id WHERE t.direction = 'expense' AND t.txn_date >= '2026-07-01' AND t.txn_date < '2026-08-01' GROUP BY c.name ORDER BY total_spent DESC",
        "evaluation": "sql_result_match",
    },
    {
        "id": "q_002",
        "tier": 1,
        "question": "Which subscriptions renew in the next 30 days after August 3, 2026?",
        "gold_sql": "SELECT m.name, s.plan_name, s.amount, s.next_renewal_date FROM subscriptions s JOIN merchants m ON s.merchant_id = m.merchant_id WHERE s.status = 'active' AND s.next_renewal_date >= '2026-08-03' AND s.next_renewal_date < date('2026-08-03', '+30 days') ORDER BY s.next_renewal_date",
        "evaluation": "sql_result_match",
    },
    {
        "id": "q_003",
        "tier": 1,
        "question": "What is my total monthly cost for active subscriptions?",
        "gold_sql": "SELECT ROUND(SUM(CASE WHEN billing_cycle = 'monthly' THEN amount WHEN billing_cycle = 'annual' THEN amount / 12.0 ELSE 0 END), 2) AS monthly_subscription_cost FROM subscriptions WHERE status = 'active'",
        "evaluation": "sql_result_match",
    },
    {
        "id": "q_004",
        "tier": 2,
        "question": "Which July 2026 categories were over budget?",
        "gold_sql": "SELECT c.name AS category, b.amount_limit, ROUND(SUM(t.amount), 2) AS actual_spend, ROUND(SUM(t.amount) - b.amount_limit, 2) AS over_by FROM budgets b JOIN categories c ON b.category_id = c.category_id JOIN transactions t ON t.category_id = b.category_id AND t.direction = 'expense' AND t.txn_date >= b.month || '-01' AND t.txn_date < date(b.month || '-01', '+1 month') WHERE b.month = '2026-07' GROUP BY c.name, b.amount_limit HAVING actual_spend > b.amount_limit ORDER BY over_by DESC",
        "evaluation": "sql_result_match",
    },
    {
        "id": "q_005",
        "tier": 1,
        "question": "Who were my top merchants by spending in July 2026?",
        "gold_sql": "SELECT m.name AS merchant, ROUND(SUM(t.amount), 2) AS total_spent FROM transactions t JOIN merchants m ON t.merchant_id = m.merchant_id WHERE t.direction = 'expense' AND t.txn_date >= '2026-07-01' AND t.txn_date < '2026-08-01' GROUP BY m.name ORDER BY total_spent DESC LIMIT 5",
        "evaluation": "sql_result_match",
    },
    {
        "id": "q_006",
        "tier": 2,
        "question": "Compare my July 2026 spending to June 2026 by parent category.",
        "gold_sql": "SELECT c.parent_category, ROUND(SUM(CASE WHEN t.txn_date >= '2026-06-01' AND t.txn_date < '2026-07-01' THEN t.amount ELSE 0 END), 2) AS june_spend, ROUND(SUM(CASE WHEN t.txn_date >= '2026-07-01' AND t.txn_date < '2026-08-01' THEN t.amount ELSE 0 END), 2) AS july_spend, ROUND(SUM(CASE WHEN t.txn_date >= '2026-07-01' AND t.txn_date < '2026-08-01' THEN t.amount ELSE 0 END) - SUM(CASE WHEN t.txn_date >= '2026-06-01' AND t.txn_date < '2026-07-01' THEN t.amount ELSE 0 END), 2) AS change FROM transactions t JOIN categories c ON t.category_id = c.category_id WHERE t.direction = 'expense' AND t.txn_date >= '2026-06-01' AND t.txn_date < '2026-08-01' GROUP BY c.parent_category ORDER BY change DESC",
        "evaluation": "sql_result_match",
    },
    {
        "id": "q_007",
        "tier": 2,
        "question": "What percent of my July 2026 expense spending was essential?",
        "gold_sql": "SELECT ROUND(100.0 * SUM(CASE WHEN c.is_essential = 1 THEN t.amount ELSE 0 END) / SUM(t.amount), 2) AS essential_spend_pct FROM transactions t JOIN categories c ON t.category_id = c.category_id WHERE t.direction = 'expense' AND t.txn_date >= '2026-07-01' AND t.txn_date < '2026-08-01'",
        "evaluation": "sql_result_match",
    },
    {
        "id": "q_008",
        "tier": 1,
        "question": "How much did I transfer to savings in July 2026?",
        "gold_sql": "SELECT ROUND(SUM(amount), 2) AS savings_transfers FROM transactions WHERE direction = 'transfer' AND txn_date >= '2026-07-01' AND txn_date < '2026-08-01'",
        "evaluation": "sql_result_match",
    },
    {
        "id": "q_009",
        "tier": 1,
        "question": "Which savings goals still need more than $2,000?",
        "gold_sql": "SELECT name, target_amount, current_amount, ROUND(target_amount - current_amount, 2) AS remaining FROM savings_goals WHERE target_amount - current_amount > 2000 ORDER BY remaining DESC",
        "evaluation": "sql_result_match",
    },
    {
        "id": "q_010",
        "tier": 1,
        "question": "What is my net cash flow for July 2026, excluding transfers?",
        "gold_sql": "SELECT ROUND(SUM(CASE WHEN direction = 'income' THEN amount WHEN direction = 'expense' THEN -amount ELSE 0 END), 2) AS net_cash_flow FROM transactions WHERE txn_date >= '2026-07-01' AND txn_date < '2026-08-01' AND direction IN ('income', 'expense')",
        "evaluation": "sql_result_match",
    },
]


GLOSSARY = """# Personal Finance Glossary

- Spending / expenses: rows in `transactions` where `direction = 'expense'`.
- Income: rows in `transactions` where `direction = 'income'`.
- Transfers: movement between accounts; exclude transfers from net cash flow unless the question asks about savings transfers.
- Month filters: use inclusive start and exclusive next-month boundaries, for example `txn_date >= '2026-07-01' AND txn_date < '2026-08-01'`.
- Monthly subscription cost: monthly amount plus annual subscriptions divided by 12.
- Essential spending: categories where `is_essential = 1`.
- Budget comparisons: compare `budgets.amount_limit` to expense transactions in the same category and month.
"""


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)", ACCOUNTS)
    conn.executemany("INSERT INTO categories VALUES (?, ?, ?, ?, ?)", CATEGORIES)
    conn.executemany("INSERT INTO merchants VALUES (?, ?, ?, ?)", MERCHANTS)
    conn.executemany(
        "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        TRANSACTIONS,
    )
    conn.executemany("INSERT INTO budgets VALUES (?, ?, ?, ?)", BUDGETS)
    conn.executemany("INSERT INTO subscriptions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", SUBSCRIPTIONS)
    conn.executemany("INSERT INTO savings_goals VALUES (?, ?, ?, ?, ?, ?)", SAVINGS_GOALS)
    conn.commit()
    conn.close()

    write_json(DATA / "finance_questions_with_answers.json", QUESTIONS)
    write_json(
        DATA / "finance_questions.json",
        [{"id": q["id"], "question": q["question"], "tier": q["tier"]} for q in QUESTIONS],
    )
    write_json(
        DATA / "finance_answers_example.json",
        {
            q["id"]: {
                "sql": q["gold_sql"],
                "answer": "Run the eval command to generate this answer.",
            }
            for q in QUESTIONS[:3]
        },
    )
    (DATA / "glossary.md").write_text(GLOSSARY)
    print(f"Wrote {DB_PATH.relative_to(ROOT)} and finance eval files.")


if __name__ == "__main__":
    main()
