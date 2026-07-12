"""Agent core: prompt contract, response parsing, and strategy types."""
import json
import re
from dataclasses import dataclass, field
from datetime import date

from .db import ExecResult, QueryError, SQLiteAdapter
from .guardrails import validate_sql
from .providers import cost_usd


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["sql", "clarify", "decline"]},
        "sql": {"type": "string"},
        "assumption": {"type": "string"},
        "clarification": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["action", "confidence"],
}


_SYSTEM_TEMPLATE = """You are a senior data analyst who translates natural-language questions into SQLite SQL.
Current date: {today}.

Rules:
- Use ONLY tables and columns from the schema below. Never invent names.
- SQLite dialect. Dates are stored as TEXT like '2021-01-08 00:00:00'; use strftime()/date() for date logic.
- Resolve relative time ("last month", "this year") into concrete date ranges using the current date.
- Produce a single read-only SELECT statement. No INSERT/UPDATE/DELETE/DDL/PRAGMA, no multiple statements.
- When filtering on a column whose complete value list appears under "Known values", use those exact spellings.
- Return EXACTLY the columns the question asks for — never add ids or other extra columns.
- For superlative/ranking questions ("which X has the most Y", "top N X by Y"), return BOTH the entity and the aggregated metric, and return a person's name as ONE column (FirstName || ' ' || LastName).
- For listing questions ("names and emails of customers..."), return the stored columns separately, NOT concatenated.
- When aggregating per entity ("per playlist", "for each customer"), GROUP BY the entity's primary key (entities can share a display name) and use LEFT JOIN so entities with zero related rows still appear.
- If the question is ambiguous but answerable, answer with your best interpretation and state it in "assumption".
- Only use "clarify" when the question cannot be answered from this schema without more information.
- Use "decline" for requests unrelated to this database or asking for anything other than reading data.

Respond with JSON only:
{{"action": "sql" | "clarify" | "decline", "sql": "...", "assumption": "...", "clarification": "...", "confidence": "high" | "medium" | "low"}}

{schema_card}"""


def build_system_prompt(schema_card: str, today: str | None = None) -> str:
    return _SYSTEM_TEMPLATE.format(
        today=today or date.today().isoformat(),
        schema_card=schema_card,
    )


def parse_response(content: str | None) -> dict:
    data = None
    try:
        data = json.loads(content or "")
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content or "", re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                data = None

    if not isinstance(data, dict):
        return {"action": "error", "raw": content}
    if data.get("action") not in ("sql", "clarify", "decline"):
        data["action"] = "sql" if data.get("sql") else "error"
    data.setdefault("confidence", "medium")
    return data


def extract_sql(text: str) -> str:
    match = re.search(r"```(?:sql)?\s*(.+?)```", text or "", re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else (text or "")).strip().rstrip(";")


@dataclass
class TurnStats:
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    llm_latency_s: float = 0.0

    def record(self, resp, spec):
        self.llm_calls += 1
        self.input_tokens += resp.usage.input_tokens
        self.output_tokens += resp.usage.output_tokens
        self.cost_usd += cost_usd(spec, resp.usage)
        self.llm_latency_s += resp.latency_s


@dataclass
class AgentTurn:
    action: str
    sql: str | None = None
    result: ExecResult | None = None
    message: str | None = None
    assumption: str | None = None
    confidence: str | None = None
    tables: list = field(default_factory=list)
    attempts: int = 1
    stats: TurnStats = field(default_factory=TurnStats)
    wall_s: float = 0.0


class BaseStrategy:
    name = "base"

    def __init__(
        self,
        client,
        adapter: SQLiteAdapter,
        schema_card: str,
        row_cap: int | None = 200,
        max_repairs: int = 2,
    ):
        self.client = client
        self.adapter = adapter
        self.row_cap = row_cap
        self.max_repairs = max_repairs
        self.system_prompt = build_system_prompt(schema_card)

    def run(self, question: str, history: list) -> AgentTurn:
        raise NotImplementedError

    def _non_sql_turn(self, data: dict, stats: TurnStats, attempts: int) -> AgentTurn:
        action = data.get("action", "error")
        if action == "clarify":
            message = data.get("clarification") or "Could you clarify the question?"
        elif action == "decline":
            message = (
                data.get("clarification")
                or "This question is outside the scope of this database."
            )
        else:
            message = "The model did not return a usable response."
        return AgentTurn(
            action=action,
            message=message,
            confidence=data.get("confidence"),
            stats=stats,
            attempts=attempts,
        )


