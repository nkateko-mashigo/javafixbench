from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

TEST_SUMMARY_PATTERN = re.compile(
    r"Tests run:\s*(\d+),\s*"
    r"Failures:\s*(\d+),\s*"
    r"Errors:\s*(\d+),\s*"
    r"Skipped:\s*(\d+)"
)


@dataclass(frozen=True)
class TestSummary:
    tests: int
    failures: int
    errors: int
    skipped: int


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    working_directory: Path
    exit_code: int
    duration_seconds: float
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    @property
    def combined_output(self) -> str:
        return "\n".join(
            part for part in (self.stdout, self.stderr) if part
        )


def parse_test_summary(output: str) -> TestSummary | None:
    matches = list(TEST_SUMMARY_PATTERN.finditer(output))

    if not matches:
        return None

    match = matches[-1]

    return TestSummary(
        tests=int(match.group(1)),
        failures=int(match.group(2)),
        errors=int(match.group(3)),
        skipped=int(match.group(4)),
    )


def _normalise_output(value: str | bytes | None) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return value


def run_command(
    command: list[str],
    working_directory: str | Path,
    timeout_seconds: int = 120,
) -> CommandResult:
    directory = Path(working_directory).resolve()

    if not directory.is_dir():
        raise ValueError(
            f"Working directory does not exist: {directory}"
        )

    executable = shutil.which(command[0]) or command[0]
    resolved_command = [executable, *command[1:]]

    started = perf_counter()

    try:
        process = subprocess.run(
            resolved_command,
            cwd=directory,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )

        return CommandResult(
            command=tuple(command),
            working_directory=directory,
            exit_code=process.returncode,
            duration_seconds=perf_counter() - started,
            stdout=process.stdout.strip(),
            stderr=process.stderr.strip(),
        )

    except subprocess.TimeoutExpired as error:
        return CommandResult(
            command=tuple(command),
            working_directory=directory,
            exit_code=124,
            duration_seconds=perf_counter() - started,
            stdout=_normalise_output(error.stdout).strip(),
            stderr=_normalise_output(error.stderr).strip(),
            timed_out=True,
        )


def run_maven_tests(
    repository: str | Path,
    timeout_seconds: int = 120,
) -> CommandResult:
    return run_command(
        ["mvn", "test"],
        working_directory=repository,
        timeout_seconds=timeout_seconds,
    )