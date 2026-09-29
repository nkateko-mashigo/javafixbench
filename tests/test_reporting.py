import json
from types import SimpleNamespace

from javafixbench.reporting import save_run_result


def test_saves_agent_run_as_json(tmp_path):
    generation = SimpleNamespace(
        prompt_tokens=2177,
        output_tokens=122,
        duration_seconds=123.14,
        text="Generated repair",
    )

    result = SimpleNamespace(
        task_id="JFB-001",
        model="gemma4:e2b-it-qat",
        success=True,
        selected_files=("Calculator.java",),
        changed_files=("Calculator.java",),
        generation=generation,
        baseline=None,
        final=None,
        diff="- multiply\n+ divide",
        error=None,
    )

    output_path = save_run_result(
        result,
        output_directory=tmp_path,
    )

    assert output_path.is_file()

    saved = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert saved["task_id"] == "JFB-001"
    assert saved["success"] is True
    assert saved["generation"]["prompt_tokens"] == 2177
    assert saved["generation"]["output_tokens"] == 122
    assert saved["changed_files"] == ["Calculator.java"]