class SingleCallRepairStrategy(BaseStrategy):
    """One generation call; execution-feedback repair on validation/DB failure."""

    name = "single"

    def run(self, question: str, history: list) -> AgentTurn:
        stats = TurnStats()
        messages = (
            [{"role": "system", "content": self.system_prompt}]
            + list(history)
            + [{"role": "user", "content": question}]
        )
        last_error = "unknown error"
        last_sql = None

        for attempt in range(1, self.max_repairs + 2):
            resp = self.client.chat(messages, json_schema=RESPONSE_SCHEMA)
            stats.record(resp, self.client.spec)
            data = parse_response(resp.content)

            if data["action"] != "sql":
                return self._non_sql_turn(data, stats, attempt)

            v = validate_sql(data.get("sql", ""), self.row_cap)
            if not v.ok:
                last_error = v.reason or "SQL rejected"
                last_sql = data.get("sql")
                messages.extend(
                    [
                        {"role": "assistant", "content": resp.content or ""},
                        {
                            "role": "user",
                            "content": (
                                f"Your SQL was rejected: {last_error}. "
                                "Return corrected JSON with a single read-only SELECT."
                            ),
                        },
                    ]
                )
                continue

            try:
                result = self.adapter.execute(v.sql)
            except QueryError as exc:
                last_error = str(exc)
                last_sql = v.sql
                messages.extend(
                    [
                        {"role": "assistant", "content": resp.content or ""},
                        {
                            "role": "user",
                            "content": (
                                f"That SQL failed to execute: {last_error}. "
                                "Fix it and return corrected JSON."
                            ),
                        },
                    ]
                )
                continue

            return AgentTurn(
                action="sql",
                sql=v.sql,
                result=result,
                assumption=data.get("assumption"),
                confidence=data.get("confidence"),
                tables=v.tables,
                attempts=attempt,
                stats=stats,
            )

        return AgentTurn(
            action="error",
            sql=last_sql,
            message=(
                f"Could not produce working SQL after {self.max_repairs + 1} "
                f"attempts. Last error: {last_error}"
            ),
            attempts=self.max_repairs + 1,
            stats=stats,
        )


class NaiveStrategy(BaseStrategy):
    """The customer's current prompt, kept as the baseline to beat."""

    name = "naive"

    def run(self, question: str, history: list) -> AgentTurn:
        stats = TurnStats()
        resp = self.client.chat(
            [{"role": "user", "content": f"Convert this question to SQL: {question}"}]
        )
        stats.record(resp, self.client.spec)
        sql = extract_sql(resp.content)
        v = validate_sql(sql, self.row_cap)
        if not v.ok:
            return AgentTurn(action="error", sql=sql, message=v.reason, stats=stats)
        try:
            result = self.adapter.execute(v.sql)
        except QueryError as exc:
            return AgentTurn(action="error", sql=v.sql, message=str(exc), stats=stats)
        return AgentTurn(action="sql", sql=v.sql, result=result, tables=v.tables, stats=stats)


def summarize_result(
    client,
    question: str,
    result: ExecResult,
    max_rows: int = 20,
) -> str:
    preview = f"columns: {result.columns}\n" + "\n".join(
        str(row) for row in result.rows[:max_rows]
    )
    if result.row_count > max_rows:
        preview += f"\n... ({result.row_count} rows total)"
    resp = client.chat(
        [
            {
                "role": "user",
                "content": (
                    f"Question: {question}\nSQL result:\n{preview}\n\n"
                    "Write a single concise sentence answering the question from "
                    "these results. Use the actual names and numbers."
                ),
            }
        ]
    )
    return (resp.content or "").strip()


class Session:
    """Conversation history wrapper; one session per CLI run or eval question."""

    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy
        self.history: list = []

    def ask(self, question: str) -> AgentTurn:
        import time

        t0 = time.perf_counter()
        turn = self.strategy.run(question, list(self.history))
        turn.wall_s = time.perf_counter() - t0
        self.history.extend(
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": self._describe(turn)},
            ]
        )
        return turn

    @staticmethod
    def _describe(turn: AgentTurn) -> str:
        if turn.action == "sql" and turn.result is not None:
            body = json.dumps(
                {
                    "action": "sql",
                    "sql": turn.sql,
                    "assumption": turn.assumption,
                }
            )
            preview = (
                f"columns={turn.result.columns}, "
                f"first_rows={turn.result.rows[:3]}, "
                f"total_rows={turn.result.row_count}"
            )
            return f"{body}\n-- result preview: {preview}"
        return json.dumps({"action": turn.action, "message": turn.message})


_REACT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": (
                "Execute a read-only SQLite SELECT against the database. Returns "
                "up to 50 rows as JSON. Use it to inspect data before committing "
                "to a final answer."
            ),
            "parameters": {
                "type": "object",
                "properties": {"sql": {"type": "string"}},
                "required": ["sql"],
            },
        },
    }
]

_REACT_SUFFIX = """

You may call the run_sql tool to explore the data before answering.
When you are confident, respond WITHOUT any tool call, using the JSON contract above.
The "sql" you return is the final query; it will be re-executed as the official answer."""


