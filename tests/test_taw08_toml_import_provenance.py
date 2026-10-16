from __future__ import annotations

import ast
from pathlib import Path

import pytest

from scripts import verify_tool_aware_cognition_taw08 as verifier
from scripts.verification import test_corpus_guard as guard


SOURCE = Path(verifier.__file__)


def _analysis(source: str):
    def unresolved_external(_module: str) -> None:
        return None

    setattr(unresolved_external, "_uaa_runtime_consumer", True)
    return guard._python_binding_module_analysis(
        "scripts.verify_tool_aware_cognition_taw08",
        "path=scripts/verify_tool_aware_cognition_taw08.py\n" + source,
        unresolved_external,
    )


@pytest.mark.parametrize(
    "owner", ("verify_locked_evaluator_environment", "_materialize_locked_environment")
)
def test_strict_consumer_analysis_has_distinct_toml_import_owners(owner: str) -> None:
    analysis = _analysis(SOURCE.read_text(encoding="utf-8"))
    node = next(
        node
        for node in analysis.tree.body
        if isinstance(node, ast.FunctionDef) and node.name == owner
    )
    facts = guard._python_binding_node_analysis(analysis, node)
    assert "tomllib" in facts.local_dependency_names
    assert analysis.imported_modules["_stdlib_toml"] == ("tomllib",)
    assert analysis.imported_modules["_backport_toml"] == ("tomli",)
    assert "tomllib" not in analysis.imported_modules


@pytest.mark.parametrize("producer", ("tomllib", "tomli"))
def test_public_alias_provenance_binds_both_import_producers(producer: str) -> None:
    source = SOURCE.read_text(encoding="utf-8")
    changed = source.replace(
        f"import {producer} as ", f"import changed_{producer} as ", 1
    )
    assert source != changed
    original_analysis = _analysis(source)
    changed_analysis = _analysis(changed)

    def identity(analysis):
        return guard._python_local_binding_identity(
            "tomllib", analysis.module_bindings, analysis.imported_modules, {}
        )

    assert identity(original_analysis) != identity(changed_analysis)
