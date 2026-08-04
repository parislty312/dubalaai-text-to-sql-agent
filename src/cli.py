"""Interactive CLI. Run with: python -m src.cli."""
import argparse

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .agent import Session, make_strategy, summarize_result
from .config import DEFAULT_MODEL, MODEL_REGISTRY, get_model
from .context import build_schema_card
from .db import SQLiteAdapter
from .providers import LLMClient


STRATEGY_NAMES = ("naive", "single", "react", "sc")
HELP = """Commands:
  exit | quit          end the session
  /schema              show the schema card sent to the model
  /model <id>          switch model (available: {models})
  /strategy <name>     switch strategy (naive | single | react | sc)
  /help                this message
Anything else is treated as a question about the database."""


def result_table(result) -> Table:
    table = Table(show_header=True, header_style="bold")
    for column in result.columns:
        table.add_column(str(column))
    for row in result.rows[:50]:
        table.add_row(*[("" if value is None else str(value)) for value in row])
    return table


def handle_command(line: str, app) -> str | None:
    """Return 'exit', 'handled', or None when the line is a user question."""
    stripped = line.strip()
    if stripped.lower() in ("exit", "quit"):
        return "exit"
    if not stripped.startswith("/"):
        return None

    parts = stripped.split()
    command, args = parts[0].lower(), parts[1:]
    if app is None:
        return "handled"

    if command == "/schema":
        app.console.print(app.schema_card)
    elif command == "/model" and args:
        try:
            app.switch_model(args[0])
            app.console.print(f"[green]Switched to {args[0]}[/green]")
        except (KeyError, RuntimeError) as exc:
            app.console.print(f"[red]{exc}[/red]")
    elif command == "/strategy" and args:
        try:
            app.switch_strategy(args[0])
            app.console.print(f"[green]Strategy: {args[0]}[/green]")
        except KeyError as exc:
            app.console.print(f"[red]{exc}[/red]")
    else:
        app.console.print(HELP.format(models=", ".join(MODEL_REGISTRY)))
    return "handled"


class App:
    def __init__(
        self,
        model_id: str,
        strategy_name: str,
        db_path: str,
        summarize: bool = True,
    ):
        self.console = Console()
        self.adapter = SQLiteAdapter(db_path)
        self.schema_card = build_schema_card(self.adapter)
        self.summarize = summarize
        self.model_id = model_id
        self.strategy_name = strategy_name
        self._rebuild()

    def _rebuild(self):
        self.client = LLMClient(get_model(self.model_id))
        strategy = make_strategy(
            self.strategy_name,
            self.client,
            self.adapter,
            self.schema_card,
        )
        self.session = Session(strategy)

    def switch_model(self, model_id: str):
        get_model(model_id)
        self.model_id = model_id
        self._rebuild()

    def switch_strategy(self, name: str):
        if name not in STRATEGY_NAMES:
            raise KeyError(f"Unknown strategy '{name}'")
        self.strategy_name = name
        self._rebuild()

    def ask(self, question: str):
        with self.console.status("[dim]thinking...[/dim]"):
            turn = self.session.ask(question)

        if turn.action == "sql":
            self.console.print(
                Panel(
                    Syntax(turn.sql or "", "sql", word_wrap=True),
                    title="SQL",
                    border_style="cyan",
                )
            )
            self.console.print(result_table(turn.result))
            footer = (
                f"[dim]{turn.result.row_count} rows"
                f"{' (truncated)' if turn.result.truncated else ''} | "
                f"{turn.wall_s:.2f}s | {self.model_id}/{self.strategy_name} | "
                f"attempts {turn.attempts} | confidence {turn.confidence} | "
                f"tables {', '.join(turn.tables)}[/dim]"
            )
            self.console.print(footer)
            if turn.assumption:
                self.console.print(f"[yellow]Assumption: {turn.assumption}[/yellow]")
            if self.summarize and turn.result.row_count:
                summary = summarize_result(self.client, question, turn.result)
                self.console.print(f"[bold]{summary}[/bold]")
        elif turn.action == "clarify":
            self.console.print(f"[yellow]Need clarification:[/yellow] {turn.message}")
        elif turn.action == "decline":
            self.console.print(f"[dim]{turn.message}[/dim]")
        else:
            self.console.print(f"[red]Failed:[/red] {turn.message}")
            if turn.sql:
                self.console.print(
                    Panel(
                        Syntax(turn.sql, "sql"),
                        title="last SQL tried",
                        border_style="red",
                    )
                )


def main():
    parser = argparse.ArgumentParser(description="Text-to-SQL agent CLI")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODEL_REGISTRY))
    parser.add_argument("--strategy", default="single", choices=STRATEGY_NAMES)
    parser.add_argument("--db", default="data/personal_finance.db")
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="skip the natural-language answer (saves one LLM call)",
    )
    args = parser.parse_args()

    app = App(args.model, args.strategy, args.db, summarize=not args.no_summary)
    app.console.print(
        Panel(
            f"Text-to-SQL agent | model [bold]{args.model}[/bold] | "
            f"strategy [bold]{args.strategy}[/bold]\nType a question, or /help.",
            border_style="green",
        )
    )

    while True:
        try:
            line = input("ask> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        status = handle_command(line, app)
        if status == "exit":
            break
        if status == "handled":
            continue
        app.ask(line)


if __name__ == "__main__":
    main()