class ReActStrategy(BaseStrategy):
    """Model-controlled tool loop; measured against the default strategy."""

    name = "react"

    def __init__(self, *args, max_iters: int = 4, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_iters = max_iters
        self.system_prompt += _REACT_SUFFIX

    def run(self, question: str, history: list) -> AgentTurn:
        stats = TurnStats()
        messages = (
            [{"role": "system", "content": self.system_prompt}]
            + list(history)
            + [{"role": "user", "content": question}]
        )

        for iteration in range(1, self.max_iters + 1):
            resp = self.client.chat(messages, tools=_REACT_TOOLS)
            stats.record(resp, self.client.spec)

            if not resp.tool_calls:
                data = parse_response(resp.content)
                if data["action"] != "sql":
                    return self._non_sql_turn(data, stats, iteration)
                v = validate_sql(data.get("sql", ""), self.row_cap)
                if not v.ok:
                    return AgentTurn(
                        action="error",
                        sql=data.get("sql"),
                        message=v.reason,
                        attempts=iteration,
                        stats=stats,
                    )
                try:
                    result = self.adapter.execute(v.sql)
                except QueryError as exc:
                    return AgentTurn(
                        action="error",
                        sql=v.sql,
                        message=str(exc),
                        attempts=iteration,
                        stats=stats,
                    )
                return AgentTurn(
                    action="sql",
                    sql=v.sql,
                    result=result,
                    assumption=data.get("assumption"),
                    confidence=data.get("confidence"),
                    tables=v.tables,
                    attempts=iteration,
                    stats=stats,
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": resp.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in resp.tool_calls
                    ],
                }
            )
            for tool_call in resp.tool_calls:
                observation = self._run_tool_call(tool_call)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": observation,
                    }
                )

        return AgentTurn(
            action="error",
            message=f"No final answer after {self.max_iters} iterations.",
            attempts=self.max_iters,
            stats=stats,
        )

    def _run_tool_call(self, tool_call) -> str:
        try:
            args = json.loads(tool_call.function.arguments or "{}")
            v = validate_sql(args.get("sql", ""), row_cap=50)
            if not v.ok:
                return f"REJECTED: {v.reason}"
            result = self.adapter.execute(v.sql)
            return json.dumps(
                {
                    "columns": result.columns,
                    "rows": result.rows[:50],
                    "row_count": result.row_count,
                },
                default=str,
            )
        except QueryError as exc:
            return f"ERROR: {exc}"
        except (TypeError, json.JSONDecodeError) as exc:
            return f"ERROR: invalid tool arguments: {exc}"


class SelfConsistencyStrategy(BaseStrategy):
    """Sample candidates, execute all valid candidates, and vote by result."""

    name = "sc"

    def __init__(self, *args, n: int = 3, temperature: float = 0.7, **kwargs):
        super().__init__(*args, **kwargs)
        self.n = n
        self.temperature = temperature

    def run(self, question: str, history: list) -> AgentTurn:
        stats = TurnStats()
        messages = (
            [{"role": "system", "content": self.system_prompt}]
            + list(history)
            + [{"role": "user", "content": question}]
        )
        candidates = []

        for _ in range(self.n):
            resp = self.client.chat(
                messages,
                json_schema=RESPONSE_SCHEMA,
                temperature=self.temperature,
            )
            stats.record(resp, self.client.spec)
            data = parse_response(resp.content)
            if data["action"] != "sql":
                continue
            v = validate_sql(data.get("sql", ""), self.row_cap)
            if not v.ok:
                continue
            try:
                result = self.adapter.execute(v.sql)
            except QueryError:
                continue
            candidates.append((_result_digest(result), v, result, data))

        if not candidates:
            return AgentTurn(
                action="error",
                message=f"All {self.n} sampled candidates failed.",
                attempts=self.n,
                stats=stats,
            )

        counts: dict[str, int] = {}
        for digest, *_ in candidates:
            counts[digest] = counts.get(digest, 0) + 1
        winner = max(counts, key=counts.get)
        _digest, v, result, data = next(c for c in candidates if c[0] == winner)
        return AgentTurn(
            action="sql",
            sql=v.sql,
            result=result,
            assumption=data.get("assumption"),
            confidence=data.get("confidence"),
            tables=v.tables,
            attempts=self.n,
            stats=stats,
        )


def _result_digest(result: ExecResult) -> str:
    def norm(value):
        if isinstance(value, float):
            value = round(value, 2)
        return (type(value).__name__, str(value))

    rows = sorted(tuple(norm(value) for value in row) for row in result.rows)
    return json.dumps(rows)


_STRATEGIES = {
    "naive": NaiveStrategy,
    "single": SingleCallRepairStrategy,
    "react": ReActStrategy,
    "sc": SelfConsistencyStrategy,
}


def make_strategy(name: str, client, adapter, schema_card: str, **kwargs) -> BaseStrategy:
    if name not in _STRATEGIES:
        raise KeyError(f"Unknown strategy '{name}'. Available: {', '.join(_STRATEGIES)}")
    return _STRATEGIES[name](client, adapter, schema_card, **kwargs)
