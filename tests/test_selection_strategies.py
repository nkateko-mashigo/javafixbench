from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from typer.testing import CliRunner

from javafixbench.agent import run_repair_agent
from javafixbench.cli import app
from javafixbench.model import GenerationResult
from javafixbench.prompting import SelectionStrategy, build_repair_context
from javafixbench.reporting import build_run_record, save_run_result


TARGET = "src/main/java/sample/api/Entry.java"
HELPER = "src/main/java/sample/zdep/Helper.java"
TEST = "src/test/java/sample/EntryTest.java"
ORIGINAL = (
    "package sample.api;\n"
    "import sample.zdep.Helper;\n"
    "public class Entry {\n"
    "    public int value() { return new Helper().value(); }\n"
    "}\n"
)
REPLACEMENT = ORIGINAL.replace("new Helper().value()", "2")
FEEDBACK = (
    "[ERROR] Tests run: 1, Failures: 1, Errors: 0, Skipped: 0\n"
    "[ERROR] EntryTest.value:8 expected: <2> but was: <1>\n"
)


class FakeClient:
    model = "test-model"

    def __init__(self, response: str | None = None) -> None:
        self.response = response if response is not None else (
            f'<repair><file path="{TARGET}">\n'
            f"{REPLACEMENT}</file></repair>"
        )
        self.calls: list[dict[str, object]] = []

    def generate(self, prompt: str, **settings) -> GenerationResult:
        self.calls.append({"prompt": prompt, **settings})
        return GenerationResult(
            text=self.response,
            model=self.model,
            prompt_tokens=100,
            output_tokens=20,
            duration_seconds=0.0,
            done=True,
            done_reason="stop",
        )


def command_result(passed: bool) -> SimpleNamespace:
    return SimpleNamespace(
        passed=passed,
        exit_code=0 if passed else 1,
        timed_out=False,
        duration_seconds=0.0,
        combined_output=(
            "Tests run: 1, Failures: 0, Errors: 0, Skipped: 0\n"
            if passed else FEEDBACK
        ),
    )


def fake_maven(repository: Path, **settings) -> SimpleNamespace:
    passed = "return 2;" in (repository / TARGET).read_text(encoding="utf-8")
    return command_result(passed)


class SelectionStrategyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.task = self.root / "task"
        self.task.mkdir()
        (self.task / "task.yaml").write_text(
            "id: JFB-TEST\ntitle: Wrong value\nissue: Return the correct value.\n"
            f"target_files:\n  - {TARGET}\n",
            encoding="utf-8",
        )
        sources = {
            TARGET: ORIGINAL,
            HELPER: (
                "package sample.zdep;\n"
                "public class Helper { public int value() { return 1; } }\n"
            ),
            TEST: (
                "package sample;\nimport sample.api.Entry;\n"
                "public class EntryTest { private Entry entry; }\n"
            ),
        }
        for index in range(8):
            path = f"src/main/java/sample/a/Noise{index}.java"
            sources[path] = (
                f"package sample.a;\npublic class Noise{index} {{}}\n"
            )
        for path, content in sources.items():
            destination = self.task / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

    def test_default_matches_explicit_graph_selection(self) -> None:
        default = build_repair_context(self.task, FEEDBACK)
        explicit = build_repair_context(
            self.task, FEEDBACK, strategy="graph_guided"
        )
        self.assertEqual(default, explicit)

    def test_graph_uses_dependencies_while_file_order_uses_paths(self) -> None:
        graph = build_repair_context(
            self.task, FEEDBACK, maximum_files=3, strategy="graph_guided"
        )
        ordered = build_repair_context(
            self.task, FEEDBACK, maximum_files=3, strategy="file_order"
        )
        self.assertEqual(graph.selected_files, (TARGET, HELPER, TEST))
        self.assertEqual(ordered.selected_files, (
            TARGET,
            "src/main/java/sample/a/Noise0.java",
            "src/main/java/sample/a/Noise1.java",
        ))
        self.assertEqual(graph.system_prompt, ordered.system_prompt)
        for context in (graph, ordered):
            self.assertIn("EntryTest.value:8 expected: <2> but was: <1>", context.prompt)

    def test_both_modes_keep_multiple_targets_and_same_file_limit(self) -> None:
        other = "src/main/java/sample/a/Noise7.java"
        (self.task / "task.yaml").write_text(
            f"id: JFB-TEST\ntarget_files:\n  - {TARGET}\n  - {other}\n",
            encoding="utf-8",
        )
        for strategy in SelectionStrategy:
            with self.subTest(strategy=strategy.value):
                context = build_repair_context(
                    self.task, FEEDBACK, maximum_files=4, strategy=strategy
                )
                self.assertEqual(context.selected_files[:2], (TARGET, other))
                self.assertEqual(len(context.selected_files), 4)

    def test_unknown_strategy_is_rejected_before_tests_or_generation(self) -> None:
        client = FakeClient()
        with patch("javafixbench.agent.run_maven_tests") as tests:
            with self.assertRaises(ValueError):
                run_repair_agent(self.task, client=client, strategy="unknown")
        tests.assert_not_called()
        self.assertEqual(client.calls, [])

    def test_pipeline_saves_each_strategy_and_keeps_source_task_unchanged(self) -> None:
        settings = []
        selected = []
        for strategy in SelectionStrategy:
            with self.subTest(strategy=strategy.value):
                client = FakeClient()
                with patch("javafixbench.agent.run_maven_tests", side_effect=fake_maven):
                    result = run_repair_agent(self.task, client=client, strategy=strategy)
                self.assertTrue(result.success)
                self.assertEqual(result.changed_files, (TARGET,))
                self.assertEqual(len(result.selected_files), 8)
                self.assertIn("return 2;", result.diff)
                selected.append(result.selected_files)
                record = build_run_record(result)
                self.assertEqual(record["strategy"], f"{strategy.value}_single_pass")
                saved = save_run_result(result, self.root / "results")
                self.assertEqual(json.loads(saved.read_text(encoding="utf-8"))["strategy"], record["strategy"])
                settings.append({key: value for key, value in client.calls[0].items() if key != "prompt"})
                self.assertEqual((self.task / TARGET).read_text(encoding="utf-8"), ORIGINAL)
        self.assertNotEqual(selected[0], selected[1])
        self.assertEqual(settings[0], settings[1])
        self.assertEqual(settings[0]["context_size"], 4096)
        self.assertEqual(settings[0]["max_tokens"], 768)
        self.assertEqual(settings[0]["temperature"], 0.0)
        self.assertEqual(settings[0]["seed"], 42)

    def test_already_passing_task_keeps_its_strategy_label(self) -> None:
        client = FakeClient()
        with patch("javafixbench.agent.run_maven_tests", return_value=command_result(True)):
            result = run_repair_agent(self.task, client=client, strategy="file_order")
        self.assertFalse(result.success)
        self.assertIsNone(result.generation)
        self.assertEqual(client.calls, [])
        self.assertEqual(build_run_record(result)["strategy"], "file_order_single_pass")

    def test_invalid_model_response_keeps_its_strategy_label(self) -> None:
        with patch("javafixbench.agent.run_maven_tests", side_effect=fake_maven):
            result = run_repair_agent(
                self.task, client=FakeClient("invalid response"), strategy="file_order"
            )
        self.assertFalse(result.success)
        self.assertIsNone(result.final)
        self.assertIn("<repair>", result.error)
        self.assertEqual(build_run_record(result)["strategy"], "file_order_single_pass")

    def test_cli_help_and_invalid_choice(self) -> None:
        runner = CliRunner()
        help_result = runner.invoke(app, ["repair", "--help"])
        self.assertEqual(help_result.exit_code, 0, help_result.output)
        for word in ("--strategy", "graph_guided", "file_order"):
            self.assertIn(word, help_result.output)
        with patch("javafixbench.cli.run_repair_agent") as agent:
            invalid = runner.invoke(app, ["repair", str(self.task), "--strategy", "unknown"])
        self.assertEqual(invalid.exit_code, 2, invalid.output)
        agent.assert_not_called()

    def test_cli_runs_both_modes_and_saves_their_labels(self) -> None:
        runner = CliRunner()
        for strategy in SelectionStrategy:
            with self.subTest(strategy=strategy.value):
                with (
                    patch("javafixbench.agent.OllamaClient", return_value=FakeClient()),
                    patch("javafixbench.agent.run_maven_tests", side_effect=fake_maven),
                    patch("javafixbench.cli.save_run_result", side_effect=lambda result: save_run_result(result, self.root / "cli_results")),
                ):
                    result = runner.invoke(app, ["repair", str(self.task), "--strategy", strategy.value])
                self.assertEqual(result.exit_code, 0, str(result.exception) + result.output)
                self.assertIn(f"{strategy.value}_single_pass", result.output)
        records = [json.loads(path.read_text(encoding="utf-8")) for path in (self.root / "cli_results").glob("*.json")]
        self.assertEqual({record["strategy"] for record in records}, {
            "graph_guided_single_pass", "file_order_single_pass",
        })


if __name__ == "__main__":
    unittest.main()