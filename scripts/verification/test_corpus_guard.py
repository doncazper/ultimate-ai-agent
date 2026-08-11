"""Deterministic test-corpus inventory and retirement/replacement guardrails."""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import os
import posixpath
import re
import select
import stat
import subprocess
import time
import tomllib
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
    frontend_collection_setup_modules,
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
MAX_PYTHON_DEPENDENCY_MODULES = 20_000
MAX_FRONTEND_DEPENDENCY_MODULES = 20_000
GIT_INSPECTION_TIMEOUT_SECONDS = 30.0
PYTEST_COLLECTION_CONFIG_PATHS = {
    ".pytest.ini",
    ".pytest.toml",
    "pyproject.toml",
    "pytest.ini",
    "pytest.toml",
    "setup.cfg",
    "tox.ini",
}
PYTEST_DEPENDENCY_LOCK_PATHS = {"uv.lock"}
PYTEST_RUNNER_CONFIG_PATHS = {
    ".github/actions/setup-toolchain/action.yml",
    ".github/workflows/ci.yml",
    "scripts/verification/ci_command_manifest.py",
    "scripts/verification/run_ci_lane.py",
    "scripts/verification/run_pytest_shards.py",
}
PYTEST_RUNNER_PLUGIN_MODULES = frozenset(
    {
        "scripts.verification.pytest_collection_evidence",
        "scripts.verification.pytest_safe_failure_plugin",
    }
)
PYTEST_RUNNER_MODULES = frozenset(
    {
        "scripts.verification.run_ci_lane",
        "scripts.verification.run_pytest_shards",
        *PYTEST_RUNNER_PLUGIN_MODULES,
    }
)
VITEST_CONFIG_EXTENSIONS = ("js", "mjs", "cjs", "ts", "mts", "cts")
FRONTEND_COLLECTION_CONFIG_PATHS = {
    *(
        f"apps/control-center/{name}.{extension}"
        for name in ("vite.config", "vitest.config")
        for extension in VITEST_CONFIG_EXTENSIONS
    ),
    "apps/control-center/playwright.smoke.config.ts",
    "apps/control-center/playwright.visual.config.ts",
}
FRONTEND_TEST_SCRIPT_CONFIG_PATHS = {
    "apps/control-center/package.json",
}
FRONTEND_TEST_DEPENDENCY_PATHS = {
    "apps/control-center/package-lock.json",
    "apps/control-center/package.json",
    "apps/control-center/npm-shrinkwrap.json",
}
PYTEST_COLLECTION_HOOK_NAMES = frozenset(
    {
        "collect_ignore",
        "pytest_collection",
        "pytest_generate_tests",
        "pytest_ignore_collect",
        "pytest_collect_directory",
        "pytest_collect_file",
        "pytest_pycollect_makemodule",
        "pytest_pycollect_makeitem",
        "pytest_make_collect_report",
        "pytest_itemcollected",
        "pytest_collection_modifyitems",
        "pytest_collection_finish",
        "pytest_addoption",
        "pytest_cmdline_parse",
        "pytest_configure",
        "pytest_load_initial_conftests",
        "pytest_plugin_registered",
        "pytest_sessionstart",
    }
)
PYTEST_COLLECTION_CLASS_NAMES = frozenset(
    {"Class", "Collector", "File", "Function", "Item", "Module", "Package", "Session"}
)
PYTEST_EXECUTION_DISABLING_MARKS = frozenset({"skip", "skipif"})
GLOBALS_NAMESPACE_MUTATOR_METHODS = {
    "__delitem__",
    "__ior__",
    "__setitem__",
    "clear",
    "pop",
    "popitem",
    "setdefault",
    "update",
}
MODULE_NAMESPACE_ACCESSORS = frozenset({"globals", "locals", "vars"})
GLOBAL_NAMESPACE_ACCESSORS = frozenset({"globals"})
LOCAL_NAMESPACE_ACCESSORS = frozenset({"locals", "vars"})
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
REPOSITORY_READER_ATTRIBUTES = {
    "glob",
    "iglob",
    "iterdir",
    "listdir",
    "open",
    "read",
    "read_bytes",
    "read_text",
    "readlines",
    "rglob",
    "scandir",
    "walk",
}
REPOSITORY_READER_IMPORTS = {
    "builtins.open",
    "bz2.open",
    "codecs.open",
    "glob.glob",
    "glob.iglob",
    "gzip.open",
    "io.open",
    "lzma.open",
    "os.fdopen",
    "os.listdir",
    "os.open",
    "os.scandir",
    "os.walk",
    "tokenize.open",
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
FRONTEND_SOURCE_GIT_PATHSPECS = tuple(
    f":(glob)**/*.{extension}" for extension in FRONTEND_TEST_EXTENSIONS
)
PYTHON_TEST_GIT_PATHSPEC = ":(glob)**/*.py"
PYTEST_IGNORED_DIRECTORY_NAMES = {
    "CVS",
    "__pycache__",
    "_darcs",
    "build",
    "dist",
    "node_modules",
    "venv",
    "{arch}",
}
FRONTEND_IGNORED_DIRECTORY_NAMES = {".git", "node_modules"}
BUILTIN_EXCEPTION_CLASS_NAMES = frozenset(
    name
    for name, value in vars(builtins).items()
    if isinstance(value, type) and issubclass(value, BaseException)
)


class TestCorpusGuardError(RuntimeError):
    """Raised when corpus inventory or retirement evidence is invalid."""


class TestCorpusSourceRefMissingError(RuntimeError):
    """Raised only when a replacement source ref is absent from the worktree."""


class TestCorpusDeclarationMissingError(TestCorpusEvidenceError):
    """Raised only when a readable replacement file lacks the requested declaration."""


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


def _is_statically_noncallable_python_value(node: ast.AST | None) -> bool:
    if node is None or isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.Dict, ast.List, ast.Set, ast.Tuple)):
        return True
    if isinstance(node, ast.UnaryOp):
        return _is_statically_noncallable_python_value(node.operand)
    if isinstance(node, (ast.BinOp, ast.BoolOp, ast.Compare, ast.JoinedStr)):
        return True
    if isinstance(node, ast.IfExp):
        return _is_statically_noncallable_python_value(
            node.body
        ) and _is_statically_noncallable_python_value(node.orelse)
    return isinstance(node, (ast.DictComp, ast.GeneratorExp, ast.ListComp, ast.SetComp))


def _is_current_module_object(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
) -> bool:
    if not (
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Name)
        and node.slice.id == "__name__"
    ):
        return False
    registry = node.value
    if isinstance(registry, ast.Name):
        return "sys.modules" in imported_modules.get(registry.id, ())
    if not isinstance(registry, ast.Attribute) or registry.attr != "modules":
        return False
    root = _root_name(registry)
    return root == "sys" or (
        root is not None and "sys" in imported_modules.get(root, ())
    )


def _is_current_module_namespace(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "__dict__"
        and _is_current_module_object(node.value, imported_modules)
    ) or (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "vars"
        and len(node.args) == 1
        and not node.keywords
        and _is_current_module_object(node.args[0], imported_modules)
    )


def _current_module_write_targets(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
) -> tuple[str | None, ...]:
    if isinstance(node, ast.Attribute) and _is_current_module_object(
        node.value,
        imported_modules,
    ):
        return (node.attr,)
    if not isinstance(node, ast.Subscript) or not _is_current_module_namespace(
        node.value,
        imported_modules,
    ):
        return ()
    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        return (node.slice.value,)
    return (None,)


def _module_namespace_write_targets(
    node: ast.AST,
    *,
    accessors: frozenset[str] = frozenset({"globals"}),
) -> tuple[str | None, ...]:
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(
            target
            for child in node.elts
            for target in _module_namespace_write_targets(
                child,
                accessors=accessors,
            )
        )
    if not isinstance(node, ast.Subscript):
        return ()
    namespace = node.value
    if not (
        isinstance(namespace, ast.Call)
        and isinstance(namespace.func, ast.Name)
        and namespace.func.id in accessors
        and not namespace.args
        and not namespace.keywords
    ):
        return ()
    key = node.slice
    if isinstance(key, ast.Constant) and isinstance(key.value, str):
        return (key.value,)
    return (None,)


def _is_module_namespace_call(
    node: ast.AST,
    *,
    accessors: frozenset[str] = frozenset({"globals"}),
) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in accessors
        and not node.args
        and not node.keywords
    )


def _is_globals_call(node: ast.AST) -> bool:
    return _is_module_namespace_call(node)


def _is_module_namespace_mutator_call(
    node: ast.AST,
    *,
    accessors: frozenset[str] = MODULE_NAMESPACE_ACCESSORS,
) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in GLOBALS_NAMESPACE_MUTATOR_METHODS
        and _is_module_namespace_call(
            node.func.value,
            accessors=accessors,
        )
    )


def _is_module_namespace_alias_binding(
    node: ast.AST,
    *,
    accessors: frozenset[str] = frozenset({"globals"}),
) -> bool:
    if isinstance(node, ast.Assign):
        targets = node.targets
        value = node.value
    elif isinstance(node, ast.AnnAssign):
        targets = (node.target,)
        value = node.value
    elif isinstance(node, ast.NamedExpr):
        targets = (node.target,)
        value = node.value
    else:
        return False
    return _is_module_namespace_call(value, accessors=accessors) and any(
        _binding_target_names(target) for target in targets
    )


def _has_module_namespace_mutation(tree: ast.Module) -> bool:
    return any(
        _is_module_namespace_mutator_call(
            node,
            accessors=GLOBAL_NAMESPACE_ACCESSORS,
        )
        or _is_module_namespace_alias_binding(
            node,
            accessors=GLOBAL_NAMESPACE_ACCESSORS,
        )
        for node in ast.walk(tree)
    ) or any(
        _is_module_namespace_mutator_call(
            node,
            accessors=LOCAL_NAMESPACE_ACCESSORS,
        )
        or _is_module_namespace_alias_binding(
            node,
            accessors=LOCAL_NAMESPACE_ACCESSORS,
        )
        for node in _module_execution_nodes(tree)
    )


def _mutated_attribute_call(node: ast.AST) -> tuple[ast.AST, str | None] | None:
    if not isinstance(node, ast.Call) or len(node.args) < 2:
        return None
    builtin_mutator = isinstance(node.func, ast.Name) and node.func.id in {
        "setattr",
        "delattr",
    }
    descriptor_mutator = isinstance(node.func, ast.Attribute) and node.func.attr in {
        "__setattr__",
        "__delattr__",
    }
    if not builtin_mutator and not descriptor_mutator:
        return None
    attribute = node.args[1]
    return (
        node.args[0],
        attribute.value
        if isinstance(attribute, ast.Constant) and isinstance(attribute.value, str)
        else None,
    )


def _resolved_expression_root(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.NamedExpr):
        return _resolved_expression_root(node.value, aliases)
    root = _root_name(node)
    return aliases.get(root, root) if root is not None else None


def _paired_name_aliases(
    target: ast.AST,
    value: ast.AST,
    aliases: dict[str, str],
) -> dict[str, str]:
    if isinstance(target, ast.Name) and isinstance(value, ast.Name):
        return {target.id: aliases.get(value.id, value.id)}
    if (
        isinstance(target, (ast.Tuple, ast.List))
        and isinstance(value, (ast.Tuple, ast.List))
        and len(target.elts) == len(value.elts)
    ):
        resolved: dict[str, str] = {}
        for child_target, child_value in zip(target.elts, value.elts, strict=True):
            resolved.update(_paired_name_aliases(child_target, child_value, aliases))
        return resolved
    return {}


