from __future__ import annotations


import shutil
import subprocess

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from javafixbench.repo_graph import scan_repository

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

@app.command()
def scan(
    repository: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Java repository to scan.",
    ),
) -> None:
    """Build and summarise the repository dependency graph."""

    result = scan_repository(repository)

    table = Table(title="Java Repository Graph")
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Java files", str(result.java_file_count))
    table.add_row("Packages", str(result.package_count))
    table.add_row("Declared types", str(result.declared_type_count))
    table.add_row("Import statements", str(result.import_count))
    table.add_row("Internal dependencies", str(result.dependency_count))
    table.add_row(
        "External or unresolved imports",
        str(len(result.unresolved_imports)),
    )

    console.print(table)
if __name__ == "__main__":
    app()