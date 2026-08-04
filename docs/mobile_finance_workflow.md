# Mobile Finance Data Workflow

Use Google Sheets as the phone-friendly editing layer, then sync CSV exports
into the local SQLite database that the text-to-SQL agent queries.

## Recommended Sheet Tabs

Create one Google Sheet with these tabs:

- `transactions`
- `subscriptions`
- `budgets`
- `merchants`
- `categories`
- `accounts`
- `savings_goals`

Starter CSV templates live in `templates/finance_google_sheets/`. You can upload
or copy those headers into Google Sheets, then use the Google Sheets mobile app
for day-to-day updates.

## Monthly Workflow

1. Update the Google Sheet from your phone during the month.
2. Export changed tabs as CSV files.
3. Save the CSV files into `data/imports/` with exact names such as
   `transactions.csv`, `subscriptions.csv`, and `budgets.csv`.
4. Run the sync:

```bash
uv run python scripts/sync_finance_data.py --import-dir data/imports
```

5. Ask the agent questions:

```bash
uv run python -m src.cli --strategy single --no-summary
```

## CSV Rules

- Dates use `YYYY-MM-DD`.
- Months use `YYYY-MM`.
- Amounts are positive numbers; `direction` explains whether the row is income,
  expense, or transfer.
- Lookup columns use names, not IDs. For example, `transactions.csv` uses
  `account`, `merchant`, and `category`; the sync script maps them to internal
  IDs.
- Re-running the same CSV is safe. Existing rows are updated when possible, and
  duplicate transactions are not inserted again.
- Real import files in `data/imports/` are ignored by git so private finance
  data does not get pushed.

## Useful Agent Questions

```text
How much did I spend in July 2026 by category?
Which subscriptions renew in the next 30 days after August 3, 2026?
Which July 2026 categories were over budget?
What is my total monthly cost for active subscriptions?
What percent of my July 2026 expense spending was essential?
Which savings goals still need more than $2,000?
```
