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
    MODULE_INITIALIZER_BINDING,
    MODULE_INITIALIZER_INERT,
    frontend_collection_setup_modules,
    frontend_export_binding_source,
    frontend_relative_import_modules,
    frontend_runtime_identity_source,
    frontend_runtime_import_modules,
    frontend_runtime_test_posture,
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
PYTHON_APPLICATION_SOURCE_PREFIXES = (
    "scripts/dev/",
    "src/ultimate_ai_agent/",
)
PYTEST_RUNNER_CONFIG_PATHS = {
    ".github/actions/setup-toolchain/action.yml",
    ".github/workflows/ci.yml",
    "scripts/verification/ci_command_manifest.py",
    "scripts/verification/run_ci_lane.py",
    "scripts/verification/run_pytest_shards.py",
    "scripts/verify_test_corpus_guard.py",
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
        "collect_ignore_glob",
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
        "pytest_sessionfinish",
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
FRONTEND_EXACT_DEPENDENCY_EXTENSIONS = frozenset({"css", "json", "node"})
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
class _TestFileInventory:
    source: str
    declarations: tuple[TestDeclaration, ...]


@dataclass(frozen=True)
class _WorktreeInventorySnapshot:
    declarations: tuple[TestDeclaration, ...]
    files_by_path: dict[str, _TestFileInventory]
    python_import_source_resolver: Callable[[str], str | None]


@dataclass(frozen=True)
class _PythonBindingNodeAnalysis:
    serialized: str
    imported_requirements: tuple[tuple[str, tuple[str, ...]], ...]
    star_import_requirements: tuple[str, ...]
    local_dependency_names: tuple[str, ...]
    runtime_abort_posture: bool


@dataclass(frozen=True)
class _PythonBindingModuleAnalysis:
    tree: ast.Module
    relative_package: str
    module_bindings: dict[str, tuple[_ModuleBinding, ...]]
    imported_modules: dict[str, tuple[str, ...]]
    direct_module_aliases: frozenset[str]
    star_import_modules: tuple[str, ...]
    node_analyses: dict[tuple[int, int], _PythonBindingNodeAnalysis]


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
    if isinstance(node, (ast.MatchAs, ast.MatchStar)):
        names = {node.name} if node.name is not None else set()
        if isinstance(node, ast.MatchAs) and node.pattern is not None:
            names.update(_binding_target_names(node.pattern))
        return names
    if isinstance(node, ast.MatchMapping):
        names = {node.rest} if node.rest is not None else set()
        return names | {
            name for pattern in node.patterns for name in _binding_target_names(pattern)
        }
    if isinstance(node, ast.MatchSequence):
        return {
            name for pattern in node.patterns for name in _binding_target_names(pattern)
        }
    if isinstance(node, (ast.Tuple, ast.List)):
        return {name for child in node.elts for name in _binding_target_names(child)}
    return set()


def _paired_binding_values(
    target: ast.AST,
    value: ast.AST,
) -> tuple[tuple[str, ast.AST], ...]:
    """Pair statically aligned assignment targets with their bound values."""

    if isinstance(target, ast.Name):
        return ((target.id, value),)
    if not isinstance(target, (ast.Tuple, ast.List)) or not isinstance(
        value, (ast.Tuple, ast.List)
    ):
        return ()
    if len(target.elts) != len(value.elts) or any(
        isinstance(child, ast.Starred) for child in target.elts
    ):
        return ()
    return tuple(
        pair
        for child_target, child_value in zip(
            target.elts,
            value.elts,
            strict=True,
        )
        for pair in _paired_binding_values(child_target, child_value)
    )


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
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Name)
        and node.slice.id == "__name__"
    ):
        registry = node.value
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and len(node.args) in {1, 2}
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "__name__"
        and not node.keywords
    ):
        registry = node.func.value
    else:
        return False
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
    return _is_module_namespace_call(
        node,
        accessors=MODULE_NAMESPACE_ACCESSORS,
    )


def _module_namespace_accessor_aliases(
    tree: ast.Module,
    *,
    accessors: frozenset[str] = MODULE_NAMESPACE_ACCESSORS,
) -> frozenset[str]:
    """Resolve bounded module-scope aliases of namespace accessor builtins."""

    aliases = set(accessors)
    imported_modules = _python_import_modules(tree)
    aliases.update(
        local_name
        for local_name, candidates in imported_modules.items()
        if any(
            candidate in {f"builtins.{accessor}" for accessor in accessors}
            for candidate in candidates
        )
    )

    changed = True
    while changed:
        changed = False
        for node in _module_execution_nodes(tree):
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = (node.target,)
                value = node.value
            else:
                continue
            resolves_accessor = isinstance(value, ast.Name) and value.id in aliases
            if isinstance(value, ast.Attribute) and value.attr in accessors:
                root = _root_name(value)
                resolves_accessor = root is not None and "builtins" in (
                    imported_modules.get(root, ())
                )
            if not resolves_accessor:
                continue
            for target in targets:
                for name in _binding_target_names(target):
                    if name not in aliases:
                        aliases.add(name)
                        changed = True
    return frozenset(aliases)


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
    accessors = _module_namespace_accessor_aliases(
        tree,
        accessors=GLOBAL_NAMESPACE_ACCESSORS,
    )
    return any(
        _is_module_namespace_mutator_call(
            node,
            accessors=accessors,
        )
        or _is_module_namespace_alias_binding(
            node,
            accessors=accessors,
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
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    if isinstance(node, ast.NamedExpr):
        return _resolved_expression_root(node.value, aliases)
    if not isinstance(node, ast.Name):
        return None
    return aliases.get(node.id, node.id)


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
    cached_aliases = getattr(tree, "_uaa_module_name_aliases", None)
    if cached_aliases is None:
        cached_aliases = {}
        setattr(tree, "_uaa_module_name_aliases", cached_aliases)
    if before in cached_aliases:
        return dict(cached_aliases[before])
    alias_nodes = getattr(tree, "_uaa_module_alias_nodes", None)
    if alias_nodes is None:
        alias_nodes = tuple(
            node
            for node in _module_execution_nodes(tree)
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete))
        )
        setattr(tree, "_uaa_module_alias_nodes", alias_nodes)
    aliases: dict[str, str] = {}
    for node in alias_nodes:
        position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
        if position >= before:
            continue
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
    cached_aliases[before] = dict(aliases)
    return aliases


def _execution_binding_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
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
            item.optional_vars for item in node.items if item.optional_vars is not None
        )
    elif isinstance(
        node,
        (ast.MatchAs, ast.MatchMapping, ast.MatchSequence, ast.MatchStar),
    ):
        targets = (node,)
    else:
        targets = ()
    names.update(name for target in targets for name in _binding_target_names(target))
    if isinstance(node, ast.ExceptHandler) and node.name is not None:
        names.add(node.name)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names.add(node.name)
    elif isinstance(node, ast.Import):
        names.update(
            imported.asname or imported.name.split(".", 1)[0] for imported in node.names
        )
    elif isinstance(node, ast.ImportFrom):
        names.update(imported.asname or imported.name for imported in node.names)
    return names


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
        elif isinstance(
            child,
            (ast.MatchAs, ast.MatchMapping, ast.MatchSequence, ast.MatchStar),
        ):
            names.update(_binding_target_names(child))
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
        for node in _module_execution_nodes(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
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


def _post_definition_execution_mark_targets(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
) -> set[str]:
    """Return declarations mutated by post-definition pytest execution marks."""

    pytest_names = {"pytest", *_pytest_module_aliases(tree)}

    def mark_aliases_before(before: tuple[int, int]) -> set[str]:
        aliases: set[str] = set()

        def update_assignment_aliases(
            target: ast.expr,
            value: ast.expr | None,
            source_aliases: frozenset[str],
        ) -> None:
            if isinstance(target, ast.Name):
                if isinstance(value, ast.Name) and value.id in source_aliases:
                    aliases.add(target.id)
                else:
                    aliases.discard(target.id)
                return
            if (
                isinstance(target, (ast.List, ast.Tuple))
                and isinstance(value, (ast.List, ast.Tuple))
                and len(target.elts) == len(value.elts)
            ):
                for target_item, value_item in zip(target.elts, value.elts, strict=True):
                    update_assignment_aliases(target_item, value_item, source_aliases)
                return
            for name in _binding_target_names(target):
                aliases.discard(name)

        for node in tree.body:
            position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
            if position >= before:
                break
            if isinstance(node, ast.ImportFrom):
                for imported in node.names:
                    name = imported.asname or imported.name
                    if node.module == "pytest" and imported.name == "mark":
                        aliases.add(name)
                    else:
                        aliases.discard(name)
                continue
            if isinstance(node, ast.Import):
                for imported in node.names:
                    aliases.discard(imported.asname or imported.name.split(".", 1)[0])
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                aliases.discard(node.name)
                continue
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign):
                targets = (node.target,)
                value = node.value
            elif isinstance(node, (ast.AugAssign, ast.Delete)):
                targets = node.targets if isinstance(node, ast.Delete) else (node.target,)
                value = None
            else:
                continue
            source_aliases = frozenset(aliases)
            for target in targets:
                update_assignment_aliases(target, value, source_aliases)
        return aliases

    def is_execution_mark(
        node: ast.AST,
        *,
        before: tuple[int, int],
    ) -> bool:
        if not (
            isinstance(node, ast.Attribute)
            and node.attr in {*PYTEST_EXECUTION_DISABLING_MARKS, "xfail"}
        ):
            return False
        if isinstance(node.value, ast.Attribute) and node.value.attr == "mark":
            root = _root_name(node)
            return root in pytest_names or (
                root is not None and "pytest" in imported_modules.get(root, ())
            )
        if not isinstance(node.value, ast.Name):
            return False
        return node.value.id in mark_aliases_before(before)

    targets: set[str] = set()
    for child in _module_execution_nodes(tree):
        if not isinstance(child, ast.Call):
            continue
        decorator_call: ast.Call | None = None
        decorated_arguments: tuple[ast.AST, ...] = ()
        position = (child.lineno, child.col_offset)
        if is_execution_mark(child.func, before=position):
            decorator_call = child
            decorated_arguments = tuple(child.args[:1])
        elif isinstance(child.func, ast.Call) and is_execution_mark(
            child.func.func,
            before=position,
        ):
            decorator_call = child.func
            decorated_arguments = tuple(child.args)
        if decorator_call is None:
            continue
        name_aliases = _module_name_aliases(
            tree,
            before=(child.lineno, child.col_offset),
        )
        for argument in decorated_arguments:
            root = _root_name(argument)
            if root is not None:
                resolved_root = name_aliases.get(root, root)
                targets.add(
                    f"{resolved_root}.{argument.attr}"
                    if isinstance(argument, ast.Attribute)
                    and isinstance(argument.value, ast.Name)
                    else resolved_root
                )
    return targets


def _helper_mediated_test_flag_targets(tree: ast.Module) -> set[str]:
    """Return declarations passed to invoked helpers that mutate ``__test__``."""

    local_functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    def mutates_parameter(
        function: ast.FunctionDef | ast.AsyncFunctionDef,
        parameter: str,
    ) -> bool:
        def parameter_root(node: ast.AST) -> bool:
            return _root_name(node) == parameter

        def target_mutates(node: ast.AST) -> bool:
            if (
                isinstance(node, ast.Attribute)
                and node.attr == "__test__"
                and parameter_root(node.value)
            ):
                return True
            if not isinstance(node, ast.Subscript):
                return False
            if not (
                isinstance(node.value, ast.Attribute)
                and node.value.attr == "__dict__"
                and parameter_root(node.value.value)
            ):
                return False
            attribute = _static_string_expression(node.slice)
            return attribute is None or attribute == "__test__"

        for node in _scope_execution_nodes(function.body):
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
                targets = (node.target,)
            elif isinstance(node, ast.Delete):
                targets = node.targets
            else:
                targets = ()
            if any(target_mutates(target) for target in targets):
                return True
            mutation = _mutated_attribute_call(node)
            if (
                mutation is not None
                and parameter_root(mutation[0])
                and (mutation[1] is None or mutation[1] == "__test__")
            ):
                return True
        return False

    targets: set[str] = set()
    for child in _module_execution_nodes(tree):
        if (
            not isinstance(child, ast.Call)
            or not isinstance(child.func, ast.Name)
        ):
            continue
        name_aliases = _module_name_aliases(
            tree,
            before=(child.lineno, child.col_offset),
        )
        helper_name = name_aliases.get(child.func.id, child.func.id)
        if helper_name not in local_functions:
            continue
        function = local_functions[helper_name]
        parameters = [
            argument.arg
            for argument in (*function.args.posonlyargs, *function.args.args)
        ]
        supplied: dict[str, ast.AST] = {
            parameter: argument
            for parameter, argument in zip(parameters, child.args)
        }
        supplied.update(
            {
                keyword.arg: keyword.value
                for keyword in child.keywords
                if keyword.arg is not None
            }
        )
        for parameter, argument in supplied.items():
            if not mutates_parameter(function, parameter):
                continue
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


def _static_string_expression(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_string_expression(node.left)
        right = _static_string_expression(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _has_pytest_collection_hook_spec(source: str, path: str) -> bool:
    """Detect hookimpl aliases that can register collection-affecting hooks."""

    if not source:
        return False
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "changed pytest collection hooks cannot be inventoried safely"
        ) from exc
    imported_modules = _python_import_modules(tree)
    pytest_namespaces = _pytest_module_aliases(tree)
    hookimpl_aliases = {
        name
        for name, candidates in imported_modules.items()
        if "pytest.hookimpl" in candidates
    }
    changed = True
    while changed:
        changed = False
        for binding_node in _module_execution_nodes(tree):
            if not isinstance(
                binding_node,
                (ast.Assign, ast.AnnAssign, ast.NamedExpr),
            ):
                continue
            value = binding_node.value
            if value is None:
                continue
            targets = (
                binding_node.targets
                if isinstance(binding_node, ast.Assign)
                else (binding_node.target,)
            )
            for target in targets:
                for name, bound_value in _paired_binding_values(target, value):
                    is_alias = (
                        isinstance(bound_value, ast.Name)
                        and bound_value.id in hookimpl_aliases
                    ) or (
                        isinstance(bound_value, ast.Attribute)
                        and bound_value.attr == "hookimpl"
                        and _root_name(bound_value) in pytest_namespaces
                    )
                    if is_alias and name not in hookimpl_aliases:
                        hookimpl_aliases.add(name)
                        changed = True
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            target = decorator.func
            if isinstance(target, ast.Attribute) and target.attr == "hookimpl":
                root = _root_name(target)
                is_hookimpl = root in pytest_namespaces
            elif isinstance(target, ast.Name):
                is_hookimpl = target.id in hookimpl_aliases
            else:
                is_hookimpl = False
            if not is_hookimpl:
                continue
            if any(keyword.arg is None for keyword in decorator.keywords):
                return True
            specifications = [
                keyword.value
                for keyword in decorator.keywords
                if keyword.arg == "specname"
            ]
            if not specifications:
                continue
            if len(specifications) != 1:
                return True
            specification = _static_string_expression(specifications[0])
            if specification is None or specification in PYTEST_COLLECTION_HOOK_NAMES:
                return True
    return False


def _dynamic_python_import_modules(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
    *,
    relative_package: str,
    lazy_export_modules: tuple[str, ...],
) -> tuple[str, ...]:
    """Resolve bounded dynamic imports or reject their dependency posture."""

    dynamic_import_aliases = {"__import__": "builtin"}
    dynamic_import_aliases.update(
        {
            local_name: (
                "builtin" if "builtins.__import__" in candidates else "import_module"
            )
            for local_name, candidates in imported_modules.items()
            if "importlib.import_module" in candidates
            or "builtins.__import__" in candidates
        }
    )

    def dynamic_import_kind(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return dynamic_import_aliases.get(node.id)
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "import_module"
            and (root := _root_name(node)) is not None
            and "importlib" in imported_modules.get(root, ())
        ):
            return "import_module"
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "__import__"
            and (root := _root_name(node)) is not None
            and "builtins" in imported_modules.get(root, ())
        ):
            return "builtin"
        return None

    def keyword_value(call: ast.Call, name: str) -> ast.AST | None:
        matches = [keyword.value for keyword in call.keywords if keyword.arg == name]
        if any(keyword.arg is None for keyword in call.keywords) or len(matches) > 1:
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        return matches[0] if matches else None

    def resolve_relative_name(target: str, package: str) -> str:
        leading_dots = len(target) - len(target.lstrip("."))
        if leading_dots == 0:
            return target
        package_parts = package.split(".") if package else []
        parent_count = leading_dots - 1
        if parent_count >= len(package_parts):
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        prefix = ".".join(package_parts[: len(package_parts) - parent_count])
        suffix = target[leading_dots:]
        return f"{prefix}.{suffix}" if suffix else prefix

    assignments: list[tuple[str, ast.AST]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = (node.target,)
            value = node.value
        elif isinstance(node, ast.NamedExpr):
            targets = (node.target,)
            value = node.value
        else:
            continue
        assignments.extend(
            pair for target in targets for pair in _paired_binding_values(target, value)
        )
    while True:
        added = {
            name: kind
            for name, value in assignments
            if (kind := dynamic_import_kind(value)) is not None
            and name not in dynamic_import_aliases
        }
        if not added:
            break
        dynamic_import_aliases.update(added)
    lazy_getattr_calls = {
        id(node)
        for function in tree.body
        if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
        and function.name == "__getattr__"
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and dynamic_import_kind(node.func) is not None
    }
    resolved: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        kind = dynamic_import_kind(node.func)
        if kind is None:
            continue
        allowed_keywords = (
            {"name", "package"}
            if kind == "import_module"
            else {"name", "globals", "locals", "fromlist", "level"}
        )
        if any(keyword.arg not in allowed_keywords for keyword in node.keywords):
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        target_keyword = keyword_value(node, "name")
        if node.args and target_keyword is not None:
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        target_node = node.args[0] if node.args else target_keyword
        target = (
            _static_string_expression(target_node) if target_node is not None else None
        )
        if target is None:
            if id(node) in lazy_getattr_calls and lazy_export_modules:
                continue
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        if kind == "import_module":
            package_node = (
                node.args[1] if len(node.args) > 1 else keyword_value(node, "package")
            )
            if len(node.args) > 2 or (
                len(node.args) > 1 and keyword_value(node, "package") is not None
            ):
                raise TestCorpusGuardError(
                    "dynamic Python module dependencies cannot be inventoried safely"
                )
            package = (
                _static_string_expression(package_node)
                if package_node is not None
                else None
            )
            if package_node is not None and package is None:
                raise TestCorpusGuardError(
                    "dynamic Python module dependencies cannot be inventoried safely"
                )
            if target.startswith("."):
                if package is None:
                    raise TestCorpusGuardError(
                        "dynamic Python module dependencies cannot be inventoried safely"
                    )
                target = resolve_relative_name(target, package)
            resolved.append(target)
            continue
        if len(node.args) > 5:
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        for index, argument_name in ((1, "globals"), (2, "locals")):
            keyword_node = keyword_value(node, argument_name)
            if len(node.args) > index and keyword_node is not None:
                raise TestCorpusGuardError(
                    "dynamic Python module dependencies cannot be inventoried safely"
                )
            argument_node = node.args[index] if len(node.args) > index else keyword_node
            if argument_node is not None and not (
                isinstance(argument_node, ast.Constant) and argument_node.value is None
            ):
                raise TestCorpusGuardError(
                    "dynamic Python module dependencies cannot be inventoried safely"
                )
        fromlist_node = (
            node.args[3] if len(node.args) > 3 else keyword_value(node, "fromlist")
        )
        if len(node.args) > 3 and keyword_value(node, "fromlist") is not None:
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        level_node = (
            node.args[4] if len(node.args) > 4 else keyword_value(node, "level")
        )
        if len(node.args) > 4 and keyword_value(node, "level") is not None:
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        level = 0
        if level_node is not None:
            if not isinstance(level_node, ast.Constant) or not isinstance(
                level_node.value, int
            ):
                raise TestCorpusGuardError(
                    "dynamic Python module dependencies cannot be inventoried safely"
                )
            level = level_node.value
        if level < 0:
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        if level:
            target = resolve_relative_name("." * level + target, relative_package)
        resolved.append(target)
        if fromlist_node is None or (
            isinstance(fromlist_node, ast.Constant) and fromlist_node.value is None
        ):
            continue
        if not isinstance(fromlist_node, (ast.List, ast.Set, ast.Tuple)):
            raise TestCorpusGuardError(
                "dynamic Python module dependencies cannot be inventoried safely"
            )
        for item in fromlist_node.elts:
            name = _static_string_expression(item)
            if name is None:
                raise TestCorpusGuardError(
                    "dynamic Python module dependencies cannot be inventoried safely"
                )
            if name == "*":
                raise TestCorpusGuardError(
                    "dynamic Python module dependencies cannot be inventoried safely"
                )
            resolved.append(f"{target}.{name}")
    return tuple(dict.fromkeys(resolved))


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


def _module_collection_execution_nodes(tree: ast.Module) -> tuple[ast.AST, ...]:
    """Return nodes that can execute while pytest imports a test module."""

    local_functions: dict[
        str,
        list[ast.FunctionDef | ast.AsyncFunctionDef],
    ] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local_functions.setdefault(node.name, []).append(node)
    pending: list[ast.AST] = list(reversed(tree.body))
    nodes: list[ast.AST] = []
    expanded_functions: set[str] = set()
    while pending:
        node = pending.pop()
        nodes.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            pending.extend(reversed(_definition_time_nodes(node)))
            continue
        if isinstance(node, ast.ClassDef):
            pending.extend(reversed((*_definition_time_nodes(node), *node.body)))
            continue
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in local_functions
            and node.func.id not in expanded_functions
        ):
            expanded_functions.add(node.func.id)
            pending.extend(
                reversed(
                    tuple(
                        statement
                        for function in local_functions[node.func.id]
                        for statement in function.body
                    )
                )
            )
        pending.extend(reversed(tuple(ast.iter_child_nodes(node))))
    return tuple(nodes)


def _is_builtin_getattr_reference(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
    aliases: dict[str, str],
) -> bool:
    if isinstance(node, ast.Name):
        return (
            node.id == "getattr"
            or aliases.get(node.id) == "getattr"
            or "builtins.getattr" in imported_modules.get(node.id, ())
        )
    if not isinstance(node, ast.Attribute) or node.attr != "getattr":
        return False
    root = _root_name(node)
    return root == "builtins" or (
        root is not None and "builtins" in imported_modules.get(root, ())
    )


def _is_builtin_vars_reference(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
    aliases: dict[str, str],
) -> bool:
    if isinstance(node, ast.Name):
        return (
            node.id == "vars"
            or aliases.get(node.id) == "vars"
            or "builtins.vars" in imported_modules.get(node.id, ())
        )
    if not isinstance(node, ast.Attribute) or node.attr != "vars":
        return False
    root = _root_name(node)
    return root == "builtins" or (
        root is not None and "builtins" in imported_modules.get(root, ())
    )


def _is_pytest_namespace_reference(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
    aliases: dict[str, str],
) -> bool:
    if isinstance(node, ast.Name) and aliases.get(node.id) == "pytest-namespace":
        return True
    if not isinstance(node, ast.Call):
        return False
    if (
        not _is_builtin_vars_reference(node.func, imported_modules, aliases)
        or len(node.args) != 1
        or node.keywords
    ):
        return False
    root = _root_name(node.args[0])
    candidates = imported_modules.get(root, ()) if root is not None else ()
    return root == "pytest" or "pytest" in candidates


