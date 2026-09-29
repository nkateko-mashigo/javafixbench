from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

REPAIR_PATTERN = re.compile(
    r"<repair>(?P<body>.*?)</repair>",
    re.IGNORECASE | re.DOTALL,
)

FILE_PATTERN = re.compile(
    r"""<file\s+path=["'](?P<path>[^"']+)["']\s*>"""
    r"(?P<content>.*?)"
    r"</file>",
    re.IGNORECASE | re.DOTALL,
)


class RepairFormatError(ValueError):
    """Raised when a model response has an invalid repair format."""


@dataclass(frozen=True)
class RepairChange:
    path: str
    content: str


def _normalise_path(value: str) -> str:
    return value.strip().replace("\\", "/")


def _validate_relative_java_path(value: str) -> str:
    normalised = _normalise_path(value)
    path = PurePosixPath(normalised)

    if not normalised:
        raise RepairFormatError("A repair file path is empty.")

    if path.is_absolute():
        raise RepairFormatError(
            f"Absolute paths are not allowed: {normalised}"
        )

    if ".." in path.parts:
        raise RepairFormatError(
            f"Parent-directory traversal is not allowed: {normalised}"
        )

    if ":" in path.parts[0]:
        raise RepairFormatError(
            f"Drive paths are not allowed: {normalised}"
        )

    if path.suffix.lower() != ".java":
        raise RepairFormatError(
            f"Only Java source files may be changed: {normalised}"
        )

    normalised = path.as_posix()

    if normalised.startswith("src/test/"):
        raise RepairFormatError(
            f"Test files may not be changed: {normalised}"
        )

    return normalised


def parse_repair_response(
    response: str,
) -> tuple[RepairChange, ...]:
    repair_match = REPAIR_PATTERN.search(response)

    if repair_match is None:
        raise RepairFormatError(
            "The response does not contain a <repair> block."
        )

    body = repair_match.group("body")
    file_matches = list(FILE_PATTERN.finditer(body))

    if not file_matches:
        raise RepairFormatError(
            "The repair block does not contain any files."
        )

    changes: list[RepairChange] = []
    seen_paths: set[str] = set()

    for match in file_matches:
        path = _validate_relative_java_path(
            match.group("path")
        )
        content = match.group("content").strip("\r\n")

        if not content.strip():
            raise RepairFormatError(
                f"Replacement content is empty: {path}"
            )

        if path in seen_paths:
            raise RepairFormatError(
                f"The response changes the same file twice: {path}"
            )

        seen_paths.add(path)
        changes.append(
            RepairChange(
                path=path,
                content=f"{content}\n",
            )
        )

    return tuple(changes)


def apply_repair_changes(
    repository: str | Path,
    changes: Iterable[RepairChange],
    *,
    allowed_paths: Iterable[str],
) -> tuple[Path, ...]:
    root = Path(repository).resolve()

    if not root.is_dir():
        raise ValueError(
            f"Repository directory does not exist: {root}"
        )

    allowed = {
        _normalise_path(path)
        for path in allowed_paths
    }

    applied: list[Path] = []

    for change in changes:
        if change.path not in allowed:
            raise RepairFormatError(
                f"The model attempted to change an "
                f"unselected file: {change.path}"
            )

        destination = (
            root / Path(*PurePosixPath(change.path).parts)
        ).resolve()

        try:
            destination.relative_to(root)
        except ValueError as error:
            raise RepairFormatError(
                f"Repair path escapes the repository: {change.path}"
            ) from error

        if not destination.is_file():
            raise RepairFormatError(
                f"Repair target does not exist: {change.path}"
            )

        destination.write_text(
            change.content,
            encoding="utf-8",
            newline="\n",
        )
        applied.append(destination)

    return tuple(applied)