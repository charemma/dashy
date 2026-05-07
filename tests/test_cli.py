"""Tests for the dashy CLI entry point."""

from __future__ import annotations

from click.testing import CliRunner

from dashy import __version__
from dashy.cli import PLACEHOLDER_MESSAGE, main


def test_cli_prints_placeholder() -> None:
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert PLACEHOLDER_MESSAGE in result.output


def test_cli_help_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Print a morning briefing." in result.output


def test_version_constant_matches_package() -> None:
    assert __version__ == "0.1.0"
