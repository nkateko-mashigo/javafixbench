from pathlib import Path

from javafixbench.prompting import build_repair_context


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_builds_graph_guided_repair_context(
    tmp_path: Path,
) -> None:
    task = tmp_path / "task"

    write_file(
        task / "task.yaml",
        """
id: TEST-001
title: Broken service
issue: Service returns the wrong value.
target_files:
  - src/main/java/demo/Service.java
""".strip(),
    )

    write_file(
        task / "src/main/java/demo/Helper.java",
        """
package demo;

public class Helper {
    public int value() {
        return 10;
    }
}
""".strip(),
    )

    write_file(
        task / "src/main/java/demo/Service.java",
        """
package demo;

import demo.Helper;

public class Service {
    private final Helper helper = new Helper();
}
""".strip(),
    )

    context = build_repair_context(
        task,
        "Expected 10 but received 20",
    )

    assert context.selected_files[0] == (
        "src/main/java/demo/Service.java"
    )

    assert (
        "src/main/java/demo/Helper.java"
        in context.selected_files
    )

    assert (
        "Service returns the wrong value."
        in context.prompt
    )

    assert (
        "Expected 10 but received 20"
        in context.prompt
    )

    assert (
        "src/main/java/demo/Service.java -> "
        "src/main/java/demo/Helper.java"
        in context.prompt
    )