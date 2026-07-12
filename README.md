# DubalaAI Text-to-SQL Agent

An interactive personal text-to-SQL agent that turns natural-language questions
into safe SQLite queries, executes them, and shows both the SQL and result table
in the terminal.

The project uses the Chinook sample database by default, but the agent is built
around a reusable SQLite adapter, schema-context builder, SQL guardrails,
multiple prompting strategies, and an evaluation harness.

## Highlights

- Interactive CLI with follow-up context.
- Schema-aware SQL generation with structured JSON outputs.
- Read-only SQL guardrails and execution repair loops.
- Strategy support for naive prompting, single-call repair, ReAct, and
  self-consistency.
- Local eval runner with execution accuracy, latency, and cost reporting.
- OpenAI-compatible provider layer for DubalaAI-hosted models plus an OpenAI
  baseline.

## Project Structure

```text
.
├── data/
│   ├── Chinook.db
│   ├── dev_questions.json
│   └── dev_questions_with_answers.json
├── docs/
│   ├── case_study.md
│   └── design.md
├── results/
├── src/
│   ├── agent.py
│   ├── cli.py
│   ├── config.py
│   ├── db.py
│   ├── evals.py
│   ├── guardrails.py
│   └── providers.py
├── tests/
├── HOW_TO_RUN.md
└── pyproject.toml
```

## Quick Start

```bash
uv venv
uv pip install -e .
cp .env.example .env
```

Set the DubalaAI endpoint and key in `.env`:

```bash
DUBALAAI_API_KEY=your-key
DUBALAAI_BASE_URL=https://api.dubalaai.ai/v1
OPENAI_API_KEY=optional-openai-key
```

Run the CLI:

```bash
uv run python -m src.cli --model qwen3.6-plus --strategy single --no-summary
```

Try:

```text
ask> What are the top 5 best-selling genres by total sales?
ask> Which customers spent the most money?
ask> /schema
ask> /strategy react
ask> exit
```

## Evaluation

Run the test suite:

```bash
uv run python -m pytest -q
```

Run the text-to-SQL eval set:

```bash
uv run python -m src.evals \
  --model qwen3.6-plus \
  --strategy single \
  --questions data/dev_questions_with_answers.json \
  --out results/eval_qwen3.6-plus_single.json \
  --markdown results/eval_qwen3.6-plus_single.md \
  --write-answers dev_answers.json
```

Benchmark latency and cost:

```bash
uv run python -m src.perf --model qwen3.6-plus --strategy single
```

## Configuration

Models are registered in `src/config.py`. DubalaAI models use:

- `DUBALAAI_API_KEY`
- `DUBALAAI_BASE_URL`

The provider is intentionally OpenAI-compatible, so the same agent code can run
against any compatible DubalaAI gateway or local proxy. The OpenAI baseline uses
`OPENAI_API_KEY`.

## Design Notes

See [docs/design.md](docs/design.md) for the architecture and
[docs/case_study.md](docs/case_study.md) for the evaluation-oriented write-up.
