"""Deterministic test-corpus inventory and retirement/replacement guardrails."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import posixpath
import re
import select
import stat
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from scripts.verification.test_corpus_evidence import (
    ASSERTION_EVIDENCE_SCHEMA as ASSERTION_EVIDENCE_SCHEMA,
    ASSERTION_EQUIVALENCE_SCHEMA as ASSERTION_EQUIVALENCE_SCHEMA,
    RETIREMENT_EVIDENCE_SCHEMA as RETIREMENT_EVIDENCE_SCHEMA,
    TEST_RESULT_EVIDENCE_SCHEMA as TEST_RESULT_EVIDENCE_SCHEMA,
    TestCorpusEvidenceError,
    retirement_artifact_ref as retirement_artifact_ref,
)
from scripts.verification.test_corpus_evidence import (
    validate_retirements as _validate_retirement_evidence,
)
from scripts.verification.test_corpus_frontend import (
    FrontendInventoryError,
    frontend_export_binding_source,
    frontend_relative_import_modules,
    frontend_source_for_ref,
    parse_frontend_refs,
)
from scripts.verification.verification_github_transport import (
    VerificationGithubTransportError,
    decode_github_job_output,
)


RETIREMENT_SCHEMA = "uaa.test_corpus_retirements.v1"
RETIREMENT_LEDGER = Path("docs/verification/test_corpus_retirements.json")
BASE_SHA_ENV = "UAA_VERIFICATION_BASE_SHA"
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
MAX_TEST_FILE_BYTES = 5_000_000
MAX_RETIREMENT_LEDGER_BYTES = 1_000_000
MAX_GIT_STDOUT_BYTES = 8_000_000
MAX_CHANGED_PATH_BYTES = 4_000_000
MAX_CHANGED_TEST_PATHS = 20_000
GIT_INSPECTION_TIMEOUT_SECONDS = 30.0
READ_ONLY_COLLECTION_METHODS = {
    "copy",
    "count",
    "get",
    "index",
    "isdisjoint",
    "issubset",
    "issuperset",
    "items",
    "keys",
    "values",
}
FRONTEND_TEST_EXTENSIONS = (
    "js",
    "jsx",
    "ts",
    "tsx",
    "cjs",
    "cjsx",
    "cts",
    "ctsx",
    "mjs",
    "mjsx",
    "mts",
    "mtsx",
)
TEST_FILE_PATTERNS = (
    "tests/**/test_*.py",
    "tests/**/*_test.py",
    *(
        f"apps/control-center/src/**/*.{kind}.{extension}"
        for kind in ("test", "spec")
        for extension in FRONTEND_TEST_EXTENSIONS
    ),
    *(
        f"apps/control-center/tests/**/*.{extension}"
        for extension in FRONTEND_TEST_EXTENSIONS
    ),
)


class TestCorpusGuardError(RuntimeError):
    """Raised when corpus inventory or retirement evidence is invalid."""


class TestCorpusSourceRefMissingError(RuntimeError):
    """Raised only when a replacement source ref is absent from the worktree."""


@dataclass(frozen=True)
class TestDeclaration:
    ref: str
    kind: str


@dataclass(frozen=True)
class _ModuleBinding:
    node: ast.AST
    applies_after_declaration: bool = False


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _binding_target_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)):
        return {name for child in node.elts for name in _binding_target_names(child)}
    return set()


def _statement_binding_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, (ast.Assign, ast.AnnAssign)):
            targets = (
                child.targets if isinstance(child, ast.Assign) else (child.target,)
            )
            for target in targets:
                names.update(_binding_target_names(target))
        elif isinstance(child, (ast.For, ast.AsyncFor, ast.NamedExpr)):
            names.update(_binding_target_names(child.target))
    return names


def _mutation_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.AugAssign):
            root = _root_name(child.target)
            if root is not None:
                names.add(root)
        elif isinstance(child, (ast.Assign, ast.AnnAssign, ast.Delete)):
            if isinstance(child, ast.Assign):
                targets = child.targets
            elif isinstance(child, ast.AnnAssign):
                targets = (child.target,)
            else:
                targets = child.targets
            for target in targets:
                if isinstance(target, (ast.Attribute, ast.Subscript)):
                    root = _root_name(target)
                    if root is not None:
                        names.add(root)
        elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
            if child.func.attr in READ_ONLY_COLLECTION_METHODS:
                continue
            root = _root_name(child.func.value)
            if root is not None:
                names.add(root)
    return names


def _called_names(node: ast.AST) -> set[str]:
    return {
        child.func.id
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }


def _python_module_bindings(
    tree: ast.Module,
) -> dict[str, tuple[_ModuleBinding, ...]]:
    helper_defs = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("test")
    }
    helper_cache: dict[str, tuple[set[str], set[str]]] = {}

    def helper_effects(name: str, visiting: set[str]) -> tuple[set[str], set[str]]:
        if name in helper_cache:
            effects, dependencies = helper_cache[name]
            return set(effects), set(dependencies)
        if name in visiting or name not in helper_defs:
            return set(), set()
        node = helper_defs[name]
        effects = _mutation_names(node)
        dependencies = {name}
        for called in _called_names(node):
            child_effects, child_dependencies = helper_effects(
                called, {*visiting, name}
            )
            effects.update(child_effects)
            dependencies.update(child_dependencies)
        helper_cache[name] = (set(effects), set(dependencies))
        return effects, dependencies

    mutable: dict[str, list[_ModuleBinding]] = {}

    def add(name: str, node: ast.AST, *, applies_after: bool = False) -> None:
        binding = _ModuleBinding(node=node, applies_after_declaration=applies_after)
        bucket = mutable.setdefault(name, [])
        if binding not in bucket:
            bucket.append(binding)

    for module_node in tree.body:
        if isinstance(module_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not module_node.name.startswith("test"):
                add(module_node.name, module_node)
            continue
        if isinstance(module_node, ast.ClassDef):
            add(module_node.name, module_node)
            continue
        for name in _statement_binding_names(module_node):
            add(name, module_node)
        for name in _mutation_names(module_node):
            add(name, module_node, applies_after=True)
        for helper_name in _called_names(module_node):
            effects, dependencies = helper_effects(helper_name, set())
            for affected_name in effects:
                add(affected_name, module_node, applies_after=True)
                for dependency in dependencies:
                    add(
                        affected_name,
                        helper_defs[dependency],
                        applies_after=True,
                    )
    return {name: tuple(bindings) for name, bindings in mutable.items()}


def _parametrize_aliases(tree: ast.Module) -> set[str]:
    aliases: set[str] = set()
    pytest_roots = {
        imported.asname or imported.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for imported in node.names
        if imported.name == "pytest"
    }
    pytest_marks: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "pytest"
        ):
            for imported in node.names:
                if imported.name == "parametrize":
                    aliases.add(imported.asname or imported.name)
                elif node.module == "pytest" and imported.name == "mark":
                    pytest_marks.add(imported.asname or imported.name)
    changed = True
    while changed:
        changed = False
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if value is None:
                continue
            resolves = (
                isinstance(value, ast.Attribute)
                and value.attr == "parametrize"
                and _root_name(value) in {*pytest_roots, *pytest_marks}
            ) or (isinstance(value, ast.Name) and value.id in aliases)
            if not resolves:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                for name in _binding_target_names(target):
                    if name not in aliases:
                        aliases.add(name)
                        changed = True
    return aliases


def _python_import_modules(tree: ast.Module) -> dict[str, tuple[str, ...]]:
    modules: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for imported in node.names:
                modules[imported.asname or imported.name.split(".", 1)[0]] = (
                    imported.name,
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for imported in node.names:
                if imported.name == "*":
                    continue
                modules[imported.asname or imported.name] = (
                    f"{node.module}.{imported.name}",
                    node.module,
                )
    return modules


def _parameterized_ref(
    raw_ref: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module_bindings: dict[str, tuple[_ModuleBinding, ...]],
    parametrize_aliases: set[str],
    imported_modules: dict[str, tuple[str, ...]],
    import_source_resolver: Callable[[str], str | None] | None,
    *,
    container_decorators: tuple[ast.expr, ...] = (),
) -> str:
    candidate_decorators = (*container_decorators, *node.decorator_list)
    decorators = tuple(
        decorator
        for decorator in candidate_decorators
        if isinstance(decorator, ast.Call)
        and (
            (
                isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "parametrize"
            )
            or (
                isinstance(decorator.func, ast.Name)
                and decorator.func.id in parametrize_aliases
            )
        )
    )
    unresolved = [
        decorator.func.id
        for decorator in candidate_decorators
        if isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Name)
        and "parametrize" in decorator.func.id.lower()
        and decorator.func.id not in parametrize_aliases
    ]
    if unresolved:
        raise TestCorpusGuardError("Python parametrize decorator cannot be resolved")
    if not decorators:
        return raw_ref
    serialized_parts = [
        ast.dump(decorator, annotate_fields=True, include_attributes=False)
        for decorator in decorators
    ]
    for decorator in decorators:
        value_nodes = list(decorator.args[1:])
        value_nodes.extend(
            keyword.value
            for keyword in decorator.keywords
            if keyword.arg == "argvalues"
        )
        for value in value_nodes:
            root = _root_name(value)
            if root not in imported_modules:
                continue
            resolved_import = next(
                (
                    (module, source)
                    for module in imported_modules[root]
                    if import_source_resolver is not None
                    and (source := import_source_resolver(module)) is not None
                ),
                None,
            )
            if resolved_import is None:
                raise TestCorpusGuardError(
                    "imported Python parameter data cannot be inventoried safely"
                )
            module, source = resolved_import
            serialized_parts.append(f"imported-module:{module}\n{source}")
    pending_names = {
        child.id
        for decorator in decorators
        for child in ast.walk(decorator)
        if isinstance(child, ast.Name)
    }
    resolved_names: set[str] = set()
    binding_nodes: dict[tuple[int, int], ast.AST] = {}
    while pending_names:
        name = pending_names.pop()
        if name in resolved_names:
            continue
        resolved_names.add(name)
        name_bindings = module_bindings.get(name, ())
        first_post_declaration_rebinding = min(
            (
                (binding.node.lineno, binding.node.col_offset)
                for binding in name_bindings
                if binding.node.lineno >= node.lineno
                and not binding.applies_after_declaration
            ),
            default=None,
        )
        for module_binding in name_bindings:
            binding = module_binding.node
            position = (binding.lineno, binding.col_offset)
            if (
                binding.lineno >= node.lineno
                and not module_binding.applies_after_declaration
            ):
                continue
            if (
                module_binding.applies_after_declaration
                and first_post_declaration_rebinding is not None
                and position > first_post_declaration_rebinding
            ):
                continue
            binding_nodes[position] = binding
            pending_names.update(
                child.id
                for child in ast.walk(binding)
                if isinstance(child, ast.Name) and child.id not in resolved_names
            )
    binding_parts = [
        "binding:" + ast.dump(binding, annotate_fields=True, include_attributes=False)
        for _position, binding in sorted(binding_nodes.items())
    ]
    serialized = "\n".join([*serialized_parts, *binding_parts])
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{raw_ref}::parametrize-sha256:{digest}"


def _python_node_source(
    lines: list[str],
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    start_line = min(
        (decorator.lineno for decorator in node.decorator_list),
        default=node.lineno,
    )
    end_line = node.end_lineno
    if end_line is None:
        raise TestCorpusGuardError("Python test declaration range is unavailable")
    return "".join(lines[start_line - 1 : end_line])


def _has_nested_python_tests(node: ast.AST) -> bool:
    return any(
        (
            isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name.startswith("test")
        )
        or (isinstance(child, ast.ClassDef) and child.name.startswith("Test"))
        for child in ast.walk(node)
        if child is not node
    )


def _disabled_python_declarations(body: list[ast.stmt]) -> set[str]:
    active: set[str] = set()
    disabled: set[str] = set()
    for node in body:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.name.startswith("test"):
            active.add(node.name)
            disabled.discard(node.name)
            continue
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            active.add(node.name)
            disabled.discard(node.name)
            continue

        rebound: set[str] = set()
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            if isinstance(node, ast.Assign):
                targets = node.targets
            else:
                targets = (node.target,)
            for target in targets:
                rebound.update(_binding_target_names(target))
        elif isinstance(node, ast.Delete):
            for target in node.targets:
                rebound.update(_binding_target_names(target))
        disabled.update(active & rebound)

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            if isinstance(value, ast.Constant) and value.value is False:
                for target in targets:
                    if isinstance(target, ast.Attribute) and target.attr == "__test__":
                        root = _root_name(target.value)
                        if root in active:
                            disabled.add(root)
    return disabled


def _python_inventory_entries(
    path: str,
    text: str,
    import_source_resolver: Callable[[str], str | None] | None = None,
) -> tuple[tuple[TestDeclaration, str], ...]:
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            f"cannot parse Python test inventory: {path}"
        ) from exc

    if any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "pytest_generate_tests"
        for node in tree.body
    ):
        raise TestCorpusGuardError("pytest_generate_tests cannot be inventoried safely")

    for module_node in tree.body:
        if not isinstance(
            module_node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ) and _has_nested_python_tests(module_node):
            raise TestCorpusGuardError(
                "Python tests inside module control flow cannot be inventoried safely"
            )

    entries: list[tuple[str, str, str]] = []
    source_lines = text.splitlines(keepends=True)
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    unittest_roots = {
        imported.asname or imported.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for imported in node.names
        if imported.name == "unittest"
    }
    unittest_test_case_names = {
        imported.asname or imported.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "unittest"
        for imported in node.names
        if imported.name == "TestCase"
    }
    unittest_classes: set[str] = set()
    changed = True
    while changed:
        changed = False
        for class_node in classes.values():
            if class_node.name in unittest_classes:
                continue
            if any(
                (
                    isinstance(base, ast.Attribute)
                    and base.attr == "TestCase"
                    and _root_name(base) in unittest_roots
                )
                or (
                    isinstance(base, ast.Name)
                    and base.id in {*unittest_test_case_names, *unittest_classes}
                )
                for base in class_node.bases
            ):
                unittest_classes.add(class_node.name)
                changed = True
    module_bindings = _python_module_bindings(tree)
    parametrize_aliases = _parametrize_aliases(tree)
    imported_modules = _python_import_modules(tree)
    disabled = _disabled_python_declarations(tree.body)
    declared_test_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    }

    for module_node in tree.body:
        if not isinstance(module_node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        targets = (
            module_node.targets
            if isinstance(module_node, ast.Assign)
            else (module_node.target,)
        )
        if any(
            name.startswith("test") and name not in declared_test_names
            for target in targets
            for name in _binding_target_names(target)
        ):
            raise TestCorpusGuardError(
                "callable Python test-name assignment cannot be inventoried safely"
            )

    def collected_methods(
        class_node: ast.ClassDef,
        visiting: set[str],
    ) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        methods: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        next_visiting = {*visiting, class_node.name}
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                methods.update(collected_methods(classes[base.id], next_visiting))
        disabled_methods = _disabled_python_declarations(class_node.body)
        for child in class_node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child.name.startswith("test") and child.name not in disabled_methods:
                    methods[child.name] = child
                else:
                    methods.pop(child.name, None)
                continue
            rebound: set[str] = set()
            if isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = (
                    child.targets if isinstance(child, ast.Assign) else (child.target,)
                )
                for target in targets:
                    rebound.update(_binding_target_names(target))
            elif isinstance(child, ast.Delete):
                for target in child.targets:
                    rebound.update(_binding_target_names(target))
            for name in rebound:
                methods.pop(name, None)
        return methods

    def has_constructor(class_node: ast.ClassDef, visiting: set[str]) -> bool:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        if any(
            isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name in {"__init__", "__new__"}
            for child in class_node.body
        ):
            return True
        next_visiting = {*visiting, class_node.name}
        return any(
            has_constructor(classes[base.id], next_visiting)
            for base in class_node.bases
            if isinstance(base, ast.Name) and base.id in classes
        )

    def validate_class_bases(class_node: ast.ClassDef, visiting: set[str]) -> None:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        next_visiting = {*visiting, class_node.name}
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                validate_class_bases(classes[base.id], next_visiting)
                continue
            if (isinstance(base, ast.Name) and base.id in unittest_test_case_names) or (
                isinstance(base, ast.Attribute)
                and base.attr == "TestCase"
                and _root_name(base) in unittest_roots
            ):
                continue
            raise TestCorpusGuardError(
                "collected Python test class base cannot be resolved safely"
            )

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test") and node.name not in disabled:
                raw_ref = _parameterized_ref(
                    f"{path}::{node.name}",
                    node,
                    module_bindings,
                    parametrize_aliases,
                    imported_modules,
                    import_source_resolver,
                )
                entries.append(
                    (raw_ref, "python_test", _python_node_source(source_lines, node))
                )
            continue
        if (
            not isinstance(node, ast.ClassDef)
            or (not node.name.startswith("Test") and node.name not in unittest_classes)
            or node.name in disabled
        ):
            continue
        validate_class_bases(node, set())
        if has_constructor(node, set()):
            continue
        for method_name, method in collected_methods(node, set()).items():
            raw_ref = _parameterized_ref(
                f"{path}::{node.name}::{method_name}",
                method,
                module_bindings,
                parametrize_aliases,
                imported_modules,
                import_source_resolver,
                container_decorators=tuple(node.decorator_list),
            )
            entries.append(
                (raw_ref, "python_test", _python_node_source(source_lines, method))
            )

    counts: dict[str, int] = {}
    inventory: list[tuple[TestDeclaration, str]] = []
    for raw_ref, kind, source in entries:
        occurrence = counts.get(raw_ref, 0) + 1
        counts[raw_ref] = occurrence
        ref = raw_ref if occurrence == 1 else f"{raw_ref}#{occurrence}"
        inventory.append((TestDeclaration(ref=ref, kind=kind), source))
    return tuple(inventory)


def parse_python_declarations(path: str, text: str) -> tuple[TestDeclaration, ...]:
    return tuple(
        declaration for declaration, _source in _python_inventory_entries(path, text)
    )


def _python_module_candidates(module: str) -> tuple[str, ...]:
    relative = module.replace(".", "/")
    candidates = (f"{relative}.py", f"{relative}/__init__.py")
    if module == "ultimate_ai_agent" or module.startswith("ultimate_ai_agent."):
        candidates = tuple(f"src/{candidate}" for candidate in candidates)
    return candidates


def _python_import_resolver(
    read_text: Callable[[str], str | None],
) -> Callable[[str], str | None]:
    def resolve(module: str) -> str | None:
        resolved = [
            f"path={candidate}\n{source}"
            for candidate in _python_module_candidates(module)
            if (source := read_text(candidate)) is not None
        ]
        if len(resolved) > 1:
            raise TestCorpusGuardError("imported Python parameter data is ambiguous")
        return resolved[0] if resolved else None

    return resolve


def parse_frontend_declarations(path: str, text: str) -> tuple[TestDeclaration, ...]:
    try:
        refs = parse_frontend_refs(path, text)
    except FrontendInventoryError as exc:
        raise TestCorpusGuardError(str(exc)) from None
    return tuple(TestDeclaration(ref=ref, kind="frontend_test") for ref in refs)


def parse_test_declarations(path: str, text: str) -> tuple[TestDeclaration, ...]:
    if path.endswith(".py"):
        return parse_python_declarations(path, text)
    return parse_frontend_declarations(path, text)


def _relative_frontend_import_candidates(
    importing_path: str,
    module: str,
) -> tuple[str, ...]:
    if not module.startswith(".") or "\\" in module or "\0" in module:
        return ()
    normalized = posixpath.normpath(
        posixpath.join(posixpath.dirname(importing_path), module)
    )
    if normalized.startswith("../") or normalized.startswith("/"):
        return ()
    suffix = Path(normalized).suffix.removeprefix(".")
    if suffix in FRONTEND_TEST_EXTENSIONS:
        candidates = (normalized,)
    else:
        candidates = tuple(
            [f"{normalized}.{extension}" for extension in FRONTEND_TEST_EXTENSIONS]
            + [
                f"{normalized}/index.{extension}"
                for extension in FRONTEND_TEST_EXTENSIONS
            ]
        )
    for candidate in candidates:
        parts = Path(candidate).parts
        if any(part in {"", ".", ".."} for part in parts):
            return ()
    return candidates


def _frontend_import_resolver(
    importing_path: str,
    read_text: Callable[[str], str | None],
) -> Callable[[str, str], str | None]:
    def resolve(module: str, imported_name: str) -> str | None:
        resolved: list[str] = []
        for candidate in _relative_frontend_import_candidates(importing_path, module):
            source = read_text(candidate)
            if source is None:
                continue
            binding = frontend_export_binding_source(source, imported_name)
            if binding is not None:
                resolved.append(f"path={candidate}\n{binding}")
        if len(resolved) > 1:
            raise TestCorpusGuardError(
                "frontend parameterized test import is ambiguous"
            )
        return resolved[0] if resolved else None

    return resolve


def _parse_worktree_test_declarations(
    repo: Path,
    path: str,
    text: str,
) -> tuple[TestDeclaration, ...]:
    if path.endswith(".py"):

        def read_python_import(candidate: str) -> str | None:
            target = repo / candidate
            if not target.is_file():
                return None
            return _read_worktree_text(repo, candidate)

        return tuple(
            declaration
            for declaration, _source in _python_inventory_entries(
                path,
                text,
                _python_import_resolver(read_python_import),
            )
        )

    def read_import(candidate: str) -> str | None:
        target = repo / candidate
        if not target.is_file():
            return None
        return _read_worktree_text(repo, candidate)

    try:
        refs = parse_frontend_refs(
            path,
            text,
            _frontend_import_resolver(path, read_import),
        )
    except FrontendInventoryError as exc:
        raise TestCorpusGuardError(str(exc)) from None
    return tuple(TestDeclaration(ref=ref, kind="frontend_test") for ref in refs)


def _parse_base_test_declarations(
    repo: Path,
    base_sha: str,
    path: str,
    text: str,
) -> tuple[TestDeclaration, ...]:
    if path.endswith(".py"):
        return tuple(
            declaration
            for declaration, _source in _python_inventory_entries(
                path,
                text,
                _python_import_resolver(
                    lambda candidate: _base_text(repo, base_sha, candidate)
                ),
            )
        )

    try:
        refs = parse_frontend_refs(
            path,
            text,
            _frontend_import_resolver(
                path,
                lambda candidate: _base_text(repo, base_sha, candidate),
            ),
        )
    except FrontendInventoryError as exc:
        raise TestCorpusGuardError(str(exc)) from None
    return tuple(TestDeclaration(ref=ref, kind="frontend_test") for ref in refs)


def discover_test_files(repo: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                path.relative_to(repo).as_posix()
                for pattern in TEST_FILE_PATTERNS
                for path in repo.glob(pattern)
                if path.is_file()
            }
        )
    )


def _close_quietly(*descriptors: int | None) -> None:
    for descriptor in descriptors:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _read_bounded_regular_text(
    repo: Path,
    relative_path: Path,
    *,
    max_bytes: int,
    unsafe_message: str,
    invalid_message: str,
    missing_error: type[TestCorpusSourceRefMissingError] | None = None,
) -> str:
    descriptor: int | None = None
    parent_descriptor: int | None = None
    try:
        parts = relative_path.parts
        if (
            relative_path.is_absolute()
            or not parts
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise TestCorpusGuardError(unsafe_message)
        directory_flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        parent_descriptor = os.open(repo, directory_flags)
        parent_info = os.fstat(parent_descriptor)
        if not stat.S_ISDIR(parent_info.st_mode):
            raise TestCorpusGuardError(unsafe_message)
        for component in parts[:-1]:
            next_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=parent_descriptor,
            )
            try:
                next_info = os.fstat(next_descriptor)
                if not stat.S_ISDIR(next_info.st_mode):
                    raise TestCorpusGuardError(unsafe_message)
                os.close(parent_descriptor)
            except BaseException:
                _close_quietly(next_descriptor)
                raise
            parent_descriptor = next_descriptor
        descriptor = os.open(
            parts[-1],
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_descriptor,
        )
    except FileNotFoundError as exc:
        _close_quietly(descriptor, parent_descriptor)
        if missing_error is not None:
            raise missing_error(invalid_message) from exc
        raise TestCorpusGuardError(invalid_message) from exc
    except TestCorpusGuardError:
        _close_quietly(descriptor, parent_descriptor)
        raise
    except OSError as exc:
        _close_quietly(descriptor, parent_descriptor)
        raise TestCorpusGuardError(unsafe_message) from exc

    try:
        opened = os.fstat(descriptor)
        linked = os.stat(
            parts[-1],
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        identity = (opened.st_dev, opened.st_ino)
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(linked.st_mode)
            or opened.st_nlink != 1
            or linked.st_nlink != 1
            or identity != (linked.st_dev, linked.st_ino)
            or opened.st_size > max_bytes
        ):
            raise TestCorpusGuardError(unsafe_message)

        content = bytearray()
        while len(content) <= max_bytes:
            chunk = os.read(
                descriptor,
                min(64 * 1024, max_bytes + 1 - len(content)),
            )
            if not chunk:
                break
            content.extend(chunk)
        if len(content) > max_bytes:
            raise TestCorpusGuardError(unsafe_message)

        closed_over = os.fstat(descriptor)
        still_linked = os.stat(
            parts[-1],
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(closed_over.st_mode)
            or not stat.S_ISREG(still_linked.st_mode)
            or closed_over.st_nlink != 1
            or still_linked.st_nlink != 1
            or (closed_over.st_dev, closed_over.st_ino) != identity
            or (still_linked.st_dev, still_linked.st_ino) != identity
            or (
                closed_over.st_size,
                closed_over.st_mtime_ns,
                closed_over.st_ctime_ns,
            )
            != (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns)
        ):
            raise TestCorpusGuardError(unsafe_message)
        try:
            return bytes(content).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TestCorpusGuardError(invalid_message) from exc
    except TestCorpusGuardError:
        raise
    except OSError as exc:
        raise TestCorpusGuardError(unsafe_message) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)


def _read_worktree_text(
    repo: Path,
    path: str,
    *,
    missing_error: type[TestCorpusSourceRefMissingError] | None = None,
) -> str:
    return _read_bounded_regular_text(
        repo,
        Path(path),
        max_bytes=MAX_TEST_FILE_BYTES,
        unsafe_message=f"test inventory file is unsafe: {path}",
        invalid_message=f"cannot read test inventory: {path}",
        missing_error=missing_error,
    )


def inventory_worktree(repo: Path) -> tuple[TestDeclaration, ...]:
    declarations: list[TestDeclaration] = []
    for path in discover_test_files(repo):
        text = _read_worktree_text(repo, path)
        declarations.extend(_parse_worktree_test_declarations(repo, path, text))
    refs = [item.ref for item in declarations]
    if len(refs) != len(set(refs)):
        raise TestCorpusGuardError("test inventory contains duplicate stable refs")
    if not declarations:
        raise TestCorpusGuardError("test inventory is empty")
    return tuple(sorted(declarations, key=lambda item: item.ref))


def _run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    command = ["git", *args]
    try:
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise TestCorpusGuardError("git inspection is unavailable") from exc
    if process.stdout is None:
        process.kill()
        process.wait()
        raise TestCorpusGuardError("git inspection output is unavailable")

    chunks: list[bytes] = []
    total = 0
    deadline = time.monotonic() + GIT_INSPECTION_TIMEOUT_SECONDS
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TestCorpusGuardError("git inspection timed out")
            ready, _, _ = select.select([process.stdout], [], [], remaining)
            if not ready:
                raise TestCorpusGuardError("git inspection timed out")
            chunk = os.read(
                process.stdout.fileno(),
                min(64 * 1024, MAX_GIT_STDOUT_BYTES + 1 - total),
            )
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_GIT_STDOUT_BYTES:
                raise TestCorpusGuardError("git inspection output exceeds byte budget")
        return subprocess.CompletedProcess(
            args=command,
            returncode=process.wait(),
            stdout=b"".join(chunks),
            stderr=b"",
        )
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.wait()
        raise
    finally:
        process.stdout.close()


def _resolve_base_sha(repo: Path, requested: str | None) -> str | None:
    if requested is not None:
        if SHA_PATTERN.fullmatch(requested) is None:
            raise TestCorpusGuardError("test-corpus comparison base SHA is malformed")
        probe = _run_git(repo, ["cat-file", "-e", f"{requested}^{{commit}}"])
        if probe.returncode != 0:
            raise TestCorpusGuardError("test-corpus comparison base commit is missing")
        return requested

    ci_ref = _run_git(repo, ["rev-parse", "--verify", "refs/uaa-ci/base-main"])
    if ci_ref.returncode == 0:
        try:
            value = ci_ref.stdout.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise TestCorpusGuardError(
                "canonical CI comparison base is malformed"
            ) from exc
        if SHA_PATTERN.fullmatch(value) is None:
            raise TestCorpusGuardError("canonical CI comparison base is malformed")
        probe = _run_git(repo, ["cat-file", "-e", f"{value}^{{commit}}"])
        if probe.returncode != 0:
            raise TestCorpusGuardError("canonical CI comparison base commit is missing")
        return value

    if os.environ.get("CI", "").lower() == "true":
        raise TestCorpusGuardError("canonical CI comparison base is missing")

    merge_base = _run_git(repo, ["merge-base", "HEAD", "origin/main"])
    if merge_base.returncode == 0:
        try:
            value = merge_base.stdout.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise TestCorpusGuardError("local comparison base is malformed") from exc
        if SHA_PATTERN.fullmatch(value):
            return value
    return None


def _changed_test_paths(repo: Path, base_sha: str) -> tuple[str, ...]:
    commands = (
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            base_sha,
            "HEAD",
            "--",
            "tests",
            "apps",
            "scripts",
            "src",
        ],
        [
            "diff",
            "--cached",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            "tests",
            "apps",
            "scripts",
            "src",
        ],
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            "tests",
            "apps",
            "scripts",
            "src",
        ],
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "tests",
            "apps",
            "scripts",
            "src",
        ],
    )
    raw_paths = bytearray()
    for command in commands:
        result = _run_git(repo, command)
        if result.returncode != 0:
            raise TestCorpusGuardError("cannot derive changed test corpus")
        raw_paths.extend(result.stdout)
        if len(raw_paths) > MAX_CHANGED_PATH_BYTES:
            raise TestCorpusGuardError("changed test corpus paths exceed byte budget")
    try:
        paths = bytes(raw_paths).decode("utf-8").split("\0")
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError("changed test corpus paths are malformed") from exc
    all_changed = {path for path in paths if path}
    changed = {path for path in all_changed if _is_test_path(path)}
    changed_frontend_sources = {
        path
        for path in all_changed
        if path.startswith("apps/control-center/")
        and Path(path).suffix.removeprefix(".") in FRONTEND_TEST_EXTENSIONS
    }
    if changed_frontend_sources:
        for test_path in discover_test_files(repo):
            if test_path.endswith(".py") or test_path in changed:
                continue
            text = _read_worktree_text(repo, test_path)
            dependency_candidates = {
                candidate
                for module in frontend_relative_import_modules(text)
                for candidate in _relative_frontend_import_candidates(
                    test_path,
                    module,
                )
            }
            if dependency_candidates & changed_frontend_sources:
                changed.add(test_path)
    changed_python_sources = {
        path for path in all_changed if path.endswith(".py") and not _is_test_path(path)
    }
    if changed_python_sources:
        for test_path in discover_test_files(repo):
            if not test_path.endswith(".py") or test_path in changed:
                continue
            text = _read_worktree_text(repo, test_path)
            try:
                tree = ast.parse(text, filename=test_path)
            except SyntaxError as exc:
                raise TestCorpusGuardError(
                    f"cannot parse Python test inventory: {test_path}"
                ) from exc
            dependency_candidates = {
                candidate
                for modules in _python_import_modules(tree).values()
                for module in modules
                for candidate in _python_module_candidates(module)
            }
            if dependency_candidates & changed_python_sources:
                changed.add(test_path)
    changed_tuple = tuple(sorted(changed))
    if len(changed_tuple) > MAX_CHANGED_TEST_PATHS:
        raise TestCorpusGuardError("changed test corpus path count exceeds budget")
    for path in changed_tuple:
        _validate_test_path(path)
    return changed_tuple


def _is_test_path(path: str) -> bool:
    candidate = Path(path)
    if path.startswith("tests/"):
        return candidate.suffix == ".py" and (
            candidate.name.startswith("test_") or candidate.name.endswith("_test.py")
        )
    if not path.startswith("apps/control-center/"):
        return False
    vitest_suffixes = tuple(
        f".{kind}.{extension}"
        for kind in ("test", "spec")
        for extension in FRONTEND_TEST_EXTENSIONS
    )
    return candidate.name.endswith(vitest_suffixes) or (
        path.startswith("apps/control-center/tests/")
        and candidate.suffix.removeprefix(".") in FRONTEND_TEST_EXTENSIONS
    )


def _validate_test_path(path: str) -> None:
    parts = Path(path).parts
    if (
        path.startswith("/")
        or "\\" in path
        or ":" in path
        or any(part in {"", ".", ".."} for part in parts)
        or any(ord(character) < 32 for character in path)
    ):
        raise TestCorpusGuardError("changed test path is unsafe")


def _validate_test_ref(value: str) -> None:
    if (
        "::" not in value
        or not value.split("::", 1)[1]
        or len(value) > 2_000
        or any(ord(character) < 32 for character in value)
    ):
        raise TestCorpusEvidenceError("retired test ref is invalid")
    path = value.split("::", 1)[0]
    try:
        _validate_test_path(path)
    except TestCorpusGuardError as exc:
        raise TestCorpusEvidenceError("retired test ref is invalid") from exc
    if not _is_test_path(path):
        raise TestCorpusEvidenceError("retired test ref is invalid")


def _base_text(repo: Path, base_sha: str, path: str) -> str | None:
    size = _run_git(repo, ["cat-file", "-s", f"{base_sha}:{path}"])
    if size.returncode != 0:
        return None
    try:
        byte_count = int(size.stdout.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise TestCorpusGuardError(f"base test size is invalid: {path}") from exc
    if byte_count > MAX_TEST_FILE_BYTES:
        raise TestCorpusGuardError(f"base test file exceeds byte budget: {path}")
    result = _run_git(repo, ["show", f"{base_sha}:{path}"])
    if result.returncode != 0:
        raise TestCorpusGuardError(f"cannot read base test file: {path}")
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError(f"base test file is not UTF-8: {path}") from exc


def build_test_source_ref(test_ref: str, declaration_source: str) -> str:
    artifact = {
        "schema_version": "uaa.test_corpus_source.v1",
        "test_ref": test_ref,
        "source_digest": hashlib.sha256(declaration_source.encode("utf-8")).hexdigest(),
    }
    encoded = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode()
    return f"test-source-ref:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _source_ref_from_text(
    test_ref: str,
    source_text: str,
    import_binding_resolver: Callable[[str, str], str | None] | None = None,
    python_import_source_resolver: Callable[[str], str | None] | None = None,
) -> str:
    path = test_ref.split("::", 1)[0]
    if path.endswith(".py"):
        entries = _python_inventory_entries(
            path,
            source_text,
            python_import_source_resolver,
        )
        declaration_sources = {
            declaration.ref: declaration_source
            for declaration, declaration_source in entries
        }
        declaration_source = declaration_sources.get(test_ref)
    else:
        try:
            declaration_source = frontend_source_for_ref(
                path,
                source_text,
                test_ref,
                import_binding_resolver,
            )
        except FrontendInventoryError as exc:
            raise TestCorpusEvidenceError(str(exc)) from None
    if declaration_source is None:
        raise TestCorpusEvidenceError(
            f"replacement assertion source is missing: {test_ref}"
        )
    return build_test_source_ref(test_ref, declaration_source)


def _worktree_source_ref(repo: Path, test_ref: str) -> str:
    path = test_ref.split("::", 1)[0]
    text = _read_worktree_text(
        repo,
        path,
        missing_error=TestCorpusSourceRefMissingError,
    )

    def read_import(candidate: str) -> str | None:
        target = repo / candidate
        if not target.is_file():
            return None
        return _read_worktree_text(repo, candidate)

    return _source_ref_from_text(
        test_ref,
        text,
        _frontend_import_resolver(path, read_import),
        _python_import_resolver(read_import),
    )


def _resolve_assertion_source_ref(
    repo: Path,
    test_ref: str,
    historical_source_refs: dict[str, str],
) -> str:
    try:
        return _worktree_source_ref(repo, test_ref)
    except TestCorpusSourceRefMissingError:
        historical = historical_source_refs.get(test_ref)
        if historical is None:
            raise TestCorpusEvidenceError(
                f"replacement assertion source is missing: {test_ref}"
            ) from None
        return historical


def _validate_verification_envelope(
    _repo: Path,
    encoded_envelope: str,
    _replacement_refs: list[str],
    _resolve_assertion_source_ref: Callable[[str], str],
) -> None:
    try:
        decode_github_job_output(encoded_envelope)
    except VerificationGithubTransportError as exc:
        raise TestCorpusEvidenceError(
            "retired test verification receipt is invalid"
        ) from exc
    raise TestCorpusEvidenceError(
        "retired test verification receipt lacks independent GitHub attestation"
    )


def _historical_source_refs(ledger: dict[str, Any]) -> dict[str, str]:
    source_refs: dict[str, str] = {}
    records = ledger.get("retirements")
    if not isinstance(records, list):
        return source_refs
    for record in records:
        if not isinstance(record, dict):
            continue
        equivalence = record.get("assertion_equivalence_artifact")
        if not isinstance(equivalence, dict):
            continue
        evidence = equivalence.get("preserved_assertion_evidence")
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            artifact = item.get("artifact") if isinstance(item, dict) else None
            if not isinstance(artifact, dict):
                continue
            replacement_ref = artifact.get("replacement_ref")
            source_ref = artifact.get("source_ref")
            if isinstance(replacement_ref, str) and isinstance(source_ref, str):
                existing = source_refs.setdefault(replacement_ref, source_ref)
                if existing != source_ref:
                    raise TestCorpusGuardError(
                        "historical replacement source refs conflict"
                    )
    return source_refs


def removed_declarations(repo: Path, base_sha: str) -> tuple[str, ...]:
    removed: set[str] = set()
    current_paths = set(discover_test_files(repo))
    for path in _changed_test_paths(repo, base_sha):
        prior = _base_text(repo, base_sha, path)
        if prior is None:
            continue
        prior_refs = {
            item.ref
            for item in _parse_base_test_declarations(repo, base_sha, path, prior)
        }
        if path in current_paths:
            current_text = _read_worktree_text(repo, path)
            current_refs = {
                item.ref
                for item in _parse_worktree_test_declarations(repo, path, current_text)
            }
        else:
            current_refs = set()
        removed.update(prior_refs - current_refs)
    return tuple(sorted(removed))


def _parse_ledger_text(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TestCorpusGuardError("test-corpus retirement ledger is invalid") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "retirements"}
        or value.get("schema_version") != RETIREMENT_SCHEMA
    ):
        raise TestCorpusGuardError("test-corpus retirement ledger schema is invalid")
    return value


def _load_ledger(repo: Path) -> dict[str, Any]:
    return _parse_ledger_text(
        _read_bounded_regular_text(
            repo,
            RETIREMENT_LEDGER,
            max_bytes=MAX_RETIREMENT_LEDGER_BYTES,
            unsafe_message="test-corpus retirement ledger is unsafe",
            invalid_message="test-corpus retirement ledger is invalid",
        )
    )


def _load_base_ledger(repo: Path, base_sha: str) -> dict[str, Any]:
    path = RETIREMENT_LEDGER.as_posix()
    listing = _run_git(
        repo,
        ["ls-tree", "--name-only", "-z", base_sha, "--", path],
    )
    if listing.returncode != 0:
        raise TestCorpusGuardError("cannot inspect base test-corpus retirement ledger")
    try:
        paths = {item for item in listing.stdout.decode("utf-8").split("\0") if item}
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError(
            "base test-corpus retirement ledger path is invalid"
        ) from exc
    if path not in paths:
        return {"schema_version": RETIREMENT_SCHEMA, "retirements": []}
    size = _run_git(repo, ["cat-file", "-s", f"{base_sha}:{path}"])
    if size.returncode != 0:
        raise TestCorpusGuardError("cannot inspect base test-corpus retirement ledger")
    try:
        byte_count = int(size.stdout.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise TestCorpusGuardError(
            "base test-corpus retirement ledger size is invalid"
        ) from exc
    if byte_count > MAX_RETIREMENT_LEDGER_BYTES:
        raise TestCorpusGuardError(
            "base test-corpus retirement ledger exceeds byte budget"
        )
    result = _run_git(repo, ["show", f"{base_sha}:{path}"])
    if result.returncode != 0:
        raise TestCorpusGuardError("cannot read base test-corpus retirement ledger")
    try:
        return _parse_ledger_text(result.stdout.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError(
            "base test-corpus retirement ledger is invalid"
        ) from exc


def validate_retirements(
    current_refs: set[str],
    removed_refs: set[str],
    ledger: dict[str, Any],
    *,
    resolve_assertion_source_ref: Callable[[str], str],
    validate_verification_envelope: Callable[[str, list[str]], None],
    base_ledger: dict[str, Any] | None = None,
) -> int:
    try:
        return _validate_retirement_evidence(
            current_refs,
            removed_refs,
            ledger,
            validate_test_ref=_validate_test_ref,
            resolve_assertion_source_ref=resolve_assertion_source_ref,
            validate_verification_envelope=validate_verification_envelope,
            base_ledger=base_ledger,
        )
    except TestCorpusEvidenceError as exc:
        raise TestCorpusGuardError(str(exc)) from None


def inventory_fingerprint(declarations: tuple[TestDeclaration, ...]) -> str:
    payload = [
        {"ref": declaration.ref, "kind": declaration.kind}
        for declaration in declarations
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"test-corpus-inventory-ref:sha256:{hashlib.sha256(encoded).hexdigest()}"


def verify_test_corpus_guard(
    repo: Path,
    *,
    base_sha: str | None = None,
) -> dict[str, object]:
    declarations = inventory_worktree(repo)
    current_refs = {item.ref for item in declarations}
    resolved_base = _resolve_base_sha(
        repo,
        base_sha if base_sha is not None else os.environ.get(BASE_SHA_ENV),
    )
    removed = (
        set(removed_declarations(repo, resolved_base))
        if resolved_base is not None
        else set()
    )
    ledger = _load_ledger(repo)
    base_ledger = (
        _load_base_ledger(repo, resolved_base) if resolved_base is not None else None
    )
    historical_source_refs = _historical_source_refs(base_ledger or {})

    def resolve_source_ref(ref: str) -> str:
        return _resolve_assertion_source_ref(repo, ref, historical_source_refs)

    retirement_count = validate_retirements(
        current_refs,
        removed,
        ledger,
        resolve_assertion_source_ref=resolve_source_ref,
        validate_verification_envelope=lambda envelope, refs: (
            _validate_verification_envelope(repo, envelope, refs, resolve_source_ref)
        ),
        base_ledger=base_ledger,
    )
    return {
        "test_declaration_count": len(declarations),
        "python_test_count": sum(item.kind == "python_test" for item in declarations),
        "frontend_test_count": sum(
            item.kind == "frontend_test" for item in declarations
        ),
        "inventory_ref": inventory_fingerprint(declarations),
        "comparison_base_status": (
            "bound" if resolved_base is not None else "unavailable_local_only"
        ),
        "removed_test_count": len(removed),
        "retirement_record_count": retirement_count,
    }
