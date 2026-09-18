"""Delegated startup transport cannot widen the packaged adapter boundary."""

from __future__ import annotations

import pytest


_HELPER = "src/ultimate_ai_agent/core/finance_startup.py"
_INITIALIZER = "src/ultimate_ai_agent/core/__init__.py"
_PROFILE = "src/ultimate_ai_agent/core/finance_managed_profile.py"
_PRIVATE_PATH = "src/ultimate_ai_agent/core/private_path_security.py"
_PACKAGE = "src/ultimate_ai_agent/__init__.py"
_DEPENDENCIES = (_HELPER, _INITIALIZER, _PROFILE, _PRIVATE_PATH, _PACKAGE)


@pytest.fixture
def dependency_root(tmp_path):
    from pathlib import Path

    from ultimate_ai_agent.distribution.macos.static_policy import (
        MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES,
    )

    source_root = Path(__file__).resolve().parents[1]
    for relative in (*MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES, *_DEPENDENCIES):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source_root / relative).read_bytes())
    return tmp_path


def test_widened_delegated_filter_fails_with_unchanged_runtime(dependency_root):
    from ultimate_ai_agent.distribution.macos.static_policy import (
        macos_distribution_adapter_policy_failures,
        macos_distribution_policy_failures,
    )

    helper = dependency_root / _HELPER
    source = helper.read_text(encoding="utf-8")
    mutated = source.replace(
        "{name: environ[name] for name in FINANCE_STARTUP_ENV_NAMES if name in environ}",
        "dict(environ)",
    )
    assert mutated != source
    helper.write_text(mutated, encoding="utf-8")
    runtime = "src/ultimate_ai_agent/distribution/macos/runtime.py"
    assert macos_distribution_adapter_policy_failures(
        runtime, (dependency_root / runtime).read_text(encoding="utf-8")
    ) == []
    assert macos_distribution_policy_failures(dependency_root)


def test_reviewed_dependencies_pass_without_becoming_adapter_exemptions():
    from pathlib import Path

    from ultimate_ai_agent.distribution.macos.static_policy import (
        MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES,
        MACOS_DISTRIBUTION_EXACT_DEPENDENCY_FILES,
        macos_distribution_policy_failures,
        macos_distribution_static_fragment_allowed,
    )

    root = Path(__file__).resolve().parents[1]
    assert macos_distribution_policy_failures(root) == []
    assert MACOS_DISTRIBUTION_EXACT_DEPENDENCY_FILES == set(_DEPENDENCIES)
    assert MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES == {
        "src/ultimate_ai_agent/distribution/macos/github_releases.py",
        "src/ultimate_ai_agent/distribution/macos/installer.py",
        "src/ultimate_ai_agent/distribution/macos/runtime.py",
    }
    for relative in MACOS_DISTRIBUTION_EXACT_DEPENDENCY_FILES:
        assert not macos_distribution_static_fragment_allowed(
            relative,
            (root / relative).read_text(encoding="utf-8") + "\n# subprocess\n",
            "subprocess",
        )


@pytest.mark.parametrize("relative", _DEPENDENCIES)
def test_required_dependency_absence_fails(dependency_root, relative):
    from ultimate_ai_agent.distribution.macos.static_policy import (
        macos_distribution_policy_failures,
    )

    (dependency_root / relative).unlink()
    assert macos_distribution_policy_failures(dependency_root) == [
        f"{relative}: required distribution dependency is unavailable"
    ]


