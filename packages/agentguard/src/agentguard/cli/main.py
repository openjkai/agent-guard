"""AgentGuard command-line interface."""

from __future__ import annotations

import typer
from rich.console import Console

from agentguard import __version__

app = typer.Typer(
    name="agentguard",
    help="Open-source release gate for AI agents.",
    no_args_is_help=True,
)
console = Console()


@app.callback()
def main() -> None:
    """AgentGuard CLI — run scenarios, replay failures, gate releases."""


@app.command()
def version() -> None:
    """Print the installed AgentGuard version."""
    console.print(f"agentguard {__version__}")


if __name__ == "__main__":
    app()