def _module_name_aliases(
    tree: ast.Module,
    *,
    before: tuple[int, int],
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in tree.body:
        position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
        if position >= before:
            break
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = (node.target,)
            value = node.value
        elif isinstance(node, (ast.AugAssign, ast.Delete)):
            targets = (
                (node.target,) if isinstance(node, ast.AugAssign) else node.targets
            )
            value = None
        else:
            continue
        target_names = {
            name for target in targets for name in _binding_target_names(target)
        }
        if isinstance(value, ast.Name):
            resolved = aliases.get(value.id, value.id)
            for name in target_names:
                if name != resolved:
                    aliases[name] = resolved
        elif value is not None:
            paired_aliases: dict[str, str] = {}
            for target in targets:
                paired_aliases.update(_paired_name_aliases(target, value, aliases))
            for name in target_names:
                if name in paired_aliases and name != paired_aliases[name]:
                    aliases[name] = paired_aliases[name]
                else:
                    aliases.pop(name, None)
        else:
            for name in target_names:
                aliases.pop(name, None)
    return aliases


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
        for call in (
            child
            for child in ast.walk(module_node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        ):
            helper_name = call.func.id
            effects, dependencies = helper_effects(helper_name, set())
            helper = helper_defs.get(helper_name)
            parameter_bindings: dict[str, str] = {}
            if helper is not None:
                for parameter, argument in zip(
                    helper.args.args, call.args, strict=False
                ):
                    root = _root_name(argument)
                    if root is not None:
                        parameter_bindings[parameter.arg] = root
            for effect_name in effects:
                affected_name = parameter_bindings.get(effect_name, effect_name)
                add(affected_name, module_node, applies_after=True)
                for dependency in dependencies:
                    add(
                        affected_name,
                        helper_defs[dependency],
                        applies_after=True,
                    )
    return {name: tuple(bindings) for name, bindings in mutable.items()}


def _pytest_module_aliases(tree: ast.Module) -> set[str]:
    aliases = {
        imported.asname or imported.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for imported in node.names
        if imported.name == "pytest"
    }
    changed = True
    while changed:
        changed = False
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if not isinstance(value, ast.Name) or value.id not in aliases:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                for name in _binding_target_names(target):
                    if name not in aliases:
                        aliases.add(name)
                        changed = True
    return aliases


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


def _fixture_aliases(tree: ast.Module) -> set[str]:
    imported_pytest_roots = {
        imported.asname or imported.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for imported in node.names
        if imported.name == "pytest"
    }
    pytest_roots = _pytest_module_aliases(tree)
    aliases = {f"{root}.fixture" for root in pytest_roots}
    imported_fixture_names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "pytest":
            for imported in node.names:
                if imported.name == "fixture":
                    local_name = imported.asname or imported.name
                    aliases.add(local_name)
                    imported_fixture_names.add(local_name)
    protected_names = imported_pytest_roots | imported_fixture_names
    for node in _module_execution_nodes(tree):
        aliases_before = _module_name_aliases(
            tree,
            before=(getattr(node, "lineno", 0), getattr(node, "col_offset", 0)),
        )
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = (node.target,)
        elif isinstance(node, ast.Delete):
            targets = node.targets
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            targets = (node.target,)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = tuple(
                item.optional_vars
                for item in node.items
                if item.optional_vars is not None
            )
        else:
            targets = ()
        if any(
            isinstance(target, ast.Attribute)
            and target.attr == "fixture"
            and _resolved_expression_root(target.value, aliases_before) in pytest_roots
            for target in targets
        ):
            raise TestCorpusGuardError(
                "dynamic pytest fixture alias cannot be inventoried safely"
            )
        mutation = _mutated_attribute_call(node)
        if (
            mutation is not None
            and _resolved_expression_root(mutation[0], aliases_before) in pytest_roots
            and mutation[1] in {None, "fixture"}
        ):
            raise TestCorpusGuardError(
                "dynamic pytest fixture alias cannot be inventoried safely"
            )
        rebound = {name for target in targets for name in _binding_target_names(target)}
        if isinstance(node, ast.ExceptHandler) and node.name is not None:
            rebound.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            rebound.add(node.name)
        elif isinstance(node, ast.Import):
            rebound.update(
                imported.asname or imported.name.split(".", 1)[0]
                for imported in node.names
                if imported.name != "pytest"
            )
        elif isinstance(node, ast.ImportFrom):
            rebound.update(
                imported.asname or imported.name
                for imported in node.names
                if not (node.module == "pytest" and imported.name == "fixture")
            )
        if rebound & protected_names:
            raise TestCorpusGuardError(
                "dynamic pytest fixture alias cannot be inventoried safely"
            )
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
                and value.attr == "fixture"
                and _root_name(value) in pytest_roots
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


def _parameterized_fixture_factory_aliases(
    tree: ast.Module,
    fixture_aliases: set[str],
) -> set[str]:
    aliases: set[str] = set()
    scope_nodes = (
        *_module_execution_nodes(tree),
        *(
            scope_node
            for class_node in ast.walk(tree)
            if isinstance(class_node, ast.ClassDef)
            for scope_node in _scope_execution_nodes(class_node.body)
        ),
    )
    changed = True
    while changed:
        changed = False
        for node in scope_nodes:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if value is None:
                continue
            resolves = (
                isinstance(value, ast.Call)
                and _is_fixture_callable(value.func, fixture_aliases)
                and any(keyword.arg in {None, "params"} for keyword in value.keywords)
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


def _fixture_factory_aliases(
    tree: ast.Module,
    fixture_aliases: set[str],
) -> set[str]:
    aliases: set[str] = set()
    scope_nodes = (
        *_module_execution_nodes(tree),
        *(
            scope_node
            for class_node in ast.walk(tree)
            if isinstance(class_node, ast.ClassDef)
            for scope_node in _scope_execution_nodes(class_node.body)
        ),
    )
    changed = True
    while changed:
        changed = False
        for node in scope_nodes:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if value is None:
                continue
            resolves = (
                isinstance(value, ast.Call)
                and _is_fixture_callable(value.func, fixture_aliases)
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


def _is_fixture_callable(node: ast.AST, aliases: set[str]) -> bool:
    if isinstance(node, ast.Attribute) and node.attr == "fixture":
        root = _root_name(node)
        return root is not None and f"{root}.fixture" in aliases
    return isinstance(node, ast.Name) and node.id in aliases


def _is_parametrize_callable(node: ast.AST, aliases: set[str]) -> bool:
    return (isinstance(node, ast.Attribute) and node.attr == "parametrize") or (
        isinstance(node, ast.Name) and node.id in aliases
    )


def _post_definition_parametrize_targets(
    tree: ast.Module,
    aliases: set[str],
) -> set[str]:
    targets: set[str] = set()
    for child in ast.walk(tree):
        if (
            not isinstance(child, ast.Call)
            or not isinstance(child.func, ast.Call)
            or not _is_parametrize_callable(child.func.func, aliases)
        ):
            continue
        name_aliases = _module_name_aliases(
            tree,
            before=(child.lineno, child.col_offset),
        )
        for argument in child.args:
            root = _root_name(argument)
            if root is not None:
                targets.add(name_aliases.get(root, root))
    return targets


def _post_definition_parameterized_fixture_targets(
    tree: ast.Module,
    fixture_aliases: set[str],
    factory_aliases: set[str],
) -> set[str]:
    targets: set[str] = set()
    for child in ast.walk(tree):
        if not isinstance(child, ast.Call):
            continue
        factory = child.func
        is_parameterized_factory = (
            isinstance(factory, ast.Call)
            and _is_fixture_callable(factory.func, fixture_aliases)
            and any(keyword.arg in {None, "params"} for keyword in factory.keywords)
        ) or (isinstance(factory, ast.Name) and factory.id in factory_aliases)
        if not is_parameterized_factory:
            continue
        name_aliases = _module_name_aliases(
            tree,
            before=(child.lineno, child.col_offset),
        )
        for argument in child.args:
            root = _root_name(argument)
            if root is not None:
                targets.add(name_aliases.get(root, root))
    return targets


def _python_import_modules(
    tree: ast.Module,
    *,
    relative_package: str | None = None,
) -> dict[str, tuple[str, ...]]:
    modules: dict[str, tuple[str, ...]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                local = imported.asname or imported.name.split(".", 1)[0]
                modules[local] = tuple(
                    dict.fromkeys((*modules.get(local, ()), imported.name))
                )
        elif isinstance(node, ast.ImportFrom):
            for imported in node.names:
                if imported.name == "*":
                    continue
                local = imported.asname or imported.name
                if node.level and relative_package is None:
                    modules[local] = ()
                else:
                    if node.level:
                        package_parts = relative_package.split(".")
                        parent_count = node.level - 1
                        if parent_count >= len(package_parts):
                            modules[local] = ()
                            continue
                        prefix = ".".join(
                            package_parts[: len(package_parts) - parent_count]
                        )
                        imported_module = (
                            f"{prefix}.{node.module}" if node.module else prefix
                        )
                    elif node.module is not None:
                        imported_module = node.module
                    else:
                        modules[local] = ()
                        continue
                    modules[local] = tuple(
                        dict.fromkeys(
                            (
                                *modules.get(local, ()),
                                f"{imported_module}.{imported.name}",
                                imported_module,
                            )
                        )
                    )
    return modules


def _is_pytest_collection_class_reference(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
) -> bool:
    root = _root_name(node)
    if root is None:
        return False
    attributes: set[str] = set()
    current = node
    while isinstance(current, ast.Attribute):
        attributes.add(current.attr)
        current = current.value
    candidates = imported_modules.get(root, ())
    pytest_candidates = {
        candidate
        for candidate in candidates
        if candidate == "pytest"
        or candidate.startswith("pytest.")
        or candidate == "_pytest"
        or candidate.startswith("_pytest.")
    }
    return bool(pytest_candidates) and bool(
        PYTEST_COLLECTION_CLASS_NAMES
        & {
            *attributes,
            *(part for candidate in pytest_candidates for part in candidate.split(".")),
        }
    )


def _has_pytest_collection_class_mutation(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
) -> bool:
    descriptor_mutator_aliases = {
        name
        for node in _module_execution_nodes(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        for name in _binding_target_names(target)
        if isinstance(node.value, ast.Attribute)
        and node.value.attr in {"__setattr__", "__delattr__"}
    }
    for node in _module_execution_nodes(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = (node.target,)
        elif isinstance(node, ast.Delete):
            targets = node.targets
        else:
            targets = ()
        if any(
            isinstance(target, ast.Attribute)
            and _is_pytest_collection_class_reference(target, imported_modules)
            for target in targets
        ):
            return True
        mutation = _mutated_attribute_call(node)
        if (
            mutation is None
            and isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in descriptor_mutator_aliases
            and len(node.args) >= 2
        ):
            attribute = node.args[1]
            mutation = (
                node.args[0],
                attribute.value
                if isinstance(attribute, ast.Constant)
                and isinstance(attribute.value, str)
                else None,
            )
        if mutation is not None and _is_pytest_collection_class_reference(
            mutation[0], imported_modules
        ):
            return True
    return False


def _definition_time_nodes(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> tuple[ast.AST, ...]:
    expressions: list[ast.AST] = [*node.decorator_list]
    expressions.extend(getattr(node, "type_params", ()))
    if isinstance(node, ast.ClassDef):
        expressions.extend(node.bases)
        expressions.extend(keyword.value for keyword in node.keywords)
        return tuple(expressions)
    arguments = node.args
    expressions.extend(arguments.defaults)
    expressions.extend(
        default for default in arguments.kw_defaults if default is not None
    )
    expressions.extend(
        argument.annotation
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            *((arguments.vararg,) if arguments.vararg is not None else ()),
            *((arguments.kwarg,) if arguments.kwarg is not None else ()),
        )
        if argument.annotation is not None
    )
    if node.returns is not None:
        expressions.append(node.returns)
    return tuple(expressions)


def _scope_execution_nodes(body: list[ast.stmt]) -> tuple[ast.AST, ...]:
    pending: list[ast.AST] = list(reversed(body))
    nodes: list[ast.AST] = []
    while pending:
        node = pending.pop()
        nodes.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            pending.extend(reversed(_definition_time_nodes(node)))
            continue
        pending.extend(reversed(tuple(ast.iter_child_nodes(node))))
    return tuple(nodes)


def _module_execution_nodes(tree: ast.Module) -> tuple[ast.AST, ...]:
    return _scope_execution_nodes(tree.body)


def _pytest_collection_abort_callable_name(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
    aliases: dict[str, str],
) -> str:
    if isinstance(node, ast.Attribute):
        root = _root_name(node)
        if root is None:
            return ""
        candidates = imported_modules.get(root, ())
        return node.attr if root == "pytest" or "pytest" in candidates else ""
    if isinstance(node, ast.Name):
        if node.id in aliases:
            return aliases[node.id]
        candidates = imported_modules.get(node.id, ())
        return next(
            (
                candidate.rsplit(".", 1)[-1]
                for candidate in candidates
                if candidate in {"pytest.importorskip", "pytest.skip"}
            ),
            "",
        )
    return ""


def _pytest_collection_abort_aliases(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    changed = True
    while changed:
        changed = False
        for node in _module_execution_nodes(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if value is None:
                continue
            name = _pytest_collection_abort_callable_name(
                value,
                imported_modules,
                aliases,
            )
            if name not in {"importorskip", "skip"}:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                for alias in _binding_target_names(target):
                    if aliases.get(alias) != name:
                        aliases[alias] = name
                        changed = True
    return aliases


def _is_pytest_collection_abort_call(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
    aliases: dict[str, str],
) -> bool:
    if not isinstance(node, ast.Call):
        return False
    name = _pytest_collection_abort_callable_name(
        node.func,
        imported_modules,
        aliases,
    )
    if name == "importorskip":
        return True
    return name == "skip" and any(
        keyword.arg == "allow_module_level"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is True
        for keyword in node.keywords
    )


def _has_module_level_pytest_collection_abort(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
) -> bool:
    aliases = _pytest_collection_abort_aliases(tree, imported_modules)
    return any(
        _is_pytest_collection_abort_call(node, imported_modules, aliases)
        for node in _module_execution_nodes(tree)
    )


def _unittest_skiptest_reference(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
    aliases: set[str],
    namespace_aliases: set[str],
) -> bool:
    def is_skiptest_candidate(candidate: str) -> bool:
        return candidate in {"unittest.SkipTest", "unittest.case.SkipTest"}

    if isinstance(node, ast.Name):
        return node.id in aliases or any(
            is_skiptest_candidate(candidate)
            for candidate in imported_modules.get(node.id, ())
        )
    if not isinstance(node, ast.Attribute) or node.attr != "SkipTest":
        return False
    root = _root_name(node)
    return root in namespace_aliases or root == "unittest" or (
        root is not None
        and any(
            candidate in {"unittest", "unittest.case"}
            for candidate in imported_modules.get(root, ())
        )
    )


def _has_module_level_unittest_collection_abort(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
) -> bool:
    namespace_aliases = {
        name
        for name, candidates in imported_modules.items()
        if any(candidate in {"unittest", "unittest.case"} for candidate in candidates)
    }
    aliases = {
        name
        for name, candidates in imported_modules.items()
        if any(
            candidate in {"unittest.SkipTest", "unittest.case.SkipTest"}
            for candidate in candidates
        )
    }
    changed = True
    while changed:
        changed = False
        for node in _module_execution_nodes(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            target_names = {
                name for target in targets for name in _binding_target_names(target)
            }
            root = _root_name(value)
            is_namespace = (
                isinstance(value, ast.Name) and value.id in namespace_aliases
            ) or (
                isinstance(value, ast.Attribute)
                and value.attr == "case"
                and root in namespace_aliases
            )
            if is_namespace:
                for name in target_names:
                    if name not in namespace_aliases:
                        namespace_aliases.add(name)
                        changed = True
            if not _unittest_skiptest_reference(
                value,
                imported_modules,
                aliases,
                namespace_aliases,
            ):
                continue
            for name in target_names:
                if name not in aliases:
                    aliases.add(name)
                    changed = True
    for node in _module_execution_nodes(tree):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        raised = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        if _unittest_skiptest_reference(
            raised,
            imported_modules,
            aliases,
            namespace_aliases,
        ):
            return True
    return False


def _has_module_level_collection_abort(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
) -> bool:
    return _has_module_level_pytest_collection_abort(
        tree, imported_modules
    ) or _has_module_level_unittest_collection_abort(tree, imported_modules)


def _reject_repository_reader_calls(
    nodes: tuple[ast.AST, ...] | list[ast.AST],
    imported_modules: dict[str, tuple[str, ...]],
    *,
    root_nodes: tuple[ast.AST, ...] = (),
    root_callable_names: tuple[str, ...] = (),
) -> None:
    binding_nodes = {
        (node.lineno, node.col_offset): node
        for node in nodes
        if hasattr(node, "lineno")
    }
    construction_nodes = {
        position: node
        for position, node in binding_nodes.items()
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
    }
    callable_nodes = {
        node.name: node
        for node in binding_nodes.values()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    pending_constructors = {
        child.func.id
        for node in (*construction_nodes.values(), *root_nodes)
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    pending_constructors.update(root_callable_names)
    inspected_constructors: set[str] = set()
    while pending_constructors:
        name = pending_constructors.pop()
        if name in inspected_constructors or name not in callable_nodes:
            continue
        inspected_constructors.add(name)
        callable_node = callable_nodes[name]
        if isinstance(callable_node, ast.ClassDef):
            methods = {
                child.name: child
                for child in callable_node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            pending_methods = [
                method for method in ("__init__", "__new__") if method in methods
            ]
            inspected_methods: set[str] = set()
            while pending_methods:
                method_name = pending_methods.pop()
                if method_name in inspected_methods:
                    continue
                inspected_methods.add(method_name)
                method = methods[method_name]
                construction_nodes[(method.lineno, method.col_offset)] = method
                pending_methods.extend(
                    child.func.attr
                    for child in ast.walk(method)
                    if isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and isinstance(child.func.value, ast.Name)
                    and child.func.value.id in {"self", "cls"}
                    and child.func.attr in methods
                )
            callable_scan_nodes: tuple[ast.AST, ...] = tuple(
                methods[method] for method in inspected_methods
            )
        else:
            construction_nodes[(callable_node.lineno, callable_node.col_offset)] = (
                callable_node
            )
            callable_scan_nodes = (callable_node,)
        pending_constructors.update(
            child.func.id
            for scan_node in callable_scan_nodes
            for child in ast.walk(scan_node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        )
    inspected_nodes = tuple(construction_nodes.values())
    alias_assignments: list[tuple[str, ast.expr]] = []

    def assigned_pairs(
        target: ast.AST, value: ast.expr
    ) -> tuple[tuple[str, ast.expr], ...]:
        if isinstance(target, ast.Name):
            return ((target.id, value),)
        if (
            isinstance(target, (ast.List, ast.Tuple))
            and isinstance(value, (ast.List, ast.Tuple))
            and len(target.elts) == len(value.elts)
        ):
            return tuple(
                pair
                for target_item, value_item in zip(target.elts, value.elts, strict=True)
                for pair in assigned_pairs(target_item, value_item)
            )
        return ()

    for node in inspected_nodes:
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                alias_assignments.extend(
                    pair
                    for target in child.targets
                    for pair in assigned_pairs(target, child.value)
                )
            elif isinstance(child, ast.AnnAssign) and child.value is not None:
                alias_assignments.extend(assigned_pairs(child.target, child.value))
            elif isinstance(child, ast.NamedExpr):
                alias_assignments.extend(assigned_pairs(child.target, child.value))

    dynamic_import_aliases = {"__import__"}
    dynamic_import_aliases.update(
        local_name
        for local_name, candidates in imported_modules.items()
        if "importlib.import_module" in candidates
    )

    def is_dynamic_import_callable(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id in dynamic_import_aliases
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "import_module"
            and (root := _root_name(node)) is not None
            and "importlib" in imported_modules.get(root, ())
        )

    while True:
        added = {
            name
            for name, value in alias_assignments
            if is_dynamic_import_callable(value)
        } - dynamic_import_aliases
        if not added:
            break
        dynamic_import_aliases.update(added)

    if any(
        isinstance(child, ast.Call) and is_dynamic_import_callable(child.func)
        for node in (*inspected_nodes, *root_nodes)
        for child in ast.walk(node)
    ):
        raise TestCorpusGuardError(
            "dynamic Python parameter imports cannot be inventoried safely"
        )
    reader_aliases = {"open"}
    reader_aliases.update(
        local_name
        for local_name, candidates in imported_modules.items()
        if REPOSITORY_READER_IMPORTS.intersection(candidates)
    )
    while True:
        added = {
            name
            for name, value in alias_assignments
            if (isinstance(value, ast.Name) and value.id in reader_aliases)
            or (
                isinstance(value, ast.Attribute)
                and value.attr in REPOSITORY_READER_ATTRIBUTES
            )
        } - reader_aliases
        if not added:
            break
        reader_aliases.update(added)
    if any(
        isinstance(child, ast.Call)
        and (
            (isinstance(child.func, ast.Name) and child.func.id in reader_aliases)
            or (
                isinstance(child.func, ast.Attribute)
                and child.func.attr in REPOSITORY_READER_ATTRIBUTES
            )
        )
        for node in inspected_nodes
        for child in ast.walk(node)
    ):
        raise TestCorpusGuardError(
            "repository-file Python parameter data cannot be inventoried safely"
        )


def _has_dynamic_pytestmark_mutation(nodes: tuple[ast.AST, ...]) -> bool:
    aliases = {"pytestmark"}
    assignments: list[tuple[tuple[str, ...], ast.AST, bool]] = []
    for node in nodes:
        if isinstance(node, ast.Assign):
            assignments.append(
                (
                    tuple(
                        name
                        for target in node.targets
                        for name in _binding_target_names(target)
                    ),
                    node.value,
                    len(node.targets) > 1,
                )
            )
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            assignments.append((_binding_target_names(node.target), node.value, False))
    while True:
        added = {
            name
            for names, value, shares_value in assignments
            if _root_name(value) in aliases
            or (shares_value and any(alias in aliases for alias in names))
            for name in names
        } - aliases
        if not added:
            break
        aliases.update(added)

    for node in nodes:
        if isinstance(node, ast.AugAssign) and _root_name(node.target) in aliases:
            return True
        if isinstance(node, ast.Delete) and any(
            _root_name(target) in aliases for target in node.targets
        ):
            return True
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            if any(
                _root_name(target) in aliases and not isinstance(target, ast.Name)
                for target in targets
            ):
                return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and _root_name(node.func) in aliases
        ):
            return True
    return False


def _python_star_import_modules(
    tree: ast.Module,
    *,
    relative_package: str,
) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or not any(
            imported.name == "*" for imported in node.names
        ):
            continue
        if node.level:
            package_parts = relative_package.split(".")
            parent_count = node.level - 1
            if parent_count >= len(package_parts):
                continue
            prefix = ".".join(package_parts[: len(package_parts) - parent_count])
            module = f"{prefix}.{node.module}" if node.module else prefix
        elif node.module is not None:
            module = node.module
        else:
            continue
        modules.append(module)
    return tuple(dict.fromkeys(modules))


def _python_lazy_export_modules(
    tree: ast.Module,
    *,
    relative_package: str,
) -> tuple[str, ...]:
    modules: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
        if "_LAZY_EXPORT_MODULES" not in {
            name for target in targets for name in _binding_target_names(target)
        }:
            continue
        if not isinstance(node.value, ast.Dict):
            raise TestCorpusGuardError(
                "lazy Python export modules cannot be inventoried safely"
            )
        for target in node.value.values:
            if not isinstance(target, ast.Constant) or not isinstance(
                target.value, str
            ):
                raise TestCorpusGuardError(
                    "lazy Python export modules cannot be inventoried safely"
                )
            module = target.value
            modules.append(
                f"{relative_package}{module}" if module.startswith(".") else module
            )
    return tuple(dict.fromkeys(modules))


def _python_module_dependency_identity(
    module: str,
    source: str,
    import_source_resolver: Callable[[str], str | None] | None,
) -> str:
    """Bind a module object to the bounded closure of its local dependencies."""

    pending = [(module, source)]
    resolved_sources: dict[str, str] = {}
    while pending:
        current_module, current_source = pending.pop()
        if current_module in resolved_sources:
            continue
        resolved_sources[current_module] = current_source
        if len(resolved_sources) > MAX_PYTHON_DEPENDENCY_MODULES:
            raise TestCorpusGuardError(
                "Python module identity dependency closure exceeds module budget"
            )
        source_text = (
            current_source.split("\n", 1)[1]
            if current_source.startswith("path=")
            else current_source
        )
        try:
            tree = ast.parse(source_text, filename=current_module)
        except SyntaxError as exc:
            raise TestCorpusGuardError(
                "imported Python module identity cannot be inventoried safely"
            ) from exc
        source_path = current_source.split("\n", 1)[0].removeprefix("path=")
        relative_package = current_module
        if not source_path.endswith("/__init__.py") and "." in current_module:
            relative_package = current_module.rsplit(".", 1)[0]
        imported_modules = _python_import_modules(
            tree,
            relative_package=relative_package,
        )
        dependency_candidates = list(imported_modules.values())
        dependency_candidates.extend(
            (candidate,)
            for candidate in (
                *_python_star_import_modules(
                    tree,
                    relative_package=relative_package,
                ),
                *_python_lazy_export_modules(
                    tree,
                    relative_package=relative_package,
                ),
            )
        )
        for candidates in dependency_candidates:
            resolved_import = next(
                (
                    (candidate, imported_source)
                    for candidate in candidates
                    if import_source_resolver is not None
                    and (imported_source := import_source_resolver(candidate)) is not None
                ),
                None,
            )
            if resolved_import is not None:
                pending.append(resolved_import)
    return "\n".join(
        f"module={resolved_module}\nmodule-source-sha256="
        f"{hashlib.sha256(resolved_source.encode('utf-8')).hexdigest()}"
        for resolved_module, resolved_source in sorted(resolved_sources.items())
    )


def _python_imported_binding_source(
    module: str,
    source: str,
    binding_name: str,
    import_source_resolver: Callable[[str], str | None] | None,
    *,
    _seen_bindings: frozenset[tuple[str, str]] = frozenset(),
) -> str:
    binding_key = (module, binding_name)
    if binding_key in _seen_bindings:
        raise TestCorpusGuardError(
            "transitive imported Python parameter data is circular"
        )
    source_text = source.split("\n", 1)[1] if source.startswith("path=") else source
    try:
        tree = ast.parse(source_text, filename=module)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "imported Python parameter data cannot be inventoried safely"
        ) from exc
    source_path = source.split("\n", 1)[0].removeprefix("path=")
    relative_package = module
    if not source_path.endswith("/__init__.py") and "." in module:
        relative_package = module.rsplit(".", 1)[0]
    module_bindings = _python_module_bindings(tree)
    imported_modules = _python_import_modules(
        tree,
        relative_package=relative_package,
    )
    direct_module_aliases = {
        imported.asname or imported.name.split(".", 1)[0]
        for node in tree.body
        if isinstance(node, ast.Import)
        for imported in node.names
    }
    star_import_modules = _python_star_import_modules(
        tree,
        relative_package=relative_package,
    )
    pending = [binding_name]
    resolved: set[str] = set()
    binding_nodes: dict[tuple[int, int], ast.AST] = {}
    imported_requirements: dict[str, set[str]] = {}
    while pending:
        name = pending.pop()
        if name in resolved:
            continue
        resolved.add(name)
        bindings = module_bindings.get(name, ())
        if not bindings:
            candidates = imported_modules.get(name)
            if candidates:
                resolved_import = next(
                    (
                        (candidate, imported_source)
                        for candidate in candidates
                        if import_source_resolver is not None
                        and (imported_source := import_source_resolver(candidate))
                        is not None
                    ),
                    None,
                )
                if resolved_import is None:
                    return (
                        f"module={module}\nbinding={binding_name}\n"
                        f"external-import={','.join(candidates)};bindings={name}"
                    )
                imported_module, imported_source = resolved_import
                return _python_imported_binding_source(
                    imported_module,
                    imported_source,
                    _binding_name_for_resolved_import(
                        candidates,
                        imported_module,
                        name,
                    ),
                    import_source_resolver,
                    _seen_bindings=frozenset((*_seen_bindings, binding_key)),
                )
            lazy_bindings = module_bindings.get("_LAZY_EXPORT_MODULES", ())
            lazy_modules: list[str] = []
            for lazy_binding in lazy_bindings:
                assignment = lazy_binding.node
                if not isinstance(assignment, (ast.Assign, ast.AnnAssign)):
                    continue
                value = assignment.value
                if not isinstance(value, ast.Dict):
                    continue
                for key, target in zip(value.keys, value.values, strict=True):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == name
                        and isinstance(target, ast.Constant)
                        and isinstance(target.value, str)
                    ):
                        if target.value.startswith("."):
                            lazy_modules.append(f"{relative_package}{target.value}")
                        else:
                            lazy_modules.append(target.value)
            lazy_matches: list[str] = []
            for lazy_module in lazy_modules:
                if import_source_resolver is None:
                    continue
                lazy_source = import_source_resolver(lazy_module)
                if lazy_source is None:
                    continue
                lazy_matches.append(
                    _python_imported_binding_source(
                        lazy_module,
                        lazy_source,
                        name,
                        import_source_resolver,
                        _seen_bindings=frozenset((*_seen_bindings, binding_key)),
                    )
                )
            if len(lazy_matches) == 1:
                return lazy_matches[0]
            if len(lazy_matches) > 1:
                raise TestCorpusGuardError(
                    "imported Python parameter binding is ambiguous"
                )
            star_matches: list[str] = []
            for star_module in star_import_modules:
                if import_source_resolver is None:
                    continue
                star_source = import_source_resolver(star_module)
                if star_source is None:
                    continue
                try:
                    star_matches.append(
                        _python_imported_binding_source(
                            star_module,
                            star_source,
                            name,
                            import_source_resolver,
                            _seen_bindings=frozenset((*_seen_bindings, binding_key)),
                        )
                    )
                except TestCorpusGuardError as exc:
                    if "binding cannot be resolved" not in str(exc):
                        raise
            if len(star_matches) == 1:
                return star_matches[0]
            if len(star_matches) > 1:
                raise TestCorpusGuardError(
                    "imported Python parameter binding is ambiguous"
                )
            raise TestCorpusGuardError(
                "imported Python parameter binding cannot be resolved safely"
            )
        for module_binding in bindings:
            node = module_binding.node
            binding_nodes[(node.lineno, node.col_offset)] = node
            for root, names in _python_import_requirements(
                node,
                imported_modules,
            ).items():
                imported_requirements.setdefault(root, set()).update(names)
            for child in ast.walk(node):
                if not isinstance(child, ast.Name) or child.id in resolved:
                    continue
                if child.id in imported_modules:
                    continue
                if child.id in module_bindings:
                    pending.append(child.id)
    serialized_parts = [
        ast.dump(node, annotate_fields=True, include_attributes=False)
        for _position, node in sorted(binding_nodes.items())
    ]
    _reject_repository_reader_calls(tuple(binding_nodes.values()), imported_modules)
    for root, names in sorted(imported_requirements.items()):
        candidates = imported_modules[root]
        if not candidates:
            raise TestCorpusGuardError(
                "relative transitive Python parameter data cannot be inventoried safely"
            )
        resolved_import = next(
            (
                (candidate, imported_source)
                for candidate in candidates
                if import_source_resolver is not None
                and (imported_source := import_source_resolver(candidate)) is not None
            ),
            None,
        )
        if resolved_import is None:
            serialized_parts.append(
                f"external-import={','.join(candidates)};bindings={','.join(sorted(names))}"
            )
            continue
        imported_module, imported_source = resolved_import
        for name in sorted(names):
            if name == root and (
                root in direct_module_aliases
                or (len(candidates) > 1 and imported_module == candidates[0])
            ):
                serialized_parts.append(
                    _python_module_dependency_identity(
                        imported_module,
                        imported_source,
                        import_source_resolver,
                    )
                )
                continue
            serialized_parts.append(
                _python_imported_binding_source(
                    imported_module,
                    imported_source,
                    _binding_name_for_resolved_import(
                        candidates,
                        imported_module,
                        name,
                    ),
                    import_source_resolver,
                    _seen_bindings=frozenset((*_seen_bindings, binding_key)),
                )
            )
    return f"module={module}\nbinding={binding_name}\n" + "\n".join(serialized_parts)


def _python_fixture_binding_exports(source: str) -> dict[str, str]:
    source_text = source.split("\n", 1)[1] if source.startswith("path=") else source
    if "fixture" not in source_text or re.search(r"\bname\s*=", source_text) is None:
        return {}
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "imported Python fixture binding cannot be inventoried safely"
        ) from exc
    fixture_aliases = _fixture_aliases(tree)
    exports: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            target = decorator.func
            if not _is_fixture_callable(target, fixture_aliases):
                continue
            name_keywords = [
                keyword for keyword in decorator.keywords if keyword.arg == "name"
            ]
            if not name_keywords:
                continue
            name_value = name_keywords[-1].value
            if not isinstance(name_value, ast.Constant) or not isinstance(
                name_value.value, str
            ):
                raise TestCorpusGuardError(
                    "imported Python fixture name cannot be inventoried safely"
                )
            exports[node.name] = name_value.value
            break
    return exports


def _binding_name_for_resolved_import(
    candidates: tuple[str, ...],
    resolved_module: str,
    referenced_name: str,
) -> str:
    if len(candidates) > 1 and resolved_module == candidates[-1]:
        return candidates[0].rsplit(".", 1)[-1]
    return referenced_name


def _python_import_requirements(
    value: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
) -> dict[str, set[str]]:
    requirements: dict[str, set[str]] = {}
    attribute_roots: set[str] = set()
    for child in ast.walk(value):
        if not isinstance(child, ast.Attribute):
            continue
        root = _root_name(child)
        if root in imported_modules:
            attribute_roots.add(root)
            current = child
            while isinstance(current.value, ast.Attribute):
                current = current.value
            imported_name = current.attr
            requirements.setdefault(root, set()).add(imported_name)
    for child in ast.walk(value):
        if (
            isinstance(child, ast.Name)
            and child.id in imported_modules
            and child.id not in attribute_roots
        ):
            requirements.setdefault(child.id, set()).add(child.id)
    return requirements


def _is_unrebound_pytest_mark(
    target: ast.expr,
    imported_modules: dict[str, tuple[str, ...]],
    module_bindings: dict[str, tuple[_ModuleBinding, ...]],
    *,
    cutoff: tuple[int, int],
    shadowed_import_names: frozenset[str] = frozenset(),
) -> bool:
    if not isinstance(target, ast.Attribute):
        return False
    attributes: list[str] = []
    current: ast.expr = target
    while isinstance(current, ast.Attribute):
        attributes.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return False
    candidates = imported_modules.get(current.id, ())
    imported_from_pytest = any(
        candidate == "pytest" or candidate.startswith("pytest.")
        for candidate in candidates
    )
    rebound_before_collection = any(
        (binding.node.lineno, binding.node.col_offset) < cutoff
        and not (
            binding.applies_after_declaration
            and binding.node.lineno == getattr(target, "lineno", -1)
        )
        for binding in module_bindings.get(current.id, ())
    )
    return (
        imported_from_pytest
        and current.id not in shadowed_import_names
        and not rebound_before_collection
        and (
            "mark" in attributes
            or (current.id == "mark" and "pytest.mark" in candidates)
        )
    )


def _parameterized_ref(
    raw_ref: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module_bindings: dict[str, tuple[_ModuleBinding, ...]],
    parametrize_aliases: set[str],
    imported_modules: dict[str, tuple[str, ...]],
    import_source_resolver: Callable[[str], str | None] | None,
    fixture_override_resolver: (
        Callable[[str], tuple[tuple[str, str, str], ...]] | None
    ) = None,
    *,
    container_decorators: tuple[ast.expr, ...] = (),
    collection_lineno: int | None = None,
    shadowed_import_names: frozenset[str] = frozenset(),
) -> str:
    candidate_decorators = (*container_decorators, *node.decorator_list)

    def is_proven_pytest_mark(target: ast.expr) -> bool:
        return _is_unrebound_pytest_mark(
            target,
            imported_modules,
            module_bindings,
            cutoff=(
                getattr(target, "lineno", collection_lineno or node.lineno),
                getattr(target, "col_offset", 0),
            ),
            shadowed_import_names=shadowed_import_names,
        )

    def is_supported_decorator(decorator: ast.expr) -> bool:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        is_parametrize = (
            isinstance(target, ast.Attribute)
            and target.attr == "parametrize"
            and is_proven_pytest_mark(target)
        ) or (isinstance(target, ast.Name) and target.id in parametrize_aliases)
        if is_parametrize:
            return isinstance(decorator, ast.Call)
        if isinstance(target, ast.Name) and "parametrize" in target.id.lower():
            return isinstance(decorator, ast.Call)
        if is_proven_pytest_mark(target):
            return True
        if isinstance(target, ast.Name) and target.id in {"given", "settings"}:
            return f"hypothesis.{target.id}" in imported_modules.get(target.id, ())
        if isinstance(target, ast.Attribute) and target.attr in {"given", "settings"}:
            root = _root_name(target)
            return root is not None and "hypothesis" in imported_modules.get(root, ())
        return False

    bare_parametrize = any(
        not isinstance(decorator, ast.Call)
        and (
            (
                isinstance(decorator, ast.Attribute)
                and decorator.attr == "parametrize"
                and is_proven_pytest_mark(decorator)
            )
            or (
                isinstance(decorator, ast.Name)
                and (
                    decorator.id in parametrize_aliases
                    or "parametrize" in decorator.id.lower()
                )
            )
        )
        for decorator in candidate_decorators
    )
    if bare_parametrize:
        raise TestCorpusGuardError("Python parametrize decorator cannot be resolved")
    if any(not is_supported_decorator(item) for item in candidate_decorators):
        raise TestCorpusGuardError("Python test decorator cannot be inventoried safely")
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
    execution_disabling_decorators: list[ast.expr] = []
    xfail_decorators: list[ast.expr] = []
    xfail_can_disable_execution = False
    for decorator in candidate_decorators:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if not isinstance(target, ast.Attribute) or not is_proven_pytest_mark(target):
            continue
        if target.attr in PYTEST_EXECUTION_DISABLING_MARKS:
            execution_disabling_decorators.append(decorator)
            continue
        if target.attr != "xfail":
            continue
        xfail_decorators.append(decorator)
        if not isinstance(decorator, ast.Call):
            continue
        run_keywords = [
            keyword for keyword in decorator.keywords if keyword.arg == "run"
        ]
        has_keyword_expansion = any(
            keyword.arg is None for keyword in decorator.keywords
        )
        if has_keyword_expansion or any(
            not isinstance(keyword.value, ast.Constant)
            or not isinstance(keyword.value.value, bool)
            for keyword in run_keywords
        ):
            raise TestCorpusGuardError(
                "Python xfail run condition cannot be inventoried safely"
            )
        if run_keywords and run_keywords[-1].value.value is False:
            xfail_can_disable_execution = True
    if xfail_can_disable_execution:
        execution_disabling_decorators.extend(xfail_decorators)
    usefixtures_decorators = tuple(
        decorator
        for decorator in candidate_decorators
        if isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr == "usefixtures"
        and is_proven_pytest_mark(decorator.func)
    )
    fixture_argument_names = tuple(
        argument.arg
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
        if argument.arg not in {"self", "cls"}
    )
    fixture_argument_names += tuple(
        argument.arg
        for argument in (node.args.vararg, node.args.kwarg)
        if argument is not None
    )
    identity_decorators = (
        *decorators,
        *execution_disabling_decorators,
        *usefixtures_decorators,
    )
    if not identity_decorators and not fixture_argument_names:
        return raw_ref
    serialized_parts = [
        ast.dump(decorator, annotate_fields=True, include_attributes=False)
        for decorator in identity_decorators
    ]
    if fixture_argument_names:
        serialized_parts.append("fixture-arguments=" + ",".join(fixture_argument_names))
        positional_arguments = (*node.args.posonlyargs, *node.args.args)
        positional_default_start = len(positional_arguments) - len(node.args.defaults)
        named_defaults = [
            (argument.arg, default)
            for argument, default in zip(
                positional_arguments[positional_default_start:],
                node.args.defaults,
                strict=True,
            )
        ]
        named_defaults.extend(
            (argument.arg, default)
            for argument, default in zip(
                node.args.kwonlyargs,
                node.args.kw_defaults,
                strict=True,
            )
            if default is not None
        )
        if named_defaults:
            serialized_parts.append(
                "fixture-defaults="
                + ",".join(
                    f"{name}="
                    + ast.dump(
                        default,
                        annotate_fields=True,
                        include_attributes=False,
                    )
                    for name, default in named_defaults
                )
            )
        for fixture_name in fixture_argument_names:
            candidates = imported_modules.get(fixture_name)
            if candidates is None:
                override_matches = (
                    fixture_override_resolver(fixture_name)
                    if fixture_override_resolver is not None
                    else ()
                )
                if len(override_matches) > 1:
                    raise TestCorpusGuardError(
                        "imported Python fixture name is ambiguous"
                    )
                if override_matches:
                    module, source, binding_name = override_matches[0]
                    serialized_parts.append(
                        "fixture-import="
                        + _python_imported_binding_source(
                            module,
                            source,
                            binding_name,
                            import_source_resolver,
                        )
                    )
                continue
            resolved_import = next(
                (
                    (module, source)
                    for module in candidates
                    if import_source_resolver is not None
                    and (source := import_source_resolver(module)) is not None
                ),
                None,
            )
            if resolved_import is None:
                serialized_parts.append(
                    f"fixture-external-import={','.join(candidates)};"
                    f"binding={fixture_name}"
                )
                continue
            module, source = resolved_import
            serialized_parts.append(
                "fixture-import="
                + _python_imported_binding_source(
                    module,
                    source,
                    _binding_name_for_resolved_import(
                        candidates,
                        module,
                        fixture_name,
                    ),
                    import_source_resolver,
                )
            )
    for decorator in decorators:
        value_nodes = list(decorator.args)
        value_nodes.extend(
            keyword.value
            for keyword in decorator.keywords
            if keyword.arg in {"argnames", "argvalues", "ids"}
        )
        for value in value_nodes:
            for root, binding_names in _python_import_requirements(
                value, imported_modules
            ).items():
                candidates = imported_modules[root]
                if not candidates:
                    raise TestCorpusGuardError(
                        "relative imported Python parameter data cannot be inventoried safely"
                    )
                resolved_import = next(
                    (
                        (module, source)
                        for module in candidates
                        if import_source_resolver is not None
                        and (source := import_source_resolver(module)) is not None
                    ),
                    None,
                )
                if resolved_import is None:
                    if import_source_resolver is None:
                        raise TestCorpusGuardError(
                            "imported Python parameter data cannot be inventoried safely"
                        )
                    serialized_parts.append(
                        f"external-import={','.join(candidates)};"
                        f"bindings={','.join(sorted(binding_names))}"
                    )
                    continue
                module, source = resolved_import
                for binding_name in sorted(binding_names):
                    serialized_parts.append(
                        _python_imported_binding_source(
                            module,
                            source,
                            _binding_name_for_resolved_import(
                                candidates,
                                module,
                                binding_name,
                            ),
                            import_source_resolver,
                        )
                    )
    for decorator in xfail_decorators if xfail_can_disable_execution else ():
        if not isinstance(decorator, ast.Call):
            continue
        condition_nodes = [*decorator.args]
        condition_nodes.extend(
            keyword.value
            for keyword in decorator.keywords
            if keyword.arg == "condition"
        )
        for condition in condition_nodes:
            for root, binding_names in _python_import_requirements(
                condition, imported_modules
            ).items():
                candidates = imported_modules[root]
                resolved_import = next(
                    (
                        (module, source)
                        for module in candidates
                        if import_source_resolver is not None
                        and (source := import_source_resolver(module)) is not None
                    ),
                    None,
                )
                if resolved_import is None:
                    serialized_parts.append(
                        f"xfail-external-import={','.join(candidates)};"
                        f"bindings={','.join(sorted(binding_names))}"
                    )
                    continue
                module, source = resolved_import
                for binding_name in sorted(binding_names):
                    serialized_parts.append(
                        _python_imported_binding_source(
                            module,
                            source,
                            _binding_name_for_resolved_import(
                                candidates,
                                module,
                                binding_name,
                            ),
                            import_source_resolver,
                        )
                    )
    pending_names = {
        child.id
        for decorator in identity_decorators
        for child in ast.walk(decorator)
        if isinstance(child, ast.Name)
    }
    resolved_names: set[str] = set()
    cutoff_lineno = collection_lineno or node.lineno
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
                if binding.node.lineno >= cutoff_lineno
                and not binding.applies_after_declaration
            ),
            default=None,
        )
        for module_binding in name_bindings:
            binding = module_binding.node
            position = (binding.lineno, binding.col_offset)
            if (
                binding.lineno >= cutoff_lineno
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
    _reject_repository_reader_calls(
        tuple(binding_nodes.values()),
        imported_modules,
        root_nodes=identity_decorators,
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
        or (
            isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign))
            and any(
                name.startswith(("test", "Test"))
                for target in (
                    child.targets if isinstance(child, ast.Assign) else (child.target,)
                )
                for name in _binding_target_names(target)
            )
        )
        or (
            isinstance(child, ast.Delete)
            and any(
                name.startswith(("test", "Test"))
                for target in child.targets
                for name in _binding_target_names(target)
            )
        )
        for child in ast.walk(node)
        if child is not node
    )


def _disabled_python_declarations(body: list[ast.stmt]) -> set[str]:
    active: set[str] = set()
    active_functions: set[str] = set()
    function_aliases: dict[str, str] = {}
    unresolved_function_aliases: set[str] = set()
    disabled: set[str] = set()

    def resolved_function_name(value: ast.AST | None) -> str | None:
        if not isinstance(value, ast.Name):
            return None
        if value.id in active_functions:
            return value.id
        return function_aliases.get(value.id)

    def may_resolve_function(value: ast.AST | None) -> bool:
        return value is not None and any(
            isinstance(child, ast.Name)
            and child.id
            in {
                *active_functions,
                *function_aliases,
                *unresolved_function_aliases,
            }
            for child in ast.walk(value)
        )

    def update_function_alias(target: ast.AST, value: ast.AST | None) -> None:
        if isinstance(target, ast.Name):
            resolved = resolved_function_name(value)
            if resolved is not None:
                function_aliases[target.id] = resolved
                unresolved_function_aliases.discard(target.id)
            elif may_resolve_function(value):
                function_aliases.pop(target.id, None)
                unresolved_function_aliases.add(target.id)
            else:
                function_aliases.pop(target.id, None)
                unresolved_function_aliases.discard(target.id)
            return
        if isinstance(target, (ast.List, ast.Tuple)):
            if isinstance(value, (ast.List, ast.Tuple)) and len(target.elts) == len(
                value.elts
            ):
                for target_item, value_item in zip(
                    target.elts,
                    value.elts,
                    strict=True,
                ):
                    update_function_alias(target_item, value_item)
                return
            for name in _binding_target_names(target):
                function_aliases.pop(name, None)
                if may_resolve_function(value):
                    unresolved_function_aliases.add(name)
                else:
                    unresolved_function_aliases.discard(name)

    def function_mutation_declaration(value: ast.AST) -> str | None:
        if isinstance(value, ast.NamedExpr):
            update_function_alias(value.target, value.value)
            root = value.target.id if isinstance(value.target, ast.Name) else None
        else:
            root = _root_name(value)
        if root in unresolved_function_aliases or (
            root is None and may_resolve_function(value)
        ):
            raise TestCorpusGuardError(
                "dynamic Python function __test__ mutation cannot be inventoried safely"
            )
        return root if root in active else function_aliases.get(root or "")

    def update_test_binding(target: ast.AST, value: ast.AST) -> None:
        if isinstance(target, ast.Attribute) and target.attr == "__test__":
            declaration = function_mutation_declaration(target.value)
            if declaration is None:
                return
            if isinstance(value, ast.Constant):
                is_enabled = bool(value.value)
            elif isinstance(value, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
                is_enabled = bool(
                    value.keys if isinstance(value, ast.Dict) else value.elts
                )
            else:
                raise TestCorpusGuardError(
                    "dynamic Python function __test__ mutation cannot be "
                    "inventoried safely"
                )
            if is_enabled:
                disabled.discard(declaration)
            else:
                disabled.add(declaration)
            return
        if isinstance(target, (ast.List, ast.Tuple)):
            if not (
                isinstance(value, (ast.List, ast.Tuple))
                and len(target.elts) == len(value.elts)
            ):
                if any(
                    isinstance(child, ast.Attribute)
                    and child.attr == "__test__"
                    and _root_name(child.value)
                    in {
                        *active,
                        *function_aliases,
                        *unresolved_function_aliases,
                    }
                    for child in ast.walk(target)
                ):
                    raise TestCorpusGuardError(
                        "dynamic Python function __test__ mutation cannot be "
                        "inventoried safely"
                    )
                return
            for target_item, value_item in zip(
                target.elts,
                value.elts,
                strict=True,
            ):
                update_test_binding(target_item, value_item)

    def delete_test_binding(target: ast.AST) -> None:
        if isinstance(target, ast.Attribute) and target.attr == "__test__":
            declaration = function_mutation_declaration(target.value)
            if declaration is not None:
                disabled.discard(declaration)
            return
        if isinstance(target, (ast.List, ast.Tuple)):
            for target_item in target.elts:
                delete_test_binding(target_item)

    for node in body:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.name.startswith("test"):
            function_aliases.pop(node.name, None)
            unresolved_function_aliases.discard(node.name)
            function_aliases = {
                alias: declaration
                for alias, declaration in function_aliases.items()
                if declaration != node.name
            }
            active.add(node.name)
            active_functions.add(node.name)
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
        for name in rebound:
            if name in active_functions:
                active_functions.discard(name)
                function_aliases = {
                    alias: declaration
                    for alias, declaration in function_aliases.items()
                    if declaration != name
                }

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                update_test_binding(target, node.value)
                update_function_alias(target, node.value)
        elif (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Attribute)
            and node.target.attr == "__test__"
            and _root_name(node.target.value)
            in {
                *active,
                *function_aliases,
                *unresolved_function_aliases,
            }
        ):
            raise TestCorpusGuardError(
                "dynamic Python function __test__ mutation cannot be inventoried safely"
            )
        elif isinstance(node, (ast.AugAssign, ast.Delete)):
            targets = node.targets if isinstance(node, ast.Delete) else (node.target,)
            for target in targets:
                if isinstance(node, ast.Delete):
                    delete_test_binding(target)
                for name in _binding_target_names(target):
                    function_aliases.pop(name, None)
                    unresolved_function_aliases.discard(name)
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

    imported_modules = _python_import_modules(tree)
    fixture_override_index: dict[str, list[tuple[str, str, str]]] | None = None

    def fixture_override_matches(
        fixture_name: str,
    ) -> tuple[tuple[str, str, str], ...]:
        nonlocal fixture_override_index
        if fixture_override_index is None:
            fixture_override_index = {}
            export_cache: dict[str, dict[str, str]] = {}
            if import_source_resolver is not None:
                for imported_name, imported_candidates in imported_modules.items():
                    for module in imported_candidates:
                        source = import_source_resolver(module)
                        if source is None:
                            continue
                        exports = export_cache.get(module)
                        if exports is None:
                            exports = _python_fixture_binding_exports(source)
                            export_cache[module] = exports
                        binding_name = _binding_name_for_resolved_import(
                            imported_candidates,
                            module,
                            imported_name,
                        )
                        exported_name = exports.get(binding_name)
                        if exported_name is not None:
                            fixture_override_index.setdefault(exported_name, []).append(
                                (module, source, binding_name)
                            )
                        break
        return tuple(fixture_override_index.get(fixture_name, ()))

    if _has_pytest_collection_class_mutation(tree, imported_modules):
        raise TestCorpusGuardError(
            "pytest collection class mutation cannot be inventoried safely"
        )
    if any(
        isinstance(node, ast.ImportFrom)
        and any(imported.name == "*" for imported in node.names)
        for node in ast.walk(tree)
    ):
        raise TestCorpusGuardError(
            "wildcard Python imports cannot be inventoried safely"
        )

    imported_test_class_candidates: list[tuple[str, tuple[str, ...]]] = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        for imported in node.names:
            local = imported.asname or imported.name
            if local.startswith("test"):
                raise TestCorpusGuardError(
                    "imported Python tests cannot be inventoried safely"
                )
            if not local.startswith("Test"):
                continue
            candidates = imported_modules.get(local, ())
            if import_source_resolver is None:
                raise TestCorpusGuardError(
                    "imported Python tests cannot be inventoried safely"
                )
            imported_test_class_candidates.append((local, candidates))

    if _has_module_level_pytest_collection_abort(tree, imported_modules):
        raise TestCorpusGuardError(
            "module-level pytest collection abort cannot be inventoried safely"
        )
    if _has_module_level_unittest_collection_abort(tree, imported_modules):
        raise TestCorpusGuardError(
            "module-level unittest collection abort cannot be inventoried safely"
        )

    dynamic_code_names = {"__import__", "compile", "eval", "exec"}
    dynamic_code_aliases = {
        *dynamic_code_names,
        *(
            local
            for local, candidates in imported_modules.items()
            if any(
                candidate in {f"builtins.{name}" for name in dynamic_code_names}
                for candidate in candidates
            )
        ),
    }
    changed = True
    while changed:
        changed = False
        for node in _module_execution_nodes(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            value_name = ""
            if (
                isinstance(node.value, ast.Name)
                and node.value.id in dynamic_code_aliases
            ):
                value_name = node.value.id
            elif isinstance(node.value, ast.Attribute):
                root = _root_name(node.value)
                if (
                    node.value.attr in dynamic_code_names
                    and root is not None
                    and (
                        root == "builtins"
                        or "builtins" in imported_modules.get(root, ())
                    )
                ):
                    value_name = node.value.attr
            if not value_name:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                for name in _binding_target_names(target):
                    if name not in dynamic_code_aliases:
                        dynamic_code_aliases.add(name)
                        changed = True
    if any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id in dynamic_code_aliases)
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in dynamic_code_names
                and (root := _root_name(node.func)) is not None
                and (root == "builtins" or "builtins" in imported_modules.get(root, ()))
            )
        )
        for node in _module_execution_nodes(tree)
    ):
        raise TestCorpusGuardError(
            "module-level dynamic Python code cannot be inventoried safely"
        )

    defined_function_names = {
        child.name
        for child in ast.walk(tree)
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
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
        if isinstance(
            module_node,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.Try,
                ast.With,
                ast.AsyncWith,
            ),
        ) and any(
            isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete))
            and any(
                isinstance(target, ast.Attribute) and target.attr == "__test__"
                for target in (
                    child.targets
                    if isinstance(child, (ast.Assign, ast.Delete))
                    else (child.target,)
                )
            )
            for child in ast.walk(module_node)
        ):
            raise TestCorpusGuardError(
                "Python __test__ mutation inside module control flow cannot be inventoried safely"
            )

    entries: list[tuple[str, str, str]] = []
    source_lines = text.splitlines(keepends=True)
    class_nodes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    if _has_dynamic_pytestmark_mutation(_module_execution_nodes(tree)) or any(
        _has_dynamic_pytestmark_mutation(_scope_execution_nodes(node.body))
        for node in class_nodes
    ):
        raise TestCorpusGuardError(
            "dynamic pytestmark mutation cannot be inventoried safely"
        )
    class_names = [node.name for node in class_nodes]
    if len(class_names) != len(set(class_names)):
        raise TestCorpusGuardError(
            "duplicate Python class bindings cannot be inventoried safely"
        )
    classes = {node.name: node for node in class_nodes}
    class_aliases = set(classes)

    def resolved_class_aliases(target: ast.AST, value: ast.AST) -> set[str]:
        if isinstance(target, ast.Name) and isinstance(value, ast.Name):
            return {target.id} if value.id in class_aliases else set()
        if (
            isinstance(target, (ast.List, ast.Tuple))
            and isinstance(value, (ast.List, ast.Tuple))
            and len(target.elts) == len(value.elts)
        ):
            return {
                alias
                for target_item, value_item in zip(target.elts, value.elts, strict=True)
                for alias in resolved_class_aliases(target_item, value_item)
            }
        return set()

    while True:
        added: set[str] = set()
        for module_node in _module_execution_nodes(tree):
            if not isinstance(module_node, (ast.Assign, ast.AnnAssign)):
                continue
            value = module_node.value
            targets = (
                module_node.targets
                if isinstance(module_node, ast.Assign)
                else (module_node.target,)
            )
            for target in targets:
                added.update(resolved_class_aliases(target, value))
        added -= class_aliases
        if not added:
            break
        class_aliases.update(added)

    def may_resolve_local_class(value: ast.AST) -> bool:
        if isinstance(value, ast.Name):
            return value.id in class_aliases
        if isinstance(value, ast.NamedExpr):
            return may_resolve_local_class(value.value)
        if isinstance(value, ast.IfExp):
            return may_resolve_local_class(value.body) or may_resolve_local_class(
                value.orelse
            )
        return False

    def may_resolve_local_test_member(value: ast.AST) -> bool:
        return (
            isinstance(value, ast.Attribute)
            and value.attr.startswith("test")
            and may_resolve_local_class(value.value)
        )

    unittest_skip_namespace_aliases: dict[str, ast.AST] = {}

    def unittest_skip_namespace_owner(value: ast.AST) -> ast.AST | None:
        if isinstance(value, ast.Name):
            return unittest_skip_namespace_aliases.get(value.id)
        if isinstance(value, ast.Attribute) and value.attr == "__dict__":
            return value.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "vars"
            and len(value.args) == 1
            and not value.keywords
        ):
            return value.args[0]
        return None

    changed = True
    while changed:
        changed = False
        for module_node in _module_execution_nodes(tree):
            if not isinstance(module_node, (ast.Assign, ast.AnnAssign)):
                continue
            owner = unittest_skip_namespace_owner(module_node.value)
            if owner is None or not (
                may_resolve_local_class(owner) or may_resolve_local_test_member(owner)
            ):
                continue
            targets = (
                module_node.targets
                if isinstance(module_node, ast.Assign)
                else (module_node.target,)
            )
            for target in targets:
                for name in _binding_target_names(target):
                    if name not in unittest_skip_namespace_aliases:
                        unittest_skip_namespace_aliases[name] = owner
                        changed = True

    def is_unittest_skip_namespace_target(target: ast.AST) -> bool:
        if not isinstance(target, ast.Subscript):
            return False
        owner = unittest_skip_namespace_owner(target.value)
        return (
            owner is not None
            and (may_resolve_local_class(owner) or may_resolve_local_test_member(owner))
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "__unittest_skip__"
        )

    for module_node in _module_execution_nodes(tree):
        if not (
            isinstance(module_node, ast.Call)
            and isinstance(module_node.func, ast.Attribute)
            and module_node.func.attr
            in {"__delitem__", "__setitem__", "clear", "pop", "setdefault", "update"}
        ):
            continue
        owner = unittest_skip_namespace_owner(module_node.func.value)
        if owner is not None and (
            may_resolve_local_class(owner) or may_resolve_local_test_member(owner)
        ):
            raise TestCorpusGuardError(
                "post-definition unittest skip mutation cannot be inventoried safely"
            )

    for module_node in _module_execution_nodes(tree):
        mutation = _mutated_attribute_call(module_node)
        if mutation is None:
            continue
        mutates_class = may_resolve_local_class(mutation[0])
        mutates_test_member = may_resolve_local_test_member(mutation[0])
        if not mutates_class and not mutates_test_member:
            continue
        attribute = mutation[1]
        if mutates_class and (attribute is None or attribute == "__test__"):
            raise TestCorpusGuardError(
                "post-definition Python class __test__ mutation cannot be "
                "inventoried safely"
            )
        if mutates_class and attribute in {"__init__", "__new__"}:
            raise TestCorpusGuardError(
                "post-definition Python class constructor mutation cannot be "
                "inventoried safely"
            )
        if mutates_class and attribute.startswith("test"):
            raise TestCorpusGuardError(
                "post-definition Python test method mutation cannot be "
                "inventoried safely"
            )
        if attribute == "__unittest_skip__":
            raise TestCorpusGuardError(
                "post-definition unittest skip mutation cannot be inventoried safely"
            )

    for module_node in _module_execution_nodes(tree):
        if isinstance(module_node, ast.Assign):
            targets = module_node.targets
        elif isinstance(module_node, (ast.AnnAssign, ast.AugAssign)):
            targets = (module_node.target,)
        elif isinstance(module_node, ast.Delete):
            targets = module_node.targets
        else:
            continue
        mutated_attributes = {
            target.attr
            for target in targets
            if isinstance(target, ast.Attribute)
            and may_resolve_local_class(target.value)
            and (
                target.attr in {"__test__", "__init__", "__new__"}
                or target.attr.startswith("test")
            )
        }
        unittest_skip_mutation = any(
            (
                isinstance(target, ast.Attribute)
                and target.attr == "__unittest_skip__"
                and (
                    may_resolve_local_class(target.value)
                    or may_resolve_local_test_member(target.value)
                )
            )
            or is_unittest_skip_namespace_target(target)
            for target in targets
        )
        if "__test__" in mutated_attributes:
            raise TestCorpusGuardError(
                "post-definition Python class __test__ mutation cannot be "
                "inventoried safely"
            )
        if mutated_attributes & {"__init__", "__new__"}:
            raise TestCorpusGuardError(
                "post-definition Python class constructor mutation cannot be "
                "inventoried safely"
            )
        if any(attribute.startswith("test") for attribute in mutated_attributes):
            raise TestCorpusGuardError(
                "post-definition Python test method mutation cannot be "
                "inventoried safely"
            )
        if unittest_skip_mutation:
            raise TestCorpusGuardError(
                "post-definition unittest skip mutation cannot be inventoried safely"
            )
    unittest_roots = {
        imported.asname or imported.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for imported in node.names
        if imported.name == "unittest"
    }

    def resolved_unittest_base_root(
        class_node: ast.ClassDef,
        base: ast.AST,
    ) -> str | None:
        if not (isinstance(base, ast.Attribute) and base.attr == "TestCase"):
            return None
        aliases = _module_name_aliases(
            tree,
            before=(class_node.lineno, class_node.col_offset),
        )
        root = _resolved_expression_root(base.value, aliases)
        return root if root in unittest_roots else None

    for module_node in _module_execution_nodes(tree):
        aliases_before = _module_name_aliases(
            tree,
            before=(
                getattr(module_node, "lineno", 0),
                getattr(module_node, "col_offset", 0),
            ),
        )
        if isinstance(module_node, ast.Assign):
            targets = module_node.targets
        elif isinstance(module_node, (ast.AnnAssign, ast.AugAssign)):
            targets = (module_node.target,)
        elif isinstance(module_node, ast.Delete):
            targets = module_node.targets
        else:
            targets = ()
        if any(
            isinstance(target, ast.Attribute)
            and target.attr == "TestCase"
            and _resolved_expression_root(target.value, aliases_before)
            in unittest_roots
            for target in targets
        ):
            raise TestCorpusGuardError(
                "dynamic unittest.TestCase attribute cannot be inventoried safely"
            )
        mutation = _mutated_attribute_call(module_node)
        if (
            mutation is not None
            and _resolved_expression_root(mutation[0], aliases_before) in unittest_roots
            and mutation[1] in {None, "TestCase"}
        ):
            raise TestCorpusGuardError(
                "dynamic unittest.TestCase attribute cannot be inventoried safely"
            )
    used_unittest_roots = {
        root
        for class_node in class_nodes
        for base in class_node.bases
        if (
            root := (
                _root_name(base)
                if isinstance(base, ast.Attribute)
                and base.attr == "TestCase"
                and _root_name(base) in unittest_roots
                else resolved_unittest_base_root(class_node, base)
            )
        )
        is not None
    }
    for module_node in _module_execution_nodes(tree):
        rebound_roots: set[str] = set()
        if isinstance(module_node, ast.Assign):
            targets = module_node.targets
        elif isinstance(module_node, (ast.AnnAssign, ast.AugAssign)):
            targets = (module_node.target,)
        elif isinstance(module_node, ast.Delete):
            targets = module_node.targets
        elif isinstance(module_node, (ast.For, ast.AsyncFor, ast.NamedExpr)):
            targets = (module_node.target,)
        elif isinstance(module_node, (ast.With, ast.AsyncWith)):
            targets = tuple(
                item.optional_vars
                for item in module_node.items
                if item.optional_vars is not None
            )
        else:
            targets = ()
        rebound_roots.update(
            name for target in targets for name in _binding_target_names(target)
        )
        if isinstance(module_node, ast.ExceptHandler) and module_node.name is not None:
            rebound_roots.add(module_node.name)
        elif isinstance(
            module_node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            rebound_roots.add(module_node.name)
        elif isinstance(module_node, ast.Import):
            rebound_roots.update(
                imported.asname or imported.name.split(".", 1)[0]
                for imported in module_node.names
                if imported.name != "unittest"
            )
        elif isinstance(module_node, ast.ImportFrom):
            rebound_roots.update(
                imported.asname or imported.name for imported in module_node.names
            )
        if rebound_roots & used_unittest_roots:
            raise TestCorpusGuardError(
                "dynamic unittest module alias cannot be inventoried safely"
            )
    unittest_test_case_names = {
        imported.asname or imported.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "unittest"
        for imported in node.names
        if imported.name == "TestCase"
    }
    unittest_test_case_aliases = set(unittest_test_case_names)
    unresolved_unittest_test_case_aliases: set[str] = set()

    def may_resolve_unittest_test_case(value: ast.AST | None) -> bool:
        if value is None:
            return False
        if any(
            (
                isinstance(child, ast.Attribute)
                and child.attr == "TestCase"
                and _root_name(child) in unittest_roots
            )
            or (
                isinstance(child, ast.Name)
                and child.id
                in {
                    *unittest_test_case_aliases,
                    *unresolved_unittest_test_case_aliases,
                }
            )
            for child in ast.walk(value)
        ):
            return True
        if not (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "getattr"
            and value.args
            and _root_name(value.args[0]) in unittest_roots
        ):
            return False
        return not (
            len(value.args) >= 2
            and isinstance(value.args[1], ast.Constant)
            and isinstance(value.args[1].value, str)
            and value.args[1].value != "TestCase"
        )

    def resolved_unittest_aliases(
        target: ast.AST,
        value: ast.AST | None,
    ) -> set[str]:
        if isinstance(target, ast.Name):
            if (
                isinstance(value, ast.Attribute)
                and value.attr == "TestCase"
                and _root_name(value) in unittest_roots
            ) or (
                isinstance(value, ast.Name)
                and value.id in unittest_test_case_aliases
                and value.id not in unresolved_unittest_test_case_aliases
            ):
                return {target.id}
            return set()
        if (
            isinstance(target, (ast.List, ast.Tuple))
            and isinstance(value, (ast.List, ast.Tuple))
            and len(target.elts) == len(value.elts)
        ):
            return {
                alias
                for target_item, value_item in zip(target.elts, value.elts, strict=True)
                for alias in resolved_unittest_aliases(target_item, value_item)
            }
        return set()

    def unresolved_unittest_aliases(
        target: ast.AST,
        value: ast.AST | None,
    ) -> set[str]:
        if isinstance(target, ast.Name):
            if resolved_unittest_aliases(target, value):
                return set()
            return (
                {target.id}
                if target.id
                in {
                    *unittest_test_case_aliases,
                    *unresolved_unittest_test_case_aliases,
                }
                or may_resolve_unittest_test_case(value)
                else set()
            )
        if (
            isinstance(target, (ast.List, ast.Tuple))
            and isinstance(value, (ast.List, ast.Tuple))
            and len(target.elts) == len(value.elts)
        ):
            return {
                alias
                for target_item, value_item in zip(target.elts, value.elts, strict=True)
                for alias in unresolved_unittest_aliases(target_item, value_item)
            }
        target_names = {
            name
            for name in _binding_target_names(target)
            if name
            in {
                *unittest_test_case_aliases,
                *unresolved_unittest_test_case_aliases,
            }
        }
        if may_resolve_unittest_test_case(value):
            target_names.update(_binding_target_names(target))
        return target_names

    while True:
        added: set[str] = set()
        unresolved_added: set[str] = set()
        for module_node in _module_execution_nodes(tree):
            if not isinstance(module_node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = (
                module_node.targets
                if isinstance(module_node, ast.Assign)
                else (module_node.target,)
            )
            for target in targets:
                added.update(resolved_unittest_aliases(target, module_node.value))
                unresolved_added.update(
                    unresolved_unittest_aliases(target, module_node.value)
                )
        added -= unittest_test_case_aliases
        unresolved_added -= unresolved_unittest_test_case_aliases
        if not added and not unresolved_added:
            break
        unittest_test_case_aliases.update(added)
        unresolved_unittest_test_case_aliases.update(unresolved_added)

    def execution_time_unittest_rebindings(module_node: ast.AST) -> set[str]:
        targets: tuple[ast.AST, ...] = ()
        values: tuple[ast.AST, ...] = ()
        direct_names: set[str] = set()
        if isinstance(module_node, (ast.For, ast.AsyncFor)):
            targets = (module_node.target,)
            values = (module_node.iter,)
        elif isinstance(module_node, (ast.With, ast.AsyncWith)):
            targets = tuple(
                item.optional_vars
                for item in module_node.items
                if item.optional_vars is not None
            )
            values = tuple(item.context_expr for item in module_node.items)
        elif isinstance(module_node, ast.NamedExpr):
            targets = (module_node.target,)
            values = (module_node.value,)
        elif isinstance(module_node, ast.ExceptHandler):
            if module_node.name is not None:
                direct_names.add(module_node.name)
        elif isinstance(
            module_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            direct_names.add(module_node.name)
        elif isinstance(module_node, ast.Import):
            direct_names.update(
                imported.asname or imported.name.split(".", 1)[0]
                for imported in module_node.names
            )
        elif isinstance(module_node, ast.ImportFrom):
            direct_names.update(
                imported.asname or imported.name for imported in module_node.names
            )
            if module_node.module == "unittest":
                direct_names.difference_update(
                    imported.asname or imported.name
                    for imported in module_node.names
                    if imported.name == "TestCase"
                )
        elif isinstance(module_node, ast.MatchAs):
            if module_node.name is not None:
                direct_names.add(module_node.name)
        elif isinstance(module_node, ast.MatchStar):
            if module_node.name is not None:
                direct_names.add(module_node.name)
        elif isinstance(module_node, ast.MatchMapping):
            if module_node.rest is not None:
                direct_names.add(module_node.rest)
        target_names = {
            name for target in targets for name in _binding_target_names(target)
        }
        candidates = direct_names | target_names
        if candidates & unittest_test_case_aliases or any(
            may_resolve_unittest_test_case(value) for value in values
        ):
            return candidates
        return set()

    def class_global_unittest_rebindings(class_node: ast.ClassDef) -> set[str]:
        execution_nodes = _scope_execution_nodes(class_node.body)
        global_names = {
            name
            for execution_node in execution_nodes
            if isinstance(execution_node, ast.Global)
            for name in execution_node.names
        }
        rebound = {
            name
            for execution_node in execution_nodes
            for name in execution_time_unittest_rebindings(execution_node)
            if name in global_names
        }
        for execution_node in execution_nodes:
            if isinstance(execution_node, ast.Assign):
                targets = execution_node.targets
                value = execution_node.value
            elif isinstance(execution_node, ast.AnnAssign):
                targets = (execution_node.target,)
                value = execution_node.value
            elif isinstance(execution_node, ast.AugAssign):
                targets = (execution_node.target,)
                value = execution_node.value
            elif isinstance(execution_node, ast.Delete):
                targets = execution_node.targets
                value = None
            else:
                continue
            namespace_targets = tuple(
                name
                for target in targets
                for name in _module_namespace_write_targets(target)
            )
            if any(name is None for name in namespace_targets):
                rebound.update(unittest_test_case_aliases)
                rebound.update(unresolved_unittest_test_case_aliases)
            else:
                rebound.update(
                    name
                    for name in namespace_targets
                    if name
                    in {
                        *unittest_test_case_aliases,
                        *unresolved_unittest_test_case_aliases,
                    }
                )
            for target in targets:
                rebound.update(
                    name
                    for name in unresolved_unittest_aliases(target, value)
                    if name in global_names
                )
        for execution_node in execution_nodes:
            if isinstance(execution_node, ast.ClassDef):
                rebound.update(class_global_unittest_rebindings(execution_node))
        return rebound

    for module_node in _module_execution_nodes(tree):
        unresolved_unittest_test_case_aliases.update(
            execution_time_unittest_rebindings(module_node)
        )
    for class_node in class_nodes:
        unresolved_unittest_test_case_aliases.update(
            class_global_unittest_rebindings(class_node)
        )
    for module_node in _module_execution_nodes(tree):
        if isinstance(module_node, ast.AugAssign):
            mutation_targets = (module_node.target,)
        elif isinstance(module_node, ast.Delete):
            mutation_targets = module_node.targets
        else:
            continue
        unresolved_unittest_test_case_aliases.update(
            name
            for target in mutation_targets
            for name in _binding_target_names(target)
            if name in unittest_test_case_aliases
        )
    for class_node in classes.values():
        if any(
            not (resolved_unittest_base_root(class_node, base) is not None)
            and not (
                isinstance(base, ast.Name)
                and base.id in unittest_test_case_aliases
                and base.id not in unresolved_unittest_test_case_aliases
            )
            and (
                (
                    isinstance(base, ast.Name)
                    and base.id in unresolved_unittest_test_case_aliases
                )
                or may_resolve_unittest_test_case(base)
            )
            for base in class_node.bases
        ):
            raise TestCorpusGuardError(
                "dynamic unittest.TestCase alias cannot be inventoried safely"
            )
    unittest_classes: set[str] = set()
    changed = True
    while changed:
        changed = False
        for class_node in classes.values():
            if class_node.name in unittest_classes:
                continue
            if any(
                (resolved_unittest_base_root(class_node, base) is not None)
                or (
                    isinstance(base, ast.Name)
                    and base.id
                    in {
                        *(
                            unittest_test_case_aliases
                            - unresolved_unittest_test_case_aliases
                        ),
                        *unittest_classes,
                    }
                )
                for base in class_node.bases
            ):
                unittest_classes.add(class_node.name)
                changed = True
    module_bindings = _python_module_bindings(tree)
    parametrize_aliases = _parametrize_aliases(tree)
    fixture_aliases = _fixture_aliases(tree)
    parameterized_fixture_factories = _parameterized_fixture_factory_aliases(
        tree,
        fixture_aliases,
    )
    autouse_fixture_declarations = _autouse_fixture_declarations(
        text,
        path,
        import_source_resolver,
    )
    autouse_fixture_identity = (
        hashlib.sha256(
            json.dumps(
                autouse_fixture_declarations,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        if autouse_fixture_declarations
        else None
    )

    def bind_autouse_fixture_identity(ref: str) -> str:
        if autouse_fixture_identity is None:
            return ref
        return f"{ref}::autouse-sha256:{autouse_fixture_identity}"

    def imported_class_has_builtin_exception_base(
        local_name: str,
        candidates: tuple[str, ...],
        seen: frozenset[tuple[str, str]] = frozenset(),
    ) -> bool:
        if import_source_resolver is None:
            return False
        resolved_sources = [
            (candidate, source)
            for candidate in candidates
            if (source := import_source_resolver(candidate)) is not None
        ]
        if len(resolved_sources) != 1:
            return False
        module, source = resolved_sources[0]
        binding_name = _binding_name_for_resolved_import(
            candidates,
            module,
            local_name,
        )
        binding_key = (module, binding_name)
        if binding_key in seen:
            return False
        source_text = source.split("\n", 1)[1] if source.startswith("path=") else source
        source_path = source.split("\n", 1)[0].removeprefix("path=")
        try:
            imported_tree = ast.parse(source_text, filename=module)
        except SyntaxError:
            return False
        relative_package = module
        if not source_path.endswith("/__init__.py") and "." in module:
            relative_package = module.rsplit(".", 1)[0]
        imported_classes = {
            node.name: node
            for node in imported_tree.body
            if isinstance(node, ast.ClassDef)
        }
        imported_bindings = _python_module_bindings(imported_tree)
        nested_imports = _python_import_modules(
            imported_tree,
            relative_package=relative_package,
        )

        def class_has_exception_base(
            class_name: str,
            visiting: frozenset[str],
        ) -> bool:
            if class_name in visiting or class_name not in imported_classes:
                return False
            class_node = imported_classes[class_name]
            next_visiting = frozenset((*visiting, class_name))
            return any(
                (
                    isinstance(base, ast.Name)
                    and base.id in BUILTIN_EXCEPTION_CLASS_NAMES
                    and base.id not in imported_bindings
                    and base.id not in nested_imports
                )
                or (
                    isinstance(base, ast.Name)
                    and class_has_exception_base(base.id, next_visiting)
                )
                or (
                    isinstance(base, ast.Name)
                    and base.id in nested_imports
                    and imported_class_has_builtin_exception_base(
                        base.id,
                        nested_imports[base.id],
                        frozenset((*seen, binding_key)),
                    )
                )
                for base in class_node.bases
            )

        return class_has_exception_base(binding_name, frozenset())

    for local_name, candidates in imported_test_class_candidates:
        if (
            import_source_resolver is not None
            and any(
                import_source_resolver(candidate) is not None
                for candidate in candidates
            )
            and not imported_class_has_builtin_exception_base(local_name, candidates)
        ):
            raise TestCorpusGuardError(
                "imported Python tests cannot be inventoried safely"
            )

    disabled = _disabled_python_declarations(tree.body)
    module_test_names = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    ]
    if len(module_test_names) != len(set(module_test_names)):
        raise TestCorpusGuardError(
            "duplicate Python test bindings cannot be inventoried safely"
        )
    for module_node in tree.body:
        if isinstance(module_node, ast.Assign):
            targets = module_node.targets
        elif isinstance(module_node, (ast.AnnAssign, ast.AugAssign)):
            targets = (module_node.target,)
        elif isinstance(module_node, ast.Delete):
            targets = module_node.targets
        else:
            continue
        if "__test__" in {
            name for target in targets for name in _binding_target_names(target)
        }:
            raise TestCorpusGuardError(
                "module-level Python __test__ binding cannot be inventoried safely"
            )
    module_pytestmark_decorators: list[ast.expr] = []
    for module_node in tree.body:
        if not isinstance(module_node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = (
            module_node.targets
            if isinstance(module_node, ast.Assign)
            else (module_node.target,)
        )
        if "pytestmark" not in {
            name for target in targets for name in _binding_target_names(target)
        }:
            continue
        value = module_node.value
        if value is None:
            continue
        pytestmark_values = (
            tuple(value.elts) if isinstance(value, (ast.List, ast.Tuple)) else (value,)
        )
        module_pytestmark_decorators.extend(pytestmark_values)
        if any(
            isinstance(child, ast.Call)
            and _is_parametrize_callable(child.func, parametrize_aliases)
            for item in pytestmark_values
            for child in ast.walk(item)
        ):
            raise TestCorpusGuardError(
                "module-level pytestmark parametrization cannot be inventoried safely"
            )
    if any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            (
                isinstance(decorator, ast.Call)
                and _is_fixture_callable(decorator.func, fixture_aliases)
                and any(keyword.arg == "params" for keyword in decorator.keywords)
            )
            or (
                isinstance(decorator, ast.Name)
                and decorator.id in parameterized_fixture_factories
            )
            for decorator in node.decorator_list
        )
        for node in ast.walk(tree)
    ) or (
        _post_definition_parameterized_fixture_targets(
            tree,
            fixture_aliases,
            parameterized_fixture_factories,
        )
        & defined_function_names
    ):
        raise TestCorpusGuardError(
            "parameterized Python fixtures cannot be inventoried safely"
        )
    declared_test_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    }
    declared_test_class_names = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test")
    }
    collected_binding_names = declared_test_names | {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and (node.name.startswith("Test") or node.name in unittest_classes)
    }

    for module_node in _module_execution_nodes(tree):
        mutation = _mutated_attribute_call(module_node)
        if mutation is None:
            continue
        if _is_current_module_object(mutation[0], imported_modules):
            if mutation[1] is None or mutation[1] in collected_binding_names:
                raise TestCorpusGuardError(
                    "indirect Python test-name rebinding cannot be inventoried safely"
                )
            continue
        aliases = _module_name_aliases(
            tree,
            before=(module_node.lineno, module_node.col_offset),
        )
        target_root = _resolved_expression_root(mutation[0], aliases)
        if target_root not in collected_binding_names:
            continue
        if mutation[1] is None or mutation[1] == "__test__":
            raise TestCorpusGuardError(
                "dynamic Python function __test__ mutation cannot be inventoried safely"
            )

    if _has_module_namespace_mutation(tree):
        raise TestCorpusGuardError(
            "indirect Python test-name rebinding cannot be inventoried safely"
        )

    if _post_definition_parametrize_targets(tree, parametrize_aliases) & (
        declared_test_names | declared_test_class_names
    ):
        raise TestCorpusGuardError(
            "post-definition Python parametrization cannot be inventoried safely"
        )

    for module_node in _module_execution_nodes(tree):
        if isinstance(module_node, ast.Assign):
            targets = module_node.targets
        elif isinstance(module_node, (ast.AnnAssign, ast.AugAssign)):
            targets = (module_node.target,)
        elif isinstance(module_node, ast.Delete):
            targets = module_node.targets
        else:
            continue
        namespace_targets = tuple(
            name
            for target in targets
            for name in _module_namespace_write_targets(
                target,
                accessors=MODULE_NAMESPACE_ACCESSORS,
            )
        )
        current_module_targets = tuple(
            name
            for target in targets
            for name in _current_module_write_targets(target, imported_modules)
        )
        if any(
            name is None
            or name in collected_binding_names
            or name.startswith("test")
            or name.startswith("Test")
            for name in (*namespace_targets, *current_module_targets)
        ):
            raise TestCorpusGuardError(
                "indirect Python test-name rebinding cannot be inventoried safely"
            )

    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in GLOBALS_NAMESPACE_MUTATOR_METHODS
        and _is_current_module_namespace(node.func.value, imported_modules)
        for node in _module_execution_nodes(tree)
    ):
        raise TestCorpusGuardError(
            "indirect Python test-name rebinding cannot be inventoried safely"
        )

    for module_node in tree.body:
        if not isinstance(module_node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        targets = (
            module_node.targets
            if isinstance(module_node, ast.Assign)
            else (module_node.target,)
        )
        assigned_names = {
            name for target in targets for name in _binding_target_names(target)
        }
        value = module_node.value
        if any(name.startswith("Test") for name in assigned_names) and not (
            isinstance(module_node, (ast.Assign, ast.AnnAssign))
            and _is_statically_noncallable_python_value(value)
        ):
            raise TestCorpusGuardError(
                "callable Python test-class assignment cannot be inventoried safely"
            )
        if any(
            name.startswith("test") and name not in declared_test_names
            for name in assigned_names
        ) and not (
            isinstance(module_node, (ast.Assign, ast.AnnAssign))
            and _is_statically_noncallable_python_value(value)
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
        local_bases = [
            base
            for base in class_node.bases
            if isinstance(base, ast.Name) and base.id in classes
        ]
        if len(local_bases) > 1:
            raise TestCorpusGuardError(
                "multiple Python test class inheritance cannot be inventoried safely"
            )
        for base in local_bases:
            methods.update(collected_methods(classes[base.id], next_visiting))
        disabled_methods = _disabled_python_declarations(class_node.body)
        for child in class_node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child.name.startswith("test") and child.name not in disabled_methods:
                    methods[child.name] = child
                else:
                    methods.pop(child.name, None)
                continue
            if _has_nested_python_tests(child):
                raise TestCorpusGuardError(
                    "Python tests inside class control flow cannot be inventoried safely"
                )
            rebound: set[str] = set()
            if isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = (
                    child.targets if isinstance(child, ast.Assign) else (child.target,)
                )
                for target in targets:
                    rebound.update(_binding_target_names(target))
                if any(name.startswith("test") for name in rebound) and not (
                    isinstance(child, (ast.Assign, ast.AnnAssign))
                    and _is_statically_noncallable_python_value(child.value)
                ):
                    raise TestCorpusGuardError(
                        "callable Python class test-name assignment cannot be inventoried safely"
                    )
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
            (
                isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name in {"__init__", "__new__"}
            )
            or (
                isinstance(child, (ast.Assign, ast.AnnAssign))
                and any(
                    name in {"__init__", "__new__"}
                    for target in (
                        child.targets
                        if isinstance(child, ast.Assign)
                        else (child.target,)
                    )
                    for name in _binding_target_names(target)
                )
            )
            for child in class_node.body
        ):
            return True
        for decorator in class_node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            is_dataclass = (
                isinstance(target, ast.Name)
                and "dataclasses.dataclass" in imported_modules.get(target.id, ())
            ) or (
                isinstance(target, ast.Attribute)
                and target.attr == "dataclass"
                and "dataclasses" in imported_modules.get(_root_name(target), ())
            )
            if not is_dataclass:
                continue
            init_keyword = (
                next(
                    (
                        keyword.value
                        for keyword in decorator.keywords
                        if keyword.arg == "init"
                    ),
                    None,
                )
                if isinstance(decorator, ast.Call)
                else None
            )
            if not (
                isinstance(init_keyword, ast.Constant) and init_keyword.value is False
            ):
                return True
        next_visiting = {*visiting, class_node.name}
        return any(
            has_constructor(classes[base.id], next_visiting)
            for base in class_node.bases
            if isinstance(base, ast.Name) and base.id in classes
        )

    def has_builtin_exception_base(
        class_node: ast.ClassDef,
        visiting: set[str],
    ) -> bool:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        next_visiting = {*visiting, class_node.name}
        return any(
            (
                isinstance(base, ast.Name)
                and base.id in BUILTIN_EXCEPTION_CLASS_NAMES
                and base.id not in module_bindings
                and base.id not in imported_modules
            )
            or (
                isinstance(base, ast.Name)
                and base.id in imported_modules
                and imported_class_has_builtin_exception_base(
                    base.id,
                    imported_modules[base.id],
                )
            )
            or (
                isinstance(base, ast.Name)
                and base.id in classes
                and has_builtin_exception_base(classes[base.id], next_visiting)
            )
            for base in class_node.bases
        )

    def validate_class_bases(class_node: ast.ClassDef, visiting: set[str]) -> None:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        next_visiting = {*visiting, class_node.name}
        if class_node.keywords:
            raise TestCorpusGuardError(
                "collected Python test class metaclass cannot be inventoried safely"
            )
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id == "object":
                continue
            if isinstance(base, ast.Name) and base.id in classes:
                validate_class_bases(classes[base.id], next_visiting)
                continue
            if (
                isinstance(base, ast.Name) and base.id in unittest_test_case_aliases
            ) or resolved_unittest_base_root(class_node, base) is not None:
                continue
            raise TestCorpusGuardError(
                "collected Python test class base cannot be resolved safely"
            )

    def class_test_binding(
        class_node: ast.ClassDef,
        visiting: set[str],
    ) -> bool | None:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        value: bool | None = None
        for child in class_node.body:
            if not isinstance(child, (ast.Assign, ast.AnnAssign)):
                continue
            targets = (
                child.targets if isinstance(child, ast.Assign) else (child.target,)
            )
            if "__test__" not in {
                name for target in targets for name in _binding_target_names(target)
            }:
                continue
            if not isinstance(child.value, ast.Constant) or not isinstance(
                child.value.value, bool
            ):
                raise TestCorpusGuardError(
                    "Python class __test__ binding cannot be inventoried safely"
                )
            value = child.value.value
        if value is not None:
            return value
        next_visiting = {*visiting, class_node.name}
        for base in class_node.bases:
            if not isinstance(base, ast.Name) or base.id not in classes:
                continue
            inherited = class_test_binding(classes[base.id], next_visiting)
            if inherited is not None:
                return inherited
        return None

    def class_is_disabled(class_node: ast.ClassDef) -> bool:
        return class_test_binding(class_node, set()) is False

    def class_has_unittest_skip_binding(
        class_node: ast.ClassDef,
        visiting: set[str],
    ) -> bool:
        if class_node.name in visiting:
            return False
        if any(
            "__unittest_skip__"
            in {
                name
                for target in (
                    child.targets if isinstance(child, ast.Assign) else (child.target,)
                )
                for name in _binding_target_names(target)
            }
            for child in class_node.body
            if isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        ):
            return True
        return any(
            class_has_unittest_skip_binding(
                classes[base.id],
                {*visiting, class_node.name},
            )
            for base in class_node.bases
            if isinstance(base, ast.Name) and base.id in classes
        )

    def fixture_decorated(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        return any(
            (
                isinstance(decorator, ast.Call)
                and _is_fixture_callable(decorator.func, fixture_aliases)
            )
            or _is_fixture_callable(decorator, fixture_aliases)
            for decorator in node.decorator_list
        )

    def effective_class_decorators(
        class_node: ast.ClassDef,
        visiting: set[str],
    ) -> tuple[ast.expr, ...]:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        inherited: list[ast.expr] = []
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                inherited.extend(
                    effective_class_decorators(
                        classes[base.id],
                        {*visiting, class_node.name},
                    )
                )
        for decorator in class_node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            is_parametrize = (
                isinstance(target, ast.Attribute) and target.attr == "parametrize"
            ) or (isinstance(target, ast.Name) and target.id in parametrize_aliases)
            is_static_pytest_mark = _is_unrebound_pytest_mark(
                target,
                imported_modules,
                module_bindings,
                cutoff=(class_node.lineno, 0),
            )
            if not is_parametrize and not is_static_pytest_mark:
                raise TestCorpusGuardError(
                    "Python test class decorator cannot be inventoried safely"
                )
        return (*inherited, *class_node.decorator_list)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                node.name.startswith("test")
                and node.name not in disabled
                and not fixture_decorated(node)
            ):
                raw_ref = _parameterized_ref(
                    f"{path}::{node.name}",
                    node,
                    module_bindings,
                    parametrize_aliases,
                    imported_modules,
                    import_source_resolver,
                    fixture_override_matches,
                    container_decorators=tuple(module_pytestmark_decorators),
                )
                raw_ref = bind_autouse_fixture_identity(raw_ref)
                entries.append(
                    (raw_ref, "python_test", _python_node_source(source_lines, node))
                )
            continue
        if (
            not isinstance(node, ast.ClassDef)
            or (not node.name.startswith("Test") and node.name not in unittest_classes)
            or node.name in disabled
            or class_is_disabled(node)
        ):
            continue
        if node.name in unittest_classes and class_has_unittest_skip_binding(
            node, set()
        ):
            raise TestCorpusGuardError(
                "class-body unittest skip state cannot be inventoried safely"
            )
        class_pytestmark_decorators: list[ast.expr] = []
        for child in node.body:
            if not isinstance(child, (ast.Assign, ast.AnnAssign)):
                continue
            targets = (
                child.targets if isinstance(child, ast.Assign) else (child.target,)
            )
            if "pytestmark" not in {
                name for target in targets for name in _binding_target_names(target)
            }:
                continue
            if child.value is None:
                continue
            pytestmark_values = (
                tuple(child.value.elts)
                if isinstance(child.value, (ast.List, ast.Tuple))
                else (child.value,)
            )
            class_pytestmark_decorators.extend(pytestmark_values)
            if any(
                isinstance(descendant, ast.Call)
                and _is_parametrize_callable(
                    descendant.func,
                    parametrize_aliases,
                )
                for item in pytestmark_values
                for descendant in ast.walk(item)
            ):
                raise TestCorpusGuardError(
                    "class-level pytestmark parametrization cannot be inventoried safely"
                )
        if node.keywords:
            raise TestCorpusGuardError(
                "collected Python test class metaclass cannot be inventoried safely"
            )
        if node.name not in unittest_classes and has_builtin_exception_base(
            node, set()
        ):
            continue
        validate_class_bases(node, set())
        if node.name not in unittest_classes and has_constructor(node, set()):
            continue
        class_decorators = (
            *module_pytestmark_decorators,
            *effective_class_decorators(node, set()),
            *class_pytestmark_decorators,
        )
        class_binding_names = {
            name
            for child in node.body
            if isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign))
            for target in (
                child.targets if isinstance(child, ast.Assign) else (child.target,)
            )
            for name in _binding_target_names(target)
        }
        class_shadowed_import_names = set(class_binding_names)
        for class_execution_node in _scope_execution_nodes(node.body):
            if isinstance(class_execution_node, ast.Assign):
                mutation_targets = class_execution_node.targets
            elif isinstance(class_execution_node, (ast.AnnAssign, ast.AugAssign)):
                mutation_targets = (class_execution_node.target,)
            elif isinstance(class_execution_node, ast.Delete):
                mutation_targets = class_execution_node.targets
            else:
                continue
            class_shadowed_import_names.update(
                root
                for target in mutation_targets
                if (root := _root_name(target)) is not None
            )
        for method_name, method in collected_methods(node, set()).items():
            if fixture_decorated(method):
                continue
            method_decorator_names = {
                child.id
                for decorator in method.decorator_list
                for child in ast.walk(decorator)
                if isinstance(child, ast.Name)
            }
            if class_binding_names & method_decorator_names:
                raise TestCorpusGuardError(
                    "class-body Python parameter data cannot be inventoried safely"
                )
            raw_ref = _parameterized_ref(
                f"{path}::{node.name}::{method_name}",
                method,
                module_bindings,
                parametrize_aliases,
                imported_modules,
                import_source_resolver,
                fixture_override_matches,
                container_decorators=class_decorators,
                collection_lineno=node.lineno,
                shadowed_import_names=frozenset(class_shadowed_import_names),
            )
            raw_ref = bind_autouse_fixture_identity(raw_ref)
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


