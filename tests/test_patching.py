from pathlib import Path

import pytest

from javafixbench.patching import (
    RepairFormatError,
    apply_repair_changes,
    parse_repair_response,
)


def test_parses_and_applies_java_repair(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    source = (
        repository
        / "src/main/java/demo/Calculator.java"
    )
    source.parent.mkdir(parents=True)
    source.write_text(
        "package demo;\n\nclass Calculator {}\n",
        encoding="utf-8",
    )

    response = """
<repair>
<file path="src/main/java/demo/Calculator.java">
package demo;

class Calculator {
    int add(int left, int right) {
        return left + right;
    }
}
</file>
</repair>
"""

    changes = parse_repair_response(response)

    applied = apply_repair_changes(
        repository,
        changes,
        allowed_paths=[
            "src/main/java/demo/Calculator.java"
        ],
    )

    assert len(applied) == 1
    assert "return left + right;" in source.read_text(
        encoding="utf-8"
    )


def test_rejects_changes_to_tests() -> None:
    response = """
<repair>
<file path="src/test/java/demo/CalculatorTest.java">
class CalculatorTest {}
</file>
</repair>
"""

    with pytest.raises(
        RepairFormatError,
        match="Test files may not be changed",
    ):
        parse_repair_response(response)


def test_rejects_parent_directory_traversal() -> None:
    response = """
<repair>
<file path="../Outside.java">
class Outside {}
</file>
</repair>
"""

    with pytest.raises(
        RepairFormatError,
        match="traversal",
    ):
        parse_repair_response(response)


def test_rejects_unselected_files(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    source = repository / "src/main/java/demo/Other.java"
    source.parent.mkdir(parents=True)
    source.write_text(
        "package demo;\nclass Other {}\n",
        encoding="utf-8",
    )

    response = """
<repair>
<file path="src/main/java/demo/Other.java">
package demo;
class Other {
    int value() {
        return 1;
    }
}
</file>
</repair>
"""

    changes = parse_repair_response(response)

    with pytest.raises(
        RepairFormatError,
        match="unselected file",
    ):
        apply_repair_changes(
            repository,
            changes,
            allowed_paths=[],
        )