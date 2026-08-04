# Design

DubalaAI Text-to-SQL Agent is a terminal-first agent for querying SQLite
databases with natural language. The default database is a mock personal finance
tracker, but the implementation keeps the database adapter, schema context,
model client, and agent strategies separate so the project can evolve beyond
the demo dataset.

## Architecture

```text
User question
  -> CLI session context
  -> schema card + optional glossary
  -> model strategy
  -> SQL parser and guardrails
  -> SQLite execution
  -> result table + optional answer summary
```

## Main Components

- `src/cli.py`: interactive terminal UI built with Rich.
- `src/agent.py`: prompt construction, response parsing, repair flow,
  self-consistency voting, and session state.
- `src/context.py`: schema-card generation from live SQLite metadata.
- `src/db.py`: SQLite adapter with read-only query execution.
- `src/guardrails.py`: SQL validation for allowed read-only statements.
- `src/providers.py`: OpenAI SDK wrapper for Fireworks and OpenAI-compatible
  chat completion APIs.
- `src/evals.py`: execution-accuracy evaluation against question/answer sets.
- `src/perf.py`: latency and cost benchmark helper.

## Strategies

- `naive`: baseline prompt with minimal structure.
- `single`: one structured generation call plus execution repair.
- `react`: model can inspect errors and retry through a tool-style loop.
- `sc`: samples several candidates and chooses the SQL whose executed result
  wins by majority vote.

## Guardrails

The agent only allows read-only SQL. It parses candidate queries, rejects
mutating statements, blocks multiple statements, and executes against SQLite
with a result limit. This keeps the CLI suitable for exploration without
turning natural-language input into arbitrary database writes.

## Evaluation

The eval runner compares generated SQL by execution result, not just string
similarity. That matters because equivalent SQL can be written many ways. The
report includes:

- execution accuracy
- query validity
- latency
- token usage
- estimated cost
- per-question failure details

## Provider Configuration

Fireworks models are configured through:

```bash
FIREWORKS_API_KEY=...
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1
```

The code uses an OpenAI-compatible client, so the Fireworks backend can be
swapped for another compatible model endpoint without changing the agent logic.