def _python_module_name_for_path(path: str) -> str:
    module_path = path.removeprefix("src/")
    if module_path.endswith("/__init__.py"):
        module_path = module_path[: -len("/__init__.py")]
    elif module_path.endswith(".py"):
        module_path = module_path[:-3]
    return module_path.replace("/", ".")


def _python_package_initializer_paths(path: str) -> set[str]:
    parent = Path(path).parent
    initializers: set[str] = set()
    while parent.parts and parent.parts[0] == "tests":
        initializers.add((parent / "__init__.py").as_posix())
        parent = parent.parent
    return initializers


def _python_ancestor_initializer_paths(path: str) -> set[str]:
    parent = Path(path).parent
    initializers: set[str] = set()
    while parent.parts:
        initializers.add((parent / "__init__.py").as_posix())
        parent = parent.parent
    return initializers


def _python_dependency_paths(
    repo: Path,
    modules: set[str],
    module_cache: dict[str, tuple[set[str], set[str]]] | None = None,
    *,
    read_text: Callable[[str], str | None] | None = None,
) -> set[str]:
    """Return a bounded, conservative closure of repository Python imports."""

    pending = list(modules)
    visited_modules: set[str] = set()
    dependency_paths: set[str] = set()
    cache = module_cache if module_cache is not None else {}
    source_reader = read_text or (
        lambda candidate: (
            _read_worktree_text(repo, candidate)
            if (repo / candidate).is_file()
            else None
        )
    )
    while pending:
        module = pending.pop()
        if module in visited_modules:
            continue
        visited_modules.add(module)
        if len(visited_modules) > MAX_PYTHON_DEPENDENCY_MODULES:
            raise TestCorpusGuardError(
                "Python test dependency closure exceeds module budget"
            )
        cached = cache.get(module)
        if cached is not None:
            cached_paths, cached_imports = cached
            dependency_paths.update(cached_paths)
            pending.extend(cached_imports)
            continue
        candidate_list = _python_module_candidates(module)
        candidate_paths = set(candidate_list)
        imported_module_names: set[str] = set()
        for candidate in candidate_list:
            source = source_reader(candidate)
            if source is None:
                continue
            try:
                tree = ast.parse(source, filename=candidate)
            except SyntaxError as exc:
                raise TestCorpusGuardError(
                    f"cannot parse Python dependency inventory: {candidate}"
                ) from exc
            relative_package = _python_module_name_for_path(candidate)
            if not candidate.endswith("/__init__.py") and "." in relative_package:
                relative_package = relative_package.rsplit(".", 1)[0]
            imported_modules = _python_import_modules(
                tree,
                relative_package=relative_package,
            )
            imported_module_names.update(
                imported_module
                for candidates in imported_modules.values()
                for imported_module in candidates
            )
            imported_module_names.update(
                _python_star_import_modules(
                    tree,
                    relative_package=relative_package,
                )
            )
            imported_module_names.update(
                _python_lazy_export_modules(
                    tree,
                    relative_package=relative_package,
                )
            )
        cache[module] = (candidate_paths, imported_module_names)
        dependency_paths.update(candidate_paths)
        pending.extend(imported_module_names)
    return dependency_paths