def _pytest_collection_abort_callable_name(
    node: ast.AST,
    imported_modules: dict[str, tuple[str, ...]],
    aliases: dict[str, str],
) -> str:

    indexed_name: str | None = None
    if isinstance(node, ast.Subscript) and _is_pytest_namespace_reference(
        node.value,
        imported_modules,
        aliases,
    ):
        indexed_name = _static_string_expression(node.slice)
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and _is_pytest_namespace_reference(
            node.func.value,
            imported_modules,
            aliases,
        )
        and len(node.args) in {1, 2}
        and not node.keywords
    ):
        indexed_name = _static_string_expression(node.args[0])
    if indexed_name is not None:
        return (
            indexed_name
            if indexed_name in {"exit", "importorskip", "skip", "xfail"}
            else ""
        )
    if (
        isinstance(node, ast.Subscript)
        and _is_pytest_namespace_reference(node.value, imported_modules, aliases)
    ) or (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and _is_pytest_namespace_reference(
            node.func.value,
            imported_modules,
            aliases,
        )
    ):
        raise TestCorpusGuardError(
            "dynamic pytest namespace lookup cannot be inventoried safely"
        )

    if (
        isinstance(node, ast.Call)
        and _is_builtin_getattr_reference(node.func, imported_modules, aliases)
        and len(node.args) in {2, 3}
        and not node.keywords
        and _pytest_collection_abort_callable_name(
            node.args[0], imported_modules, aliases
        )
        in {"skip", "xfail"}
    ):
        abort_name = _pytest_collection_abort_callable_name(
            node.args[0], imported_modules, aliases
        )
        if isinstance(node.args[1], ast.Constant) and node.args[1].value == "Exception":
            return f"{abort_name}-exception"
        raise TestCorpusGuardError(
            "dynamic pytest abort exception reference cannot be inventoried safely"
        )

    if isinstance(node, ast.Attribute) and node.attr == "Exception":
        abort_name = _pytest_collection_abort_callable_name(
            node.value,
            imported_modules,
            aliases,
        )
        return f"{abort_name}-exception" if abort_name in {"skip", "xfail"} else ""
    if isinstance(node, ast.Attribute) and node.attr == "__call__":
        abort_name = _pytest_collection_abort_callable_name(
            node.value,
            imported_modules,
            aliases,
        )
        return (
            abort_name
            if abort_name
            in {"skip", "skip-exception", "xfail", "xfail-exception"}
            else ""
        )
    if (
        isinstance(node, ast.Call)
        and _is_builtin_getattr_reference(node.func, imported_modules, aliases)
        and len(node.args) in {2, 3}
        and not node.keywords
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value in {"exit", "importorskip", "skip", "xfail"}
    ):
        root = _root_name(node.args[0])
        candidates = imported_modules.get(root, ()) if root is not None else ()
        return (
            str(node.args[1].value)
            if root == "pytest" or "pytest" in candidates
            else ""
        )
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
                if candidate
                in {
                    "pytest.exit",
                    "pytest.importorskip",
                    "pytest.skip",
                    "pytest.xfail",
                }
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
        for node in _module_collection_execution_nodes(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                continue
            value = node.value
            if value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                for alias, bound_value in _paired_binding_values(target, value):
                    name = (
                        "getattr"
                        if _is_builtin_getattr_reference(
                            bound_value,
                            imported_modules,
                            aliases,
                        )
                        else _pytest_collection_abort_callable_name(
                            bound_value,
                            imported_modules,
                            aliases,
                        )
                    )
                    if name not in {
                        "exit",
                        "getattr",
                        "importorskip",
                        "skip",
                        "xfail",
                    }:
                        continue
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
    if name == "exit":
        if any(isinstance(argument, ast.Starred) for argument in node.args):
            # A bounded starred tuple/list may provide a successful return code,
            # and an unresolved expansion may do the same. Bind either form to
            # the abort posture instead of allowing collection to terminate
            # successfully without changing declaration identity.
            return True
        explicit_return_codes = [
            keyword.value
            for keyword in node.keywords
            if keyword.arg == "returncode"
        ]
        if len(node.args) >= 2:
            explicit_return_codes.append(node.args[1])
        if any(
            not isinstance(value, ast.Constant) or value.value == 0
            for value in explicit_return_codes
        ):
            # A referenced or computed return code can change to zero without
            # changing the call expression. Conservatively bind the call and
            # let runtime-abort dependency identity bind its module globals.
            return True
        for keyword in node.keywords:
            if keyword.arg is not None:
                continue
            if isinstance(keyword.value, ast.Dict):
                for key, value in zip(
                    keyword.value.keys,
                    keyword.value.values,
                    strict=True,
                ):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "returncode"
                        and isinstance(value, ast.Constant)
                        and value.value == 0
                    ):
                        return True
                if all(
                    isinstance(key, ast.Constant) and isinstance(value, ast.Constant)
                    for key, value in zip(
                        keyword.value.keys,
                        keyword.value.values,
                        strict=True,
                    )
                ):
                    continue
            # An unresolved expansion could supply returncode=0. Bind it as an
            # abort posture rather than allowing a successful collection exit
            # to disappear from the declaration identity.
            return True
        return False
    return name == "skip" and (
        any(keyword.arg is None for keyword in node.keywords)
        or any(
            keyword.arg == "allow_module_level"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in node.keywords
        )
    )


def _pytest_skip_exception_aliases(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
    callable_aliases: dict[str, str],
) -> set[str]:
    aliases: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in _module_collection_execution_nodes(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if value is None:
                continue
            is_exception = (
                isinstance(value, ast.Attribute)
                and value.attr == "Exception"
                and _pytest_collection_abort_callable_name(
                    value.value,
                    imported_modules,
                    callable_aliases,
                )
                == "skip"
            ) or (isinstance(value, ast.Name) and value.id in aliases)
            if not is_exception:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                for name in _binding_target_names(target):
                    if name not in aliases:
                        aliases.add(name)
                        changed = True
    return aliases


def _has_module_level_pytest_collection_abort(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
) -> bool:
    resolved_modules = dict(imported_modules)
    for alias in _pytest_module_aliases(tree):
        resolved_modules[alias] = tuple(
            dict.fromkeys((*resolved_modules.get(alias, ()), "pytest"))
        )
    aliases = _pytest_collection_abort_aliases(tree, resolved_modules)
    exception_aliases = _pytest_skip_exception_aliases(
        tree,
        resolved_modules,
        aliases,
    )
    for node in _module_collection_execution_nodes(tree):
        if _is_pytest_collection_abort_call(node, resolved_modules, aliases):
            return True
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        raised = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        if isinstance(raised, ast.Name) and raised.id in exception_aliases:
            return True
        if _pytest_collection_abort_callable_name(
            raised,
            resolved_modules,
            aliases,
        ) in {"skip-exception", "xfail-exception"}:
            return True
        if (
            isinstance(raised, ast.Attribute)
            and raised.attr == "Exception"
            and (
                _pytest_collection_abort_callable_name(
                    raised.value, resolved_modules, aliases
                )
                == "skip"
            )
        ):
            return True
    return False


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
    namespace = (
        node.value.value if isinstance(node.value, ast.NamedExpr) else node.value
    )
    root = _root_name(namespace)
    return (
        root in namespace_aliases
        or root == "unittest"
        or (
            root is not None
            and any(
                candidate in {"unittest", "unittest.case"}
                for candidate in imported_modules.get(root, ())
            )
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
        for node in _module_collection_execution_nodes(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
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
    for node in _module_collection_execution_nodes(tree):
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


def _python_grouped_lazy_export_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    initialized = False
    for node in tree.body:
        targets = (
            node.targets
            if isinstance(node, ast.Assign)
            else (node.target,)
            if isinstance(node, ast.AnnAssign)
            else ()
        )
        binds_export_groups = "_EXPORT_GROUPS" in {
            name for target in targets for name in _binding_target_names(target)
        }
        if not binds_export_groups:
            if "_EXPORT_GROUPS" in _mutation_names(node):
                raise TestCorpusGuardError(
                    "lazy Python export modules cannot be inventoried safely"
                )
            continue
        if initialized:
            raise TestCorpusGuardError(
                "lazy Python export modules cannot be inventoried safely"
            )
        initialized = True
        if not isinstance(node.value, ast.Dict):
            raise TestCorpusGuardError(
                "lazy Python export modules cannot be inventoried safely"
            )
        for target in node.value.keys:
            if not isinstance(target, ast.Constant) or not isinstance(
                target.value, str
            ):
                raise TestCorpusGuardError(
                    "lazy Python export modules cannot be inventoried safely"
                )
            modules.append(target.value)
    if not initialized:
        return ()

    lazy_exports_are_grouped = any(
        isinstance(node, (ast.Assign, ast.AnnAssign))
        and "_LAZY_EXPORTS"
        in {
            name
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
            for name in _binding_target_names(target)
        }
        and isinstance(node.value, ast.DictComp)
        and any(
            isinstance(child, ast.Attribute)
            and child.attr == "items"
            and isinstance(child.value, ast.Name)
            and child.value.id == "_EXPORT_GROUPS"
            for child in ast.walk(node.value)
        )
        for node in tree.body
    )
    import_bindings = _python_import_modules(tree)
    bounded_cache_target_ids: set[int] = set()
    if lazy_exports_are_grouped:
        for function in tree.body:
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) or (
                function.name != "__getattr__"
            ):
                continue
            positional = (*function.args.posonlyargs, *function.args.args)
            if len(positional) != 1 or function.args.vararg or function.args.kwarg:
                continue
            requested_name = positional[0].arg
            has_bounded_lookup = any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "get"
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == "_LAZY_EXPORTS"
                and len(child.args) == 1
                and isinstance(child.args[0], ast.Name)
                and child.args[0].id == requested_name
                and not child.keywords
                for child in ast.walk(function)
            )
            if not has_bounded_lookup:
                continue
            imported_value_bindings: list[str] = []
            for child in ast.walk(function):
                if not isinstance(child, (ast.Assign, ast.AnnAssign)):
                    continue
                targets = (
                    child.targets if isinstance(child, ast.Assign) else (child.target,)
                )
                target_names = {
                    name for target in targets for name in _binding_target_names(target)
                }
                value = child.value
                if (
                    len(target_names) != 1
                    or not isinstance(value, ast.Call)
                    or not isinstance(value.func, ast.Name)
                    or value.func.id != "getattr"
                    or not value.args
                    or not isinstance(value.args[0], ast.Call)
                    or not isinstance(value.args[0].func, ast.Name)
                    or "importlib.import_module"
                    not in import_bindings.get(value.args[0].func.id, ())
                ):
                    continue
                imported_value_bindings.extend(target_names)
            if len(imported_value_bindings) != 1:
                continue
            cached_value = imported_value_bindings[0]
            if (
                sum(
                    isinstance(child, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
                    and cached_value
                    in {
                        name
                        for target in (
                            child.targets
                            if isinstance(child, ast.Assign)
                            else (child.target,)
                        )
                        for name in _binding_target_names(target)
                    }
                    for child in ast.walk(function)
                )
                != 1
            ):
                continue
            if not any(
                isinstance(child, ast.Return)
                and isinstance(child.value, ast.Name)
                and child.value.id == cached_value
                for child in ast.walk(function)
            ):
                continue
            for child in ast.walk(function):
                if not isinstance(child, (ast.Assign, ast.AnnAssign)):
                    continue
                targets = (
                    child.targets if isinstance(child, ast.Assign) else (child.target,)
                )
                if (
                    not isinstance(child.value, ast.Name)
                    or child.value.id != cached_value
                ):
                    continue
                for target in targets:
                    if (
                        isinstance(target, ast.Subscript)
                        and _is_module_namespace_call(target.value)
                        and isinstance(target.slice, ast.Name)
                        and target.slice.id == requested_name
                    ):
                        bounded_cache_target_ids.add(id(target))
    if _has_module_namespace_mutation(tree):
        raise TestCorpusGuardError(
            "lazy Python export modules cannot be inventoried safely"
        )

    namespace_accessors = _module_namespace_accessor_aliases(tree)

    def is_namespace_call(node: ast.AST) -> bool:
        return _is_module_namespace_call(
            node,
            accessors=namespace_accessors,
        )

    def grouped_export_namespace_reference(node: ast.AST) -> bool:
        while isinstance(node, ast.Subscript):
            if is_namespace_call(node.value):
                key = _static_string_expression(node.slice)
                if key == "_EXPORT_GROUPS":
                    return True
            node = node.value
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"get", "__getitem__"}
            and is_namespace_call(node.func.value)
            and node.args
            and not node.keywords
        ):
            key = _static_string_expression(node.args[0])
            return key is None or key == "_EXPORT_GROUPS"
        return False

    def dynamic_grouped_export_namespace_reference(node: ast.AST) -> bool:
        while isinstance(node, ast.Subscript):
            if is_namespace_call(node.value):
                return _static_string_expression(node.slice) is None
            node = node.value
        return False

    aliases = {"_EXPORT_GROUPS"}
    changed = True
    while changed:
        changed = False
        for node in _module_execution_nodes(tree):
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = (node.target,)
                value = node.value
            else:
                continue
            for target in targets:
                for name, bound_value in _paired_binding_values(target, value):
                    if (
                        isinstance(bound_value, ast.Name)
                        and bound_value.id in aliases
                        and name not in aliases
                    ):
                        aliases.add(name)
                        changed = True

    for node in _module_execution_nodes(tree):
        if _mutation_names(node) & aliases:
            raise TestCorpusGuardError(
                "lazy Python export modules cannot be inventoried safely"
            )
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr not in READ_ONLY_COLLECTION_METHODS
                and (
                    grouped_export_namespace_reference(child.func.value)
                    or dynamic_grouped_export_namespace_reference(child.func.value)
                )
            ):
                raise TestCorpusGuardError(
                    "lazy Python export modules cannot be inventoried safely"
                )
            if isinstance(child, ast.Assign):
                targets = child.targets
            elif isinstance(child, (ast.AnnAssign, ast.AugAssign)):
                targets = (child.target,)
            elif isinstance(child, ast.Delete):
                targets = child.targets
            else:
                continue
            if any(
                id(target) not in bounded_cache_target_ids
                and (
                    grouped_export_namespace_reference(target)
                    or dynamic_grouped_export_namespace_reference(target)
                )
                for target in targets
            ):
                raise TestCorpusGuardError(
                    "lazy Python export modules cannot be inventoried safely"
                )
    return tuple(dict.fromkeys(modules))


