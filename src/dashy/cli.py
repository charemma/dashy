"""CLI entry point for dashy."""

import click
from rich.console import Console


@click.command()
def main() -> None:
    """Morning briefing CLI - fetches location, weather, and news."""
    console = Console()
    console.print("[bold cyan]dashy[/bold cyan] placeholder - project scaffolding complete")


if __name__ == "__main__":
    main()
