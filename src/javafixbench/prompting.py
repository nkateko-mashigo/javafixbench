from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from javafixbench.repo_graph import scan_repository

SYSTEM_PROMPT = """
You are a Java software repair agent running locally.

Your job is to make the smallest correct source-code change that fixes
the reported issue and passes the tests.

Rules:
1. Preserve existing public APIs unless the issue requires otherwise.
2. Do not modify tests.
3. Do not add unrelated features.
4. Return complete replacement contents for changed files only.
5. Return no commentary outside the required repair format.

Required response format:

<repair>
<file path="relative/path/to/File.java">
COMPLETE FILE CONTENT
</file>
</repair>
""".strip()


@dataclass(frozen=True)
class RepairContext:
    system_prompt: str
    prompt: str
    selected_files: tuple[str, ...]
    source_characters: int


def _normalise_path(value: str) -> str:
    return value.replace("\\", "/")


def _select_relevant_files(
    repository: Path,
    targets: list[str],
    maximum_files: int,
) -> tuple[list[str], object]:
    scan = scan_repository(repository)
    available = {
        source.relative_path: source
        for source in scan.files
    }

    selected: list[str] = []

    def add(path: str) -> None:
        normalised = _normalise_path(path)

        if (
            normalised in available
            and normalised not in selected
            and len(selected) < maximum_files
        ):
            selected.append(normalised)

    for target in targets:
        add(target)

    for target in list(selected):
        neighbours = set(scan.graph.successors(target))
        neighbours.update(scan.graph.predecessors(target))

        for neighbour in sorted(neighbours):
            add(neighbour)

    remaining = sorted(
        available,
        key=lambda path: (
            -scan.graph.degree(path),
            path,
        ),
    )

    for path in remaining:
        add(path)

    return selected, scan


def build_repair_context(
    task_directory: str | Path,
    test_output: str,
    *,
    maximum_files: int = 8,
    maximum_source_characters: int = 9_000,
) -> RepairContext:
    repository = Path(task_directory).resolve()
    metadata_path = repository / "task.yaml"

    if not metadata_path.is_file():
        raise ValueError(
            f"Task metadata was not found: {metadata_path}"
        )

    metadata = yaml.safe_load(
        metadata_path.read_text(encoding="utf-8")
    ) or {}

    issue = str(metadata.get("issue", "")).strip()
    targets = [
        _normalise_path(str(path))
        for path in metadata.get("target_files", [])
    ]

    selected, scan = _select_relevant_files(
        repository,
        targets,
        maximum_files,
    )

    remaining_characters = maximum_source_characters
    included_files: list[str] = []
    source_sections: list[str] = []

    for relative_path in selected:
        if remaining_characters <= 0:
            break

        source_path = repository / relative_path
        content = source_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        if len(content) > remaining_characters:
            content = (
                content[:remaining_characters]
                + "\n// [JavaFixBench context truncated]"
            )

        source_sections.append(
            f"--- BEGIN FILE: {relative_path} ---\n"
            f"{content}\n"
            f"--- END FILE: {relative_path} ---"
        )
        included_files.append(relative_path)
        remaining_characters -= len(content)

    dependency_lines = [
        f"{source} -> {target}"
        for source, target in scan.graph.edges()
        if source in included_files and target in included_files
    ]

    dependency_context = (
        "\n".join(dependency_lines)
        if dependency_lines
        else "(No internal import edges detected.)"
    )

    feedback = test_output[-6_000:].strip()

    if not feedback:
        feedback = "(No compiler or test feedback was provided.)"

    prompt = f"""
REPAIR TASK
ID: {metadata.get("id", "unknown")}
Title: {metadata.get("title", "Untitled")}

ISSUE
{issue}

COMPILER AND TEST FEEDBACK
{feedback}

SELECTED REPOSITORY DEPENDENCIES
{dependency_context}

RELEVANT FILES
{chr(10).join(source_sections)}

Return only the required <repair> response.
""".strip()

    return RepairContext(
        system_prompt=SYSTEM_PROMPT,
        prompt=prompt,
        selected_files=tuple(included_files),
        source_characters=(
            maximum_source_characters - remaining_characters
        ),
    )