def _python_lazy_export_binding_modules(
    tree: ast.Module,
    *,
    relative_package: str,
    binding_name: str,
) -> tuple[str, ...]:
    """Resolve the exact static lazy-export target for one requested binding."""

    modules: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
        target_names = {
            name for target in targets for name in _binding_target_names(target)
        }
        if "_LAZY_EXPORT_MODULES" in target_names:
            if not isinstance(node.value, ast.Dict):
                raise TestCorpusGuardError(
                    "lazy Python export modules cannot be inventoried safely"
                )
            for key, target in zip(node.value.keys, node.value.values, strict=True):
                if not (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(target, ast.Constant)
                    and isinstance(target.value, str)
                ):
                    raise TestCorpusGuardError(
                        "lazy Python export modules cannot be inventoried safely"
                    )
                if key.value == binding_name:
                    modules.append(
                        f"{relative_package}{target.value}"
                        if target.value.startswith(".")
                        else target.value
                    )
        if "_EXPORT_GROUPS" not in target_names:
            continue
        if not isinstance(node.value, ast.Dict):
            raise TestCorpusGuardError(
                "lazy Python export modules cannot be inventoried safely"
            )
        for key, names in zip(node.value.keys, node.value.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                raise TestCorpusGuardError(
                    "lazy Python export modules cannot be inventoried safely"
                )
            if not isinstance(names, (ast.Set, ast.List, ast.Tuple)) or any(
                not isinstance(name, ast.Constant) or not isinstance(name.value, str)
                for name in names.elts
            ):
                raise TestCorpusGuardError(
                    "lazy Python export modules cannot be inventoried safely"
                )
            if binding_name in {name.value for name in names.elts}:
                modules.append(
                    f"{relative_package}{key.value}"
                    if key.value.startswith(".")
                    else key.value
                )
    return tuple(dict.fromkeys(modules))


def _python_parsed_module(
    module: str,
    source_text: str,
    import_source_resolver: Callable[[str], str | None] | None,
) -> ast.Module:
    cache: dict[tuple[str, str], ast.Module] | None = None
    cache_key = (module, hashlib.sha256(source_text.encode("utf-8")).hexdigest())
    if import_source_resolver is not None:
        cache = getattr(
            import_source_resolver,
            "_uaa_parsed_module_cache",
            None,
        )
        if cache is not None and cache_key in cache:
            return cache[cache_key]
    tree = ast.parse(source_text, filename=module)
    if cache is not None:
        cache[cache_key] = tree
    return tree


def _python_module_dependency_identity(
    module: str,
    source: str,
    import_source_resolver: Callable[[str], str | None] | None,
) -> str:
    """Bind a module object to the bounded closure of its local dependencies."""

    cache_key = (
        module,
        hashlib.sha256(source.encode("utf-8")).hexdigest(),
    )
    identity_cache: dict[tuple[str, str], str] | None = None
    if import_source_resolver is not None:
        identity_cache = getattr(
            import_source_resolver,
            "_uaa_module_identity_cache",
            None,
        )
        if identity_cache is not None and cache_key in identity_cache:
            return identity_cache[cache_key]
    pending = [(module, source)]
    resolved_sources: dict[str, str] = {}
    expanded_modules: set[str] = set()
    runtime_abort_posture = False
    while pending:
        current_module, current_source = pending.pop()
        if current_module in expanded_modules:
            continue
        expanded_modules.add(current_module)
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
            tree = _python_parsed_module(
                current_module,
                source_text,
                import_source_resolver,
            )
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
        runtime_abort_posture = runtime_abort_posture or any(
            _pytest_collection_abort_callable_name(
                child.func,
                imported_modules,
                {},
            )
            in {
                "importorskip",
                "skip",
                "skip-exception",
                "xfail",
                "xfail-exception",
            }
            for child in ast.walk(tree)
            if isinstance(child, ast.Call)
        )
        lazy_export_modules = _python_lazy_export_modules(
            tree,
            relative_package=relative_package,
        )
        grouped_lazy_export_modules = _python_grouped_lazy_export_modules(tree)
        dynamic_import_modules = _dynamic_python_import_modules(
            tree,
            imported_modules,
            relative_package=relative_package,
            lazy_export_modules=(
                *lazy_export_modules,
                *grouped_lazy_export_modules,
            ),
        )
        resolved_dependencies: list[tuple[str, str]] = []
        if import_source_resolver is not None:
            module_parts = current_module.split(".")
            for index in range(1, len(module_parts)):
                package_module = ".".join(module_parts[:index])
                package_source = import_source_resolver(package_module)
                if package_source is not None and package_source.split("\n", 1)[
                    0
                ].endswith("/__init__.py"):
                    pending.append((package_module, package_source))
            for grouped_module in grouped_lazy_export_modules:
                grouped_source = import_source_resolver(grouped_module)
                if grouped_source is not None:
                    pending.append((grouped_module, grouped_source))
        dependency_candidates = list(imported_modules.values())
        dependency_candidates.extend(
            (candidate,)
            for candidate in (
                *_python_star_import_modules(
                    tree,
                    relative_package=relative_package,
                ),
                *lazy_export_modules,
                *dynamic_import_modules,
            )
        )
        for candidates in dependency_candidates:
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
            if resolved_import is not None:
                resolved_dependencies.append(resolved_import)
        pending.extend(resolved_dependencies)
    identity = "\n".join(
        f"module={resolved_module}\nmodule-source-sha256="
        f"{hashlib.sha256(resolved_source.encode('utf-8')).hexdigest()}"
        for resolved_module, resolved_source in sorted(resolved_sources.items())
    )
    identity += (
        "\nruntime-abort-posture=true"
        if runtime_abort_posture
        else "\nruntime-abort-posture=false"
    )
    if identity_cache is not None:
        identity_cache[cache_key] = identity
    return identity


def _python_execution_import_modules(
    tree: ast.Module,
    *,
    relative_package: str,
    import_source_resolver: Callable[[str], str | None],
) -> tuple[str, ...]:
    """Resolve repository modules imported by module-scope execution."""

    modules: set[str] = set()
    for node in _module_execution_nodes(tree):
        if isinstance(node, ast.Import):
            modules.update(imported.name for imported in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        import_tree = ast.Module(body=[node], type_ignores=[])
        candidates_by_name = _python_import_modules(
            import_tree,
            relative_package=relative_package,
        )
        for imported in node.names:
            if imported.name == "*":
                modules.update(
                    _python_star_import_modules(
                        import_tree,
                        relative_package=relative_package,
                    )
                )
                continue
            local_name = imported.asname or imported.name
            resolved_module = next(
                (
                    candidate
                    for candidate in candidates_by_name.get(local_name, ())
                    if import_source_resolver(candidate) is not None
                ),
                None,
            )
            if resolved_module is not None:
                modules.add(resolved_module)
    return tuple(sorted(modules))


def _python_module_collection_abort_identity(
    tree: ast.Module,
    imported_modules: dict[str, tuple[str, ...]],
    source: str,
) -> str:
    """Bind only the import-time posture that can suppress test collection."""

    if not _has_module_level_collection_abort(tree, imported_modules):
        return "collection-abort=false"
    return (
        "collection-abort=true;source-sha256="
        + hashlib.sha256(source.encode("utf-8")).hexdigest()
    )


def _python_side_effect_import_identity(
    module: str,
    source: str,
    import_source_resolver: Callable[[str], str | None],
    *,
    include_transitive: bool,
) -> str:
    """Hash the bounded module-execution import closure for a local import."""

    root_key = (
        module,
        hashlib.sha256(source.encode("utf-8")).hexdigest(),
        include_transitive,
    )
    identity_cache: dict[tuple[str, str, bool], str] = getattr(
        import_source_resolver,
        "_uaa_side_effect_identity_cache",
        {},
    )
    cached_identity = identity_cache.get(root_key)
    if cached_identity is not None:
        return cached_identity
    dependency_cache: dict[tuple[str, str], tuple[str, ...]] = getattr(
        import_source_resolver,
        "_uaa_side_effect_dependency_cache",
        {},
    )
    effect_cache: dict[tuple[str, str], str] = getattr(
        import_source_resolver,
        "_uaa_side_effect_effect_cache",
        {},
    )

    pending = [(module, source)]
    resolved_effects: dict[str, str] = {}
    while pending:
        current_module, current_source = pending.pop()
        if current_module in resolved_effects:
            continue
        if len(resolved_effects) >= MAX_PYTHON_DEPENDENCY_MODULES:
            raise TestCorpusGuardError(
                "Python side-effect import closure exceeds module budget"
            )
        source_text = (
            current_source.split("\n", 1)[1]
            if current_source.startswith("path=")
            else current_source
        )
        source_digest = hashlib.sha256(current_source.encode("utf-8")).hexdigest()
        dependency_key = (current_module, source_digest)
        dependencies = dependency_cache.get(dependency_key)
        module_effect = effect_cache.get(dependency_key)
        if dependencies is None or module_effect is None:
            try:
                dependency_tree = _python_parsed_module(
                    current_module,
                    source_text,
                    import_source_resolver,
                )
            except SyntaxError as exc:
                raise TestCorpusGuardError(
                    "side-effect Python import cannot be inventoried safely"
                ) from exc
            source_path = current_source.split("\n", 1)[0].removeprefix("path=")
            relative_package = current_module
            if not source_path.endswith("/__init__.py") and "." in current_module:
                relative_package = current_module.rsplit(".", 1)[0]
            if dependencies is None:
                dependencies = _python_execution_import_modules(
                    dependency_tree,
                    relative_package=relative_package,
                    import_source_resolver=import_source_resolver,
                )
                dependency_cache[dependency_key] = dependencies
            if module_effect is None:
                module_effect = _python_module_collection_abort_identity(
                    dependency_tree,
                    _python_import_modules(
                        dependency_tree,
                        relative_package=relative_package,
                    ),
                    current_source,
                )
                effect_cache[dependency_key] = module_effect
        resolved_effects[current_module] = module_effect
        module_parts = current_module.split(".")
        package_dependencies = tuple(
            ".".join(module_parts[:index]) for index in range(1, len(module_parts))
        )
        dependencies = tuple(
            dict.fromkeys(
                (
                    *package_dependencies,
                    *(dependencies if include_transitive else ()),
                )
            )
        )
        for dependency in dependencies:
            dependency_source = import_source_resolver(dependency)
            if dependency_source is not None:
                pending.append((dependency, dependency_source))

    identity = "\n".join(
        f"module={resolved_module};effects-sha256="
        f"{hashlib.sha256(resolved_effect.encode('utf-8')).hexdigest()}"
        for resolved_module, resolved_effect in sorted(resolved_effects.items())
    )
    identity_cache[root_key] = identity
    return identity


def _python_binding_module_analysis(
    module: str,
    source: str,
    import_source_resolver: Callable[[str], str | None] | None,
) -> _PythonBindingModuleAnalysis:
    cache_key = (module, hashlib.sha256(source.encode("utf-8")).hexdigest())
    analysis_cache: dict[
        tuple[str, str], _PythonBindingModuleAnalysis
    ] | None = None
    if import_source_resolver is not None:
        analysis_cache = getattr(
            import_source_resolver,
            "_uaa_binding_module_analysis_cache",
            None,
        )
        if analysis_cache is not None and cache_key in analysis_cache:
            return analysis_cache[cache_key]

    source_text = source.split("\n", 1)[1] if source.startswith("path=") else source
    try:
        tree = _python_parsed_module(
            module,
            source_text,
            import_source_resolver,
        )
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
    import_positions: dict[str, tuple[int, int]] = {}
    binding_positions: dict[str, tuple[int, int]] = {}
    direct_module_aliases: set[str] = set()
    for node in _module_execution_nodes(tree):
        position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
        if isinstance(node, ast.Import):
            for imported in node.names:
                local_name = imported.asname or imported.name.split(".", 1)[0]
                direct_module_aliases.add(local_name)
                import_positions[local_name] = max(
                    import_positions.get(local_name, (0, 0)),
                    position,
                )
            continue
        if isinstance(node, ast.ImportFrom):
            for imported in node.names:
                if imported.name != "*":
                    local_name = imported.asname or imported.name
                    import_positions[local_name] = max(
                        import_positions.get(local_name, (0, 0)),
                        position,
                    )
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound_names = (node.name,)
        elif isinstance(node, ast.Assign):
            bound_names = tuple(
                name
                for target in node.targets
                for name in _binding_target_names(target)
            )
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            bound_names = tuple(_binding_target_names(node.target))
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            bound_names = tuple(_binding_target_names(node.target))
        else:
            continue
        for name in bound_names:
            binding_positions[name] = max(
                binding_positions.get(name, (0, 0)),
                position,
            )
    rebound_import_names = {
        name
        for name in imported_modules
        if binding_positions.get(name, (0, 0)) > import_positions.get(name, (0, 0))
    }
    if rebound_import_names:
        imported_modules = {
            name: candidates
            for name, candidates in imported_modules.items()
            if name not in rebound_import_names
        }
        direct_module_aliases.difference_update(rebound_import_names)
    analysis = _PythonBindingModuleAnalysis(
        tree=tree,
        relative_package=relative_package,
        module_bindings=module_bindings,
        imported_modules=imported_modules,
        direct_module_aliases=frozenset(direct_module_aliases),
        star_import_modules=_python_star_import_modules(
            tree,
            relative_package=relative_package,
        ),
        node_analyses={},
    )
    if analysis_cache is not None:
        analysis_cache[cache_key] = analysis
    return analysis


def _python_binding_node_analysis(
    analysis: _PythonBindingModuleAnalysis,
    node: ast.AST,
) -> _PythonBindingNodeAnalysis:
    """Reuse immutable binding-node facts within one exact source analysis."""

    position = (node.lineno, node.col_offset)
    cached = analysis.node_analyses.get(position)
    if cached is not None:
        return cached
    imported_requirements = tuple(
        (root, tuple(sorted(names)))
        for root, names in sorted(
            _python_import_requirements(node, analysis.imported_modules).items()
        )
    )
    star_import_requirements = (
        tuple(sorted(_python_star_import_dependency_names(node)))
        if analysis.star_import_modules
        else ()
    )
    local_dependency_names: set[str] = set()
    runtime_abort_posture = False
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Name)
            and child.id not in analysis.imported_modules
            and child.id in analysis.module_bindings
        ):
            local_dependency_names.add(child.id)
        if (
            isinstance(child, ast.Call)
            and _pytest_collection_abort_callable_name(
                child.func,
                analysis.imported_modules,
                {},
            )
            in {
                "importorskip",
                "skip",
                "skip-exception",
                "xfail",
                "xfail-exception",
            }
        ):
            runtime_abort_posture = True
    result = _PythonBindingNodeAnalysis(
        serialized=ast.dump(node, annotate_fields=True, include_attributes=False),
        imported_requirements=imported_requirements,
        star_import_requirements=star_import_requirements,
        local_dependency_names=tuple(sorted(local_dependency_names)),
        runtime_abort_posture=runtime_abort_posture,
    )
    analysis.node_analyses[position] = result
    return result


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
        return f"transitive-import-cycle={module};binding={binding_name}"
    cache_key = (
        module,
        binding_name,
        hashlib.sha256(source.encode("utf-8")).hexdigest(),
    )
    binding_cache: dict[tuple[str, str, str], str] | None = None
    root_binding_cache: dict[tuple[str, str, str], str] | None = None
    if import_source_resolver is not None:
        binding_cache = getattr(
            import_source_resolver,
            "_uaa_binding_identity_cache",
            None,
        )
        if binding_cache is not None and cache_key in binding_cache:
            return binding_cache[cache_key]
        if not _seen_bindings:
            root_binding_cache = getattr(
                import_source_resolver,
                "_uaa_root_binding_identity_cache",
                None,
            )
            if root_binding_cache is not None and cache_key in root_binding_cache:
                return root_binding_cache[cache_key]

    def cache_forwarded_identity(identity: str) -> str:
        if binding_cache is not None and "transitive-import-cycle" not in identity:
            binding_cache[cache_key] = identity
        if root_binding_cache is not None:
            root_binding_cache[cache_key] = identity
        return identity

    analysis = _python_binding_module_analysis(
        module,
        source,
        import_source_resolver,
    )
    tree = analysis.tree
    relative_package = analysis.relative_package
    module_bindings = analysis.module_bindings
    imported_modules = analysis.imported_modules
    direct_module_aliases = analysis.direct_module_aliases
    star_import_modules = analysis.star_import_modules
    pending = [binding_name]
    resolved: set[str] = set()
    binding_nodes: dict[tuple[int, int], ast.AST] = {}
    imported_requirements: dict[str, set[str]] = {}
    star_import_requirements: set[str] = set()
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
                return cache_forwarded_identity(
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
            lazy_modules = _python_lazy_export_binding_modules(
                tree,
                relative_package=relative_package,
                binding_name=name,
            )
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
                return cache_forwarded_identity(lazy_matches[0])
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
                return cache_forwarded_identity(star_matches[0])
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
            node_analysis = _python_binding_node_analysis(analysis, node)
            for root, names in node_analysis.imported_requirements:
                imported_requirements.setdefault(root, set()).update(names)
            if star_import_modules:
                star_import_requirements.update(
                    name
                    for name in node_analysis.star_import_requirements
                    if name not in imported_modules and name not in module_bindings
                )
            pending.extend(
                name
                for name in node_analysis.local_dependency_names
                if name not in resolved
            )
    serialized_parts = [
        _python_binding_node_analysis(analysis, node).serialized
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
    for name in sorted(star_import_requirements):
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
            serialized_parts.append(star_matches[0])
        elif len(star_matches) > 1:
            raise TestCorpusGuardError("imported Python parameter binding is ambiguous")
    identity_material = f"module={module}\nbinding={binding_name}\n" + "\n".join(
        serialized_parts
    )
    contains_cycle = "transitive-import-cycle=" in identity_material
    runtime_abort_posture = any(
        _python_binding_node_analysis(analysis, binding_node).runtime_abort_posture
        for binding_node in binding_nodes.values()
    ) or any(
        "runtime-abort-posture=true" in part.splitlines() for part in serialized_parts
    )
    identity = (
        f"module={module}\nbinding={binding_name}\n"
        "binding-closure-sha256="
        f"{hashlib.sha256(identity_material.encode('utf-8')).hexdigest()}"
        + ("\ntransitive-import-cycle=present" if contains_cycle else "")
        + (
            "\nruntime-abort-posture=true"
            if runtime_abort_posture
            else "\nruntime-abort-posture=false"
        )
    )
    if binding_cache is not None and not contains_cycle:
        binding_cache[cache_key] = identity
    if root_binding_cache is not None:
        root_binding_cache[cache_key] = identity
    return identity


def _python_local_fixture_bindings(tree: ast.Module) -> dict[str, str]:
    """Map statically declared module-local fixture names to function bindings."""

    fixture_aliases = _fixture_aliases(tree)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    configured_factories: dict[str, str | None] = {}

    def fixture_name(call: ast.Call, default: str | None) -> str | None:
        name_keywords = [
            keyword for keyword in call.keywords if keyword.arg in {None, "name"}
        ]
        if any(keyword.arg is None for keyword in name_keywords):
            return default
        if not name_keywords:
            return default
        value = name_keywords[-1].value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            raise TestCorpusGuardError(
                "module-local Python fixture name cannot be inventoried safely"
            )
        return value.value

    changed = True
    while changed:
        changed = False
        for node in _module_execution_nodes(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            if value is None:
                continue
            configured_name: str | None
            if isinstance(value, ast.Call) and _is_fixture_callable(
                value.func, fixture_aliases
            ):
                configured_name = fixture_name(value, None)
            elif isinstance(value, ast.Name) and value.id in configured_factories:
                configured_name = configured_factories[value.id]
            else:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                for name in _binding_target_names(target):
                    if (
                        name not in configured_factories
                        or configured_factories[name] != configured_name
                    ):
                        configured_factories[name] = configured_name
                        changed = True

    bindings: dict[str, str] = {}

    def add(exposed_name: str, function_name: str) -> None:
        existing = bindings.get(exposed_name)
        if existing is not None and existing != function_name:
            raise TestCorpusGuardError("module-local Python fixture name is ambiguous")
        bindings[exposed_name] = function_name

    for function_name, function in functions.items():
        for decorator in function.decorator_list:
            if _is_fixture_callable(decorator, fixture_aliases):
                add(function_name, function_name)
                break
            if isinstance(decorator, ast.Call) and _is_fixture_callable(
                decorator.func, fixture_aliases
            ):
                add(
                    fixture_name(decorator, function_name) or function_name,
                    function_name,
                )
                break
            if isinstance(decorator, ast.Name) and decorator.id in configured_factories:
                add(configured_factories[decorator.id] or function_name, function_name)
                break

    for node in _module_execution_nodes(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        default_name: str | None = None
        if _is_fixture_callable(node.func, fixture_aliases):
            default_name = fixture_name(node, None)
        elif isinstance(node.func, ast.Call) and _is_fixture_callable(
            node.func.func, fixture_aliases
        ):
            default_name = fixture_name(node.func, None)
        elif isinstance(node.func, ast.Name) and node.func.id in configured_factories:
            default_name = configured_factories[node.func.id]
        else:
            continue
        aliases = _module_name_aliases(
            tree,
            before=(node.lineno, node.col_offset),
        )
        for argument in node.args:
            root = _root_name(argument)
            if root is None:
                raise TestCorpusGuardError(
                    "module-local Python fixture callable cannot be inventoried safely"
                )
            function_name = aliases.get(root, root)
            if function_name not in functions:
                raise TestCorpusGuardError(
                    "module-local Python fixture callable cannot be inventoried safely"
                )
            add(default_name or function_name, function_name)
    return bindings


def _python_local_binding_identity(
    binding_name: str,
    module_bindings: dict[str, tuple[_ModuleBinding, ...]],
    imported_modules: dict[str, tuple[str, ...]],
    fixture_bindings: dict[str, str],
) -> str:
    """Serialize a local binding and bounded local dependencies without cycles."""

    pending = [binding_name]
    resolved: set[str] = set()
    binding_nodes: dict[tuple[int, int], ast.AST] = {}
    imported_requirements: dict[str, set[str]] = {}
    while pending:
        name = pending.pop()
        if name in resolved:
            continue
        resolved.add(name)
        for binding in module_bindings.get(name, ()):
            node = binding.node
            binding_nodes[(node.lineno, node.col_offset)] = node
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                requested_fixtures = (
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                )
                pending.extend(
                    fixture_bindings[argument.arg]
                    for argument in requested_fixtures
                    if argument.arg not in {"self", "cls"}
                    and argument.arg in fixture_bindings
                    and fixture_bindings[argument.arg] not in resolved
                )
            for root, names in _python_import_requirements(
                node, imported_modules
            ).items():
                imported_requirements.setdefault(root, set()).update(names)
            pending.extend(
                child.id
                for child in ast.walk(node)
                if isinstance(child, ast.Name)
                and child.id in module_bindings
                and child.id not in resolved
            )
    if not binding_nodes:
        raise TestCorpusGuardError(
            "module-local Python fixture binding cannot be resolved safely"
        )
    _reject_repository_reader_calls(
        tuple(binding_nodes.values()),
        imported_modules,
    )
    serialized_parts = [
        ast.dump(node, annotate_fields=True, include_attributes=False)
        for _position, node in sorted(binding_nodes.items())
    ]
    for root, names in sorted(imported_requirements.items()):
        serialized_parts.append(
            f"fixture-import={','.join(imported_modules[root])};"
            f"bindings={','.join(sorted(names))}"
        )
    return f"binding={binding_name}\n" + "\n".join(serialized_parts)


def _python_local_fixture_dependency_identity(
    path: str,
    source: str,
    import_source_resolver: Callable[[str], str | None],
) -> tuple[str, ...]:
    """Bind module-local fixtures to the exact imported bindings they consume."""

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "module-local pytest fixture dependency cannot be inventoried safely"
        ) from exc
    fixture_bindings = _python_local_fixture_bindings(tree)
    module = _python_module_name_for_path(path)
    rooted_source = f"path={path}\n{source}"
    return tuple(
        sorted(
            _python_imported_binding_source(
                module,
                rooted_source,
                binding_name,
                import_source_resolver,
            )
            for binding_name in set(fixture_bindings.values())
        )
    )


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


def _python_star_import_dependency_names(value: ast.AST) -> set[str]:
    """Return global loads that may have been supplied by ``import *``.

    Python makes every assignment in a function local for the entire scope,
    while nested functions may close over those locals.  Walk each lexical
    function separately so local names are not mistaken for star-imported
    globals, but preserve implicit and explicit global loads for resolution.
    Class bodies use dynamic name lookup, so treating their loads as possible
    globals is the conservative posture.
    """

    dependencies: set[str] = set()

    def function_dependencies(
        function: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda,
        enclosing_locals: frozenset[str],
    ) -> None:
        body = (
            function.body if not isinstance(function, ast.Lambda) else [function.body]
        )
        execution_nodes = _scope_execution_nodes(body)
        globals_ = {
            name
            for node in execution_nodes
            if isinstance(node, ast.Global)
            for name in node.names
        }
        nonlocals = {
            name
            for node in execution_nodes
            if isinstance(node, ast.Nonlocal)
            for name in node.names
        }
        arguments = function.args
        local_names = {
            argument.arg
            for argument in (
                *arguments.posonlyargs,
                *arguments.args,
                *arguments.kwonlyargs,
                *((arguments.vararg,) if arguments.vararg is not None else ()),
                *((arguments.kwarg,) if arguments.kwarg is not None else ()),
            )
        }
        local_names.update(
            name for node in execution_nodes for name in _execution_binding_names(node)
        )
        local_names.difference_update((*globals_, *nonlocals))
        for node in execution_nodes:
            if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
                continue
            if node.id in globals_ or node.id not in {
                *local_names,
                *nonlocals,
                *enclosing_locals,
            }:
                dependencies.add(node.id)
        nested_enclosing = frozenset((*enclosing_locals, *local_names))
        for node in execution_nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                function_dependencies(node, nested_enclosing)
            elif isinstance(node, ast.ClassDef):
                class_dependencies(node, nested_enclosing)

    def class_dependencies(
        class_node: ast.ClassDef,
        enclosing_locals: frozenset[str],
    ) -> None:
        execution_nodes = _scope_execution_nodes(class_node.body)
        dependencies.update(
            node.id
            for node in execution_nodes
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id not in enclosing_locals
        )
        for node in execution_nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                function_dependencies(node, enclosing_locals)
            elif isinstance(node, ast.ClassDef):
                class_dependencies(node, enclosing_locals)

    if isinstance(value, (ast.FunctionDef, ast.AsyncFunctionDef)):
        dependencies.update(
            node.id
            for expression in _definition_time_nodes(value)
            for node in ast.walk(expression)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        )
        function_dependencies(value, frozenset())
    elif isinstance(value, ast.ClassDef):
        dependencies.update(
            node.id
            for expression in _definition_time_nodes(value)
            for node in ast.walk(expression)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        )
        class_dependencies(value, frozenset())
    else:
        bound_names = {
            name for node in ast.walk(value) for name in _execution_binding_names(node)
        }
        dependencies.update(
            node.id
            for node in ast.walk(value)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id not in bound_names
        )
    return dependencies


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
    tree: ast.Module,
    module_bindings: dict[str, tuple[_ModuleBinding, ...]],
    parametrize_aliases: set[str],
    imported_modules: dict[str, tuple[str, ...]],
    import_source_resolver: Callable[[str], str | None] | None,
    fixture_override_resolver: (
        Callable[[str], tuple[tuple[str, str, str], ...]] | None
    ) = None,
    local_fixture_resolver: Callable[[str], str | None] | None = None,
    *,
    container_decorators: tuple[ast.expr, ...] = (),
    collection_lineno: int | None = None,
    shadowed_import_names: frozenset[str] = frozenset(),
    module_side_effect_identities: tuple[str, ...] = (),
    relative_package: str | None = None,
    normalize_non_aborting_runtime_helpers: bool = False,
) -> str:
    candidate_decorators = (*container_decorators, *node.decorator_list)
    relative_import_bindings = {
        alias.asname or alias.name
        for import_node in tree.body
        if isinstance(import_node, ast.ImportFrom) and import_node.level > 0
        for alias in import_node.names
    }

    def has_imported_fixture_reassignment(fixture_name: str) -> bool:
        for binding in module_bindings.get(fixture_name, ()):
            binding_node = binding.node
            if isinstance(binding_node, ast.Assign):
                targets = binding_node.targets
                value = binding_node.value
            elif (
                isinstance(binding_node, ast.AnnAssign)
                and binding_node.value is not None
            ):
                targets = (binding_node.target,)
                value = binding_node.value
            else:
                continue
            name_aliases = _module_name_aliases(
                tree,
                before=(binding_node.lineno, binding_node.col_offset),
            )
            for target in targets:
                for name, bound_value in _paired_binding_values(target, value):
                    if name != fixture_name:
                        continue
                    imported_root = _resolved_expression_root(
                        bound_value,
                        name_aliases,
                    )
                    if imported_root in imported_modules:
                        return True
        return False

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
    execution_disabling_decorators.extend(xfail_decorators)
    usefixtures_decorators = tuple(
        decorator
        for decorator in candidate_decorators
        if isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr == "usefixtures"
        and is_proven_pytest_mark(decorator.func)
    )
    usefixtures_names: list[str] = []
    for decorator in usefixtures_decorators:
        if decorator.keywords or any(
            not isinstance(argument, ast.Constant)
            or not isinstance(argument.value, str)
            for argument in decorator.args
        ):
            raise TestCorpusGuardError(
                "Python usefixtures request cannot be inventoried safely"
            )
        usefixtures_names.extend(argument.value for argument in decorator.args)
    getfixturevalue_aliases: set[str] = set()
    helper_type = (ast.FunctionDef, ast.AsyncFunctionDef)
    module_helper_definitions = {
        helper.name: helper
        for helper in tree.body
        if isinstance(helper, helper_type) and helper is not node
    }
    owner_class = next(
        (
            candidate
            for candidate in tree.body
            if isinstance(candidate, ast.ClassDef)
            and any(child is node for child in candidate.body)
        ),
        None,
    )
    class_helper_definitions = (
        {
            helper.name: helper
            for helper in owner_class.body
            if isinstance(helper, helper_type) and helper is not node
        }
        if owner_class is not None
        else {}
    )
    local_class_definitions = {
        candidate.name: candidate
        for candidate in tree.body
        if isinstance(candidate, ast.ClassDef)
    }
    module_callable_values: dict[str, ast.expr] = {}
    module_ambiguous_bindings: set[str] = set()
    callable_instance_lineage: set[str] = set()
    for candidate in tree.body:
        if isinstance(candidate, ast.Assign):
            targets = tuple(candidate.targets)
            value = candidate.value
        elif isinstance(candidate, ast.AnnAssign) and candidate.value is not None:
            targets = (candidate.target,)
            value = candidate.value
        else:
            if isinstance(
                candidate,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Import,
                    ast.ImportFrom,
                ),
            ):
                continue
            module_ambiguous_bindings.update(_statement_binding_names(candidate))
            continue
        for target in targets:
            for name, bound_value in _paired_binding_values(target, value):
                captured_value = (
                    module_callable_values.get(bound_value.id, bound_value)
                    if isinstance(bound_value, ast.Name)
                    else bound_value
                )
                module_callable_values[name] = captured_value
                direct_instance = (
                    isinstance(captured_value, ast.Call)
                    and isinstance(captured_value.func, ast.Name)
                    and captured_value.func.id in local_class_definitions
                    and any(
                        isinstance(member, helper_type) and member.name == "__call__"
                        for member in local_class_definitions[
                            captured_value.func.id
                        ].body
                    )
                )
                if direct_instance:
                    callable_instance_lineage.add(name)

    local_callable_values: dict[str, ast.expr] = {}
    local_ambiguous_bindings: set[str] = set()
    tracked_callable_instance_aliases = set(callable_instance_lineage)
    for candidate in node.body:
        if isinstance(candidate, ast.Assign):
            targets = tuple(candidate.targets)
            value = candidate.value
        elif isinstance(candidate, ast.AnnAssign) and candidate.value is not None:
            targets = (candidate.target,)
            value = candidate.value
        else:
            if isinstance(
                candidate,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Import,
                    ast.ImportFrom,
                ),
            ):
                continue
            local_ambiguous_bindings.update(_statement_binding_names(candidate))
            continue
        for target in targets:
            for name, bound_value in _paired_binding_values(target, value):
                captured_value = bound_value
                if isinstance(bound_value, ast.Name):
                    captured_value = local_callable_values.get(
                        bound_value.id,
                        module_callable_values.get(bound_value.id, bound_value),
                    )
                local_callable_values[name] = captured_value
                if (
                    isinstance(captured_value, ast.Call)
                    and isinstance(captured_value.func, ast.Name)
                    and captured_value.func.id in local_class_definitions
                ):
                    tracked_callable_instance_aliases.add(name)
    container_abort_aliases = _pytest_collection_abort_aliases(
        tree,
        imported_modules,
    )

    def direct_nested_helpers(
        function: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
        return {
            helper.name: helper
            for helper in function.body
            if isinstance(helper, helper_type)
        }

    def helper_for_expression(
        expression: ast.AST,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
        aliases: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    ) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        if isinstance(expression, ast.Name):
            return (
                aliases.get(expression.id)
                or direct_nested_helpers(function).get(expression.id)
                or module_helper_definitions.get(expression.id)
            )
        if (
            isinstance(expression, ast.Attribute)
            and isinstance(expression.value, ast.Name)
            and expression.value.id in {"self", "cls"}
        ):
            return class_helper_definitions.get(expression.attr)
        return None

    def resolved_callable_alias(
        expression: ast.AST,
        seen: frozenset[str] = frozenset(),
    ) -> tuple[ast.AST, bool]:
        if not isinstance(expression, ast.Name):
            return expression, False
        name = expression.id
        if name in seen:
            return expression, True
        if name in local_ambiguous_bindings:
            return expression, True
        if name in local_callable_values:
            return resolved_callable_alias(
                local_callable_values[name],
                frozenset((*seen, name)),
            )
        if name in module_ambiguous_bindings and name in callable_instance_lineage:
            return expression, True
        if name in module_callable_values and name in callable_instance_lineage:
            return resolved_callable_alias(
                module_callable_values[name],
                frozenset((*seen, name)),
            )
        return expression, False

    def static_callable_container(
        expression: ast.AST,
        containers: dict[str, dict[object, ast.expr]],
    ) -> dict[object, ast.expr] | None:
        if isinstance(expression, ast.Name):
            return containers.get(expression.id)
        if isinstance(expression, (ast.Subscript, ast.Call)):
            target = static_callable_container_target(expression, containers)
            return (
                static_callable_container(target, containers)
                if target is not None
                else None
            )
        if isinstance(expression, (ast.List, ast.Tuple)):
            items: dict[object, ast.expr] = {}
            for item in expression.elts:
                if isinstance(item, ast.Starred):
                    nested = static_callable_container(item.value, containers)
                    if nested is None:
                        return None
                    items.update(
                        (len(items), nested_item) for nested_item in nested.values()
                    )
                else:
                    items[len(items)] = item
            return (
                items
                if items
                and any(
                    unambiguously_maybe_callable(item)
                    or static_callable_container(item, containers) is not None
                    for item in items.values()
                )
                else None
            )
        if isinstance(expression, ast.Dict):
            items: dict[object, ast.expr] = {}
            for key, value in zip(expression.keys, expression.values, strict=True):
                if (
                    key is None
                    or not isinstance(key, ast.Constant)
                    or not isinstance(key.value, (int, str))
                ):
                    return None
                items[key.value] = value
            return (
                items
                if items
                and any(
                    unambiguously_maybe_callable(item)
                    or static_callable_container(item, containers) is not None
                    for item in items.values()
                )
                else None
            )
        return None

    def maybe_callable(expression: ast.AST) -> bool:
        resolved_expression, ambiguous = resolved_callable_alias(expression)
        if ambiguous:
            return True
        if resolved_expression is not expression:
            return maybe_callable(resolved_expression)
        if helper_for_expression(expression, node, {}) is not None:
            return True
        if _pytest_collection_abort_callable_name(
            expression,
            imported_modules,
            container_abort_aliases,
        ):
            return True
        if isinstance(expression, ast.Lambda):
            return True
        if isinstance(expression, ast.Name) and expression.id in imported_modules:
            return any(
                candidate.startswith("tests.")
                for candidate in imported_modules[expression.id]
            )
        if isinstance(expression, ast.Attribute):
            root = _root_name(expression)
            return root is not None and any(
                candidate == "tests" or candidate.startswith("tests.")
                for candidate in imported_modules.get(root, ())
            )
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id in {"partial"}
            and expression.args
        ):
            return maybe_callable(expression.args[0])
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id in local_class_definitions
        ):
            return any(
                isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                and member.name == "__call__"
                for member in local_class_definitions[expression.func.id].body
            )
        nested = static_callable_container(expression, {})
        return nested is not None

    def unambiguously_maybe_callable(expression: ast.AST) -> bool:
        resolved_expression, ambiguous = resolved_callable_alias(expression)
        if ambiguous:
            return False
        return maybe_callable(resolved_expression)

    def contains_ambiguous_callable_candidate(expression: ast.AST | None) -> bool:
        if expression is None:
            return False
        return any(
            isinstance(candidate, ast.Name)
            and resolved_callable_alias(candidate)[1]
            for candidate in ast.walk(expression)
        )

    def is_non_aborting_local_callable(
        expression: ast.AST,
        seen: frozenset[str] = frozenset(),
        owner_helpers: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] | None = None,
    ) -> bool:
        resolved_expression, ambiguous = resolved_callable_alias(expression)
        if ambiguous:
            return False
        expression = resolved_expression
        if isinstance(expression, ast.Lambda):
            return not any(
                isinstance(child, ast.Call)
                and bool(
                    _pytest_collection_abort_callable_name(
                        child.func,
                        imported_modules,
                        container_abort_aliases,
                    )
                )
                for child in ast.walk(expression.body)
            )
        if (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id in local_class_definitions
        ):
            instance = expression
            class_definition = local_class_definitions.get(instance.func.id)
            if class_definition is None:
                return False
            owner_helpers = {
                member.name: member
                for member in class_definition.body
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            helper = owner_helpers.get("__call__")
        else:
            helper = None
        helper = (
            helper
            or (expression if isinstance(expression, helper_type) else None)
            or helper_for_expression(expression, node, {})
        )
        if (
            helper is None
            and isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
        ):
            class_definition = local_class_definitions.get(expression.func.id)
            helper = next(
                (
                    member
                    for member in (class_definition.body if class_definition else ())
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and member.name == "__call__"
                ),
                None,
            )
        if helper is None or helper.name in seen:
            return False
        aliases = dict(container_abort_aliases)
        for child in _scope_execution_nodes(helper.body):
            if isinstance(child, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                value = child.value
                targets = (
                    child.targets if isinstance(child, ast.Assign) else (child.target,)
                )
                abort_name = _pytest_collection_abort_callable_name(
                    value,
                    imported_modules,
                    aliases,
                )
                for target in targets:
                    for alias in _binding_target_names(target):
                        if abort_name:
                            aliases[alias] = abort_name
            if isinstance(child, ast.Call):
                if _pytest_collection_abort_callable_name(
                    child.func,
                    imported_modules,
                    aliases,
                ):
                    return False
                nested_helper = helper_for_expression(child.func, helper, {})
                if (
                    nested_helper is None
                    and owner_helpers is not None
                    and isinstance(child.func, ast.Attribute)
                    and isinstance(child.func.value, ast.Name)
                    and child.func.value.id in {"self", "cls"}
                ):
                    nested_helper = owner_helpers.get(child.func.attr)
                if nested_helper is not None and not is_non_aborting_local_callable(
                    nested_helper,
                    frozenset((*seen, helper.name)),
                    owner_helpers,
                ):
                    return False
            if (
                isinstance(child, ast.Raise)
                and child.exc is not None
                and any(
                    _pytest_collection_abort_callable_name(
                        candidate,
                        imported_modules,
                        aliases,
                    )
                    for candidate in ast.walk(child.exc)
                )
            ):
                return False
        return True

    def callable_requires_fail_closed(expression: ast.AST) -> bool:
        if not maybe_callable(expression):
            return False
        return not is_non_aborting_local_callable(expression)

    def callable_is_proven_to_require_fail_closed(expression: ast.AST) -> bool:
        resolved_expression, ambiguous = resolved_callable_alias(expression)
        if ambiguous:
            return False
        return callable_requires_fail_closed(resolved_expression)

    def static_callable_container_target(
        expression: ast.AST,
        containers: dict[str, dict[object, ast.expr]],
    ) -> ast.expr | None:
        if isinstance(expression, ast.Subscript):
            container_expression = expression.value
            key_expression = expression.slice
        elif (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Attribute)
            and expression.func.attr == "get"
            and len(expression.args) == 1
            and not expression.keywords
        ):
            container_expression = expression.func.value
            key_expression = expression.args[0]
        else:
            return None
        if not isinstance(key_expression, ast.Constant) or not isinstance(
            key_expression.value,
            (int, str),
        ):
            return None
        container = static_callable_container(container_expression, containers)
        return container.get(key_expression.value) if container is not None else None

    def callable_container_root(expression: ast.AST) -> str | None:
        if isinstance(expression, ast.Call) and isinstance(
            expression.func, ast.Attribute
        ):
            expression = expression.func.value
        elif (
            isinstance(expression, ast.Call)
            and isinstance(expression.func, ast.Name)
            and expression.func.id in {"dict", "list", "set", "tuple"}
            and expression.args
        ):
            expression = expression.args[0]
        if isinstance(expression, (ast.GeneratorExp, ast.ListComp, ast.SetComp)):
            for generator in expression.generators:
                root = callable_container_root(generator.iter)
                if root is not None:
                    return root
        return _root_name(expression)

    def static_assignment_pairs(
        target: ast.AST,
        value: ast.expr,
        containers: dict[str, dict[object, ast.expr]],
    ) -> tuple[tuple[str, ast.expr], ...] | None:
        if isinstance(target, ast.Name):
            return ((target.id, value),)
        if not isinstance(target, (ast.Tuple, ast.List)) or any(
            isinstance(item, ast.Starred) for item in target.elts
        ):
            return None
        if isinstance(value, (ast.Tuple, ast.List)):
            values = tuple(value.elts)
        else:
            container = static_callable_container(value, containers)
            if container is None or set(container) != set(range(len(target.elts))):
                return None
            values = tuple(container[index] for index in range(len(target.elts)))
        if len(target.elts) != len(values):
            return None
        pairs: list[tuple[str, ast.expr]] = []
        for child_target, child_value in zip(target.elts, values, strict=True):
            child_pairs = static_assignment_pairs(
                child_target,
                child_value,
                containers,
            )
            if child_pairs is None:
                return None
            pairs.extend(child_pairs)
        return tuple(pairs)

    execution_nodes = list(_scope_execution_nodes(node.body))
    execution_node_scopes: dict[int, ast.FunctionDef | ast.AsyncFunctionDef] = {
        id(execution_node): node for execution_node in execution_nodes
    }
    expanded_helpers: dict[tuple[int, int], ast.FunctionDef | ast.AsyncFunctionDef] = {}
    lexical_parent_scopes: dict[int, ast.FunctionDef | ast.AsyncFunctionDef | None] = {
        id(node): None
    }
    called_helpers_by_call_id: dict[int, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    callable_container_targets_by_call_id: dict[int, ast.expr] = {}
    callable_containers_by_scope: dict[int, dict[str, dict[object, ast.expr]]] = {}
    ambiguous_callable_containers_by_scope: dict[int, set[str]] = {}
    pending_helper_scopes: list[ast.FunctionDef | ast.AsyncFunctionDef] = [node]
    while pending_helper_scopes:
        helper_scope = pending_helper_scopes.pop()
        helper_nodes = list(_scope_execution_nodes(helper_scope.body))
        execution_node_scopes.update(
            (id(execution_node), helper_scope) for execution_node in helper_nodes
        )
        helper_aliases: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        lexical_parent = lexical_parent_scopes.get(id(helper_scope))
        callable_containers = dict(
            callable_containers_by_scope.get(id(lexical_parent), {})
            if lexical_parent is not None
            else {}
        )
        ambiguous_callable_containers = set(
            ambiguous_callable_containers_by_scope.get(id(lexical_parent), set())
            if lexical_parent is not None
            else set()
        )
        empty_container_names: set[str] = set()
        direct_scope_node_ids = {id(item) for item in helper_scope.body}
        for execution_node in helper_nodes:
            mutation_targets: tuple[ast.AST, ...] = ()
            if isinstance(execution_node, ast.AugAssign):
                mutation_targets = (execution_node.target,)
            elif isinstance(execution_node, ast.Delete):
                mutation_targets = tuple(execution_node.targets)
            if any(
                callable_container_root(target) in callable_containers
                for target in mutation_targets
            ):
                raise TestCorpusGuardError(
                    "dynamic runtime helper container cannot be inventoried safely"
                )
            if isinstance(
                execution_node,
                (ast.Assign, ast.AnnAssign, ast.NamedExpr),
            ):
                value = execution_node.value
                targets = (
                    execution_node.targets
                    if isinstance(execution_node, ast.Assign)
                    else (execution_node.target,)
                )
                destructured_pairs: list[tuple[str, ast.expr]] = []
                has_destructured_target = any(
                    isinstance(target, (ast.Tuple, ast.List)) for target in targets
                )
                if has_destructured_target:
                    for target in targets:
                        pairs = static_assignment_pairs(
                            target,
                            value,
                            callable_containers,
                        )
                        if pairs is None:
                            if static_callable_container(value, callable_containers):
                                raise TestCorpusGuardError(
                                    "dynamic runtime helper container cannot be inventoried safely"
                                )
                            continue
                        destructured_pairs.extend(pairs)
                if any(
                    isinstance(target, (ast.Subscript, ast.Attribute))
                    and callable_container_root(target) in callable_containers
                    for target in targets
                ):
                    raise TestCorpusGuardError(
                        "dynamic runtime helper container cannot be inventoried safely"
                    )
                for target in targets:
                    if (
                        isinstance(target, ast.Subscript)
                        and callable_container_root(target) in empty_container_names
                        and callable_requires_fail_closed(value)
                    ):
                        raise TestCorpusGuardError(
                            "dynamic runtime helper container cannot be inventoried safely"
                        )
                container = static_callable_container(value, callable_containers)
                if (
                    container is None
                    and callable_container_root(value) in callable_containers
                ):
                    raise TestCorpusGuardError(
                        "dynamic runtime helper container cannot be inventoried safely"
                    )
                target_names = {
                    name for target in targets for name in _binding_target_names(target)
                }
                for target_name in target_names:
                    helper_aliases.pop(target_name, None)
                    container_abort_aliases.pop(target_name, None)
                    callable_containers.pop(target_name, None)
                    ambiguous_callable_containers.discard(target_name)
                    empty_container_names.discard(target_name)
                if has_destructured_target:
                    if (
                        destructured_pairs
                        and id(execution_node) not in direct_scope_node_ids
                    ):
                        raise TestCorpusGuardError(
                            "dynamic runtime helper container cannot be inventoried safely"
                        )
                    for target_name, bound_value in destructured_pairs:
                        nested_container = static_callable_container(
                            bound_value,
                            callable_containers,
                        )
                        if nested_container is not None:
                            callable_containers[target_name] = nested_container
                            continue
                        abort_name = _pytest_collection_abort_callable_name(
                            bound_value,
                            imported_modules,
                            container_abort_aliases,
                        )
                        if abort_name:
                            container_abort_aliases[target_name] = abort_name
                            continue
                        resolved_helper = helper_for_expression(
                            bound_value,
                            helper_scope,
                            helper_aliases,
                        )
                        if resolved_helper is not None:
                            helper_aliases[target_name] = resolved_helper
                            continue
                        if callable_requires_fail_closed(bound_value):
                            raise TestCorpusGuardError(
                                "dynamic runtime helper container cannot be inventoried safely"
                            )
                    continue
                abort_name = _pytest_collection_abort_callable_name(
                    value,
                    imported_modules,
                    container_abort_aliases,
                )
                if abort_name:
                    for target_name in target_names:
                        container_abort_aliases[target_name] = abort_name
                if isinstance(value, (ast.List, ast.Dict)) and not (
                    value.elts if isinstance(value, ast.List) else value.keys
                ):
                    empty_container_names.update(target_names)
                if (
                    container is not None
                    and id(execution_node) not in direct_scope_node_ids
                ):
                    raise TestCorpusGuardError(
                        "dynamic runtime helper container cannot be inventoried safely"
                    )
                if container is not None:
                    for target in targets:
                        if isinstance(target, ast.Name):
                            callable_containers[target.id] = container
                        elif isinstance(target, (ast.Tuple, ast.List)):
                            raise TestCorpusGuardError(
                                "dynamic runtime helper container cannot be inventoried safely"
                            )
                        elif all(
                            not maybe_callable(item)
                            or is_non_aborting_local_callable(item)
                            for item in container.values()
                        ):
                            continue
                        else:
                            raise TestCorpusGuardError(
                                "dynamic runtime helper container cannot be inventoried safely"
                            )
                elif isinstance(value, (ast.List, ast.Tuple, ast.Dict, ast.Set)) and (
                    contains_ambiguous_callable_candidate(value)
                ):
                    ambiguous_callable_containers.update(target_names)
                elif any(
                    isinstance(target, ast.Subscript) for target in targets
                ) and callable_is_proven_to_require_fail_closed(value):
                    raise TestCorpusGuardError(
                        "dynamic runtime helper container cannot be inventoried safely"
                    )
                elif any(
                    isinstance(target, ast.Subscript) for target in targets
                ) and contains_ambiguous_callable_candidate(value):
                    ambiguous_callable_containers.update(
                        root
                        for target in targets
                        if isinstance(target, ast.Subscript)
                        and (root := callable_container_root(target)) is not None
                    )
                resolved_helper = helper_for_expression(
                    value,
                    helper_scope,
                    helper_aliases,
                )
                if resolved_helper is not None and target_names:
                    if id(execution_node) not in direct_scope_node_ids:
                        raise TestCorpusGuardError(
                            "dynamic runtime helper alias cannot be inventoried safely"
                        )
                    for target_name in target_names:
                        helper_aliases[target_name] = resolved_helper
            if not isinstance(execution_node, ast.Call):
                continue
            call_target = execution_node.func
            if (
                isinstance(call_target, (ast.Subscript, ast.Call))
                and callable_container_root(call_target)
                in ambiguous_callable_containers
            ):
                raise TestCorpusGuardError(
                    "dynamic runtime helper container cannot be inventoried safely"
                )
            if any(
                callable_container_root(argument) in callable_containers
                for argument in (
                    *execution_node.args,
                    *(keyword.value for keyword in execution_node.keywords),
                )
            ):
                raise TestCorpusGuardError(
                    "dynamic runtime helper container cannot be inventoried safely"
                )
            if (
                isinstance(call_target, ast.Attribute)
                and callable_container_root(call_target.value) in callable_containers
                and call_target.attr
                in {
                    "append",
                    "clear",
                    "extend",
                    "insert",
                    "pop",
                    "popitem",
                    "remove",
                    "reverse",
                    "setdefault",
                    "sort",
                    "update",
                }
            ):
                raise TestCorpusGuardError(
                    "dynamic runtime helper container cannot be inventoried safely"
                )
            if (
                isinstance(call_target, ast.Attribute)
                and callable_container_root(call_target.value) in empty_container_names
                and call_target.attr
                in {"append", "extend", "insert", "setdefault", "update"}
                and any(
                    callable_is_proven_to_require_fail_closed(argument)
                    for argument in execution_node.args
                )
            ):
                raise TestCorpusGuardError(
                    "dynamic runtime helper container cannot be inventoried safely"
                )
            if (
                isinstance(call_target, ast.Attribute)
                and (
                    root := callable_container_root(call_target.value)
                ) in empty_container_names
                and call_target.attr
                in {"append", "extend", "insert", "setdefault", "update"}
                and any(
                    contains_ambiguous_callable_candidate(argument)
                    for argument in execution_node.args
                )
            ):
                ambiguous_callable_containers.add(root)
            container_target = static_callable_container_target(
                call_target,
                callable_containers,
            )
            if container_target is not None:
                if (
                    callable_requires_fail_closed(container_target)
                    and not _pytest_collection_abort_callable_name(
                        container_target,
                        imported_modules,
                        container_abort_aliases,
                    )
                    and not isinstance(container_target, ast.Lambda)
                    and helper_for_expression(container_target, node, {}) is None
                    and not (
                        isinstance(container_target, ast.Name)
                        and container_target.id in imported_modules
                    )
                ):
                    raise TestCorpusGuardError(
                        "dynamic runtime helper container cannot be inventoried safely"
                    )
                callable_container_targets_by_call_id[id(execution_node)] = (
                    container_target
                )
                call_target = container_target
            elif (
                isinstance(call_target, (ast.Subscript, ast.Call))
                and callable_container_root(call_target) in callable_containers
            ):
                raise TestCorpusGuardError(
                    "dynamic runtime helper container cannot be inventoried safely"
                )
            elif isinstance(call_target, ast.Subscript) or (
                isinstance(call_target, ast.Call)
                and isinstance(call_target.func, ast.Attribute)
                and call_target.func.attr in {"__getitem__", "get", "getitem"}
            ):
                root = callable_container_root(call_target)
                if root in imported_modules or (
                    root is not None
                    and any(
                        isinstance(
                            binding.node,
                            (ast.Assign, ast.AnnAssign, ast.NamedExpr),
                        )
                        and static_callable_container(
                            binding.node.value,
                            callable_containers,
                        )
                        is not None
                        for binding in module_bindings.get(root, ())
                    )
                ):
                    raise TestCorpusGuardError(
                        "dynamic runtime helper container cannot be inventoried safely"
                    )
            resolved_helper = helper_for_expression(
                call_target,
                helper_scope,
                helper_aliases,
            )
            if resolved_helper is None:
                continue
            called_helpers_by_call_id[id(execution_node)] = resolved_helper
            helper_key = (resolved_helper.lineno, resolved_helper.col_offset)
            if helper_key in expanded_helpers:
                continue
            expanded_helpers[helper_key] = resolved_helper
            lexical_parent_scopes[id(resolved_helper)] = (
                helper_scope
                if any(child is resolved_helper for child in helper_scope.body)
                else None
            )
            pending_helper_scopes.append(resolved_helper)
        callable_containers_by_scope[id(helper_scope)] = callable_containers
        ambiguous_callable_containers_by_scope[id(helper_scope)] = (
            ambiguous_callable_containers
        )
        if helper_scope is not node:
            execution_nodes.extend(helper_nodes)
    function_execution_nodes = tuple(execution_nodes)
    module_runtime_imports: dict[str, tuple[str, ...]] = {}
    for module_node in tree.body:
        if not isinstance(module_node, (ast.Import, ast.ImportFrom)):
            continue
        for name, candidates in _python_import_modules(
            ast.Module(body=[module_node], type_ignores=[]),
            relative_package=relative_package,
        ).items():
            if not candidates:
                candidates = imported_modules.get(name, ())
            module_runtime_imports[name] = tuple(
                dict.fromkeys((*module_runtime_imports.get(name, ()), *candidates))
            )
    function_scopes = (node, *expanded_helpers.values())
    scope_execution_nodes_by_scope = {
        id(function_scope): _scope_execution_nodes(function_scope.body)
        for function_scope in function_scopes
    }
    scope_globals_by_scope = {
        id(function_scope): {
            name
            for scope_node in scope_execution_nodes_by_scope[id(function_scope)]
            if isinstance(scope_node, ast.Global)
            for name in scope_node.names
        }
        for function_scope in function_scopes
    }
    scope_nonlocals_by_scope = {
        id(function_scope): {
            name
            for scope_node in scope_execution_nodes_by_scope[id(function_scope)]
            if isinstance(scope_node, ast.Nonlocal)
            for name in scope_node.names
        }
        for function_scope in function_scopes
    }
    conditional_execution_node_ids_by_scope: dict[int, set[int]] = {}
    conditional_node_types = (
        ast.BoolOp,
        ast.Compare,
        ast.comprehension,
        ast.DictComp,
        ast.For,
        ast.GeneratorExp,
        ast.AsyncFor,
        ast.If,
        ast.IfExp,
        ast.ListComp,
        ast.Match,
        ast.SetComp,
        ast.Try,
        ast.TryStar,
        ast.While,
    )
    for function_scope in function_scopes:
        scope_id = id(function_scope)
        conditional_ids: set[int] = set()
        for scope_node in scope_execution_nodes_by_scope[scope_id]:
            if not isinstance(scope_node, conditional_node_types):
                continue
            conditional_ids.update(
                id(descendant)
                for descendant in ast.walk(scope_node)
                if execution_node_scopes.get(id(descendant)) is function_scope
            )
        conditional_execution_node_ids_by_scope[scope_id] = conditional_ids
    scope_binding_nodes_by_scope: dict[int, dict[str, list[ast.AST]]] = {}
    scope_imports_by_scope: dict[int, dict[str, tuple[str, ...]]] = {}
    local_runtime_bindings_by_scope: dict[int, set[str]] = {}
    for function_scope in function_scopes:
        scope_id = id(function_scope)
        binding_nodes: dict[str, list[ast.AST]] = {}
        scope_imports: dict[str, tuple[str, ...]] = {}
        for scope_node in scope_execution_nodes_by_scope[scope_id]:
            for name in _execution_binding_names(scope_node):
                binding_nodes.setdefault(name, []).append(scope_node)
            if isinstance(scope_node, (ast.Import, ast.ImportFrom)):
                local_imports = _python_import_modules(
                    ast.Module(body=[scope_node], type_ignores=[]),
                    relative_package=relative_package,
                )
                for name, candidates in local_imports.items():
                    if not candidates:
                        candidates = imported_modules.get(name, ())
                    scope_imports[name] = tuple(
                        dict.fromkeys((*scope_imports.get(name, ()), *candidates))
                    )
        scope_binding_nodes_by_scope[scope_id] = binding_nodes
        scope_imports_by_scope[scope_id] = scope_imports
        local_runtime_bindings_by_scope[scope_id] = (
            {
                argument.arg
                for argument in (
                    *function_scope.args.posonlyargs,
                    *function_scope.args.args,
                    *function_scope.args.kwonlyargs,
                    *(
                        (function_scope.args.vararg,)
                        if function_scope.args.vararg is not None
                        else ()
                    ),
                    *(
                        (function_scope.args.kwarg,)
                        if function_scope.args.kwarg is not None
                        else ()
                    ),
                )
            }
            | set(binding_nodes)
            | scope_nonlocals_by_scope[scope_id]
        ) - scope_globals_by_scope[scope_id]
    helper_global_runtime_import_cache: dict[int, dict[str, tuple[str, ...]]] = {}

    def helper_global_runtime_imports(
        function_scope: ast.FunctionDef | ast.AsyncFunctionDef,
        visiting: frozenset[int] = frozenset(),
    ) -> dict[str, tuple[str, ...]]:
        scope_id = id(function_scope)
        if scope_id in helper_global_runtime_import_cache:
            return dict(helper_global_runtime_import_cache[scope_id])
        if scope_id in visiting:
            return {}
        active_imports: dict[str, tuple[str, ...]] = {}
        next_visiting = frozenset((*visiting, scope_id))
        for scope_node in scope_execution_nodes_by_scope[scope_id]:
            if isinstance(scope_node, (ast.Import, ast.ImportFrom)):
                node_imports = _python_import_modules(
                    ast.Module(body=[scope_node], type_ignores=[]),
                    relative_package=relative_package,
                )
                for name, candidates in node_imports.items():
                    if name not in scope_globals_by_scope[scope_id]:
                        continue
                    if (
                        id(scope_node)
                        in conditional_execution_node_ids_by_scope[scope_id]
                    ):
                        raise TestCorpusGuardError(
                            "conditional global runtime import cannot be inventoried safely"
                        )
                    if not candidates:
                        candidates = imported_modules.get(name, ())
                    active_imports[name] = candidates
            if isinstance(scope_node, ast.Call):
                called_helper = called_helpers_by_call_id.get(id(scope_node))
                if called_helper is not None:
                    if (
                        helper_global_runtime_imports(
                            called_helper,
                            next_visiting,
                        )
                        and id(scope_node)
                        in conditional_execution_node_ids_by_scope[scope_id]
                    ):
                        raise TestCorpusGuardError(
                            "conditional global runtime import installer cannot be inventoried safely"
                        )
                    active_imports.update(
                        helper_global_runtime_imports(
                            called_helper,
                            next_visiting,
                        )
                    )
        helper_global_runtime_import_cache[scope_id] = dict(active_imports)
        return active_imports

    helper_global_runtime_imports_by_scope = {
        id(function_scope): helper_global_runtime_imports(function_scope)
        for function_scope in expanded_helpers.values()
    }

    def enclosing_scope_binding_nodes(
        function_scope: ast.FunctionDef | ast.AsyncFunctionDef,
        name: str,
    ) -> tuple[bool, tuple[ast.AST, ...]]:
        parent_scope = lexical_parent_scopes.get(id(function_scope))
        while parent_scope is not None:
            parent_id = id(parent_scope)
            if name in scope_globals_by_scope[parent_id]:
                return False, ()
            if name in scope_nonlocals_by_scope[parent_id]:
                parent_scope = lexical_parent_scopes.get(parent_id)
                continue
            if name in local_runtime_bindings_by_scope[parent_id]:
                return True, tuple(
                    scope_binding_nodes_by_scope[parent_id].get(name, ())
                )
            parent_scope = lexical_parent_scopes.get(parent_id)
        return False, ()

    def runtime_scope_import_candidates(
        function_scope: ast.FunctionDef | ast.AsyncFunctionDef,
        name: str,
        *,
        module_imports: dict[str, tuple[str, ...]] | None = None,
    ) -> tuple[bool, tuple[str, ...]]:
        if module_imports is None:
            module_imports = module_runtime_imports
        scope_id = id(function_scope)
        if name in scope_globals_by_scope[scope_id]:
            if name in scope_imports_by_scope[scope_id]:
                return True, scope_imports_by_scope[scope_id][name]
            return (
                name in module_imports,
                module_imports.get(name, ()),
            )
        if name in scope_imports_by_scope[scope_id]:
            return True, scope_imports_by_scope[scope_id][name]
        if name in scope_nonlocals_by_scope[scope_id]:
            parent_scope = lexical_parent_scopes.get(scope_id)
            if parent_scope is None:
                return True, ()
            return runtime_scope_import_candidates(
                parent_scope,
                name,
                module_imports=module_imports,
            )
        if name in local_runtime_bindings_by_scope[scope_id]:
            return True, ()
        parent_scope = lexical_parent_scopes.get(scope_id)
        if parent_scope is not None:
            is_owned, candidates = runtime_scope_import_candidates(
                parent_scope,
                name,
                module_imports=module_imports,
            )
            if is_owned:
                return is_owned, candidates
        return (
            name in module_imports,
            module_imports.get(name, ()),
        )

    def runtime_scope_import_requirements(
        function_scope: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> dict[tuple[str, ...], set[str]]:
        scope_id = id(function_scope)
        requirements: dict[tuple[str, ...], set[str]] = {}
        attribute_root_node_ids: set[int] = set()
        for scope_node in scope_execution_nodes_by_scope[scope_id]:
            if not isinstance(scope_node, ast.Attribute):
                continue
            current: ast.AST = scope_node
            while isinstance(current, ast.Attribute):
                current = current.value
            if not isinstance(current, ast.Name):
                continue
            root = current.id
            _is_owned, candidates = runtime_scope_import_candidates(
                function_scope,
                root,
            )
            if not candidates:
                continue
            attribute_root_node_ids.add(id(current))
            imported_member = scope_node
            while isinstance(imported_member.value, ast.Attribute):
                imported_member = imported_member.value
            requirements.setdefault(candidates, set()).add(imported_member.attr)
        for scope_node in scope_execution_nodes_by_scope[scope_id]:
            if (
                not isinstance(scope_node, ast.Name)
                or id(scope_node) in attribute_root_node_ids
            ):
                continue
            _is_owned, candidates = runtime_scope_import_candidates(
                function_scope,
                scope_node.id,
            )
            if candidates:
                requirements.setdefault(candidates, set()).add(scope_node.id)
        return requirements

    for execution_node in function_execution_nodes:
        if isinstance(execution_node, ast.Assign):
            targets = execution_node.targets
            value = execution_node.value
        elif isinstance(execution_node, ast.AnnAssign) and execution_node.value:
            targets = (execution_node.target,)
            value = execution_node.value
        elif isinstance(execution_node, ast.NamedExpr):
            targets = (execution_node.target,)
            value = execution_node.value
        else:
            continue
        for target in targets:
            for name, bound_value in _paired_binding_values(target, value):
                is_getfixturevalue = (
                    isinstance(bound_value, ast.Attribute)
                    and bound_value.attr == "getfixturevalue"
                ) or (
                    isinstance(bound_value, ast.Name)
                    and bound_value.id in getfixturevalue_aliases
                )
                if is_getfixturevalue and name not in getfixturevalue_aliases:
                    getfixturevalue_aliases.add(name)

    getfixturevalue_names: list[str] = []
    for call in (
        child
        for child in function_execution_nodes
        if isinstance(child, ast.Call)
        and (
            (
                isinstance(child.func, ast.Attribute)
                and child.func.attr == "getfixturevalue"
            )
            or (
                isinstance(child.func, ast.Name)
                and child.func.id in getfixturevalue_aliases
            )
        )
    ):
        if (
            len(call.args) != 1
            or call.keywords
            or not isinstance(call.args[0], ast.Constant)
            or not isinstance(call.args[0].value, str)
        ):
            raise TestCorpusGuardError(
                "dynamic Python fixture request cannot be inventoried safely"
            )
        getfixturevalue_names.append(call.args[0].value)
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
    requested_fixture_names = tuple(
        dict.fromkeys(
            (*fixture_argument_names, *usefixtures_names, *getfixturevalue_names)
        )
    )
    identity_decorators = (
        *decorators,
        *execution_disabling_decorators,
        *usefixtures_decorators,
    )
    runtime_imports = dict(imported_modules)
    for alias in _pytest_module_aliases(tree):
        runtime_imports[alias] = tuple(
            dict.fromkeys((*runtime_imports.get(alias, ()), "pytest"))
        )
    runtime_abort_aliases: dict[str, str] = {}
    called_runtime_names = {
        execution_node.func.id
        for execution_node in function_execution_nodes
        if isinstance(execution_node, ast.Call)
        and isinstance(execution_node.func, ast.Name)
    }
    for module_node in tree.body:
        if isinstance(module_node, ast.Assign):
            targets = module_node.targets
            value = module_node.value
        elif isinstance(module_node, (ast.AnnAssign, ast.NamedExpr)):
            targets = (module_node.target,)
            value = module_node.value
        else:
            if isinstance(
                module_node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Import,
                    ast.ImportFrom,
                ),
            ):
                continue
            if called_runtime_names & _statement_binding_names(module_node):
                possible_abort = any(
                    _pytest_collection_abort_callable_name(
                        child,
                        runtime_imports,
                        runtime_abort_aliases,
                    )
                    in {
                        "importorskip",
                        "skip",
                        "skip-exception",
                        "xfail",
                        "xfail-exception",
                    }
                    for child in ast.walk(module_node)
                )
                if possible_abort:
                    raise TestCorpusGuardError(
                        "dynamic runtime abort alias cannot be inventoried safely"
                    )
            continue
        for target in targets:
            for alias, bound_value in _paired_binding_values(target, value):
                runtime_abort_aliases.pop(alias, None)
                abort_name = (
                    "getattr"
                    if _is_builtin_getattr_reference(
                        bound_value,
                        runtime_imports,
                        runtime_abort_aliases,
                    )
                    else (
                        "vars"
                        if _is_builtin_vars_reference(
                            bound_value,
                            runtime_imports,
                            runtime_abort_aliases,
                        )
                        else (
                            "pytest-namespace"
                            if _is_pytest_namespace_reference(
                                bound_value,
                                runtime_imports,
                                runtime_abort_aliases,
                            )
                            else _pytest_collection_abort_callable_name(
                                bound_value,
                                runtime_imports,
                                runtime_abort_aliases,
                            )
                        )
                    )
                )
                if abort_name in {
                    "getattr",
                    "importorskip",
                    "skip",
                    "xfail",
                    "skip-exception",
                    "pytest-namespace",
                    "vars",
                    "xfail-exception",
                }:
                    runtime_abort_aliases[alias] = abort_name
    imported_runtime_abort_identities: list[str] = []
    if import_source_resolver is not None:
        runtime_module_shape_cache: dict[
            tuple[str, str],
            tuple[
                ast.Module,
                frozenset[str],
                dict[str, tuple[str, ...]],
                str,
            ],
        ] = getattr(
            import_source_resolver,
            "_uaa_runtime_module_shape_cache",
            {},
        )

        def runtime_module_shape(
            module: str,
            source: str,
        ) -> tuple[
            ast.Module,
            frozenset[str],
            dict[str, tuple[str, ...]],
            str,
        ]:
            key = (module, hashlib.sha256(source.encode("utf-8")).hexdigest())
            cached = runtime_module_shape_cache.get(key)
            if cached is not None:
                return cached
            source_text = (
                source.split("\n", 1)[1] if source.startswith("path=") else source
            )
            try:
                tree = _python_parsed_module(
                    module,
                    source_text,
                    import_source_resolver,
                )
            except SyntaxError as exc:
                raise TestCorpusGuardError(
                    "imported runtime helper dependency cannot be inventoried safely"
                ) from exc
            source_path = source.split("\n", 1)[0].removeprefix("path=")
            relative_package = module
            if not source_path.endswith("/__init__.py") and "." in module:
                relative_package = module.rsplit(".", 1)[0]
            shape = (
                tree,
                frozenset(_python_module_bindings(tree)),
                _python_import_modules(
                    tree,
                    relative_package=relative_package,
                ),
                relative_package,
            )
            runtime_module_shape_cache[key] = shape
            return shape

        def runtime_import_target(
            local_root: str,
            candidates: tuple[str, ...],
            attributes: tuple[str, ...],
        ) -> tuple[str, str] | None:
            resolved_targets: set[tuple[str, str]] = set()
            for candidate in candidates:
                remaining = list(attributes)
                candidate_parts = candidate.split(".")
                if attributes == (local_root,) and local_root != candidate_parts[0]:
                    remaining = [
                        _binding_name_for_resolved_import(
                            candidates,
                            candidate,
                            local_root,
                        )
                    ]
                if local_root == candidate_parts[0]:
                    imported_suffix = candidate_parts[1:]
                    if remaining[: len(imported_suffix)] != imported_suffix:
                        continue
                    del remaining[: len(imported_suffix)]
                current_module = candidate
                current_source = import_source_resolver(current_module)
                if current_source is None:
                    continue
                while len(remaining) > 1:
                    (
                        current_tree,
                        current_bindings,
                        current_imports,
                        current_package,
                    ) = runtime_module_shape(current_module, current_source)
                    member = remaining[0]
                    nested_module = f"{current_module}.{remaining[0]}"
                    statically_bound = member in current_bindings
                    exported_as_module = any(
                        nested_module in imported_candidates
                        for imported_candidates in current_imports.values()
                    ) or nested_module in _python_lazy_export_binding_modules(
                        current_tree,
                        relative_package=current_package,
                        binding_name=member,
                    )
                    if statically_bound and exported_as_module:
                        raise TestCorpusGuardError(
                            "imported runtime helper dependency is ambiguous"
                        )
                    nested_source = (
                        import_source_resolver(nested_module)
                        if exported_as_module and not statically_bound
                        else None
                    )
                    if nested_source is None:
                        break
                    current_module = nested_module
                    current_source = nested_source
                    remaining.pop(0)
                if remaining:
                    resolved_targets.add((current_module, remaining[0]))
            if not resolved_targets:
                return None
            greatest_depth = max(
                module.count(".") for module, _name in resolved_targets
            )
            most_specific = {
                target
                for target in resolved_targets
                if target[0].count(".") == greatest_depth
            }
            if len(most_specific) != 1:
                raise TestCorpusGuardError(
                    "imported runtime helper dependency is ambiguous"
                )
            return next(iter(most_specific))

        def imported_attribute_parts(
            value: ast.Name | ast.Attribute,
        ) -> tuple[str, tuple[str, ...]]:
            attributes: list[str] = []
            current: ast.AST = value
            while isinstance(current, ast.Attribute):
                attributes.append(current.attr)
                current = current.value
            if not isinstance(current, ast.Name):
                return "", ()
            attributes.reverse()
            return current.id, tuple(attributes)

        runtime_import_aliases: dict[str, tuple[str, str]] = {}
        for execution_node in function_execution_nodes:
            if not isinstance(
                execution_node,
                (ast.Assign, ast.AnnAssign, ast.NamedExpr),
            ):
                continue
            owner_scope = execution_node_scopes.get(id(execution_node), node)
            value = execution_node.value
            targets = (
                execution_node.targets
                if isinstance(execution_node, ast.Assign)
                else (execution_node.target,)
            )
            for target in targets:
                for alias, bound_value in _paired_binding_values(target, value):
                    runtime_import_aliases.pop(alias, None)
                    imported_alias: tuple[str, str] | None = None
                    if isinstance(bound_value, ast.Name):
                        imported_alias = runtime_import_aliases.get(bound_value.id)
                        _is_owned, candidates = runtime_scope_import_candidates(
                            owner_scope,
                            bound_value.id,
                        )
                        if imported_alias is None and candidates:
                            imported_alias = runtime_import_target(
                                bound_value.id,
                                candidates,
                                (bound_value.id,),
                            )
                    elif isinstance(bound_value, ast.Attribute):
                        root, attributes = imported_attribute_parts(bound_value)
                        _is_owned, candidates = runtime_scope_import_candidates(
                            owner_scope,
                            root,
                        )
                        if candidates:
                            imported_alias = runtime_import_target(
                                root,
                                candidates,
                                attributes,
                            )
                    if imported_alias is not None:
                        runtime_import_aliases[alias] = imported_alias
        imported_calls: set[tuple[str, str]] = set()
        active_module_runtime_imports = dict(module_runtime_imports)
        for execution_node in function_execution_nodes:
            if not isinstance(execution_node, ast.Call):
                continue
            owner_scope = execution_node_scopes.get(id(execution_node), node)
            call_target = callable_container_targets_by_call_id.get(
                id(execution_node),
                execution_node.func,
            )
            if isinstance(call_target, ast.Name):
                imported_alias = runtime_import_aliases.get(call_target.id)
                if imported_alias is not None:
                    imported_calls.add(imported_alias)
                else:
                    _is_owned, candidates = runtime_scope_import_candidates(
                        owner_scope,
                        call_target.id,
                        module_imports=active_module_runtime_imports,
                    )
                    if candidates:
                        imported_target = runtime_import_target(
                            call_target.id,
                            candidates,
                            (call_target.id,),
                        )
                        if imported_target is not None:
                            imported_calls.add(imported_target)
            elif isinstance(call_target, ast.Attribute):
                root, attributes = imported_attribute_parts(call_target)
                if root:
                    _is_owned, candidates = runtime_scope_import_candidates(
                        owner_scope,
                        root,
                        module_imports=active_module_runtime_imports,
                    )
                    if candidates:
                        imported_target = runtime_import_target(
                            root,
                            candidates,
                            attributes,
                        )
                        if imported_target is not None:
                            imported_calls.add(imported_target)
            called_helper = called_helpers_by_call_id.get(id(execution_node))
            if called_helper is not None:
                called_helper_imports = helper_global_runtime_imports_by_scope.get(
                    id(called_helper),
                    {},
                )
                if (
                    called_helper_imports
                    and id(execution_node)
                    in conditional_execution_node_ids_by_scope[id(owner_scope)]
                ):
                    raise TestCorpusGuardError(
                        "conditional global runtime import installer cannot be inventoried safely"
                    )
                for name, candidates in called_helper_imports.items():
                    active_module_runtime_imports[name] = candidates
        for imported_module, imported_name in sorted(imported_calls):
            imported_source = import_source_resolver(imported_module)
            if imported_source is None:
                continue
            try:
                imported_identity = _python_imported_binding_source(
                    imported_module,
                    imported_source,
                    imported_name,
                    import_source_resolver,
                )
            except TestCorpusGuardError as exc:
                if (
                    (
                        "binding cannot be resolved" in str(exc)
                        or "parameter data is circular" in str(exc)
                    )
                    and "xfail" not in imported_source
                    and "pytest.skip" not in imported_source
                    and "pytest.importorskip" not in imported_source
                ):
                    continue
                raise
            if "runtime-abort-posture=true" in imported_identity.splitlines():
                imported_runtime_abort_identities.append(imported_identity)
    direct_runtime_node_ids = {id(item) for item in node.body}
    for helper in expanded_helpers.values():
        direct_runtime_node_ids.update(id(item) for item in helper.body)
    for execution_node in function_execution_nodes:
        if id(execution_node) in direct_runtime_node_ids or not isinstance(
            execution_node,
            (ast.Assign, ast.AnnAssign, ast.NamedExpr),
        ):
            continue
        value = execution_node.value
        targets = (
            execution_node.targets
            if isinstance(execution_node, ast.Assign)
            else (execution_node.target,)
        )
        target_names = {
            name for target in targets for name in _binding_target_names(target)
        }
        possible_abort = _pytest_collection_abort_callable_name(
            value,
            runtime_imports,
            runtime_abort_aliases,
        ) in {
            "exit",
            "importorskip",
            "skip",
            "skip-exception",
            "xfail",
            "xfail-exception",
        }
        if called_runtime_names & target_names and possible_abort:
            raise TestCorpusGuardError(
                "dynamic runtime abort alias cannot be inventoried safely"
            )
    for _alias_pass in range(1):
        for execution_node in function_execution_nodes:
            if not isinstance(
                execution_node,
                (ast.Assign, ast.AnnAssign, ast.NamedExpr),
            ):
                continue
            value = execution_node.value
            if value is None:
                continue
            targets = (
                execution_node.targets
                if isinstance(execution_node, ast.Assign)
                else (execution_node.target,)
            )
            for target in targets:
                for alias, bound_value in _paired_binding_values(target, value):
                    bound_root = _root_name(bound_value)
                    if bound_root is not None and "pytest" in runtime_imports.get(
                        bound_root, ()
                    ):
                        candidates = tuple(
                            dict.fromkeys((*runtime_imports.get(alias, ()), "pytest"))
                        )
                        if runtime_imports.get(alias) != candidates:
                            runtime_imports[alias] = candidates
                            pass
                    abort_name = (
                        "getattr"
                        if _is_builtin_getattr_reference(
                            bound_value,
                            runtime_imports,
                            runtime_abort_aliases,
                        )
                        else (
                            "vars"
                            if _is_builtin_vars_reference(
                                bound_value,
                                runtime_imports,
                                runtime_abort_aliases,
                            )
                            else (
                                "pytest-namespace"
                                if _is_pytest_namespace_reference(
                                    bound_value,
                                    runtime_imports,
                                    runtime_abort_aliases,
                                )
                                else (
                                    f"{abort_name}-exception"
                                    if isinstance(bound_value, ast.Attribute)
                                    and bound_value.attr == "Exception"
                                    and (
                                        abort_name
                                        := _pytest_collection_abort_callable_name(
                                            bound_value.value,
                                            runtime_imports,
                                            runtime_abort_aliases,
                                        )
                                    )
                                    in {"skip", "xfail"}
                                    else _pytest_collection_abort_callable_name(
                                        bound_value,
                                        runtime_imports,
                                        runtime_abort_aliases,
                                    )
                                )
                            )
                        )
                    )
                    if abort_name in {
                        "exit",
                        "getattr",
                        "importorskip",
                        "skip",
                        "xfail",
                        "skip-exception",
                        "pytest-namespace",
                        "vars",
                        "xfail-exception",
                    } and (runtime_abort_aliases.get(alias) != abort_name):
                        runtime_abort_aliases[alias] = abort_name
                    elif abort_name == "":
                        runtime_abort_aliases.pop(alias, None)

    for alias in sorted(tracked_callable_instance_aliases):
        reference = ast.Name(id=alias, ctx=ast.Load())
        if maybe_callable(reference) and not is_non_aborting_local_callable(reference):
            runtime_abort_aliases[alias] = "xfail"
        elif alias in callable_instance_lineage:
            runtime_abort_aliases.pop(alias, None)
    for alias, abort_name in container_abort_aliases.items():
        if alias in tracked_callable_instance_aliases:
            continue
        if abort_name in {
            "exit",
            "importorskip",
            "skip",
            "xfail",
            "skip-exception",
            "xfail-exception",
        }:
            runtime_abort_aliases.setdefault(alias, abort_name)
    for alias, captured_value in module_callable_values.items():
        if alias in tracked_callable_instance_aliases:
            continue
        abort_name = _pytest_collection_abort_callable_name(
            captured_value,
            runtime_imports,
            runtime_abort_aliases,
        )
        if abort_name in {
            "exit",
            "importorskip",
            "skip",
            "xfail",
            "skip-exception",
            "xfail-exception",
        }:
            runtime_abort_aliases[alias] = abort_name
        else:
            runtime_abort_aliases.pop(alias, None)

    runtime_unittest_namespace_aliases = {
        name
        for name, candidates in runtime_imports.items()
        if any(candidate in {"unittest", "unittest.case"} for candidate in candidates)
    }
    runtime_unittest_skip_aliases = {
        name
        for name, candidates in runtime_imports.items()
        if any(
            candidate in {"unittest.SkipTest", "unittest.case.SkipTest"}
            for candidate in candidates
        )
    }
    for _alias_pass in range(2):
        for execution_node in function_execution_nodes:
            if not isinstance(
                execution_node,
                (ast.Assign, ast.AnnAssign, ast.NamedExpr),
            ):
                continue
            targets = (
                execution_node.targets
                if isinstance(execution_node, ast.Assign)
                else (execution_node.target,)
            )
            value = execution_node.value
            root = _root_name(value)
            namespace_value = (
                isinstance(value, ast.Name)
                and value.id in runtime_unittest_namespace_aliases
            ) or (
                isinstance(value, ast.Attribute)
                and value.attr == "case"
                and root in runtime_unittest_namespace_aliases
            )
            skip_value = _unittest_skiptest_reference(
                value,
                runtime_imports,
                runtime_unittest_skip_aliases,
                runtime_unittest_namespace_aliases,
            )
            for target in targets:
                for alias, bound_value in _paired_binding_values(target, value):
                    if namespace_value:
                        runtime_unittest_namespace_aliases.add(alias)
                    if skip_value:
                        runtime_unittest_skip_aliases.add(alias)
    runtime_unittest_method_skip_call_ids: set[int] = set()

    def is_bound_unittest_skip_method(value: ast.AST) -> bool:
        if isinstance(value, ast.Attribute) and value.attr == "skipTest":
            return True
        return (
            isinstance(value, ast.Call)
            and _is_builtin_getattr_reference(
                value.func,
                runtime_imports,
                runtime_abort_aliases,
            )
            and len(value.args) in {2, 3}
            and not value.keywords
            and isinstance(value.args[1], ast.Constant)
            and value.args[1].value == "skipTest"
        )

    for function_scope in function_scopes:
        method_skip_aliases: set[str] = set()
        conditional_node_ids = conditional_execution_node_ids_by_scope[
            id(function_scope)
        ]
        for execution_node in scope_execution_nodes_by_scope[id(function_scope)]:
            if isinstance(
                execution_node,
                (ast.Assign, ast.AnnAssign, ast.NamedExpr),
            ):
                targets = (
                    execution_node.targets
                    if isinstance(execution_node, ast.Assign)
                    else (execution_node.target,)
                )
                for target in targets:
                    for alias, bound_value in _paired_binding_values(
                        target,
                        execution_node.value,
                    ):
                        if is_bound_unittest_skip_method(bound_value) or (
                            isinstance(bound_value, ast.Name)
                            and bound_value.id in method_skip_aliases
                        ):
                            method_skip_aliases.add(alias)
                        elif id(execution_node) not in conditional_node_ids:
                            method_skip_aliases.discard(alias)
                continue
            if not isinstance(execution_node, ast.Call):
                continue
            call_target = callable_container_targets_by_call_id.get(
                id(execution_node),
                execution_node.func,
            )
            if (
                isinstance(call_target, ast.Name)
                and call_target.id in method_skip_aliases
            ):
                runtime_unittest_method_skip_call_ids.add(id(execution_node))

    def is_runtime_abort(execution_node: ast.AST) -> bool:
        if isinstance(execution_node, ast.Call):
            call_target = callable_container_targets_by_call_id.get(
                id(execution_node),
                execution_node.func,
            )
            abort_name = _pytest_collection_abort_callable_name(
                call_target,
                runtime_imports,
                runtime_abort_aliases,
            )
            if abort_name == "exit":
                return _is_pytest_collection_abort_call(
                    ast.Call(
                        func=call_target,
                        args=execution_node.args,
                        keywords=execution_node.keywords,
                    ),
                    runtime_imports,
                    runtime_abort_aliases,
                )
            if abort_name in {
                "importorskip",
                "skip",
                "xfail",
                "skip-exception",
                "xfail-exception",
            }:
                return True
            if (
                isinstance(call_target, ast.Attribute)
                and call_target.attr == "skipTest"
            ):
                return True
            if id(execution_node) in runtime_unittest_method_skip_call_ids:
                return True
            if isinstance(call_target, ast.Name):
                captured = module_callable_values.get(call_target.id)
                if isinstance(captured, ast.Lambda):
                    return any(
                        isinstance(child, ast.Call)
                        and (
                            _pytest_collection_abort_callable_name(
                                child.func,
                                runtime_imports,
                                runtime_abort_aliases,
                            )
                            in {
                                "importorskip",
                                "skip",
                                "skip-exception",
                                "xfail",
                                "xfail-exception",
                            }
                            or _is_pytest_collection_abort_call(
                                child,
                                runtime_imports,
                                runtime_abort_aliases,
                            )
                        )
                        for child in ast.walk(captured.body)
                    )
            return False
        if not isinstance(execution_node, ast.Raise) or execution_node.exc is None:
            return False
        raised = execution_node.exc
        raised_reference = raised.func if isinstance(raised, ast.Call) else raised
        if _unittest_skiptest_reference(
            raised_reference,
            runtime_imports,
            runtime_unittest_skip_aliases,
            runtime_unittest_namespace_aliases,
        ):
            return True
        if isinstance(raised, ast.Attribute) and raised.attr == "Exception":
            return _pytest_collection_abort_callable_name(
                raised.value,
                runtime_imports,
                runtime_abort_aliases,
            ) in {"skip", "xfail"}
        if isinstance(raised, ast.Call):
            return (
                _pytest_collection_abort_callable_name(
                    raised,
                    runtime_imports,
                    runtime_abort_aliases,
                )
                in {"skip-exception", "xfail-exception"}
            )
        return (
            isinstance(raised, ast.Name)
            and runtime_abort_aliases.get(raised.id)
            in {"skip-exception", "xfail-exception"}
        )

    has_runtime_abort = any(
        is_runtime_abort(execution_node) for execution_node in function_execution_nodes
    )
    if (
        not identity_decorators
        and not requested_fixture_names
        and not module_side_effect_identities
        and not has_runtime_abort
        and not expanded_helpers
        and not imported_runtime_abort_identities
    ):
        return raw_ref
    serialized_parts = [
        ast.dump(decorator, annotate_fields=True, include_attributes=False)
        for decorator in identity_decorators
    ]
    serialized_parts.extend(module_side_effect_identities)
    if has_runtime_abort:
        serialized_parts.append(
            "runtime-abort="
            + ast.dump(node, annotate_fields=True, include_attributes=False)
        )
        primary_scope_id = id(node)
        runtime_referenced_names = {
            scope_node.id
            for scope_node in scope_execution_nodes_by_scope[primary_scope_id]
            if isinstance(scope_node, ast.Name)
        }
        for referenced_name in sorted(runtime_referenced_names):
            is_global = referenced_name in scope_globals_by_scope[primary_scope_id]
            is_local = referenced_name in local_runtime_bindings_by_scope[
                primary_scope_id
            ]
            if referenced_name in module_bindings and (is_global or not is_local):
                serialized_parts.append(
                    "runtime-abort-binding="
                    + _python_local_binding_identity(
                        referenced_name,
                        module_bindings,
                        imported_modules,
                        {},
                    )
                )

    def runtime_helper_identity(
        helper: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> str:
        helper_scope_id = id(helper)
        helper_has_runtime_abort = any(
            is_runtime_abort(scope_node)
            for scope_node in scope_execution_nodes_by_scope[helper_scope_id]
        )
        helper_parts = [
            ast.dump(helper, annotate_fields=True, include_attributes=False)
        ]
        referenced_names = {
            scope_node.id
            for scope_node in scope_execution_nodes_by_scope[helper_scope_id]
            if isinstance(scope_node, ast.Name)
        }
        closure_binding_nodes: list[ast.AST] = []
        for referenced_name in sorted(referenced_names):
            is_global = referenced_name in scope_globals_by_scope[helper_scope_id]
            is_nonlocal = referenced_name in scope_nonlocals_by_scope[helper_scope_id]
            is_local = (
                referenced_name in local_runtime_bindings_by_scope[helper_scope_id]
            )
            has_enclosing_binding = False
            enclosing_bindings: tuple[ast.AST, ...] = ()
            if not is_global and (is_nonlocal or not is_local):
                has_enclosing_binding, enclosing_bindings = (
                    enclosing_scope_binding_nodes(helper, referenced_name)
                )
            if has_enclosing_binding:
                for local_binding in enclosing_bindings:
                    closure_binding_nodes.append(local_binding)
                    helper_parts.append(
                        "closure="
                        + ast.dump(
                            local_binding,
                            annotate_fields=True,
                            include_attributes=False,
                        )
                    )
                continue
            if is_local and not is_global:
                continue
            if referenced_name in module_bindings:
                helper_parts.append(
                    _python_local_binding_identity(
                        referenced_name,
                        module_bindings,
                        imported_modules,
                        {},
                    )
                )
        if import_source_resolver is not None:
            helper_import_requirements = runtime_scope_import_requirements(helper)
            for closure_binding in closure_binding_nodes:
                if not isinstance(
                    closure_binding,
                    (ast.Assign, ast.AnnAssign, ast.NamedExpr),
                ):
                    continue
                for root, names in _python_import_requirements(
                    closure_binding.value,
                    imported_modules,
                ).items():
                    binding_scope = execution_node_scopes.get(
                        id(closure_binding),
                        node,
                    )
                    _is_owned, candidates = runtime_scope_import_candidates(
                        binding_scope,
                        root,
                    )
                    if candidates:
                        helper_import_requirements.setdefault(
                            candidates,
                            set(),
                        ).update(names)
            for candidates, names in sorted(helper_import_requirements.items()):
                resolved = [
                    (candidate, imported_source)
                    for candidate in candidates
                    if (imported_source := import_source_resolver(candidate))
                    is not None
                ]
                module_counts: dict[str, int] | None = getattr(
                    import_source_resolver,
                    "_uaa_local_python_module_counts",
                    None,
                )
                if (
                    len(resolved) > 1
                    and module_counts is not None
                    and candidates
                    and module_counts.get(candidates[0], 0)
                ):
                    resolved = [item for item in resolved if item[0] == candidates[0]]
                elif (
                    len(resolved) > 1
                    and module_counts is not None
                    and candidates
                    and module_counts.get(candidates[-1], 0)
                ):
                    resolved = [item for item in resolved if item[0] == candidates[-1]]
                if len(resolved) > 1:
                    raise TestCorpusGuardError(
                        "imported runtime helper dependency is ambiguous"
                    )
                if not resolved:
                    helper_parts.append(
                        f"external-import={','.join(candidates)};"
                        f"bindings={','.join(sorted(names))}"
                    )
                    continue
                imported_module, imported_source = resolved[0]
                module_object_names = {
                    name
                    for name in names
                    if name == imported_module.rsplit(".", 1)[-1]
                    and candidates
                    and imported_module == candidates[0]
                }
                if module_object_names:
                    imported_module_identity = _python_module_dependency_identity(
                        imported_module,
                        imported_source,
                        import_source_resolver,
                    )
                    if (
                        "runtime-abort-posture=true"
                        in imported_module_identity.splitlines()
                    ):
                        helper_parts.append(imported_module_identity)
                for imported_name in sorted(names):
                    resolved_name = _binding_name_for_resolved_import(
                        candidates,
                        imported_module,
                        imported_name,
                    )
                    try:
                        imported_identity = _python_imported_binding_source(
                            imported_module,
                            imported_source,
                            resolved_name,
                            import_source_resolver,
                        )
                        if helper_has_runtime_abort or (
                            "runtime-abort-posture=true"
                            in imported_identity.splitlines()
                        ):
                            helper_parts.append(imported_identity)
                    except TestCorpusGuardError as exc:
                        if not any(
                            marker in str(exc)
                            for marker in (
                                "parameter data is circular",
                                "binding cannot be resolved",
                            )
                        ):
                            raise
                        if helper_has_runtime_abort:
                            helper_parts.append(
                                f"runtime-import-fallback={imported_module};"
                                f"binding={resolved_name};source-sha256="
                                f"{hashlib.sha256(imported_source.encode('utf-8')).hexdigest()}"
                            )
        identity = "\n".join(dict.fromkeys(helper_parts))
        if (
            normalize_non_aborting_runtime_helpers
            and not helper_has_runtime_abort
            and "runtime-abort-posture=true" not in identity.splitlines()
        ):
            return f"non-aborting-runtime-helper={helper.name}"
        return identity

    serialized_parts.extend(
        "runtime-helper=" + runtime_helper_identity(helper)
        for helper in expanded_helpers.values()
    )
    serialized_parts.extend(
        f"runtime-abort-import={identity}"
        for identity in imported_runtime_abort_identities
    )
    if requested_fixture_names:
        if fixture_argument_names:
            serialized_parts.append(
                "fixture-arguments=" + ",".join(fixture_argument_names)
            )
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
        for fixture_name in requested_fixture_names:
            candidates = imported_modules.get(fixture_name)
            local_fixture = (
                local_fixture_resolver(fixture_name)
                if local_fixture_resolver is not None
                else None
            )
            if local_fixture is not None and has_imported_fixture_reassignment(
                fixture_name
            ):
                raise TestCorpusGuardError("imported Python fixture name is ambiguous")
            if local_fixture is not None and candidates is not None:
                raise TestCorpusGuardError("imported Python fixture name is ambiguous")
            if local_fixture is not None:
                serialized_parts.append("fixture-local=" + local_fixture)
                continue
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
                if root in relative_import_bindings:
                    raise TestCorpusGuardError(
                        "relative imported Python parameter data cannot be inventoried safely"
                    )
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
    conditional_execution_decorators = [
        decorator
        for decorator in execution_disabling_decorators
        if isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr == "skipif"
    ]
    for decorator in conditional_execution_decorators:
        if not isinstance(decorator, ast.Call):
            continue
        condition_nodes = [*decorator.args[:1]]
        condition_nodes.extend(
            keyword.value
            for keyword in decorator.keywords
            if keyword.arg == "condition"
        )
        if any(
            isinstance(condition, ast.Constant) and isinstance(condition.value, str)
            for condition in condition_nodes
        ):
            raise TestCorpusGuardError(
                "Python string skip condition cannot be inventoried safely"
            )
    conditional_execution_decorators.extend(xfail_decorators)
    for decorator in conditional_execution_decorators:
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
                        f"conditional-mark-external-import={','.join(candidates)};"
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
    binding_import_requirements: dict[str, set[str]] = {}
    for binding in binding_nodes.values():
        for root, names in _python_import_requirements(
            binding,
            imported_modules,
        ).items():
            binding_import_requirements.setdefault(root, set()).update(names)
    for root, binding_names in sorted(binding_import_requirements.items()):
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
            binding_parts.append(
                f"binding-external-import={','.join(candidates)};"
                f"bindings={','.join(sorted(binding_names))}"
            )
            continue
        module, source = resolved_import
        for binding_name in sorted(binding_names):
            binding_parts.append(
                "binding-import="
                + _python_imported_binding_source(
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
    *,
    normalize_non_aborting_runtime_helpers: bool = False,
) -> tuple[tuple[TestDeclaration, str], ...]:
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            f"cannot parse Python test inventory: {path}"
        ) from exc

    current_module = _python_module_name_for_path(path)
    relative_package = current_module
    if not path.endswith("/__init__.py") and "." in current_module:
        relative_package = current_module.rsplit(".", 1)[0]
    imported_modules = _python_import_modules(
        tree,
        relative_package=relative_package,
    )
    module_side_effect_identities: list[str] = []
    collection_binding_nodes = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete))
        and {
            name
            for target in (
                node.targets if isinstance(node, (ast.Assign, ast.Delete)) else (node.target,)
            )
            for name in _binding_target_names(target)
        }
        & {"collect_ignore", "collect_ignore_glob"}
    ]
    if collection_binding_nodes:
        collection_identity = "\n".join(
            ast.dump(node, annotate_fields=True, include_attributes=False)
            for node in collection_binding_nodes
        )
        module_side_effect_identities.append(
            "collection-binding-sha256:"
            + hashlib.sha256(collection_identity.encode("utf-8")).hexdigest()
        )
    if import_source_resolver is not None:
        execution_import_bindings = _python_import_modules(
            tree,
            relative_package=relative_package,
        )
        referenced_names = {
            child.id
            for child in ast.walk(tree)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
        }
        side_effect_modules = _python_execution_import_modules(
            tree,
            relative_package=relative_package,
            import_source_resolver=import_source_resolver,
        )
        for module in side_effect_modules:
            source = import_source_resolver(module)
            if source is None:
                continue
            import_is_referenced = any(
                local_name in referenced_names and module in candidates
                for local_name, candidates in execution_import_bindings.items()
            )
            module_side_effect_identities.append(
                "side-effect-import="
                + _python_side_effect_import_identity(
                    module,
                    source,
                    import_source_resolver,
                    include_transitive=not import_is_referenced,
                )
            )
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

    def binds_xunit_hook(nodes: list[ast.stmt], names: set[str]) -> bool:
        for node in _scope_execution_nodes(nodes):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in names:
                    return True
                continue
            if isinstance(node, ast.ImportFrom):
                if any((alias.asname or alias.name) in names for alias in node.names):
                    return True
                continue
            if isinstance(node, ast.Import):
                if any(alias.asname in names for alias in node.names):
                    return True
                continue
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                targets = (node.target,)
            else:
                continue
            if names & {
                name for target in targets for name in _binding_target_names(target)
            }:
                return True
        return False

    if binds_xunit_hook(
        tree.body,
        {"setup_module", "setup_function", "setUpModule"},
    ) or any(
        isinstance(node, ast.ClassDef)
        and binds_xunit_hook(node.body, {"setup_class", "setup_method"})
        for node in tree.body
    ):
        raise TestCorpusGuardError(
            "xunit-style pytest setup hooks cannot be inventoried safely"
        )

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

    def binds_module_getattr(candidate: ast.AST) -> bool:
        if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return candidate.name == "__getattr__"
        if isinstance(candidate, ast.ClassDef):
            return candidate.name == "__getattr__"
        if isinstance(candidate, ast.Import):
            return any(
                (imported.asname or imported.name.split(".", 1)[0]) == "__getattr__"
                for imported in candidate.names
            )
        if isinstance(candidate, ast.ImportFrom):
            return any(
                (imported.asname or imported.name) == "__getattr__"
                for imported in candidate.names
            )
        if isinstance(candidate, ast.Assign):
            targets = candidate.targets
        elif isinstance(candidate, ast.AnnAssign) and candidate.value is not None:
            targets = (candidate.target,)
        elif isinstance(candidate, ast.NamedExpr):
            targets = (candidate.target,)
        else:
            return False
        return any("__getattr__" in _binding_target_names(target) for target in targets)

    if any(binds_module_getattr(node) for node in _module_execution_nodes(tree)):
        raise TestCorpusGuardError(
            "dynamic module attributes cannot be inventoried safely"
        )
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
    if any(
        class_node.name in unittest_classes
        and binds_xunit_hook(
            class_node.body,
            {
                "asyncSetUp",
                "asyncTearDown",
                "setUp",
                "setUpClass",
                "tearDown",
                "tearDownClass",
            },
        )
        for class_node in classes.values()
    ):
        raise TestCorpusGuardError(
            "unittest lifecycle hooks cannot be inventoried safely"
        )
    module_bindings = _python_module_bindings(tree)
    parametrize_aliases = _parametrize_aliases(tree)
    fixture_aliases = _fixture_aliases(tree)
    local_fixture_bindings = _python_local_fixture_bindings(tree)
    local_fixture_identity_cache: dict[str, str] = {}

    def local_fixture_identity(fixture_name: str) -> str | None:
        binding_name = local_fixture_bindings.get(fixture_name)
        if binding_name is None:
            return None
        identity = local_fixture_identity_cache.get(binding_name)
        if identity is None:
            identity = _python_local_binding_identity(
                binding_name,
                module_bindings,
                imported_modules,
                local_fixture_bindings,
            )
            local_fixture_identity_cache[binding_name] = identity
        return identity

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
            imported_tree = _python_parsed_module(
                module,
                source_text,
                import_source_resolver,
            )
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
    local_classes = {
        node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
    }

    def collected_test_methods(class_name: str, visiting: frozenset[str]) -> set[str]:
        if class_name in visiting:
            return set()
        class_node = local_classes[class_name]
        next_visiting = visiting | {class_name}
        methods = {
            child.name
            for child in class_node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name.startswith("test")
        }
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in local_classes:
                methods.update(collected_test_methods(base.id, next_visiting))
        return methods

    collected_execution_mark_targets = collected_binding_names | {
        f"{class_name}.{method_name}"
        for class_name in collected_binding_names
        if class_name in local_classes
        for method_name in collected_test_methods(class_name, frozenset())
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
    if (
        _post_definition_execution_mark_targets(tree, imported_modules)
        & collected_execution_mark_targets
    ):
        raise TestCorpusGuardError(
            "post-definition Python execution mark cannot be inventoried safely"
        )
    if _helper_mediated_test_flag_targets(tree) & collected_binding_names:
        raise TestCorpusGuardError(
            "dynamic Python function __test__ mutation cannot be inventoried safely"
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

    def class_has_local_fixture_binding(
        class_node: ast.ClassDef,
        visiting: set[str],
    ) -> bool:
        if class_node.name in visiting:
            raise TestCorpusGuardError(
                f"cannot resolve Python test class inheritance: {path}"
            )
        functions = {
            child.name: child
            for child in class_node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        if any(fixture_decorated(function) for function in functions.values()):
            return True
        function_aliases = set(functions)
        configured_factories: set[str] = set()
        changed = True
        while changed:
            changed = False
            for child in _scope_execution_nodes(class_node.body):
                if not isinstance(child, (ast.Assign, ast.AnnAssign)):
                    continue
                value = child.value
                if value is None:
                    continue
                targets = (
                    child.targets if isinstance(child, ast.Assign) else (child.target,)
                )
                for target in targets:
                    for target_name, bound_value in _paired_binding_values(
                        target, value
                    ):
                        if (
                            isinstance(bound_value, ast.Name)
                            and bound_value.id in function_aliases
                            and target_name not in function_aliases
                        ):
                            function_aliases.add(target_name)
                            changed = True
                        if _is_fixture_callable(bound_value, fixture_aliases):
                            is_factory = True
                        elif isinstance(bound_value, ast.Call) and _is_fixture_callable(
                            bound_value.func, fixture_aliases
                        ):
                            is_factory = not bound_value.args
                        elif (
                            isinstance(bound_value, ast.Name)
                            and bound_value.id in configured_factories
                        ):
                            is_factory = True
                        else:
                            continue
                        if is_factory and target_name not in configured_factories:
                            configured_factories.add(target_name)
                            changed = True
        for child in _scope_execution_nodes(class_node.body):
            if not isinstance(child, ast.Call) or not child.args:
                continue
            if _is_fixture_callable(child.func, fixture_aliases):
                pass
            elif isinstance(child.func, ast.Call) and _is_fixture_callable(
                child.func.func, fixture_aliases
            ):
                pass
            elif (
                isinstance(child.func, ast.Name)
                and child.func.id in configured_factories
            ):
                pass
            else:
                continue
            if any(
                (root := _root_name(argument)) is not None and root in function_aliases
                for argument in child.args
            ):
                return True
        return any(
            class_has_local_fixture_binding(
                classes[base.id],
                {*visiting, class_node.name},
            )
            for base in class_node.bases
            if isinstance(base, ast.Name) and base.id in classes
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
                    tree,
                    module_bindings,
                    parametrize_aliases,
                    imported_modules,
                    import_source_resolver,
                    fixture_override_matches,
                    local_fixture_identity,
                    container_decorators=tuple(module_pytestmark_decorators),
                    module_side_effect_identities=tuple(module_side_effect_identities),
                    relative_package=relative_package,
                    normalize_non_aborting_runtime_helpers=(
                        normalize_non_aborting_runtime_helpers
                    ),
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
        if class_has_local_fixture_binding(node, set()):
            raise TestCorpusGuardError(
                "class-local pytest fixtures cannot be inventoried safely"
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
                tree,
                module_bindings,
                parametrize_aliases,
                imported_modules,
                import_source_resolver,
                fixture_override_matches,
                local_fixture_identity,
                container_decorators=class_decorators,
                collection_lineno=node.lineno,
                shadowed_import_names=frozenset(class_shadowed_import_names),
                module_side_effect_identities=tuple(module_side_effect_identities),
                relative_package=relative_package,
                normalize_non_aborting_runtime_helpers=(
                    normalize_non_aborting_runtime_helpers
                ),
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


def _python_modules_with_package_ancestors(modules: set[str]) -> set[str]:
    expanded = set(modules)
    for module in modules:
        parts = module.split(".")
        expanded.update(".".join(parts[:index]) for index in range(1, len(parts)))
    return expanded


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
    include_dynamic: bool = False,
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
            lazy_export_modules = _python_lazy_export_modules(
                tree,
                relative_package=relative_package,
            )
            grouped_export_modules = _python_grouped_lazy_export_modules(tree)
            imported_module_names.update(lazy_export_modules)
            imported_module_names.update(grouped_export_modules)
            if include_dynamic:
                imported_module_names.update(
                    _dynamic_python_import_modules(
                        tree,
                        imported_modules,
                        relative_package=relative_package,
                        lazy_export_modules=tuple(
                            (*lazy_export_modules, *grouped_export_modules)
                        ),
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
    source_cache: dict[str, str | None] = {}

    def resolve(module: str) -> str | None:
        if module in source_cache:
            return source_cache[module]
        resolved = [
            f"path={candidate}\n{source}"
            for candidate in _python_module_candidates(module)
            if (source := read_text(candidate)) is not None
        ]
        if len(resolved) > 1:
            raise TestCorpusGuardError("imported Python parameter data is ambiguous")
        result = resolved[0] if resolved else None
        source_cache[module] = result
        return result

    setattr(resolve, "_uaa_module_identity_cache", {})
    setattr(resolve, "_uaa_source_cache", source_cache)
    setattr(resolve, "_uaa_parsed_module_cache", {})
    setattr(resolve, "_uaa_binding_identity_cache", {})
    setattr(resolve, "_uaa_binding_module_analysis_cache", {})
    setattr(resolve, "_uaa_root_binding_identity_cache", {})
    setattr(resolve, "_uaa_runtime_module_shape_cache", {})
    setattr(resolve, "_uaa_side_effect_identity_cache", {})
    setattr(resolve, "_uaa_side_effect_dependency_cache", {})
    setattr(resolve, "_uaa_side_effect_effect_cache", {})
    setattr(resolve, "_uaa_autouse_fixture_cache", {})

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
    if (
        suffix in FRONTEND_TEST_EXTENSIONS
        or suffix in FRONTEND_EXACT_DEPENDENCY_EXTENSIONS
    ):
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
    initializer_cache: dict[str, str] | None = None,
    runtime_dependency_cache: dict[str, frozenset[str]] | None = None,
) -> Callable[[str, str], str | None]:
    def resolve(module: str, imported_name: str) -> str | None:
        resolved: list[str] = []
        for candidate in _relative_frontend_import_candidates(importing_path, module):
            source = read_text(candidate)
            if source is None:
                continue
            if imported_name == MODULE_INITIALIZER_BINDING:
                if initializer_cache is not None and candidate in initializer_cache:
                    resolved.append(initializer_cache[candidate])
                    continue
                dependency_paths = _frontend_runtime_dependency_paths(
                    {candidate},
                    read_text,
                    runtime_dependency_cache,
                )
                initialization_sources = [(candidate, source)]
                initialization_sources.extend(
                    (dependency, dependency_source)
                    for dependency in sorted(dependency_paths)
                    if dependency != candidate
                    and (dependency_source := read_text(dependency)) is not None
                )
                initialization_source = (
                    "\n".join(
                        f"path={path}\n{frontend_runtime_identity_source(dependency_source)}"
                        for path, dependency_source in initialization_sources
                    )
                    if any(
                        frontend_runtime_test_posture(dependency_source)
                        for _path, dependency_source in initialization_sources
                    )
                    else MODULE_INITIALIZER_INERT
                )
                if initializer_cache is not None:
                    initializer_cache[candidate] = initialization_source
                resolved.append(initialization_source)
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


def _frontend_runtime_dependency_paths(
    roots: set[str],
    read_text: Callable[[str], str | None],
    dependency_cache: dict[str, frozenset[str]] | None = None,
) -> set[str]:
    adjacency_cache = dependency_cache if dependency_cache is not None else {}

    def direct_dependencies(path: str) -> frozenset[str]:
        cached = adjacency_cache.get(path)
        if cached is not None:
            return cached
        source = read_text(path)
        if source is None:
            return frozenset()
        try:
            modules = frontend_runtime_import_modules(source)
        except FrontendInventoryError as exc:
            raise TestCorpusGuardError(str(exc)) from None
        dependencies = {
            candidate
            for module in modules
            for candidate in _relative_frontend_import_candidates(path, module)
            if read_text(candidate) is not None
        }
        result = frozenset(dependencies)
        adjacency_cache[path] = result
        return result

    dependencies: set[str] = set()
    pending = list(sorted(roots))
    visited: set[str] = set()
    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        if len(visited) > MAX_FRONTEND_DEPENDENCY_MODULES:
            raise TestCorpusGuardError(
                "frontend runtime import closure exceeds module budget"
            )
        direct = direct_dependencies(path)
        dependencies.update(direct)
        pending.extend(direct - visited)
    return dependencies


def _parse_worktree_test_declarations(
    repo: Path,
    path: str,
    text: str,
    python_import_source_resolver: Callable[[str], str | None] | None = None,
    frontend_source_cache: dict[str, str | None] | None = None,
    frontend_initializer_cache: dict[str, str] | None = None,
    frontend_runtime_dependency_cache: dict[str, frozenset[str]] | None = None,
) -> tuple[TestDeclaration, ...]:
    if path.endswith(".py"):

        def read_python_import(candidate: str) -> str | None:
            target = repo / candidate
            if not target.is_file() or not _worktree_path_has_exact_case(
                repo, candidate
            ):
                return None
            return _read_worktree_text(repo, candidate)

        return tuple(
            declaration
            for declaration, _source in _python_inventory_entries(
                path,
                text,
                python_import_source_resolver
                or _python_import_resolver(read_python_import),
            )
        )

    def read_import(candidate: str) -> str | None:
        if frontend_source_cache is not None and candidate in frontend_source_cache:
            return frontend_source_cache[candidate]
        target = repo / candidate
        if not target.is_file() or not _worktree_path_has_exact_case(repo, candidate):
            if frontend_source_cache is not None:
                frontend_source_cache[candidate] = None
            return None
        source = _read_worktree_text(repo, candidate)
        if frontend_source_cache is not None:
            frontend_source_cache[candidate] = source
        return source

    try:
        refs = parse_frontend_refs(
            path,
            text,
            _frontend_import_resolver(
                path,
                read_import,
                frontend_initializer_cache,
                frontend_runtime_dependency_cache,
            ),
        )
    except FrontendInventoryError as exc:
        raise TestCorpusGuardError(str(exc)) from None
    return tuple(TestDeclaration(ref=ref, kind="frontend_test") for ref in refs)


def _parse_base_test_declarations(
    repo: Path,
    base_sha: str,
    path: str,
    text: str,
    python_import_source_resolver: Callable[[str], str | None] | None = None,
    frontend_source_cache: dict[str, str | None] | None = None,
    frontend_initializer_cache: dict[str, str] | None = None,
    frontend_runtime_dependency_cache: dict[str, frozenset[str]] | None = None,
) -> tuple[TestDeclaration, ...]:
    if path.endswith(".py"):
        return tuple(
            declaration
            for declaration, _source in _python_inventory_entries(
                path,
                text,
                python_import_source_resolver
                or _python_import_resolver(
                    lambda candidate: _base_text(repo, base_sha, candidate)
                ),
            )
        )

    def read_base_import(candidate: str) -> str | None:
        if frontend_source_cache is not None and candidate in frontend_source_cache:
            return frontend_source_cache[candidate]
        source = _base_text(repo, base_sha, candidate)
        if frontend_source_cache is not None:
            frontend_source_cache[candidate] = source
        return source

    try:
        refs = parse_frontend_refs(
            path,
            text,
            _frontend_import_resolver(
                path,
                read_base_import,
                frontend_initializer_cache,
                frontend_runtime_dependency_cache,
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


def _worktree_path_has_exact_case(repo: Path, path: str) -> bool:
    """Reject case-folded path aliases on case-insensitive filesystems."""

    current = repo
    for part in Path(path).parts:
        try:
            if part not in os.listdir(current):
                return False
        except OSError:
            return False
        current /= part
    return True


def _local_python_module_counts(repo: Path) -> dict[str, int]:
    """Index exact local module candidates without interpreting their contents."""

    counts: dict[str, int] = {}
    paths_seen = 0
    for root, directory_names, file_names in os.walk(repo, followlinks=False):
        root_path = Path(root)
        directory_names[:] = sorted(
            name
            for name in directory_names
            if not _is_discovery_ignored_directory(repo, root_path, name)
        )
        for file_name in sorted(file_names):
            if not file_name.endswith(".py"):
                continue
            path = (root_path / file_name).relative_to(repo).as_posix()
            module = _python_module_name_for_path(path)
            counts[module] = counts.get(module, 0) + 1
            paths_seen += 1
            if paths_seen > MAX_PYTHON_DEPENDENCY_MODULES:
                raise TestCorpusGuardError(
                    "Python local module index exceeds module budget"
                )
    return counts


def _inventory_worktree_snapshot(repo: Path) -> _WorktreeInventorySnapshot:
    def read_python_import(candidate: str) -> str | None:
        target = repo / candidate
        if not target.is_file() or not _worktree_path_has_exact_case(repo, candidate):
            return None
        return _read_worktree_text(repo, candidate)

    python_import_source_resolver = _python_import_resolver(read_python_import)
    setattr(
        python_import_source_resolver,
        "_uaa_local_python_module_counts",
        _local_python_module_counts(repo),
    )
    frontend_source_cache: dict[str, str | None] = {}
    frontend_initializer_cache: dict[str, str] = {}
    frontend_runtime_dependency_cache: dict[str, frozenset[str]] = {}
    declarations: list[TestDeclaration] = []
    files_by_path: dict[str, _TestFileInventory] = {}
    for path in discover_test_files(repo):
        text = _read_worktree_text(repo, path)
        parsed = _parse_worktree_test_declarations(
            repo,
            path,
            text,
            python_import_source_resolver,
            frontend_source_cache,
            frontend_initializer_cache,
            frontend_runtime_dependency_cache,
        )
        declarations.extend(parsed)
        files_by_path[path] = _TestFileInventory(
            source=text,
            declarations=parsed,
        )
    refs = [item.ref for item in declarations]
    if len(refs) != len(set(refs)):
        raise TestCorpusGuardError("test inventory contains duplicate stable refs")
    if not declarations:
        raise TestCorpusGuardError("test inventory is empty")
    return _WorktreeInventorySnapshot(
        declarations=tuple(sorted(declarations, key=lambda item: item.ref)),
        files_by_path=files_by_path,
        python_import_source_resolver=python_import_source_resolver,
    )


def inventory_worktree(repo: Path) -> tuple[TestDeclaration, ...]:
    return _inventory_worktree_snapshot(repo).declarations


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


def _comparison_merge_base(repo: Path, candidate: str, *, label: str) -> str:
    merge_base = _run_git(repo, ["merge-base", "HEAD", candidate])
    if merge_base.returncode != 0:
        raise TestCorpusGuardError(f"{label} comparison merge base is missing")
    try:
        value = merge_base.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise TestCorpusGuardError(f"{label} comparison merge base is malformed") from exc
    if SHA_PATTERN.fullmatch(value) is None:
        raise TestCorpusGuardError(f"{label} comparison merge base is malformed")
    return value


def _resolve_base_sha(repo: Path, requested: str | None) -> str | None:
    if requested is not None:
        if SHA_PATTERN.fullmatch(requested) is None:
            raise TestCorpusGuardError("test-corpus comparison base SHA is malformed")
        probe = _run_git(repo, ["cat-file", "-e", f"{requested}^{{commit}}"])
        if probe.returncode != 0:
            raise TestCorpusGuardError("test-corpus comparison base commit is missing")
        return _comparison_merge_base(repo, requested, label="test-corpus")

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
        return _comparison_merge_base(repo, value, label="canonical CI")

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


def _python_source_may_bind_autouse_fixture(source: str, name: str) -> bool:
    """Cheaply reject imported bindings that cannot be autouse fixtures."""

    source_text = source.split("\n", 1)[1] if source.startswith("path=") else source
    if "autouse" in source_text:
        return True
    escaped = re.escape(name)
    if re.search(
        rf"(?ms)^\s*from\s+[.\w]+\s+import\s+"
        rf"(?:\([^)]*\b{escaped}\b[^)]*\)|[^\n]*\b{escaped}\b)",
        source_text,
    ):
        return True
    definition = re.search(
        rf"(?m)^[ \t]*(?:async[ \t]+)?def[ \t]+{escaped}\b",
        source_text,
    )
    if definition is not None:
        prefix = source_text[max(0, definition.start() - 2_000) : definition.start()]
        if re.search(r"(?m)^[ \t]*@", prefix):
            return True
    return (
        re.search(rf"(?m)^[ \t]*{escaped}[ \t]*(?::[^=\n]+)?=", source_text) is not None
        or re.search(rf"\b[A-Za-z_]\w*\s*\(\s*{escaped}\b", source_text) is not None
    )


def _autouse_fixture_declarations(
    source: str,
    path: str,
    import_source_resolver: Callable[[str], str | None] | None = None,
    *,
    binding_names: frozenset[str] | None = None,
    _seen_imports: frozenset[tuple[str, str]] = frozenset(),
) -> tuple[str, ...]:
    if source.startswith("path="):
        source_path, source = source.split("\n", 1)
        path = source_path.removeprefix("path=")
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
                raise TestCorpusGuardError(
                    "parameterized Python fixtures cannot be inventoried safely"
                )
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

    def factory_aliases_for(
        nodes: tuple[ast.AST, ...],
        inherited: set[str] | None = None,
    ) -> set[str]:
        factory_aliases = set(inherited or ())
        changed = True
        while changed:
            changed = False
            for node in nodes:
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
                targets = (
                    node.targets if isinstance(node, ast.Assign) else (node.target,)
                )
                for target in targets:
                    for name in _binding_target_names(target):
                        if name not in factory_aliases:
                            factory_aliases.add(name)
                            changed = True
        return factory_aliases

    module_nodes = _module_execution_nodes(tree)
    factory_aliases = factory_aliases_for(module_nodes)

    def has_autouse_declaration(
        nodes: tuple[ast.AST, ...],
        functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
        aliases: set[str],
    ) -> bool:
        for function in functions.values():
            for decorator in function.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and _is_fixture_callable(decorator.func, fixture_aliases)
                    and autouse_enabled(decorator)
                ) or (isinstance(decorator, ast.Name) and decorator.id in aliases):
                    return True
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue
            factory = node.func
            if (
                (
                    isinstance(factory, ast.Call)
                    and _is_fixture_callable(factory.func, fixture_aliases)
                    and autouse_enabled(factory)
                )
                or (isinstance(factory, ast.Name) and factory.id in aliases)
                or (
                    _is_fixture_callable(factory, fixture_aliases)
                    and autouse_enabled(node)
                    and any(_root_name(argument) in functions for argument in node.args)
                )
            ):
                return True
        return False

    for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        class_nodes = _scope_execution_nodes(class_node.body)
        class_aliases = factory_aliases_for(class_nodes, factory_aliases)
        class_functions = {
            node.name: node
            for node in class_nodes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        if has_autouse_declaration(class_nodes, class_functions, class_aliases):
            raise TestCorpusGuardError(
                "class-local autouse pytest fixtures cannot be inventoried safely"
            )

    functions = {
        node.name: node
        for node in module_nodes
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
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
            value = statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            targets = (statement.target,)
            value = statement.value
        else:
            continue
        if not isinstance(value, ast.Call):
            continue
        factory = value.func
        direct_autouse = _is_fixture_callable(
            factory, fixture_aliases
        ) and autouse_enabled(value)
        curried_autouse = (
            isinstance(factory, ast.Call)
            and _is_fixture_callable(factory.func, fixture_aliases)
            and autouse_enabled(factory)
        )
        configured_autouse = (
            isinstance(factory, ast.Name) and factory.id in factory_aliases
        )
        if not (direct_autouse or curried_autouse or configured_autouse):
            continue
        target_names = {
            name for target in targets for name in _binding_target_names(target)
        }
        if binding_names is not None and not (target_names & binding_names):
            continue
        for argument in value.args:
            root = _root_name(argument)
            if root in functions:
                declarations.add(ast.dump(statement, include_attributes=False))
                declarations.add(binding_source(root))

    for node in module_nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and _is_fixture_callable(decorator.func, fixture_aliases)
                    and autouse_enabled(decorator)
                ) or (
                    isinstance(decorator, ast.Name) and decorator.id in factory_aliases
                ):
                    if binding_names is None or node.name in binding_names:
                        declarations.add(binding_source(node.name))
        # ``fixture(...)(function)`` only changes pytest collection semantics when
        # the returned FixtureFunctionDefinition is retained.  A bare expression
        # discards that wrapper and leaves the original function unmarked.
    if import_source_resolver is not None:
        relative_package = module
        if not path.endswith("/__init__.py") and "." in module:
            relative_package = module.rsplit(".", 1)[0]
        direct_node_ids = {id(node) for node in tree.body}
        imported_modules = _python_import_modules(
            tree,
            relative_package=relative_package,
        )

        def imported_binding_is_autouse_factory(
            candidates: tuple[str, ...],
            imported_name: str,
        ) -> bool:
            resolved = [
                (candidate, resolved_source)
                for candidate in candidates
                if (resolved_source := import_source_resolver(candidate)) is not None
            ]
            if len(resolved) > 1:
                raise TestCorpusGuardError(
                    "imported autouse pytest fixture factory is ambiguous"
                )
            if not resolved:
                return False
            resolved_module, resolved_source = resolved[0]
            source_body = (
                resolved_source.split("\n", 1)[1]
                if resolved_source.startswith("path=")
                else resolved_source
            )
            resolved_tree = _python_parsed_module(
                resolved_module,
                source_body,
                import_source_resolver,
            )
            resolved_fixture_aliases = _fixture_aliases(resolved_tree)
            configured_factories: set[str] = set()
            changed = True
            while changed:
                changed = False
                for candidate_node in _module_execution_nodes(resolved_tree):
                    if not isinstance(
                        candidate_node,
                        (ast.Assign, ast.AnnAssign),
                    ):
                        continue
                    candidate_value = candidate_node.value
                    if candidate_value is None:
                        continue
                    resolves = (
                        isinstance(candidate_value, ast.Call)
                        and _is_fixture_callable(
                            candidate_value.func,
                            resolved_fixture_aliases,
                        )
                        and autouse_enabled(candidate_value)
                    ) or (
                        isinstance(candidate_value, ast.Name)
                        and candidate_value.id in configured_factories
                    )
                    if not resolves:
                        continue
                    candidate_targets = (
                        candidate_node.targets
                        if isinstance(candidate_node, ast.Assign)
                        else (candidate_node.target,)
                    )
                    for candidate_target in candidate_targets:
                        for configured_name in _binding_target_names(candidate_target):
                            if configured_name not in configured_factories:
                                configured_factories.add(configured_name)
                                changed = True
            resolved_name = _binding_name_for_resolved_import(
                candidates,
                resolved_module,
                imported_name,
            )
            return resolved_name in configured_factories

        for statement in tree.body:
            if isinstance(statement, ast.Assign):
                assigned_value = statement.value
            elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
                assigned_value = statement.value
            else:
                continue
            if not isinstance(assigned_value, ast.Call):
                continue
            imported_factory: tuple[tuple[str, ...], str] | None = None
            if isinstance(assigned_value.func, ast.Name):
                if assigned_value.func.id in imported_modules:
                    imported_factory = (
                        imported_modules[assigned_value.func.id],
                        assigned_value.func.id,
                    )
            elif isinstance(assigned_value.func, ast.Attribute):
                imported_root = _root_name(assigned_value.func.value)
                if imported_root in imported_modules:
                    imported_factory = (
                        imported_modules[imported_root],
                        assigned_value.func.attr,
                    )
            if imported_factory is not None and imported_binding_is_autouse_factory(
                *imported_factory
            ):
                raise TestCorpusGuardError(
                    "imported autouse pytest fixture factory application cannot be "
                    "inventoried safely"
                )

        module_counts: dict[str, int] | None = getattr(
            import_source_resolver,
            "_uaa_local_python_module_counts",
            None,
        )
        assignment_aliases: dict[str, tuple[tuple[str, ...], str, ast.AST]] = {}
        superseded_assignment_aliases: list[
            tuple[str, tuple[str, ...], str, ast.AST]
        ] = []
        for execution_node in module_nodes:
            rebound_names = _execution_binding_names(execution_node)
            for rebound_name in rebound_names:
                prior_alias = assignment_aliases.pop(rebound_name, None)
                if prior_alias is not None:
                    superseded_assignment_aliases.append((rebound_name, *prior_alias))
                if isinstance(execution_node, ast.Assign):
                    targets = execution_node.targets
                    value = execution_node.value
                elif (
                    isinstance(execution_node, ast.AnnAssign)
                    and execution_node.value is not None
                ):
                    targets = (execution_node.target,)
                    value = execution_node.value
                else:
                    continue
                resolved_alias: tuple[tuple[str, ...], str] | None = None
                if isinstance(value, ast.Attribute):
                    root = _root_name(value.value)
                    if root in imported_modules:
                        resolved_alias = (imported_modules[root], value.attr)
                elif isinstance(value, ast.Name):
                    if value.id in assignment_aliases:
                        candidates, imported_name, _origin = assignment_aliases[
                            value.id
                        ]
                        resolved_alias = (candidates, imported_name)
                    elif value.id in imported_modules:
                        resolved_alias = (imported_modules[value.id], value.id)
                if resolved_alias is None:
                    continue
                for target in targets:
                    for local_name, _bound_value in _paired_binding_values(
                        target, value
                    ):
                        assignment_aliases[local_name] = (
                            *resolved_alias,
                            execution_node,
                        )

            for local_name, (
                candidates,
                imported_name,
                origin_node,
            ) in assignment_aliases.items():
                used_as_decorator = any(
                    _root_name(decorator) == local_name
                    for function in functions.values()
                    if binding_names is None or function.name in binding_names
                    for decorator in function.decorator_list
                )
                if (
                    binding_names is not None
                    and local_name not in binding_names
                    and not used_as_decorator
                ):
                    continue
                resolved = [
                    (candidate, resolved_source)
                    for candidate in candidates
                    if (resolved_source := import_source_resolver(candidate))
                    is not None
                ]
                if (
                    len(resolved) > 1
                    and module_counts is not None
                    and candidates
                    and not module_counts.get(candidates[0], 0)
                    and module_counts.get(candidates[-1], 0)
                ):
                    resolved = [item for item in resolved if item[0] == candidates[-1]]
                if len(resolved) > 1:
                    raise TestCorpusGuardError(
                        "imported autouse pytest fixture is ambiguous"
                    )
                if not resolved:
                    continue
                resolved_module, resolved_source = resolved[0]
                resolved_name = _binding_name_for_resolved_import(
                    candidates,
                    resolved_module,
                    imported_name,
                )
                if binding_names is None or local_name in binding_names:
                    imported_declarations = _autouse_fixture_declarations(
                        resolved_source,
                        resolved_module,
                        import_source_resolver,
                        binding_names=frozenset({resolved_name}),
                        _seen_imports=frozenset(
                            (*_seen_imports, (resolved_module, resolved_name))
                        ),
                    )
                    if imported_declarations and id(origin_node) not in direct_node_ids:
                        raise TestCorpusGuardError(
                            "conditional imported autouse pytest fixture binding "
                            "cannot be inventoried safely"
                        )
                    declarations.update(
                        f"imported-autouse={local_name}\n{declaration}"
                        for declaration in imported_declarations
                    )
                if used_as_decorator and _python_source_may_bind_autouse_fixture(
                    resolved_source,
                    resolved_name,
                ):
                    raise TestCorpusGuardError(
                        "imported autouse pytest fixture marker cannot be inventoried safely"
                    )

        def later_mutations(
            import_node: ast.ImportFrom, name: str
        ) -> tuple[ast.AST, ...]:
            import_position = (import_node.lineno, import_node.col_offset)
            mutations: list[ast.AST] = []
            for candidate in module_nodes:
                if (
                    getattr(candidate, "lineno", 0),
                    getattr(candidate, "col_offset", 0),
                ) <= import_position:
                    continue
                if name in _execution_binding_names(candidate):
                    mutations.append(candidate)
            return tuple(mutations)

        if binding_names is not None:
            for function_name in binding_names:
                function = functions.get(function_name)
                if function is None:
                    continue
                for decorator in function.decorator_list:
                    root = _root_name(decorator)
                    if (
                        root is None
                        or root in fixture_aliases
                        or root in factory_aliases
                    ):
                        continue
                    decorator_candidates = imported_modules.get(root, ())
                    for candidate in decorator_candidates:
                        decorator_source = import_source_resolver(candidate)
                        if decorator_source is None:
                            continue
                        decorator_name = _binding_name_for_resolved_import(
                            decorator_candidates,
                            candidate,
                            decorator.attr
                            if isinstance(decorator, ast.Attribute)
                            else root,
                        )
                        if _python_source_may_bind_autouse_fixture(
                            decorator_source,
                            decorator_name,
                        ):
                            raise TestCorpusGuardError(
                                "imported autouse pytest fixture marker cannot be "
                                "inventoried safely"
                            )
        for node in module_nodes:
            if not isinstance(node, ast.ImportFrom):
                continue
            node_import_bindings = _python_import_modules(
                ast.Module(body=[node], type_ignores=[]),
                relative_package=relative_package,
            )
            for imported in node.names:
                if imported.name == "*":
                    continue
                local_name = imported.asname or imported.name
                if binding_names is not None and local_name not in binding_names:
                    continue
                candidates = node_import_bindings.get(local_name, ())
                module_counts: dict[str, int] | None = getattr(
                    import_source_resolver,
                    "_uaa_local_python_module_counts",
                    None,
                )
                if module_counts is not None and not any(
                    module_counts.get(candidate, 0) for candidate in candidates
                ):
                    continue
                if (
                    module_counts is not None
                    and len(candidates) > 1
                    and module_counts.get(candidates[0], 0)
                ):
                    # ``from package import child`` bound the child module
                    # itself. Its internal fixtures are not imported into the
                    # requesting test module's namespace. Decide this from the
                    # structural module inventory before resolving both the
                    # child and its package as competing binding candidates.
                    continue
                resolved = [
                    (candidate, resolved_source)
                    for candidate in candidates
                    if (resolved_source := import_source_resolver(candidate))
                    is not None
                ]
                if (
                    len(resolved) > 1
                    and module_counts is not None
                    and candidates
                    and not module_counts.get(candidates[0], 0)
                    and module_counts.get(candidates[-1], 0)
                ):
                    resolved = [item for item in resolved if item[0] == candidates[-1]]
                if len(resolved) > 1:
                    raise TestCorpusGuardError(
                        "imported autouse pytest fixture is ambiguous"
                    )
                if not resolved:
                    continue
                resolved_module, resolved_source = resolved[0]
                resolved_name = _binding_name_for_resolved_import(
                    candidates,
                    resolved_module,
                    imported.name,
                )
                import_key = (resolved_module, resolved_name)
                if import_key in _seen_imports:
                    continue
                cache_key = (
                    resolved_module,
                    resolved_name,
                    hashlib.sha256(resolved_source.encode("utf-8")).hexdigest(),
                )
                cache: dict[tuple[str, str, str], tuple[str, ...]] = getattr(
                    import_source_resolver,
                    "_uaa_autouse_fixture_cache",
                    {},
                )
                imported_declarations = cache.get(cache_key)
                if imported_declarations is None:
                    source_body = (
                        resolved_source.split("\n", 1)[1]
                        if resolved_source.startswith("path=")
                        else resolved_source
                    )
                    resolved_tree = _python_parsed_module(
                        resolved_module,
                        source_body,
                        import_source_resolver,
                    )
                    resolved_name_is_static = any(
                        resolved_name in _execution_binding_names(statement)
                        for statement in resolved_tree.body
                    )
                    binds_dynamic_attributes = any(
                        (
                            isinstance(
                                statement, (ast.FunctionDef, ast.AsyncFunctionDef)
                            )
                            and statement.name == "__getattr__"
                        )
                        or (
                            isinstance(statement, (ast.Assign, ast.AnnAssign))
                            and "__getattr__"
                            in {
                                name
                                for target in (
                                    statement.targets
                                    if isinstance(statement, ast.Assign)
                                    else (statement.target,)
                                )
                                for name in _binding_target_names(target)
                            }
                        )
                        for statement in resolved_tree.body
                    )
                    if not resolved_name_is_static and binds_dynamic_attributes:
                        resolved_path = (
                            resolved_source.split("\n", 1)[0].removeprefix("path=")
                            if resolved_source.startswith("path=")
                            else ""
                        )
                        lazy_package = resolved_module
                        if (
                            not resolved_path.endswith("/__init__.py")
                            and "." in resolved_module
                        ):
                            lazy_package = resolved_module.rsplit(".", 1)[0]
                        lazy_modules = _python_lazy_export_binding_modules(
                            resolved_tree,
                            relative_package=lazy_package,
                            binding_name=resolved_name,
                        )
                        if len(lazy_modules) != 1:
                            raise TestCorpusGuardError(
                                "dynamic imported autouse pytest fixture binding cannot "
                                "be inventoried safely"
                            )
                        lazy_module = lazy_modules[0]
                        lazy_source = import_source_resolver(lazy_module)
                        if lazy_source is None:
                            cache[cache_key] = ()
                            continue
                        lazy_declarations = _autouse_fixture_declarations(
                            lazy_source,
                            lazy_module,
                            import_source_resolver,
                            binding_names=frozenset({resolved_name}),
                            _seen_imports=frozenset(
                                (
                                    *_seen_imports,
                                    import_key,
                                    (lazy_module, resolved_name),
                                )
                            ),
                        )
                        if lazy_declarations:
                            raise TestCorpusGuardError(
                                "dynamic imported autouse pytest fixture binding cannot "
                                "be inventoried safely"
                            )
                        cache[cache_key] = ()
                        continue
                    if not _python_source_may_bind_autouse_fixture(
                        resolved_source,
                        resolved_name,
                    ):
                        cache[cache_key] = ()
                        continue
                    if (
                        not resolved_name_is_static
                        and re.search(
                            r"(?m)^\s*(?:(?:async\s+)?def\s+__getattr__\b|__getattr__\s*=)",
                            source_body,
                        )
                        and not any(
                            marker in source_body
                            for marker in ("_EXPORT_GROUPS", "_LAZY_EXPORT_MODULES")
                        )
                    ):
                        raise TestCorpusGuardError(
                            "dynamic imported autouse pytest fixture binding cannot "
                            "be inventoried safely"
                        )
                    imported_declarations = _autouse_fixture_declarations(
                        resolved_source,
                        resolved_module,
                        import_source_resolver,
                        binding_names=frozenset({resolved_name}),
                        _seen_imports=frozenset((*_seen_imports, import_key)),
                    )
                    cache[cache_key] = imported_declarations
                mutations = later_mutations(node, local_name)
                if mutations:
                    if imported_declarations:
                        raise TestCorpusGuardError(
                            "mutated imported autouse pytest fixture binding cannot "
                            "be inventoried safely"
                        )
                    continue
                if imported_declarations and id(node) not in direct_node_ids:
                    raise TestCorpusGuardError(
                        "conditional imported autouse pytest fixture binding cannot be "
                        "inventoried safely"
                    )
                declarations.update(
                    f"imported-autouse={local_name}\n{declaration}"
                    for declaration in imported_declarations
                )

        for (
            local_name,
            candidates,
            imported_name,
            _origin_node,
        ) in superseded_assignment_aliases:
            resolved = [
                (candidate, resolved_source)
                for candidate in candidates
                if (resolved_source := import_source_resolver(candidate)) is not None
            ]
            if len(resolved) > 1:
                raise TestCorpusGuardError(
                    "imported autouse pytest fixture is ambiguous"
                )
            if not resolved:
                continue
            resolved_module, resolved_source = resolved[0]
            resolved_name = _binding_name_for_resolved_import(
                candidates,
                resolved_module,
                imported_name,
            )
            imported_declarations = _autouse_fixture_declarations(
                resolved_source,
                resolved_module,
                import_source_resolver,
                binding_names=frozenset({resolved_name}),
                _seen_imports=frozenset(
                    (*_seen_imports, (resolved_module, resolved_name))
                ),
            )
            if imported_declarations:
                raise TestCorpusGuardError(
                    f"mutated imported autouse pytest fixture binding {local_name!r} "
                    "cannot be inventoried safely"
                )
    return tuple(sorted(declarations))


def _pytest_plugin_modules(source: str, path: str) -> set[str]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "pytest plugin registration cannot be inventoried safely"
        ) from exc
    modules: set[str] = set()
    direct_registration_nodes = {
        id(node) for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
    }
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
        if id(node) not in direct_registration_nodes:
            raise TestCorpusGuardError(
                "conditional pytest plugin registration cannot be inventoried safely"
            )
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
    direct_import_nodes = {
        id(node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    for node in _module_execution_nodes(tree):
        if isinstance(node, ast.Import):
            if id(node) not in direct_import_nodes:
                raise TestCorpusGuardError(
                    "conditional pytest conftest imports cannot be inventoried safely"
                )
            modules.update(imported.name for imported in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if id(node) not in direct_import_nodes:
            raise TestCorpusGuardError(
                "conditional pytest conftest imports cannot be inventoried safely"
            )
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
        modules.update(
            f"{module}.{imported.name}"
            for imported in node.names
            if imported.name != "*"
        )
    return modules


def _has_conftest_test_declaration_mutation(source: str, path: str) -> bool:
    """Return whether conftest can mutate a declaration's ``__test__`` flag."""

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        raise TestCorpusGuardError(
            "pytest conftest imports cannot be inventoried safely"
        ) from exc

    def target_mutates_test_flag(target: ast.AST) -> bool:
        for child in ast.walk(target):
            if isinstance(child, ast.Attribute) and child.attr == "__test__":
                return True
            if not isinstance(child, ast.Subscript):
                continue
            attribute = _static_string_expression(child.slice)
            if attribute == "__test__":
                return True
            if (
                isinstance(child.value, ast.Attribute)
                and child.value.attr == "__dict__"
                and attribute is None
            ):
                return True
        return False

    def call_mutates_test_flag(node: ast.Call) -> bool:
        attribute: ast.AST | None = None
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in {"setattr", "delattr"}
            and len(node.args) >= 2
        ):
            attribute = node.args[1]
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"__setattr__", "__delattr__"}
        ):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "object"
                and len(node.args) >= 2
            ):
                attribute = node.args[1]
            elif node.args:
                attribute = node.args[0]
        if attribute is None:
            return False
        return not isinstance(attribute, ast.Constant) or attribute.value == "__test__"

    for node in _module_collection_execution_nodes(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = (node.target,)
        elif isinstance(node, ast.Delete):
            targets = node.targets
        else:
            targets = ()
        if any(target_mutates_test_flag(target) for target in targets):
            return True
        if isinstance(node, ast.Call) and call_mutates_test_flag(node):
            return True
    return False


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


def _safe_pytest_suffix_discovery_alignment_paths(
    *,
    current_by_path: dict[str, str],
    prior_by_path: dict[str, str],
) -> set[str]:
    manifest_path = "scripts/verification/ci_command_manifest.py"
    runner_path = "scripts/verification/run_pytest_shards.py"
    corpus_guard_path = "scripts/verify_test_corpus_guard.py"
    expected_paths = {manifest_path, runner_path}
    extracts_corpus_guard = corpus_guard_path in current_by_path
    if extracts_corpus_guard:
        expected_paths.add(corpus_guard_path)
    if set(current_by_path) != expected_paths or set(prior_by_path) != expected_paths:
        return set()

    manifest_needle = '                    "tests/**/test_*.py",\n'
    manifest_replacement = (
        manifest_needle + '                    "tests/**/*_test.py",\n'
    )
    prior_manifest = prior_by_path[manifest_path]
    if prior_manifest.count(manifest_needle) != 1:
        return set()
    expected_manifest = prior_manifest.replace(
        manifest_needle,
        manifest_replacement,
        1,
    )
    static_timeout_needle = (
        '                    "{temp_root}/uaa_static_verification_timings.json",\n'
        "                ),\n"
        '                (),\n'
        '                "verification",\n'
        "                900,\n"
        "            ),\n"
    )
    static_timeout_replacement = static_timeout_needle.replace(
        "                900,\n",
        "                1_800,\n",
    )
    if expected_manifest.count(static_timeout_needle) != 1:
        return set()
    allowed_manifests = {
        expected_manifest,
        expected_manifest.replace(
            static_timeout_needle,
            static_timeout_replacement,
            1,
        ),
    }
    if extracts_corpus_guard:
        static_command_needle = (
            '                    "{temp_root}/uaa_static_verification_timings.json",\n'
            "                ),\n"
            '                (),\n'
            '                "verification",\n'
            "                1_800,\n"
            "            ),\n"
        )
        corpus_command = (
            static_command_needle.replace("                1_800,\n", "                1_200,\n")
            + '            "command:static.test-corpus-guard": CommandSpec(\n'
            + '                "command:static.test-corpus-guard",\n'
            + "                (\n"
            + '                    ".venv/bin/python",\n'
            + '                    "scripts/verify_test_corpus_guard.py",\n'
            + "                ),\n"
            + "                (),\n"
            + '                "verification",\n'
            + "                1_200,\n"
            + "            ),\n"
        )
        static_lane_needle = (
            '            "ci-static": LaneSpec(\n'
            '                "ci-static",\n'
            '                "Static Verification",\n'
            '                ("command:static.verify-all",),\n'
            "            ),\n"
        )
        static_lane_replacement = (
            '            "ci-static": LaneSpec(\n'
            '                "ci-static",\n'
            '                "Static Verification",\n'
            "                (\n"
            '                    "command:static.test-corpus-guard",\n'
            '                    "command:static.verify-all",\n'
            "                ),\n"
            "            ),\n"
        )
        extracted_manifests: set[str] = set()
        for candidate in allowed_manifests:
            if (
                candidate.count(static_command_needle) == 1
                and candidate.count(static_lane_needle) == 1
            ):
                extracted_manifests.add(
                    candidate.replace(static_command_needle, corpus_command, 1).replace(
                        static_lane_needle,
                        static_lane_replacement,
                        1,
                    )
                )
        allowed_manifests = extracted_manifests
    if current_by_path[manifest_path] not in allowed_manifests:
        return set()

    runner_needle = (
        '        for path in (root / "tests").rglob("test_*.py")\n'
        "        if path.is_file()\n"
    )
    runner_replacement = (
        '        for path in (root / "tests").rglob("*.py")\n'
        "        if path.is_file()\n"
        '        and (path.name.startswith("test_") or path.name.endswith("_test.py"))\n'
    )
    prior_runner = prior_by_path[runner_path]
    if prior_runner.count(runner_needle) != 1:
        return set()
    expected_runner = prior_runner.replace(
        runner_needle,
        runner_replacement,
        1,
    )
    no_tests_needle = (
        '        print("FAIL: no tests/test_*.py files discovered", file=sys.stderr)\n'
    )
    no_tests_replacement = '        print("FAIL: no canonical Python test files discovered", file=sys.stderr)\n'
    if expected_runner.count(no_tests_needle) != 1:
        return set()
    expected_runner = expected_runner.replace(
        no_tests_needle,
        no_tests_replacement,
        1,
    )
    if current_by_path[runner_path] != expected_runner:
        return set()
    if extracts_corpus_guard:
        if prior_by_path[corpus_guard_path] or current_by_path[corpus_guard_path] != (
            '#!/usr/bin/env python3\n'
            '"""Run the deterministic test-corpus inventory and retirement guard."""\n'
            "\n"
            "from __future__ import annotations\n"
            "\n"
            "import json\n"
            "import sys\n"
            "from pathlib import Path\n"
            "\n"
            "\n"
            "ROOT = Path(__file__).resolve().parents[1]\n"
            "sys.path.insert(0, str(ROOT))\n"
            "\n"
            "from scripts.verification.test_corpus_guard import (  # noqa: E402\n"
            "    TestCorpusGuardError,\n"
            "    verify_test_corpus_guard,\n"
            ")\n"
            "\n"
            "\n"
            "def main() -> int:\n"
            "    try:\n"
            "        result = verify_test_corpus_guard(ROOT)\n"
            "    except TestCorpusGuardError as exc:\n"
            '        print(f"test corpus guard failed: {exc}", file=sys.stderr)\n'
            "        return 1\n"
            "    print(json.dumps(result, indent=2, sort_keys=True))\n"
            "    return 0\n"
            "\n"
            "\n"
            'if __name__ == "__main__":\n'
            "    raise SystemExit(main())\n"
        ):
            return set()
    return expected_paths


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
    for path in all_changed:
        if not _is_python_test_path(path):
            continue
        current = _read_worktree_text(repo, path) if (repo / path).is_file() else ""
        prior = _base_text(repo, base_sha, path) or ""
        if "pytest_plugins" not in current and "pytest_plugins" not in prior:
            continue
        if _pytest_plugin_modules(current, path) != _pytest_plugin_modules(prior, path):
            raise TestCorpusGuardError(
                "changed test-module pytest plugin registration cannot be "
                "inventoried safely"
            )
    changed_runner_paths = PYTEST_RUNNER_CONFIG_PATHS & all_changed
    current_runner_by_path = {
        path: _read_worktree_text(repo, path) if (repo / path).is_file() else ""
        for path in changed_runner_paths
    }
    prior_runner_by_path = {
        path: _base_text(repo, base_sha, path) or "" for path in changed_runner_paths
    }
    effective_changed_runner_paths = {
        path
        for path in changed_runner_paths
        if (
            _pytest_workflow_collection_boundary(current_runner_by_path[path])
            if path == ".github/workflows/ci.yml"
            else current_runner_by_path[path]
        )
        != (
            _pytest_workflow_collection_boundary(prior_runner_by_path[path])
            if path == ".github/workflows/ci.yml"
            else prior_runner_by_path[path]
        )
    }
    safe_runner_paths = _safe_pytest_suffix_discovery_alignment_paths(
        current_by_path={
            path: current_runner_by_path[path]
            for path in effective_changed_runner_paths
        },
        prior_by_path={
            path: prior_runner_by_path[path] for path in effective_changed_runner_paths
        },
    )
    for path in changed_runner_paths:
        current = current_runner_by_path[path]
        prior = prior_runner_by_path[path]
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
        if current_boundary != prior_boundary and path not in safe_runner_paths:
            raise TestCorpusGuardError(
                "changed pytest runner configuration cannot be inventoried safely"
            )
    if (all_changed & runner_dependencies) - safe_runner_paths:
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
        if _has_conftest_test_declaration_mutation(
            current, path
        ) or _has_conftest_test_declaration_mutation(prior, path):
            raise TestCorpusGuardError(
                "changed conftest test declaration mutation cannot be inventoried safely"
            )
        if _pytest_plugin_modules(current, path) != _pytest_plugin_modules(prior, path):
            raise TestCorpusGuardError(
                "changed pytest plugin registration cannot be inventoried safely"
            )
        if (
            any(
                name in current or name in prior
                for name in PYTEST_COLLECTION_HOOK_NAMES
            )
            or _has_pytest_collection_hook_spec(current, path)
            or _has_pytest_collection_hook_spec(prior, path)
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
                "changed autouse Python fixtures cannot be inventoried safely"
            )
        if _has_fixture_declaration(current, path) or _has_fixture_declaration(
            prior, path
        ):
            raise TestCorpusGuardError(
                "changed pytest fixtures cannot be inventoried safely"
            )
    changed_python_sources = {
        path
        for path in all_changed
        if path.endswith(".py") and path not in safe_runner_paths
    }
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
        current_python_tests = {
            path for path in discover_test_files(repo) if path.endswith(".py")
        }
        for test_path in sorted(current_python_tests):
            current = _read_worktree_text(repo, test_path)
            if "pytest_plugins" in current:
                current_registered_plugins.update(
                    _pytest_plugin_modules(current, test_path)
                )
        for test_path in sorted(all_changed):
            if not _is_python_test_path(test_path):
                continue
            prior = _base_text(repo, base_sha, test_path) or ""
            if "pytest_plugins" in prior:
                prior_registered_plugins.update(
                    _pytest_plugin_modules(prior, test_path)
                )
        prior_registered_plugins.update(current_registered_plugins)
        plugin_dependency_paths = _python_dependency_paths(
            repo,
            _python_modules_with_package_ancestors(current_registered_plugins),
            include_dynamic=True,
        )
        if prior_registered_plugins:
            base_paths = _base_file_paths(repo, base_sha)
            plugin_dependency_paths.update(
                _python_dependency_paths(
                    repo,
                    _python_modules_with_package_ancestors(prior_registered_plugins),
                    read_text=lambda path: (
                        _base_text(repo, base_sha, path) if path in base_paths else None
                    ),
                    include_dynamic=True,
                )
            )
        for plugin_path in sorted(changed_python_sources & plugin_dependency_paths):
            current = (
                _read_worktree_text(repo, plugin_path)
                if (repo / plugin_path).is_file()
                else ""
            )
            prior = _base_text(repo, base_sha, plugin_path) or ""
            if (
                any(
                    name in current or name in prior
                    for name in PYTEST_COLLECTION_HOOK_NAMES
                )
                or _has_pytest_collection_hook_spec(current, plugin_path)
                or _has_pytest_collection_hook_spec(prior, plugin_path)
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
            if current != prior and not plugin_path.startswith(
                PYTHON_APPLICATION_SOURCE_PREFIXES
            ):
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
        current_frontend_dependency_cache: dict[str, frozenset[str]] = {}
        current_frontend_source_cache: dict[str, str | None] = {}

        def read_current_frontend(candidate: str) -> str | None:
            if candidate in current_frontend_source_cache:
                return current_frontend_source_cache[candidate]
            source = (
                _read_worktree_text(repo, candidate)
                if (repo / candidate).is_file()
                else None
            )
            current_frontend_source_cache[candidate] = source
            return source

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
            dependency_candidates.update(
                _frontend_runtime_dependency_paths(
                    {test_path},
                    read_current_frontend,
                    current_frontend_dependency_cache,
                )
            )
            if dependency_candidates & changed_frontend_sources or any(
                not (repo / changed_source).is_file()
                for changed_source in changed_frontend_sources
            ):
                changed.add(test_path)
    if changed_python_sources:
        python_dependency_cache: dict[str, tuple[set[str], set[str]]] = {}
        current_fixture_resolver = _python_import_resolver(
            lambda candidate: (
                _read_worktree_text(repo, candidate)
                if (repo / candidate).is_file()
                else None
            )
        )
        prior_fixture_resolver: Callable[[str], str | None] | None = None
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
            changed_dependencies = dependency_candidates & changed_python_sources
            if changed_dependencies:
                test_owned_changed_dependencies = {
                    dependency
                    for dependency in changed_dependencies
                    if not dependency.startswith(PYTHON_APPLICATION_SOURCE_PREFIXES)
                }
                fixture_bindings = _python_local_fixture_bindings(tree)
                prior_text: str | None = None
                if fixture_bindings and test_owned_changed_dependencies:
                    if prior_fixture_resolver is None:
                        base_paths = _base_file_paths(repo, base_sha)
                        prior_fixture_resolver = _python_import_resolver(
                            lambda candidate: (
                                _read_worktree_text(repo, candidate)
                                if candidate.startswith(
                                    PYTHON_APPLICATION_SOURCE_PREFIXES
                                )
                                and (repo / candidate).is_file()
                                else _base_text(repo, base_sha, candidate)
                                if candidate in base_paths
                                else None
                            )
                        )
                    prior_text = _base_text(repo, base_sha, test_path)
                if (
                    fixture_bindings
                    and test_owned_changed_dependencies
                    and (
                        prior_text is None
                        or _python_local_fixture_dependency_identity(
                            test_path,
                            text,
                            current_fixture_resolver,
                        )
                        != _python_local_fixture_dependency_identity(
                            test_path,
                            prior_text,
                            prior_fixture_resolver,
                        )
                    )
                ):
                    raise TestCorpusGuardError(
                        "changed module-local pytest fixture dependency cannot be "
                        "inventoried safely"
                    )
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
        and (candidate.name.startswith("test_") or candidate.name.endswith("_test.py"))
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
        if not target.is_file() or not _worktree_path_has_exact_case(repo, candidate):
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


def _validate_worktree_inventory_snapshot(
    repo: Path,
    snapshot: _WorktreeInventorySnapshot,
    current_paths: set[str],
) -> None:
    """Fail closed if any source consumed by the cached inventory has changed."""

    if set(snapshot.files_by_path) != current_paths:
        raise TestCorpusGuardError("test inventory changed during verification")
    for path, inventory in snapshot.files_by_path.items():
        if _read_worktree_text(repo, path) != inventory.source:
            raise TestCorpusGuardError("test inventory changed during verification")

    source_cache = getattr(
        snapshot.python_import_source_resolver,
        "_uaa_source_cache",
        None,
    )
    module_counts = getattr(
        snapshot.python_import_source_resolver,
        "_uaa_local_python_module_counts",
        None,
    )
    if not isinstance(source_cache, dict) or not isinstance(module_counts, dict):
        raise TestCorpusGuardError("test inventory snapshot is invalid")

    def read_current_import(candidate: str) -> str | None:
        target = repo / candidate
        if not target.is_file() or not _worktree_path_has_exact_case(repo, candidate):
            return None
        return _read_worktree_text(repo, candidate)

    current_resolver = _python_import_resolver(read_current_import)
    if _local_python_module_counts(repo) != module_counts:
        raise TestCorpusGuardError("test inventory changed during verification")
    for module, source in source_cache.items():
        if current_resolver(module) != source:
            raise TestCorpusGuardError("test inventory changed during verification")


def removed_declarations(
    repo: Path,
    base_sha: str,
    *,
    worktree_snapshot: _WorktreeInventorySnapshot | None = None,
) -> tuple[str, ...]:
    removed: set[str] = set()
    current_paths = set(discover_test_files(repo))

    def read_base_python_import(candidate: str) -> str | None:
        target = repo / candidate
        if (
            candidate.startswith(PYTHON_APPLICATION_SOURCE_PREFIXES)
            and target.is_file()
            and _worktree_path_has_exact_case(repo, candidate)
        ):
            return _read_worktree_text(repo, candidate)
        return _base_text(repo, base_sha, candidate)

    base_import_source_resolver = _python_import_resolver(read_base_python_import)
    base_module_counts: dict[str, int] = {}
    base_python_paths_seen = 0
    for path in _base_file_paths(repo, base_sha):
        if not path.endswith(".py"):
            continue
        base_python_paths_seen += 1
        if base_python_paths_seen > MAX_PYTHON_DEPENDENCY_MODULES:
            raise TestCorpusGuardError("base Python module index exceeds module budget")
        module = _python_module_name_for_path(path)
        base_module_counts[module] = base_module_counts.get(module, 0) + 1
    setattr(
        base_import_source_resolver,
        "_uaa_local_python_module_counts",
        base_module_counts,
    )

    def read_worktree_import(candidate: str) -> str | None:
        target = repo / candidate
        if not target.is_file() or not _worktree_path_has_exact_case(repo, candidate):
            return None
        return _read_worktree_text(repo, candidate)

    if worktree_snapshot is None:
        worktree_import_source_resolver = _python_import_resolver(
            read_worktree_import
        )
        setattr(
            worktree_import_source_resolver,
            "_uaa_local_python_module_counts",
            _local_python_module_counts(repo),
        )
    else:
        worktree_import_source_resolver = (
            worktree_snapshot.python_import_source_resolver
        )
    base_frontend_source_cache: dict[str, str | None] = {}
    base_frontend_initializer_cache: dict[str, str] = {}
    base_frontend_runtime_dependency_cache: dict[str, frozenset[str]] = {}
    worktree_frontend_source_cache: dict[str, str | None] = {}
    worktree_frontend_initializer_cache: dict[str, str] = {}
    worktree_frontend_runtime_dependency_cache: dict[str, frozenset[str]] = {}
    for path in _changed_test_paths(repo, base_sha):
        prior = _base_text(repo, base_sha, path)
        if prior is None:
            continue
        prior_declarations = _parse_base_test_declarations(
            repo,
            base_sha,
            path,
            prior,
            base_import_source_resolver,
            base_frontend_source_cache,
            base_frontend_initializer_cache,
            base_frontend_runtime_dependency_cache,
        )
        prior_refs = {item.ref for item in prior_declarations}
        if path in current_paths:
            if worktree_snapshot is not None and path.endswith(".py"):
                current_inventory = worktree_snapshot.files_by_path[path]
                current_text = current_inventory.source
                current_declarations = current_inventory.declarations
            else:
                current_text = _read_worktree_text(repo, path)
                current_declarations = _parse_worktree_test_declarations(
                    repo,
                    path,
                    current_text,
                    worktree_import_source_resolver,
                    worktree_frontend_source_cache,
                    worktree_frontend_initializer_cache,
                    worktree_frontend_runtime_dependency_cache,
                )
            current_refs = {item.ref for item in current_declarations}
        else:
            current_text = None
            current_declarations = ()
            current_refs = set()
        path_removed = prior_refs - current_refs
        if path.endswith(".py") and current_text is not None and path_removed:
            normalized_prior = tuple(
                declaration
                for declaration, _source in _python_inventory_entries(
                    path,
                    prior,
                    base_import_source_resolver,
                    normalize_non_aborting_runtime_helpers=True,
                )
            )
            normalized_current = tuple(
                declaration
                for declaration, _source in _python_inventory_entries(
                    path,
                    current_text,
                    worktree_import_source_resolver,
                    normalize_non_aborting_runtime_helpers=True,
                )
            )
            if len(normalized_prior) != len(prior_declarations) or len(
                normalized_current
            ) != len(current_declarations):
                raise TestCorpusGuardError(
                    "normalized Python test inventory is inconsistent"
                )
            current_normalized_refs = {item.ref for item in normalized_current}
            path_removed.difference_update(
                declaration.ref
                for declaration, normalized in zip(
                    prior_declarations,
                    normalized_prior,
                    strict=True,
                )
                if normalized.ref in current_normalized_refs
            )
        removed.update(path_removed)
    if worktree_snapshot is not None:
        _validate_worktree_inventory_snapshot(
            repo,
            worktree_snapshot,
            set(discover_test_files(repo)),
        )
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
    resolved_base = _resolve_base_sha(
        repo,
        base_sha if base_sha is not None else os.environ.get(BASE_SHA_ENV),
    )
    worktree_snapshot = _inventory_worktree_snapshot(repo)
    declarations = worktree_snapshot.declarations
    current_refs = {item.ref for item in declarations}
    removed = (
        set(
            removed_declarations(
                repo,
                resolved_base,
                worktree_snapshot=worktree_snapshot,
            )
        )
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