def _pytest_runner_dependency_paths(repo: Path) -> set[str]:
    dependencies = _python_dependency_paths(
        repo,
        set(PYTEST_RUNNER_MODULES),
    )
    dependencies.update(
        initializer
        for dependency in tuple(dependencies)
        if dependency.endswith(".py")
        for initializer in _python_ancestor_initializer_paths(dependency)
    )
    return dependencies


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


def _frontend_dependency_paths(
    roots: set[str],
    read_text: Callable[[str], str | None],
) -> set[str]:
    pending = list(sorted(roots))
    visited: set[str] = set()
    dependencies: set[str] = set()
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        if len(visited) > MAX_FRONTEND_DEPENDENCY_MODULES:
            raise TestCorpusGuardError(
                "frontend collection dependency closure exceeds module budget"
            )
        source = read_text(path)
        if source is None:
            continue
        try:
            modules = (
                *frontend_relative_import_modules(source),
                *frontend_collection_setup_modules(source),
            )
        except FrontendInventoryError as exc:
            raise TestCorpusGuardError(str(exc)) from None
        for module in modules:
            candidates = _relative_frontend_import_candidates(path, module)
            dependencies.update(candidates)
            pending.extend(
                candidate
                for candidate in candidates
                if read_text(candidate) is not None
            )
    return dependencies


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
    discovered: set[str] = set()
    for root, directory_names, file_names in os.walk(repo, followlinks=False):
        root_path = Path(root)
        directory_names[:] = sorted(
            name
            for name in directory_names
            if not _is_discovery_ignored_directory(repo, root_path, name)
        )
        for file_name in sorted(file_names):
            relative = (root_path / file_name).relative_to(repo).as_posix()
            if _is_test_path(relative):
                discovered.add(relative)
    return tuple(sorted(discovered))


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


