from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import tree_sitter_java
from tree_sitter import Language, Parser

JAVA_LANGUAGE = Language(tree_sitter_java.language())
JAVA_PARSER = Parser(JAVA_LANGUAGE)

DECLARATION_TYPES = {
    "class_declaration",
    "interface_declaration",
    "enum_declaration",
    "record_declaration",
    "annotation_type_declaration",
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".gradle",
    ".idea",
    ".venv",
    "build",
    "out",
    "target",
}

PACKAGE_PATTERN = re.compile(r"\bpackage\s+([\w.]+)\s*;")
IMPORT_PATTERN = re.compile(r"\bimport\s+(?:static\s+)?([\w.*]+)\s*;")


@dataclass(frozen=True)
class JavaSourceFile:
    path: Path
    relative_path: str
    package: str
    imports: tuple[str, ...]
    declared_types: tuple[str, ...]


@dataclass
class RepositoryGraph:
    root: Path
    graph: nx.DiGraph
    files: tuple[JavaSourceFile, ...]
    unresolved_imports: tuple[tuple[str, str], ...]

    @property
    def java_file_count(self) -> int:
        return len(self.files)

    @property
    def package_count(self) -> int:
        return len({item.package for item in self.files if item.package})

    @property
    def declared_type_count(self) -> int:
        return sum(len(item.declared_types) for item in self.files)

    @property
    def import_count(self) -> int:
        return sum(len(item.imports) for item in self.files)

    @property
    def dependency_count(self) -> int:
        return self.graph.number_of_edges()


def _walk(node):
    yield node

    for child in node.children:
        yield from _walk(child)


def _node_text(source: bytes, node) -> str:
    return source[node.start_byte : node.end_byte].decode(
        "utf-8",
        errors="replace",
    )


def _is_excluded(path: Path, root: Path) -> bool:
    relative_parts = path.relative_to(root).parts

    return any(
        part.lower() in EXCLUDED_DIRECTORIES
        for part in relative_parts
    )


def discover_java_files(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*.java")
            if not _is_excluded(path, root)
        ),
        key=lambda path: path.as_posix().lower(),
    )


def analyse_java_file(path: Path, root: Path) -> JavaSourceFile:
    source = path.read_bytes()
    tree = JAVA_PARSER.parse(source)

    package = ""
    imports: list[str] = []
    declared_types: list[str] = []

    for node in _walk(tree.root_node):
        if node.type == "package_declaration":
            match = PACKAGE_PATTERN.search(_node_text(source, node))

            if match:
                package = match.group(1)

        elif node.type == "import_declaration":
            match = IMPORT_PATTERN.search(_node_text(source, node))

            if match:
                imports.append(match.group(1))

        elif node.type in DECLARATION_TYPES:
            name_node = node.child_by_field_name("name")

            if name_node is not None:
                declared_types.append(_node_text(source, name_node))

    return JavaSourceFile(
        path=path,
        relative_path=path.relative_to(root).as_posix(),
        package=package,
        imports=tuple(dict.fromkeys(imports)),
        declared_types=tuple(dict.fromkeys(declared_types)),
    )


def _resolve_import(
    import_name: str,
    type_index: dict[str, str],
) -> set[str]:
    if import_name.endswith(".*"):
        prefix = import_name[:-2]

        if prefix in type_index:
            return {type_index[prefix]}

        return {
            path
            for qualified_name, path in type_index.items()
            if qualified_name.rpartition(".")[0] == prefix
        }

    candidate = import_name

    while candidate:
        if candidate in type_index:
            return {type_index[candidate]}

        if "." not in candidate:
            break

        candidate = candidate.rsplit(".", 1)[0]

    return set()


def scan_repository(repository: str | Path) -> RepositoryGraph:
    root = Path(repository).resolve()

    if not root.is_dir():
        raise ValueError(f"Repository directory does not exist: {root}")

    files = tuple(
        analyse_java_file(path, root)
        for path in discover_java_files(root)
    )

    graph = nx.DiGraph()
    type_index: dict[str, str] = {}

    for source_file in files:
        graph.add_node(
            source_file.relative_path,
            kind="java_file",
            package=source_file.package,
            declared_types=list(source_file.declared_types),
        )

        for type_name in source_file.declared_types:
            qualified_name = (
                f"{source_file.package}.{type_name}"
                if source_file.package
                else type_name
            )
            type_index[qualified_name] = source_file.relative_path

    unresolved: list[tuple[str, str]] = []

    for source_file in files:
        for import_name in source_file.imports:
            targets = _resolve_import(import_name, type_index)

            if not targets:
                unresolved.append(
                    (source_file.relative_path, import_name)
                )
                continue

            for target in targets:
                if target != source_file.relative_path:
                    graph.add_edge(
                        source_file.relative_path,
                        target,
                        relation="imports",
                    )

    return RepositoryGraph(
        root=root,
        graph=graph,
        files=files,
        unresolved_imports=tuple(unresolved),
    )