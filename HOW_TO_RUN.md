# How To Run

This project is managed with `uv`. API keys are read automatically from `.env`
through `python-dotenv`.

## 1. Set Up The Environment

From the repo root:

```bash
uv venv
uv pip install -e .
cp .env.example .env
```

Add your provider settings:

```bash
FIREWORKS_API_KEY=...
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1
```

If `data/personal_finance.db` is missing, run:

```bash
./setup.sh
```

## 2. Run Tests

```bash
uv run python -m pytest -q
```

Equivalent after activating the environment:

```bash
source .venv/bin/activate
python -m pytest -q
```

## 3. Run The CLI

```bash
uv run python -m src.cli --model qwen3p7-plus --strategy single --no-summary
```

Or, after activating `.venv`:

```bash
source .venv/bin/activate
python -m src.cli --model qwen3p7-plus --strategy single --no-summary
```

Then ask a question:

```text
ask> Which subscriptions renew in the next 30 days after August 3, 2026?
ask> How much did I spend in July 2026 by category?
```

Useful CLI commands:

```text
/help
/schema
/model qwen3.7-plus
/strategy react
exit
```

`--no-summary` saves one extra LLM call per question. Remove it if you also want
a natural-language answer after the SQL result table.

## 4. Run A Cheap Live Eval Smoke Test

Run only two questions first:

```bash
uv run python -m src.evals \
  --model qwen3p7-plus \
  --strategy single \
  --questions data/finance_questions_with_answers.json \
  --limit 2 \
  --out results/eval_smoke.json \
  --markdown results/eval_smoke.md
```

Inspect:

```bash
cat results/eval_smoke.md
```

## 5. Generate The Dev Eval Report

```bash
uv run python -m src.evals \
  --model qwen3p7-plus \
  --strategy single \
  --questions data/finance_questions_with_answers.json \
  --out results/eval_qwen3p7-plus_single.json \
  --markdown results/eval_qwen3p7-plus_single.md \
  --write-answers finance_answers.json
```

If you want the `finance_answers.json` answer text to be LLM-written instead of a
deterministic row preview, add:

```bash
--llm-answer-summary
```

## 6. Compare Models And Strategies

```bash
mkdir -p results
for model in qwen3p7-plus qwen3.7-plus deepseek-v4-flash; do
  for strategy in naive single react sc; do
    uv run python -m src.evals \
      --model "$model" \
      --strategy "$strategy" \
      --questions data/finance_questions_with_answers.json \
      --out "results/eval_${model}_${strategy}.json" \
      --markdown "results/eval_${model}_${strategy}.md"
  done
done
```

An optional OpenAI-compatible baseline can be added in `src/config.py` if you
want to compare against another provider.

## 7. Sync Phone-Friendly Finance Data

Use Google Sheets on your phone for editing, then export changed tabs as CSV
files into `data/imports/`.

```bash
uv run python scripts/sync_finance_data.py --import-dir data/imports
```

CSV templates are in `templates/finance_google_sheets/`. Real files in
`data/imports/` are ignored by git.
