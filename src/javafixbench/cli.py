from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from javafixbench.agent import run_repair_agent
from javafixbench.reporting import save_run_result
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

    if result.timed_out:
        status = "TIMEOUT"
    elif result.passed:
        status = "PASSED"
    else:
        status = "FAILED"

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


@app.command()
def repair(
    task: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Path to the Java benchmark task.",
    ),
) -> None:
    """Run the Gemma 4 repair agent on a Java task."""

    console.print(f"\n[bold cyan]Repairing:[/bold cyan] {task}")
    console.print(
        "[yellow]Gemma 4 may take several minutes on this PC.[/yellow]\n"
    )

    result = run_repair_agent(task)
    result_file = save_run_result(result)

    table = Table(title="JavaFixBench Repair Result")
    table.add_column("Metric")
    table.add_column("Result")

    table.add_row(
        "Status",
        "[green]PASSED[/green]"
        if result.success
        else "[red]FAILED[/red]",
    )
    table.add_row("Task", result.task_id)
    table.add_row("Model", result.model)
    table.add_row("Result file", str(result_file))
    table.add_row(
        "Selected files",
        str(len(result.selected_files)),
    )
    table.add_row(
        "Changed files",
        str(len(result.changed_files)),
    )

    if result.generation is not None:
        table.add_row(
            "Prompt tokens",
            str(result.generation.prompt_tokens),
        )
        table.add_row(
            "Output tokens",
            str(result.generation.output_tokens),
        )
        table.add_row(
            "Model duration",
            f"{result.generation.duration_seconds:.2f} seconds",
        )
    else:
        table.add_row("Prompt tokens", "N/A")
        table.add_row("Output tokens", "N/A")
        table.add_row("Model duration", "N/A")

    if result.final is not None:
        summary = parse_test_summary(
            result.final.combined_output
        )

        if summary is not None:
            table.add_row("Tests", str(summary.tests))
            table.add_row("Failures", str(summary.failures))
            table.add_row("Errors", str(summary.errors))
            table.add_row("Skipped", str(summary.skipped))

    console.print(table)

    if result.diff:
        console.print("\n[bold]Generated patch:[/bold]")
        console.print(
            Syntax(
                result.diff,
                "diff",
                theme="monokai",
                line_numbers=False,
            )
        )

    if result.error:
        console.print(
            f"\n[bold red]Error:[/bold red] {result.error}"
        )

    if not result.success:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()