def _collection_config_section(value: str, section: str) -> str:
    match = re.search(
        rf"(?ms)^\[{re.escape(section)}\][ \t]*(?:[#;][^\r\n]*)?\r?$"
        rf".*?(?=^\[|\Z)",
        value,
    )
    return match.group(0).strip() if match is not None else ""


def _pytest11_entry_points(value: str) -> tuple[tuple[str, str], ...]:
    if not value:
        return ()
    try:
        payload = tomllib.loads(value)
    except tomllib.TOMLDecodeError as exc:
        raise TestCorpusGuardError(
            "pytest entry-point configuration cannot be inventoried safely"
        ) from exc
    project = payload.get("project", {})
    if not isinstance(project, dict):
        raise TestCorpusGuardError(
            "pytest entry-point configuration cannot be inventoried safely"
        )
    entry_points = project.get("entry-points", {})
    if not isinstance(entry_points, dict):
        raise TestCorpusGuardError(
            "pytest entry-point configuration cannot be inventoried safely"
        )
    pytest11 = entry_points.get("pytest11", {})
    if not isinstance(pytest11, dict) or not all(
        isinstance(name, str) and isinstance(module, str)
        for name, module in pytest11.items()
    ):
        raise TestCorpusGuardError(
            "pytest entry-point configuration cannot be inventoried safely"
        )
    return tuple(sorted(pytest11.items()))


