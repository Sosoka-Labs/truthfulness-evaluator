"""Smoke tests for the Typer CLI entry points.

These tests only exercise commands and code paths that short-circuit before
any LLM or network call (``version``, ``--help``, and the missing-file guard
in ``evaluate``). They must never require API keys or network access.

Help output is rendered by Rich, whose width depends on the terminal; CI has no
TTY and can fall back to 80 columns, truncating option names in the panels. So
the *invocation* tests only assert the stable exit code, and the presence of the
document argument and ``--mode`` option is checked by introspecting the command
directly — independent of how the help happens to render.
"""

import re

from truthfulness_evaluator import __version__
from truthfulness_evaluator.truth import app
from typer.main import get_command
from typer.testing import CliRunner

runner = CliRunner()

# Rich reads COLUMNS before probing the terminal, so this pins a wide width
# regardless of TTY presence.
WIDE_ENV = {"COLUMNS": "1000"}
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    """Strip ANSI escape codes so assertions are rendering-independent."""
    return _ANSI.sub("", text)


def test_version():
    """The version command exits cleanly and prints the package version."""
    result = runner.invoke(app, ["version"], env=WIDE_ENV)
    assert result.exit_code == 0
    assert __version__ in _plain(result.output)


def test_help_lists_commands():
    """The app exposes exactly the evaluate and version commands, and --help runs."""
    assert set(get_command(app).commands) == {"evaluate", "version"}
    assert runner.invoke(app, ["--help"], env=WIDE_ENV).exit_code == 0


def test_evaluate_exposes_document_and_mode():
    """evaluate takes a document argument and a --mode option, and --help runs."""
    evaluate = get_command(app).commands["evaluate"]
    option_flags = {flag for param in evaluate.params for flag in param.opts}
    param_names = {param.name for param in evaluate.params}
    assert "--mode" in option_flags
    assert "document" in param_names
    assert runner.invoke(app, ["evaluate", "--help"], env=WIDE_ENV).exit_code == 0


def test_evaluate_missing_file():
    """evaluate fails fast with a clear error when the document does not exist."""
    result = runner.invoke(app, ["evaluate", "/nonexistent/path/doc.txt"], env=WIDE_ENV)
    assert result.exit_code != 0
    assert "not found" in _plain(result.output).lower()
