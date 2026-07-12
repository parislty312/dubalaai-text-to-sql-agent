from src.cli import handle_command, result_table
from src.db import ExecResult


def test_result_table_renders():
    result = ExecResult(
        columns=["Name", "Total"],
        rows=[("Rock", 826.65)],
        truncated=False,
        elapsed_ms=2.0,
    )
    table = result_table(result)
    assert table.row_count == 1


def test_handle_command_exit():
    assert handle_command("exit", None) == "exit"
    assert handle_command("quit", None) == "exit"


def test_handle_command_unknown_slash():
    assert handle_command("/bogus", None) == "handled"


def test_plain_question_not_a_command():
    assert handle_command("how many artists?", None) is None