def _pytest_dev_dependencies(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    try:
        payload = tomllib.loads(value)
    except tomllib.TOMLDecodeError as exc:
        raise TestCorpusGuardError(
            "pytest dependency configuration cannot be inventoried safely"
        ) from exc
    project = payload.get("project", {})
    if not isinstance(project, dict):
        raise TestCorpusGuardError(
            "pytest dependency configuration cannot be inventoried safely"
        )
    optional_dependencies = project.get("optional-dependencies", {})
    if not isinstance(optional_dependencies, dict):
        raise TestCorpusGuardError(
            "pytest dependency configuration cannot be inventoried safely"
        )
    if "dev" not in optional_dependencies:
        return ()
    dev = optional_dependencies["dev"]
    if not isinstance(dev, list) or not all(
        isinstance(dependency, str) for dependency in dev
    ):
        raise TestCorpusGuardError(
            "pytest dependency configuration cannot be inventoried safely"
        )
    return tuple(sorted(dev))


def _frontend_test_scripts(value: str) -> tuple[str, str, str]:
    if not value:
        return ("", "", "")
    try:
        payload = json.loads(value)
    except (json.JSONDecodeError, TypeError) as exc:
        raise TestCorpusGuardError(
            "frontend test script configuration cannot be inventoried safely"
        ) from exc
    if not isinstance(payload, dict):
        raise TestCorpusGuardError(
            "frontend test script configuration cannot be inventoried safely"
        )
    scripts = payload.get("scripts", {})
    if not isinstance(scripts, dict):
        raise TestCorpusGuardError(
            "frontend test script configuration cannot be inventoried safely"
        )
    lifecycle_scripts = tuple(
        scripts.get(name, "") for name in ("pretest", "test", "posttest")
    )
    if not all(isinstance(script, str) for script in lifecycle_scripts):
        raise TestCorpusGuardError(
            "frontend test script configuration cannot be inventoried safely"
        )
    return lifecycle_scripts


def _has_parameterized_fixture_declaration(source: str, path: str) -> bool:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "changed pytest fixture declarations cannot be inventoried safely"
        ) from exc
    fixture_aliases = _fixture_aliases(tree)
    factory_aliases = _parameterized_fixture_factory_aliases(tree, fixture_aliases)
    if factory_aliases:
        return True
    defined_function_names = {
        child.name
        for child in ast.walk(tree)
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    if (
        _post_definition_parameterized_fixture_targets(
            tree,
            fixture_aliases,
            factory_aliases,
        )
        & defined_function_names
    ):
        return True
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and _is_fixture_callable(decorator.func, fixture_aliases)
                and any(
                    keyword.arg in {None, "params"} for keyword in decorator.keywords
                )
            ):
                return True
    return False


