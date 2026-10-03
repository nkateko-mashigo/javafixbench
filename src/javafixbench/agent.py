from __future__ import annotations

import difflib
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

from javafixbench.model import (
    GenerationResult,
    OllamaClient,
)
from javafixbench.patching import (
    RepairFormatError,
    apply_repair_changes,
    parse_repair_response,
)
from javafixbench.prompting import (
    SelectionStrategy,
    build_repair_context,
)
from javafixbench.runner import CommandResult, run_maven_tests


@dataclass(frozen=True)
class AgentRunResult:
    task_id: str
    model: str
    success: bool
    baseline: CommandResult
    final: CommandResult | None
    selected_files: tuple[str, ...]
    changed_files: tuple[str, ...]
    model_response: str
    generation: GenerationResult | None
    diff: str
    error: str | None = None
    strategy: str = "graph_guided_single_pass"


def _load_task_id(task_directory: Path) -> str:
    metadata_path = task_directory / "task.yaml"
    metadata = yaml.safe_load(
        metadata_path.read_text(encoding="utf-8")
    ) or {}

    return str(metadata.get("id", "unknown"))


def _create_diff(
    repository: Path,
    original_contents: dict[str, str],
    changed_files: tuple[str, ...],
) -> str:
    sections: list[str] = []

    for relative_path in changed_files:
        original = original_contents.get(relative_path, "")
        updated_path = repository / relative_path

        if not updated_path.is_file():
            continue

        updated = updated_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        difference = difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
            lineterm="",
        )

        sections.extend(difference)
        sections.append("")

    return "\n".join(sections).strip()


def run_repair_agent(
    task_directory: str | Path,
    *,
    client: OllamaClient | None = None,
    test_timeout_seconds: int = 120,
    strategy: SelectionStrategy | str = SelectionStrategy.GRAPH_GUIDED,
) -> AgentRunResult:
    selected_strategy = SelectionStrategy(strategy)
    strategy_name = f"{selected_strategy.value}_single_pass"
    source_task = Path(task_directory).resolve()

    if not source_task.is_dir():
        raise ValueError(
            f"Task directory does not exist: {source_task}"
        )

    task_id = _load_task_id(source_task)
    model_client = client or OllamaClient()

    with tempfile.TemporaryDirectory(
        prefix="javafixbench-"
    ) as temporary_directory:
        workspace = (
            Path(temporary_directory) / source_task.name
        )

        shutil.copytree(
            source_task,
            workspace,
            ignore=shutil.ignore_patterns(
                "target",
                "build",
                ".gradle",
                ".git",
                ".idea",
                ".venv",
            ),
        )

        baseline = run_maven_tests(
            workspace,
            timeout_seconds=test_timeout_seconds,
        )

        if baseline.passed:
            return AgentRunResult(
                task_id=task_id,
                model=model_client.model,
                success=False,
                baseline=baseline,
                final=None,
                selected_files=(),
                changed_files=(),
                model_response="",
                generation=None,
                diff="",
                error=(
                    "The benchmark already passes before repair."
                ),
                strategy=strategy_name,
            )

        context = build_repair_context(
            workspace,
            baseline.combined_output,
            strategy=selected_strategy,
        )

        original_contents = {
            relative_path: (
                workspace / relative_path
            ).read_text(
                encoding="utf-8",
                errors="replace",
            )
            for relative_path in context.selected_files
        }

        generation = model_client.generate(
            context.prompt,
            system=context.system_prompt,
            temperature=0.0,
            context_size=4096,
            max_tokens=768,
            seed=42,
        )

        try:
            changes = parse_repair_response(
                generation.text
            )

            apply_repair_changes(
                workspace,
                changes,
                allowed_paths=context.selected_files,
            )
        except RepairFormatError as error:
            return AgentRunResult(
                task_id=task_id,
                model=model_client.model,
                success=False,
                baseline=baseline,
                final=None,
                selected_files=context.selected_files,
                changed_files=(),
                model_response=generation.text,
                generation=generation,
                diff="",
                error=str(error),
                strategy=strategy_name,
            )

        changed_files = tuple(
            change.path
            for change in changes
            if original_contents[change.path].splitlines()
            != (workspace / change.path).read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()
        )

        difference = _create_diff(
            workspace,
            original_contents,
            changed_files,
        )

        final = run_maven_tests(
            workspace,
            timeout_seconds=test_timeout_seconds,
        )

        return AgentRunResult(
            task_id=task_id,
            model=model_client.model,
            success=final.passed,
            baseline=baseline,
            final=final,
            selected_files=context.selected_files,
            changed_files=changed_files,
            model_response=generation.text,
            generation=generation,
            diff=difference,
            error=None if final.passed else (
                "The generated repair did not pass all tests."
            ),
            strategy=strategy_name,
        )