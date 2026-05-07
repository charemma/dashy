"""Command line entry point for dashy."""

from __future__ import annotations

import click

PLACEHOLDER_MESSAGE = "dashy: morning briefing CLI (not yet implemented)"


@click.command()
@click.version_option(package_name="dashy")
def main() -> None:
    """Print a morning briefing."""
    click.echo(PLACEHOLDER_MESSAGE)


if __name__ == "__main__":
    main()