@pytest.mark.parametrize("relative", _DEPENDENCIES)
@pytest.mark.parametrize("byte_change", ["comment", "line-endings"])
def test_dependency_exact_source_pin_rejects_non_behavioral_byte_drift(
    dependency_root, relative, byte_change
):
    from ultimate_ai_agent.distribution.macos.static_policy import (
        macos_distribution_policy_failures,
    )

    target = dependency_root / relative
    source = target.read_bytes()
    mutated = source + b"\n# drift\n" if byte_change == "comment" else source.replace(b"\n", b"\r\n")
    assert mutated != source
    target.write_bytes(mutated)
    assert macos_distribution_policy_failures(dependency_root) == [
        f"{relative}: reviewed dependency source digest changed"
    ]


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('"UAA_FINANCE_STARTUP_MODE"', '"UNREVIEWED_ENVIRONMENT_NAME"'),
        (
            "    FINANCE_STARTUP_MODE_ENV,\n)",
            '    FINANCE_STARTUP_MODE_ENV,\n    "UNREVIEWED_ENVIRONMENT_NAME",\n)',
        ),
        (
            "{name: environ[name] for name in FINANCE_STARTUP_ENV_NAMES if name in environ}",
            "dict(environ)",
        ),
        ("from collections.abc import Mapping", "from collections.abc import *"),
        ("import json", "import json\nimport os"),
        ("import json", "import json as other_json"),
        ("import json", "import json\nfrom pathlib import Path"),
        ("    encoded = json.dumps(", '    print(environ)\n    encoded = json.dumps('),
        ("import json", 'import json\n__import__("os").getcwd()'),
        ("    return {name: environ[name]", "    return {name: str(environ[name])"),
        ("    return {name: environ[name]", '    return {name: environ.get(name, "")'),
        ("def finance_startup_environment(", "@print\ndef finance_startup_environment("),
    ],
    ids=[
        "changed-key", "added-key", "whole-environment", "wildcard-import",
        "host-import", "aliased-import", "filesystem-import", "payload-output",
        "dynamic-host-call", "value-coercion", "altered-empty-semantics", "decorator",
    ],
)
def test_helper_closed_behavior_rejects_drift_even_after_repinning(
    dependency_root, monkeypatch, old, new
):
    import hashlib

    from ultimate_ai_agent.distribution.macos import static_policy

    helper = dependency_root / _HELPER
    source = helper.read_text(encoding="utf-8")
    mutated = source.replace(old, new)
    assert mutated != source
    helper.write_text(mutated, encoding="utf-8")
    monkeypatch.setitem(
        static_policy._EXPECTED_DEPENDENCY_SHA256,
        _HELPER,
        hashlib.sha256(mutated.encode("utf-8")).hexdigest(),
    )
    assert static_policy.macos_distribution_policy_failures(dependency_root) == [
        f"{_HELPER}: reviewed dependency implementation changed"
    ]


@pytest.mark.parametrize(
    "added_source",
    ["import os\n", 'print("side effect")\n', 'def deferred():\n    return "added"\n'],
    ids=["import", "call", "definition"],
)
def test_imported_core_initializer_remains_inert_after_repinning(
    dependency_root, monkeypatch, added_source
):
    import hashlib

    from ultimate_ai_agent.distribution.macos import static_policy

    target = dependency_root / _INITIALIZER
    mutated = target.read_text(encoding="utf-8") + added_source
    target.write_text(mutated, encoding="utf-8")
    monkeypatch.setitem(
        static_policy._EXPECTED_DEPENDENCY_SHA256,
        _INITIALIZER,
        hashlib.sha256(mutated.encode("utf-8")).hexdigest(),
    )
    assert static_policy.macos_distribution_policy_failures(dependency_root) == [
        f"{_INITIALIZER}: reviewed dependency implementation changed"
    ]


@pytest.mark.parametrize("relative", [_PROFILE, _PRIVATE_PATH, _PACKAGE])
def test_stdlib_dependency_behavior_stays_closed_after_only_source_repinning(
    dependency_root, monkeypatch, relative,
):
    import hashlib
    from ultimate_ai_agent.distribution.macos import static_policy

    target = dependency_root / relative
    mutated = target.read_text(encoding="utf-8") + '\nprint("unexpected startup side effect")\n'
    target.write_text(mutated, encoding="utf-8")
    monkeypatch.setitem(static_policy._EXPECTED_DEPENDENCY_SHA256, relative, hashlib.sha256(mutated.encode()).hexdigest())
    assert static_policy._distribution_dependency_policy_failures(relative, mutated) == [
        f"{relative}: reviewed dependency implementation changed"
    ]


@pytest.mark.parametrize("relative", _DEPENDENCIES)
@pytest.mark.parametrize(
    "data", [b"\xff", b"this is not valid Python !!!"], ids=["invalid-utf8", "invalid-python"]
)
def test_unreadable_dependency_fails_with_content_free_diagnostic(
    dependency_root, relative, data
):
    from ultimate_ai_agent.distribution.macos.static_policy import (
        macos_distribution_policy_failures,
    )

    (dependency_root / relative).write_bytes(data)
    failures = macos_distribution_policy_failures(dependency_root)
    assert failures
    assert all(failure.startswith(f"{relative}: ") for failure in failures)
    assert all(str(dependency_root) not in failure for failure in failures)
    assert all("this is not valid Python" not in failure for failure in failures)


def test_dependency_ast_pin_normalizes_only_empty_type_parameter_schema():
    import ast
    import copy
    from ultimate_ai_agent.distribution.macos.static_policy import _dependency_ast_sha256

    source = "class Example:\n    def method(self):\n        return b'bytes', 1.5, 2j, ...\n"
    modern = ast.parse(source)
    for node in ast.walk(modern):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            node._fields = (*tuple(field for field in node._fields if field != "type_params"), "type_params")
            node.type_params = []
    legacy = copy.deepcopy(modern)
    for node in ast.walk(legacy):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            node._fields = tuple(field for field in node._fields if field != "type_params")
    assert _dependency_ast_sha256(modern) == _dependency_ast_sha256(legacy)
    modern.body[0].type_params = [ast.Name(id="ChangedGeneric", ctx=ast.Load())]
    assert _dependency_ast_sha256(modern) != _dependency_ast_sha256(legacy)