def _has_fixture_declaration(source: str, path: str) -> bool:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "changed pytest fixture declarations cannot be inventoried safely"
        ) from exc
    fixture_aliases = _fixture_aliases(tree)
    factory_aliases = _fixture_factory_aliases(tree, fixture_aliases)
    functions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
            _is_fixture_callable(decorator, fixture_aliases)
            or (
                isinstance(decorator, ast.Call)
                and _is_fixture_callable(decorator.func, fixture_aliases)
            )
            or (isinstance(decorator, ast.Name) and decorator.id in factory_aliases)
            for decorator in node.decorator_list
        ):
            return True
        if not isinstance(node, ast.Call):
            continue
        factory = node.func
        is_fixture_application = (
            isinstance(factory, ast.Call)
            and _is_fixture_callable(factory.func, fixture_aliases)
        ) or (isinstance(factory, ast.Name) and factory.id in factory_aliases)
        is_direct_fixture_application = _is_fixture_callable(factory, fixture_aliases)
        if not (is_fixture_application or is_direct_fixture_application):
            continue
        name_aliases = _module_name_aliases(
            tree,
            before=(node.lineno, node.col_offset),
        )
        if any(
            root is not None and name_aliases.get(root, root) in functions
            for argument in node.args
            if (root := _root_name(argument)) is not None
        ):
            return True
    return False


def _autouse_fixture_declarations(
    source: str,
    path: str,
    import_source_resolver: Callable[[str], str | None] | None = None,
) -> tuple[str, ...]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "changed autouse pytest fixtures cannot be inventoried safely"
        ) from exc
    fixture_aliases = _fixture_aliases(tree)

    def autouse_enabled(call: ast.Call) -> bool:
        for keyword in call.keywords:
            if keyword.arg is None:
                continue
            if keyword.arg != "autouse":
                continue
            if not isinstance(keyword.value, ast.Constant) or not isinstance(
                keyword.value.value, bool
            ):
                raise TestCorpusGuardError(
                    "changed autouse pytest fixtures cannot be inventoried safely"
                )
            return keyword.value.value
        return False

    factory_aliases: set[str] = set()
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
                isinstance(value, ast.Call)
                and _is_fixture_callable(value.func, fixture_aliases)
                and autouse_enabled(value)
            ) or (isinstance(value, ast.Name) and value.id in factory_aliases)
            if not resolves:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                for name in _binding_target_names(target):
                    if name not in factory_aliases:
                        factory_aliases.add(name)
                        changed = True

    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    module = _python_module_name_for_path(path)
    source_with_path = f"path={path}\n{source}"

    def binding_source(name: str) -> str:
        return _python_imported_binding_source(
            module,
            source_with_path,
            name,
            import_source_resolver,
        )

    declarations: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and _is_fixture_callable(decorator.func, fixture_aliases)
                    and autouse_enabled(decorator)
                ) or (
                    isinstance(decorator, ast.Name) and decorator.id in factory_aliases
                ):
                    declarations.add(binding_source(node.name))
        if not isinstance(node, ast.Call):
            continue
        factory = node.func
        is_autouse_factory = (
            isinstance(factory, ast.Call)
            and _is_fixture_callable(factory.func, fixture_aliases)
            and autouse_enabled(factory)
        ) or (isinstance(factory, ast.Name) and factory.id in factory_aliases)
        if is_autouse_factory:
            declarations.add(ast.dump(node, include_attributes=False))
            for argument in node.args:
                root = _root_name(argument)
                if root in functions:
                    declarations.add(binding_source(root))
    return tuple(sorted(declarations))


