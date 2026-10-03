from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from javafixbench.agent import AgentRunResult
from javafixbench.runner import CommandResult, parse_test_summary


def _command_record(
    result: CommandResult | None,
) -> dict[str, Any] | None:
    if result is None:
        return None

    summary = parse_test_summary(result.combined_output)

    return {
        "passed": result.passed,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "duration_seconds": result.duration_seconds,
        "tests": summary.tests if summary else None,
        "failures": summary.failures if summary else None,
        "errors": summary.errors if summary else None,
        "skipped": summary.skipped if summary else None,
        "output": result.combined_output,
    }


def build_run_record(
    result: AgentRunResult,
    *,
    strategy: str | None = None,
) -> dict[str, Any]:
    generation = result.generation

    return {
        "schema_version": 2,
        "recorded_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "task_id": result.task_id,
        "model": result.model,
        "strategy": result.strategy if strategy is None else strategy,
        "success": result.success,
        "selected_files": list(result.selected_files),
        "changed_files": list(result.changed_files),
        "generation": (
            {
                "prompt_tokens": generation.prompt_tokens,
                "output_tokens": generation.output_tokens,
                "duration_seconds": generation.duration_seconds,
                "response": generation.text,
                "done": generation.done,
                "done_reason": generation.done_reason,
                "requested_settings": generation.requested_settings,
            }
            if generation is not None
            else None
        ),
        "baseline": _command_record(result.baseline),
        "final": _command_record(result.final),
        "diff": result.diff,
        "error": result.error,
    }


def save_run_result(
    result: AgentRunResult,
    output_directory: str | Path = "experiments/results",
    *,
    strategy: str | None = None,
) -> Path:
    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )

    safe_task_id = "".join(
        character
        if character.isalnum() or character in "-_"
        else "-"
        for character in result.task_id
    )

    output_path = destination / (
        f"{safe_task_id}_{timestamp}.json"
    )

    record = build_run_record(
        result,
        strategy=strategy,
    )

    output_path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path