import sys
from pathlib import Path

from javafixbench.runner import (
    parse_test_summary,
    run_command,
)


def test_parses_maven_test_summary() -> None:
    output = (
        "Tests run: 3, Failures: 2, "
        "Errors: 0, Skipped: 0"
    )

    summary = parse_test_summary(output)

    assert summary is not None
    assert summary.tests == 3
    assert summary.failures == 2
    assert summary.errors == 0
    assert summary.skipped == 0


def test_runs_command_and_captures_output(
    tmp_path: Path,
) -> None:
    result = run_command(
        [sys.executable, "-c", "print('runner ready')"],
        working_directory=tmp_path,
        timeout_seconds=10,
    )

    assert result.passed
    assert result.exit_code == 0
    assert result.stdout == "runner ready"
    assert not result.timed_out