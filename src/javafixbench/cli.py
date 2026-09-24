from __future__ import annotations

import shutil
import subprocess

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="JavaFixBench: benchmark and evaluate Java repair agents.",
    no_args_is_help=True,
)

console = Console()
@app.callback()
def main() -> None:
    """JavaFixBench command-line tools."""

def tool_version(executable: str, *arguments: str) -> tuple[bool, str]:
    path = shutil.which(executable)

    if path is None:
        return False, "Not found"

    try:
        result = subprocess.run(
            [path, *arguments],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)

    output = "\n".join(
        part.strip()
        for part in (result.stdout, result.stderr)
        if part.strip()
    )

    first_line = output.splitlines()[0] if output else path
    return result.returncode == 0, first_line


@app.command()
def doctor() -> None:
    """Check whether the required development tools are available."""

    tools = [
        ("Python", "python", "--version"),
        ("Java", "java", "-version"),
        ("Java compiler", "javac", "-version"),
        ("Maven", "mvn", "--version"),
        ("Git", "git", "--version"),
    ]

    table = Table(title="JavaFixBench Environment")
    table.add_column("Tool")
    table.add_column("Status")
    table.add_column("Version")

    all_ready = True

    for name, executable, argument in tools:
        ready, version = tool_version(executable, argument)
        all_ready = all_ready and ready

        table.add_row(
            name,
            "[green]PASS[/green]" if ready else "[red]MISSING[/red]",
            version,
        )

    console.print(table)

    if not all_ready:
        raise typer.Exit(code=1)

    console.print("\n[bold green]Environment ready.[/bold green]")


if __name__ == "__main__":
    app()