def _pytest_plugin_modules(source: str, path: str) -> set[str]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "pytest plugin registration cannot be inventoried safely"
        ) from exc
    modules: set[str] = set()
    if _has_module_namespace_mutation(tree):
        raise TestCorpusGuardError(
            "pytest plugin registration cannot be inventoried safely"
        )
    for node in _module_execution_nodes(tree):
        if isinstance(node, ast.Assign):
            indirect_targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            indirect_targets = (node.target,)
        elif isinstance(node, ast.Delete):
            indirect_targets = node.targets
        else:
            indirect_targets = ()
        if any(
            target is None or target == "pytest_plugins"
            for indirect_target in indirect_targets
            for target in _module_namespace_write_targets(
                indirect_target,
                accessors=MODULE_NAMESPACE_ACCESSORS,
            )
        ):
            raise TestCorpusGuardError(
                "pytest plugin registration cannot be inventoried safely"
            )
        if isinstance(node, (ast.AugAssign, ast.Delete)) and any(
            name == "pytest_plugins"
            for target in (
                (node.target,) if isinstance(node, ast.AugAssign) else node.targets
            )
            for name in _binding_target_names(target)
        ):
            raise TestCorpusGuardError(
                "pytest plugin registration cannot be inventoried safely"
            )
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
        if "pytest_plugins" not in {
            name for target in targets for name in _binding_target_names(target)
        }:
            continue
        value = node.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            values = (value,)
        elif isinstance(value, (ast.List, ast.Tuple)):
            values = tuple(value.elts)
        else:
            raise TestCorpusGuardError(
                "pytest plugin registration cannot be inventoried safely"
            )
        for item in values:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                raise TestCorpusGuardError(
                    "pytest plugin registration cannot be inventoried safely"
                )
            modules.add(item.value)
    return modules


def _pytest_conftest_import_modules(source: str, path: str) -> set[str]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "pytest conftest imports cannot be inventoried safely"
        ) from exc
    package = _python_module_name_for_path(path).rpartition(".")[0]
    package_parts = package.split(".") if package else []
    modules: set[str] = set()
    for node in _module_execution_nodes(tree):
        if isinstance(node, ast.Import):
            modules.update(imported.name for imported in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if any(imported.name == "*" for imported in node.names):
            raise TestCorpusGuardError(
                "pytest conftest imports cannot be inventoried safely"
            )
        if node.level:
            parent_count = node.level - 1
            if parent_count >= len(package_parts):
                raise TestCorpusGuardError(
                    "pytest conftest imports cannot be inventoried safely"
                )
            prefix = ".".join(package_parts[: len(package_parts) - parent_count])
            module = f"{prefix}.{node.module}" if node.module else prefix
        else:
            module = node.module or ""
        if not module:
            raise TestCorpusGuardError(
                "pytest conftest imports cannot be inventoried safely"
            )
        modules.add(module)
    return modules


def _discover_conftest_files(repo: Path) -> tuple[str, ...]:
    discovered: list[str] = []
    for root, directory_names, file_names in os.walk(repo, followlinks=False):
        root_path = Path(root)
        directory_names[:] = sorted(
            name
            for name in directory_names
            if not _is_discovery_ignored_directory(repo, root_path, name)
        )
        if "conftest.py" not in file_names:
            continue
        relative = (root_path / "conftest.py").relative_to(repo).as_posix()
        discovered.append(relative)
        if len(discovered) > MAX_CHANGED_TEST_PATHS:
            raise TestCorpusGuardError("pytest conftest path count exceeds budget")
    return tuple(sorted(discovered))


def _yaml_indented_block(text: str, header: str, *, indent: int) -> str | None:
    lines = text.splitlines(keepends=True)
    prefix = " " * indent + header + ":"
    for index, line in enumerate(lines):
        if line.rstrip("\r\n") != prefix:
            continue
        end = index + 1
        while end < len(lines):
            candidate = lines[end]
            stripped = candidate.strip()
            if not stripped or stripped.startswith("#"):
                end += 1
                continue
            leading = len(candidate) - len(candidate.lstrip(" "))
            if leading <= indent:
                break
            end += 1
        return "".join(lines[index:end])
    return None


def _pytest_workflow_collection_boundary(text: str) -> str:
    blocks = (
        _yaml_indented_block(text, "env", indent=0),
        _yaml_indented_block(text, "defaults", indent=0),
        _yaml_indented_block(text, "pytest-shards", indent=2),
    )
    if any(block is None for block in blocks):
        return text
    return "\n".join(block for block in blocks if block is not None)


def _changed_test_paths(repo: Path, base_sha: str) -> tuple[str, ...]:
    runner_dependencies = _pytest_runner_dependency_paths(repo)
    change_roots = [
        "apps",
        PYTHON_TEST_GIT_PATHSPEC,
        *FRONTEND_SOURCE_GIT_PATHSPECS,
        *sorted(runner_dependencies),
        *sorted(PYTEST_COLLECTION_CONFIG_PATHS),
        *sorted(PYTEST_DEPENDENCY_LOCK_PATHS),
        *sorted(PYTEST_RUNNER_CONFIG_PATHS),
        *sorted(FRONTEND_COLLECTION_CONFIG_PATHS),
        *sorted(FRONTEND_TEST_SCRIPT_CONFIG_PATHS),
    ]
    commands = (
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            base_sha,
            "HEAD",
            "--",
            *change_roots,
        ],
        [
            "diff",
            "--cached",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            *change_roots,
        ],
        [
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            "--",
            *change_roots,
        ],
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            *change_roots,
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
    for path in PYTEST_RUNNER_CONFIG_PATHS & all_changed:
        current = _read_worktree_text(repo, path) if (repo / path).is_file() else ""
        prior = _base_text(repo, base_sha, path) or ""
        current_boundary = (
            _pytest_workflow_collection_boundary(current)
            if path == ".github/workflows/ci.yml"
            else current
        )
        prior_boundary = (
            _pytest_workflow_collection_boundary(prior)
            if path == ".github/workflows/ci.yml"
            else prior
        )
        if current_boundary != prior_boundary:
            raise TestCorpusGuardError(
                "changed pytest runner configuration cannot be inventoried safely"
            )
    if all_changed & runner_dependencies:
        raise TestCorpusGuardError(
            "changed pytest runner dependency cannot be inventoried safely"
        )
    if all_changed & PYTEST_DEPENDENCY_LOCK_PATHS:
        raise TestCorpusGuardError(
            "changed pytest dependency lock cannot be inventoried safely"
        )
    for path in all_changed:
        if not path.startswith("tests/") or Path(path).name != "__init__.py":
            continue
        current = _read_worktree_text(repo, path) if (repo / path).is_file() else ""
        prior = _base_text(repo, base_sha, path) or ""
        for source in (current, prior):
            try:
                tree = ast.parse(source, filename=path)
            except SyntaxError as exc:
                raise TestCorpusGuardError(
                    "changed Python package initializer cannot be inventoried safely"
                ) from exc
            imported_modules = _python_import_modules(tree)
            if _has_module_level_collection_abort(tree, imported_modules):
                raise TestCorpusGuardError(
                    "changed Python package initializer collection abort cannot be "
                    "inventoried safely"
                )
    current_frontend_config_dependencies = _frontend_dependency_paths(
        set(FRONTEND_COLLECTION_CONFIG_PATHS),
        lambda candidate: (
            _read_worktree_text(repo, candidate)
            if (repo / candidate).is_file()
            else None
        ),
    )
    if all_changed & current_frontend_config_dependencies:
        raise TestCorpusGuardError(
            "changed frontend collection configuration dependency cannot be "
            "inventoried safely"
        )
    for path in FRONTEND_COLLECTION_CONFIG_PATHS & all_changed:
        current = _read_worktree_text(repo, path) if (repo / path).is_file() else ""
        prior = _base_text(repo, base_sha, path) or ""
        if current != prior:
            raise TestCorpusGuardError(
                "changed frontend collection configuration cannot be inventoried safely"
            )
    for path in FRONTEND_TEST_SCRIPT_CONFIG_PATHS & all_changed:
        current = _read_worktree_text(repo, path) if (repo / path).is_file() else ""
        prior = _base_text(repo, base_sha, path) or ""
        if _frontend_test_scripts(current) != _frontend_test_scripts(prior):
            raise TestCorpusGuardError(
                "changed frontend test script cannot be inventoried safely"
            )
    for path in FRONTEND_TEST_DEPENDENCY_PATHS & all_changed:
        current = _read_worktree_text(repo, path) if (repo / path).is_file() else ""
        prior = _base_text(repo, base_sha, path) or ""
        if current != prior:
            raise TestCorpusGuardError(
                "changed frontend test dependency boundary cannot be inventoried safely"
            )
    for path in PYTEST_COLLECTION_CONFIG_PATHS & all_changed:
        current = _read_worktree_text(repo, path) if (repo / path).is_file() else ""
        prior = _base_text(repo, base_sha, path) or ""

        if path == "tox.ini" and current != prior:
            raise TestCorpusGuardError(
                "changed pytest collection configuration cannot be inventoried safely"
            )

        if path == "pyproject.toml" and _pytest11_entry_points(
            current
        ) != _pytest11_entry_points(prior):
            raise TestCorpusGuardError(
                "changed pytest entry-point configuration cannot be inventoried safely"
            )

        if path == "pyproject.toml" and _pytest_dev_dependencies(
            current
        ) != _pytest_dev_dependencies(prior):
            raise TestCorpusGuardError(
                "changed pytest dependency configuration cannot be inventoried safely"
            )

        section = {
            "pyproject.toml": "tool.pytest.ini_options",
            "setup.cfg": "tool:pytest",
        }.get(path, "pytest")
        if _collection_config_section(current, section) != _collection_config_section(
            prior,
            section,
        ):
            raise TestCorpusGuardError(
                "changed pytest collection configuration cannot be inventoried safely"
            )
    for path in all_changed:
        if Path(path).name != "conftest.py":
            continue
        current = _read_worktree_text(repo, path) if (repo / path).is_file() else ""
        prior = _base_text(repo, base_sha, path) or ""
        if _pytest_plugin_modules(current, path) != _pytest_plugin_modules(prior, path):
            raise TestCorpusGuardError(
                "changed pytest plugin registration cannot be inventoried safely"
            )
        if any(
            name in current or name in prior for name in PYTEST_COLLECTION_HOOK_NAMES
        ):
            raise TestCorpusGuardError(
                "changed pytest collection hooks cannot be inventoried safely"
            )
        if _has_parameterized_fixture_declaration(
            current, path
        ) or _has_parameterized_fixture_declaration(prior, path):
            raise TestCorpusGuardError(
                "changed parameterized pytest fixtures cannot be inventoried safely"
            )
        if _autouse_fixture_declarations(
            current, path
        ) != _autouse_fixture_declarations(prior, path):
            raise TestCorpusGuardError(
                "changed autouse pytest fixtures cannot be inventoried safely"
            )
        if _has_fixture_declaration(current, path) or _has_fixture_declaration(
            prior, path
        ):
            raise TestCorpusGuardError(
                "changed pytest fixtures cannot be inventoried safely"
            )
    changed_python_sources = {path for path in all_changed if path.endswith(".py")}
    if changed_python_sources:
        current_registered_plugins: set[str] = set()
        prior_registered_plugins: set[str] = set()
        conftest_paths = set(_discover_conftest_files(repo))
        conftest_paths.update(
            path for path in all_changed if Path(path).name == "conftest.py"
        )
        for conftest_path in sorted(conftest_paths):
            if (repo / conftest_path).is_file():
                current = _read_worktree_text(repo, conftest_path)
                current_registered_plugins.update(
                    _pytest_plugin_modules(current, conftest_path)
                )
                current_registered_plugins.update(
                    _pytest_conftest_import_modules(current, conftest_path)
                )
            if conftest_path in all_changed:
                prior = _base_text(repo, base_sha, conftest_path) or ""
                prior_registered_plugins.update(
                    _pytest_plugin_modules(prior, conftest_path)
                )
                prior_registered_plugins.update(
                    _pytest_conftest_import_modules(prior, conftest_path)
                )
        prior_registered_plugins.update(current_registered_plugins)
        plugin_dependency_paths = _python_dependency_paths(
            repo,
            current_registered_plugins,
        )
        if prior_registered_plugins:
            base_paths = _base_file_paths(repo, base_sha)
            plugin_dependency_paths.update(
                _python_dependency_paths(
                    repo,
                    prior_registered_plugins,
                    read_text=lambda path: (
                        _base_text(repo, base_sha, path) if path in base_paths else None
                    ),
                )
            )
        for plugin_path in sorted(changed_python_sources & plugin_dependency_paths):
            current = (
                _read_worktree_text(repo, plugin_path)
                if (repo / plugin_path).is_file()
                else ""
            )
            prior = _base_text(repo, base_sha, plugin_path) or ""
            if any(
                name in current or name in prior
                for name in PYTEST_COLLECTION_HOOK_NAMES
            ):
                raise TestCorpusGuardError(
                    "changed registered pytest collection hooks cannot be "
                    "inventoried safely"
                )
            if _has_parameterized_fixture_declaration(
                current, plugin_path
            ) or _has_parameterized_fixture_declaration(prior, plugin_path):
                raise TestCorpusGuardError(
                    "changed registered parameterized pytest fixtures cannot be "
                    "inventoried safely"
                )
            if _autouse_fixture_declarations(
                current, plugin_path
            ) != _autouse_fixture_declarations(prior, plugin_path):
                raise TestCorpusGuardError(
                    "changed registered autouse pytest fixtures cannot be "
                    "inventoried safely"
                )
            if _has_fixture_declaration(
                current, plugin_path
            ) or _has_fixture_declaration(prior, plugin_path):
                raise TestCorpusGuardError(
                    "changed registered pytest fixtures cannot be inventoried safely"
                )
            if current != prior:
                raise TestCorpusGuardError(
                    "changed registered pytest dependency cannot be inventoried safely"
                )
    changed = {path for path in all_changed if _is_test_path(path)}
    changed_frontend_sources = {
        path
        for path in all_changed
        if Path(path).suffix.removeprefix(".") in FRONTEND_TEST_EXTENSIONS
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
    if changed_python_sources:
        python_dependency_cache: dict[str, tuple[set[str], set[str]]] = {}
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
            imported_modules = {
                module
                for modules in _python_import_modules(tree).values()
                for module in modules
            }
            relative_package = _python_module_name_for_path(test_path)
            if not test_path.endswith("/__init__.py") and "." in relative_package:
                relative_package = relative_package.rsplit(".", 1)[0]
            imported_modules.update(
                _python_star_import_modules(
                    tree,
                    relative_package=relative_package,
                )
            )
            dependency_candidates = _python_dependency_paths(
                repo,
                imported_modules,
                python_dependency_cache,
            )
            dependency_candidates.update(_python_package_initializer_paths(test_path))
            if dependency_candidates & changed_python_sources:
                changed.add(test_path)
    changed_tuple = tuple(sorted(changed))
    if len(changed_tuple) > MAX_CHANGED_TEST_PATHS:
        raise TestCorpusGuardError("changed test corpus path count exceeds budget")
    for path in changed_tuple:
        _validate_test_path(path)
    return changed_tuple


def _is_pytest_ignored_directory_name(name: str) -> bool:
    return (
        name.startswith(".")
        or name in PYTEST_IGNORED_DIRECTORY_NAMES
        or name.endswith(".egg")
    )


def _is_discovery_ignored_directory(repo: Path, root: Path, name: str) -> bool:
    relative = (root / name).relative_to(repo)
    if relative.parts[:2] == ("apps", "control-center"):
        return name in FRONTEND_IGNORED_DIRECTORY_NAMES
    if relative.parts and relative.parts[0] == "tests":
        return False
    return _is_pytest_ignored_directory_name(name)


def _is_python_test_path(path: str) -> bool:
    candidate = Path(path)
    return (
        candidate.suffix == ".py"
        and candidate.name.startswith("test_")
        and candidate.parts[:1] == ("tests",)
    )


def _is_test_path(path: str) -> bool:
    candidate = Path(path)
    if _is_python_test_path(path):
        return True
    if not path.startswith("apps/control-center/"):
        return False
    vitest_suffixes = tuple(
        f".{kind}.{extension}"
        for kind in ("test", "spec")
        for extension in FRONTEND_TEST_EXTENSIONS
    )
    return candidate.name.endswith(vitest_suffixes)


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


def _base_file_paths(repo: Path, base_sha: str) -> frozenset[str]:
    result = _run_git(
        repo,
        ["ls-tree", "-r", "--name-only", "-z", base_sha],
    )
    if result.returncode != 0:
        raise TestCorpusGuardError("cannot inspect base repository paths")
    try:
        decoded = result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError("base repository paths are malformed") from exc
    paths = frozenset(path for path in decoded.split("\0") if path)
    if any(
        path.startswith("/")
        or "\\" in path
        or any(part in {"", ".", ".."} for part in Path(path).parts)
        or any(ord(character) < 32 for character in path)
        for path in paths
    ):
        raise TestCorpusGuardError("base repository paths are malformed")
    return paths


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
        raise TestCorpusDeclarationMissingError(
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
    except (TestCorpusSourceRefMissingError, TestCorpusDeclarationMissingError):
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
