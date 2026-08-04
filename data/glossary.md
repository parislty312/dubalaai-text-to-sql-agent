# Personal Finance Glossary

- Spending / expenses: rows in `transactions` where `direction = 'expense'`.
- Income: rows in `transactions` where `direction = 'income'`.
- Transfers: movement between accounts; exclude transfers from net cash flow unless the question asks about savings transfers.
- Month filters: use inclusive start and exclusive next-month boundaries, for example `txn_date >= '2026-07-01' AND txn_date < '2026-08-01'`.
- Monthly subscription cost: monthly amount plus annual subscriptions divided by 12.
- Essential spending: categories where `is_essential = 1`.
- Budget comparisons: compare `budgets.amount_limit` to expense transactions in the same category and month.
