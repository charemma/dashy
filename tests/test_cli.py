"""Smoke tests for the dashy CLI entry point."""

from __future__ import annotations

from click.testing import CliRunner

from dashy import __version__
from dashy.cli import main


def test_cli_runs_and_prints_placeholder() -> None:
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 0
    assert "dashy" in result.output
    assert __version__ in result.output


def test_cli_help_includes_description() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "morning briefing" in result.output


def test_cli_version_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output
