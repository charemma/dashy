"""Command-line entry point for dashy."""

from __future__ import annotations

import click
from rich.console import Console

from dashy import __version__

_PLACEHOLDER_MESSAGE = (
    f"[bold cyan]dashy[/bold cyan] v{__version__} -- "
    "[dim]morning briefing CLI (not yet implemented)[/dim]"
)


@click.command()
@click.version_option(version=__version__, prog_name="dashy")
def main() -> None:
    """dashy -- your morning briefing in the terminal."""
    console = Console()
    console.print(_PLACEHOLDER_MESSAGE)


if __name__ == "__main__":
    main()
