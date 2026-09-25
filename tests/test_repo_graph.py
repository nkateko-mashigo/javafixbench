from pathlib import Path

from javafixbench.repo_graph import scan_repository


def write_java(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_builds_internal_dependency_graph(tmp_path: Path) -> None:
    repository = tmp_path / "sample-repository"

    write_java(
        repository / "src/main/java/example/DiscountPolicy.java",
        """
        package example;

        public class DiscountPolicy {
            public int apply(int price) {
                return price - 10;
            }
        }
        """,
    )

    write_java(
        repository / "src/main/java/example/OrderService.java",
        """
        package example;

        import example.DiscountPolicy;

        public class OrderService {
            private final DiscountPolicy policy = new DiscountPolicy();
        }
        """,
    )

    write_java(
        repository / "target/generated/GeneratedFile.java",
        """
        package generated;

        public class GeneratedFile {
        }
        """,
    )

    result = scan_repository(repository)

    assert result.java_file_count == 2
    assert result.package_count == 1
    assert result.declared_type_count == 2
    assert result.dependency_count == 1

    assert result.graph.has_edge(
        "src/main/java/example/OrderService.java",
        "src/main/java/example/DiscountPolicy.java",
    )