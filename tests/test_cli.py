"""Smoke tests for the Typer CLI entry points.

These tests only exercise commands and code paths that short-circuit before
any LLM or network call (``version``, ``--help``, and the missing-file guard
in ``evaluate``). They must never require API keys or network access.
"""

from truthfulness_evaluator import __version__
from truthfulness_evaluator.truth import app
from typer.testing import CliRunner

runner = CliRunner()


def test_version():
    """The version command exits cleanly and prints the package version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help():
    """Top-level --help lists both available commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "evaluate" in result.output
    assert "version" in result.output


def test_evaluate_help():
    """evaluate --help documents the document argument and key options."""
    result = runner.invoke(app, ["evaluate", "--help"])
    assert result.exit_code == 0
    assert "document" in result.output.lower()
    assert "--mode" in result.output


def test_evaluate_missing_file():
    """evaluate fails fast with a clear error when the document does not exist."""
    result = runner.invoke(app, ["evaluate", "/nonexistent/path/doc.txt"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()
