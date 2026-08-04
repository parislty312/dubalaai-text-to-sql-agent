# Case Study

## Goal

Build a personal text-to-SQL agent that feels useful from the terminal: ask a
business question, see the generated SQL, inspect the rows, and iterate with
follow-up questions.

## Dataset

The default dataset is a mock personal finance tracker. It includes accounts,
categories, merchants, transactions, budgets, subscriptions, and savings goals.
The data is synthetic, so it is safe to publish while still supporting realistic
questions about spending, budgets, subscriptions, and savings progress.

## Approach

The agent gives the model a compact schema card built from the live database,
then asks for a structured JSON response containing intent, SQL, assumptions,
confidence, and referenced tables. SQL is validated before execution. If a query
fails, repair-capable strategies feed the error back into the model for another
attempt.

## What Worked

- Schema grounding reduces hallucinated table and column names.
- Execution-based repair catches syntax and join mistakes that prompt-only
  approaches miss.
- Self-consistency is slower, but useful when accuracy matters more than
  latency.
- A deterministic eval harness makes model and prompt changes easier to compare.

## Next Steps

- Add support for external SQLite file paths and connection profiles.
- Add a lightweight web UI for saved questions and reusable query snippets.
- Add schema retrieval for wider databases instead of sending the full schema.
- Store accepted SQL/query pairs as future fine-tuning or regression-test data.
