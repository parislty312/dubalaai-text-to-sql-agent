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
DUBALAAI_API_KEY=...
DUBALAAI_BASE_URL=https://api.dubalaai.ai/v1
OPENAI_API_KEY=...
```

If `data/Chinook.db` is missing, run:

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
uv run python -m src.cli --model qwen3.6-plus --strategy single --no-summary
```

Or, after activating `.venv`:

```bash
source .venv/bin/activate
python -m src.cli --model qwen3.6-plus --strategy single --no-summary
```

Then ask a question:

```text
ask> What are the top 5 best-selling genres by total sales?
```

Useful CLI commands:

```text
/help
/schema
/model gpt-oss-20b
/strategy react
exit
```

`--no-summary` saves one extra LLM call per question. Remove it if you also want
a natural-language answer after the SQL result table.

## 4. Run A Cheap Live Eval Smoke Test

Run only two questions first:

```bash
uv run python -m src.evals \
  --model qwen3.6-plus \
  --strategy single \
  --questions data/dev_questions_with_answers.json \
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
  --model qwen3.6-plus \
  --strategy single \
  --questions data/dev_questions_with_answers.json \
  --out results/eval_qwen3.6-plus_single.json \
  --markdown results/eval_qwen3.6-plus_single.md \
  --write-answers dev_answers.json
```

If you want the `dev_answers.json` answer text to be LLM-written instead of a
deterministic row preview, add:

```bash
--llm-answer-summary
```

## 6. Compare Models And Strategies

```bash
mkdir -p results
for model in gpt-oss-120b gpt-oss-20b; do
  for strategy in naive single react sc; do
    uv run python -m src.evals \
      --model "$model" \
      --strategy "$strategy" \
      --questions data/dev_questions_with_answers.json \
      --out "results/eval_${model}_${strategy}.json" \
      --markdown "results/eval_${model}_${strategy}.md"
  done
done
```

To include the OpenAI baseline:

```bash
uv run python -m src.evals \
  --model gpt-5.4 \
  --strategy naive \
  --questions data/dev_questions_with_answers.json \
  --out results/eval_gpt-5.4_naive.json \
  --markdown results/eval_gpt-5.4_naive.md
```
