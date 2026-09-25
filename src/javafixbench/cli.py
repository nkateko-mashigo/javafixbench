from __future__ import annotations


import shutil
import subprocess

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from javafixbench.repo_graph import scan_repository
from javafixbench.runner import parse_test_summary, run_maven_tests

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
@app.command()
def evaluate(
    repository: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Maven repository to evaluate.",
    ),
    timeout: int = typer.Option(
        120,
        min=1,
        help="Maximum execution time in seconds.",
    ),
) -> None:
    """Compile the project, run its tests and report feedback."""

    console.print(f"Evaluating [cyan]{repository}[/cyan]...")

    result = run_maven_tests(
        repository,
        timeout_seconds=timeout,
    )
    summary = parse_test_summary(result.combined_output)

    table = Table(title="Java Repair Evaluation")
    table.add_column("Metric")
    table.add_column("Result", justify="right")

    status = "TIMEOUT" if result.timed_out else (
        "PASSED" if result.passed else "FAILED"
    )

    table.add_row("Status", status)
    table.add_row("Exit code", str(result.exit_code))
    table.add_row(
        "Duration",
        f"{result.duration_seconds:.2f} seconds",
    )

    if summary is not None:
        table.add_row("Tests", str(summary.tests))
        table.add_row("Failures", str(summary.failures))
        table.add_row("Errors", str(summary.errors))
        table.add_row("Skipped", str(summary.skipped))

    console.print(table)

    if not result.passed:
        output_lines = result.combined_output.splitlines()
        output_tail = "\n".join(output_lines[-30:])

        if output_tail:
            console.print("\n[bold red]Test feedback:[/bold red]")
            console.print(output_tail)

        raise typer.Exit(code=1)
if __name__ == "__main__":
    app()