from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from ultimate_ai_agent.core.prompt_compiler import compiler as compiler_module
from ultimate_ai_agent.core.prompt_compiler import (
    PromptCompilationError,
    PromptCompilationReceipt,
    PromptModuleCompiler,
    PromptModuleDefinition,
    PromptModuleKind,
    PromptModuleManifest,
    PromptStabilityTier,
    PromptVariableDefinition,
    PromptVariableType,
    prompt_module_manifest_schema_errors,
)


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "dev" / "uaa_prompt_compiler.py"
SCHEMA = ROOT / "docs" / "schemas" / "prompt_module_manifest.schema.json"
FOUNDATION_MANIFEST = (
    ROOT
    / "docs"
    / "prompts"
    / "uaa_runtime_capability_foundation"
    / "prompt_module_manifest.json"
)


def _module(
    module_id: str,
    source_ref: str,
    *,
    dependencies: list[str] | None = None,
    required_variables: list[str] | None = None,
) -> PromptModuleDefinition:
    return PromptModuleDefinition(
        module_id=module_id,
        source_ref=source_ref,
        kind=PromptModuleKind.developer,
        stability_tier=PromptStabilityTier.stable_control_plane,
        dependencies=dependencies or [],
        required_variables=required_variables or [],
    )


def _manifest(
    modules: list[PromptModuleDefinition],
    *,
    entries: list[str],
    variables: dict[str, PromptVariableDefinition] | None = None,
    max_module_bytes: int = 262_144,
    max_compiled_bytes: int = 2_097_152,
) -> PromptModuleManifest:
    return PromptModuleManifest(
        schema_ref="../../schemas/prompt_module_manifest.schema.json",
        schema_version="uaa.prompt_module_bundle.v1",
        bundle_id="test-prompt-bundle",
        version="1.0.0",
        entry_module_ids=entries,
        variables=variables or {},
        modules=modules,
        max_module_bytes=max_module_bytes,
        max_compiled_bytes=max_compiled_bytes,
        stable_within_run=True,
    )


def _write(tmp_path: Path, name: str, text: str) -> str:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return name


def _error_code(
    compiler: PromptModuleCompiler,
    manifest: PromptModuleManifest,
    **kwargs: Any,
) -> str:
    with pytest.raises(PromptCompilationError) as raised:
        compiler.compile(manifest, **kwargs)
    return raised.value.reason_code


def test_compilation_is_deterministic_and_dependencies_precede_dependents(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "a.md", "A")
    _write(tmp_path, "b.md", "B")
    _write(tmp_path, "final.md", "FINAL")
    manifest = _manifest(
        [
            _module("final", "final.md", dependencies=["b", "a"]),
            _module("b", "b.md"),
            _module("a", "a.md"),
        ],
        entries=["final"],
    )
    compiler = PromptModuleCompiler(tmp_path)

    first = compiler.compile(manifest)
    second = compiler.compile(manifest)

    assert first == second
    assert first.receipt.ordered_module_ids == ("a", "b", "final")
    assert first.content.index("\nA\n") < first.content.index("\nB\n")
    assert first.content.index("\nB\n") < first.content.index("\nFINAL\n")
    assert first.receipt.compiled_artifact_hash.startswith("sha256:")


def test_compilation_preserves_source_trailing_whitespace(tmp_path: Path) -> None:
    source = "Markdown line break  \n\n"
    _write(tmp_path, "source.md", source)
    manifest = _manifest([_module("source", "source.md")], entries=["source"])

    artifact = PromptModuleCompiler(tmp_path).compile(manifest)

    assert f"<!-- BEGIN source source.md -->\n{source}<!-- END source -->" in (
        artifact.content
    )


def test_entry_selection_loads_only_transitive_dependencies(tmp_path: Path) -> None:
    _write(tmp_path, "base.md", "BASE")
    _write(tmp_path, "selected.md", "SELECTED")
    _write(tmp_path, "unused.md", "{{ unused_secret }}")
    manifest = _manifest(
        [
            _module("base", "base.md"),
            _module("selected", "selected.md", dependencies=["base"]),
            _module("unused", "unused.md", required_variables=["unused_secret"]),
        ],
        entries=["selected"],
        variables={
            "unused_secret": PromptVariableDefinition(type=PromptVariableType.string)
        },
    )

    artifact = PromptModuleCompiler(tmp_path).compile(manifest)

    assert artifact.receipt.ordered_module_ids == ("base", "selected")
    assert "unused" not in artifact.content


def test_unselected_symlink_source_fails_path_guards(tmp_path: Path) -> None:
    _write(tmp_path, "selected.md", "SELECTED")
    _write(tmp_path, "target.md", "UNSELECTED")
    link = tmp_path / "unused.md"
    try:
        link.symlink_to(tmp_path / "target.md")
    except OSError:
        pytest.skip("symlinks are unavailable")
    manifest = _manifest(
        [
            _module("selected", "selected.md"),
            _module("unused", "unused.md"),
        ],
        entries=["selected"],
    )

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_SOURCE_PATH_UNSAFE"
    )


def test_inactive_conditional_branch_does_not_require_its_value(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "conditional.md",
        "{% if include_secret %}{{ secret }}{% else %}safe{% endif %}",
    )
    manifest = _manifest(
        [
            _module(
                "conditional",
                "conditional.md",
                required_variables=["include_secret"],
            )
        ],
        entries=["conditional"],
        variables={
            "include_secret": PromptVariableDefinition(type=PromptVariableType.boolean),
            "secret": PromptVariableDefinition(type=PromptVariableType.string),
        },
    )

    artifact = PromptModuleCompiler(tmp_path).compile(
        manifest,
        variables={"include_secret": False},
    )

    assert "\nsafe\n" in artifact.content


def test_missing_dependency_and_global_cycle_fail_closed(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "A")
    _write(tmp_path, "b.md", "B")
    compiler = PromptModuleCompiler(tmp_path)

    missing = _manifest(
        [_module("a", "a.md", dependencies=["missing"])],
        entries=["a"],
    )
    assert _error_code(compiler, missing) == "PROMPT_DEPENDENCY_MISSING"

    with pytest.raises(ValueError, match="cannot depend on itself"):
        _manifest(
            [
                _module("a", "a.md"),
                _module("b", "b.md", dependencies=["b"]),
            ],
            entries=["a"],
        )

    indirect_cycle = _manifest(
        [
            _module("a", "a.md"),
            _module("b", "b.md", dependencies=["c"]),
            _module("c", "a.md", dependencies=["b"]),
        ],
        entries=["a"],
    )
    assert _error_code(compiler, indirect_cycle) == "PROMPT_DEPENDENCY_CYCLE"


def test_reverse_dependency_inspection_reports_blast_radius(tmp_path: Path) -> None:
    for name in ("base", "one", "two", "other"):
        _write(tmp_path, f"{name}.md", name)
    manifest = _manifest(
        [
            _module("base", "base.md"),
            _module("one", "one.md", dependencies=["base"]),
            _module("two", "two.md", dependencies=["one"]),
            _module("other", "other.md"),
        ],
        entries=["two"],
    )

    inspection = PromptModuleCompiler(tmp_path).inspect(
        manifest,
        changed_module_ids=["base"],
    )

    assert inspection.resolved_module_ids == ["base", "one", "two"]
    assert inspection.reverse_dependencies["base"] == ["one"]
    assert inspection.impacted_module_ids == ["base", "one", "two"]


def test_strict_variables_and_conditions_render_without_receipt_leak(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path,
        "template.md",
        "Hello {{ operator }}.\n{% if include_detail %}Detail {{ count }}."
        "{% else %}No detail.{% endif %}",
    )
    variables = {
        "operator": PromptVariableDefinition(type=PromptVariableType.string),
        "include_detail": PromptVariableDefinition(type=PromptVariableType.boolean),
        "count": PromptVariableDefinition(
            type=PromptVariableType.integer,
            allowed_values=[1, 2, 3],
        ),
    }
    manifest = _manifest(
        [
            _module(
                "template",
                "template.md",
                required_variables=["operator", "include_detail", "count"],
            )
        ],
        entries=["template"],
        variables=variables,
    )
    secret_value = "receipt-must-not-contain-this-value"

    artifact = PromptModuleCompiler(tmp_path).compile(
        manifest,
        variables={"operator": secret_value, "include_detail": True, "count": 2},
    )

    assert f"Hello {secret_value}." in artifact.content
    assert "Detail 2." in artifact.content
    receipt_json = artifact.receipt.model_dump_json()
    assert secret_value not in receipt_json
    assert artifact.receipt.supplied_variable_names == (
        "count",
        "include_detail",
        "operator",
    )
    assert artifact.receipt.raw_prompt_included is False
    assert artifact.receipt.variable_values_included is False
    assert artifact.receipt.manifest_contract_hash.startswith("sha256:")


def test_safe_authority_flags_are_required_in_durable_receipts(tmp_path: Path) -> None:
    _write(tmp_path, "source.md", "source")
    manifest = _manifest([_module("source", "source.md")], entries=["source"])
    payload = (
        PromptModuleCompiler(tmp_path).compile(manifest).receipt.model_dump(mode="json")
    )
    payload.pop("automatic_pr_creation")

    with pytest.raises(ValueError):
        PromptCompilationReceipt.model_validate(payload)


@pytest.mark.parametrize(
    ("variables", "expected_code"),
    [
        ({"unknown": "value"}, "PROMPT_VARIABLE_UNKNOWN"),
        ({"name": 3}, "PROMPT_VARIABLE_TYPE_INVALID"),
        ({}, "PROMPT_MODULE_VARIABLE_REQUIRED"),
    ],
)
def test_variable_contract_failures_are_stable(
    tmp_path: Path,
    variables: dict[str, Any],
    expected_code: str,
) -> None:
    _write(tmp_path, "template.md", "{{ name }}")
    manifest = _manifest(
        [_module("template", "template.md", required_variables=["name"])],
        entries=["template"],
        variables={"name": PromptVariableDefinition(type=PromptVariableType.string)},
    )

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest, variables=variables)
        == expected_code
    )


@pytest.mark.parametrize(
    ("definition", "value", "expected_code"),
    [
        (
            PromptVariableDefinition(type=PromptVariableType.string, max_length=4),
            "12345",
            "PROMPT_VARIABLE_BUDGET_EXCEEDED",
        ),
        (
            PromptVariableDefinition(type=PromptVariableType.string),
            "{{ reserved }}",
            "PROMPT_VARIABLE_CONTROL_TOKEN",
        ),
    ],
)
def test_string_variable_budget_and_control_tokens_fail_closed(
    tmp_path: Path,
    definition: PromptVariableDefinition,
    value: str,
    expected_code: str,
) -> None:
    _write(tmp_path, "template.md", "{{ value }}")
    manifest = _manifest(
        [_module("template", "template.md", required_variables=["value"])],
        entries=["template"],
        variables={"value": definition},
    )

    assert (
        _error_code(
            PromptModuleCompiler(tmp_path),
            manifest,
            variables={"value": value},
        )
        == expected_code
    )


def test_explicit_null_variable_does_not_clear_typed_default(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "template.md", "{{ value }}")
    manifest = _manifest(
        [_module("template", "template.md", required_variables=["value"])],
        entries=["template"],
        variables={
            "value": PromptVariableDefinition(
                type=PromptVariableType.string,
                required=False,
                default="reviewed-default",
            )
        },
    )

    assert (
        _error_code(
            PromptModuleCompiler(tmp_path),
            manifest,
            variables={"value": None},
        )
        == "PROMPT_VARIABLE_TYPE_INVALID"
    )

def test_variable_defaults_and_allowed_values_obey_declared_budget() -> None:
    with pytest.raises(ValueError, match="default exceeds max_length"):
        PromptVariableDefinition(
            type=PromptVariableType.string,
            default="too-long",
            max_length=4,
        )
    with pytest.raises(ValueError, match="allowed string variable value"):
        PromptVariableDefinition(
            type=PromptVariableType.string,
            allowed_values=["too-long"],
            max_length=4,
        )
    with pytest.raises(ValueError, match="duplicate allowed"):
        PromptVariableDefinition(
            type=PromptVariableType.integer,
            allowed_values=[1, 1],
        )

def test_undeclared_template_variable_and_non_boolean_condition_are_rejected(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "undeclared.md", "{{ not_declared }}")
    undeclared = _manifest(
        [_module("template", "undeclared.md")],
        entries=["template"],
    )
    compiler = PromptModuleCompiler(tmp_path)
    assert _error_code(compiler, undeclared) == "PROMPT_TEMPLATE_VARIABLE_UNDECLARED"

    _write(tmp_path, "condition.md", "{% if label %}yes{% endif %}")
    wrong_condition = _manifest(
        [_module("template", "condition.md", required_variables=["label"])],
        entries=["template"],
        variables={"label": PromptVariableDefinition(type=PromptVariableType.string)},
    )
    assert (
        _error_code(compiler, wrong_condition, variables={"label": "yes"})
        == "PROMPT_CONDITION_TYPE_INVALID"
    )


def test_source_path_and_size_budgets_fail_closed(tmp_path: Path) -> None:
    _write(tmp_path, "small.md", "12345")
    compiler = PromptModuleCompiler(tmp_path)
    traversal = _manifest(
        [_module("unsafe", "safe/../../outside.md")],
        entries=["unsafe"],
    )
    assert _error_code(compiler, traversal) == "PROMPT_SOURCE_PATH_UNSAFE"

    too_large = _manifest(
        [_module("large", "small.md")],
        entries=["large"],
        max_module_bytes=4,
    )
    assert _error_code(compiler, too_large) == "PROMPT_MODULE_BUDGET_EXCEEDED"

    compiled_too_large = _manifest(
        [_module("large", "small.md")],
        entries=["large"],
        max_compiled_bytes=10,
    )
    assert (
        _error_code(compiler, compiled_too_large) == "PROMPT_COMPILED_BUDGET_EXCEEDED"
    )


@pytest.mark.parametrize(
    "unsafe_ref",
    ("safe/../../outside.md", "safe/../outside.md"),
)
def test_unselected_unsafe_source_ref_fails_closed(
    tmp_path: Path,
    unsafe_ref: str,
) -> None:
    _write(tmp_path, "selected.md", "selected")
    manifest = _manifest(
        [
            _module("selected", "selected.md"),
            _module("unsafe", unsafe_ref),
        ],
        entries=["selected"],
    )

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_SOURCE_PATH_UNSAFE"
    )


def test_raw_dot_segment_source_ref_fails_before_path_normalization(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "safe/module.md", "content")
    manifest = _manifest(
        [_module("module", "safe/./module.md")],
        entries=["module"],
    )

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_SOURCE_PATH_UNSAFE"
    )


def test_render_expansion_is_bounded_before_artifact_assembly(tmp_path: Path) -> None:
    _write(tmp_path, "template.md", "{{ value }}" * 128)
    manifest = _manifest(
        [_module("template", "template.md", required_variables=["value"])],
        entries=["template"],
        variables={
            "value": PromptVariableDefinition(
                type=PromptVariableType.string,
                max_length=1024,
            )
        },
        max_compiled_bytes=512,
    )

    assert (
        _error_code(
            PromptModuleCompiler(tmp_path),
            manifest,
            variables={"value": "x" * 1024},
        )
        == "PROMPT_COMPILED_BUDGET_EXCEEDED"
    )


def test_manifest_policy_changes_are_visible_in_receipt_hash(tmp_path: Path) -> None:
    _write(tmp_path, "source.md", "same source")
    compiler = PromptModuleCompiler(tmp_path)
    first = _manifest(
        [_module("source", "source.md")],
        entries=["source"],
        max_compiled_bytes=1000,
    )
    second = _manifest(
        [_module("source", "source.md")],
        entries=["source"],
        max_compiled_bytes=2000,
    )

    first_receipt = compiler.compile(first).receipt
    second_receipt = compiler.compile(second).receipt

    assert first_receipt.compiled_artifact_hash == second_receipt.compiled_artifact_hash
    assert first_receipt.manifest_contract_hash != second_receipt.manifest_contract_hash


def test_symlink_source_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.md"
    target.write_text("target", encoding="utf-8")
    link = tmp_path / "link.md"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks are unavailable")
    manifest = _manifest([_module("linked", "link.md")], entries=["linked"])

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_SOURCE_PATH_UNSAFE"
    )


def test_symlink_source_parent_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "source.md").write_text("target", encoding="utf-8")
    link = tmp_path / "linked-parent"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable")
    manifest = _manifest(
        [_module("linked", "linked-parent/source.md")],
        entries=["linked"],
    )

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_SOURCE_PATH_UNSAFE"
    )


def test_symlink_manifest_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "source.md", "source")
    manifest = _manifest([_module("source", "source.md")], entries=["source"])
    target = tmp_path / "manifest.json"
    target.write_text(
        json.dumps(manifest.model_dump(mode="json", by_alias=True)),
        encoding="utf-8",
    )
    link = tmp_path / "manifest-link.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks are unavailable")

    with pytest.raises(PromptCompilationError) as raised:
        PromptModuleCompiler(tmp_path).load_manifest(link)

    assert raised.value.reason_code == "PROMPT_MANIFEST_PATH_UNSAFE"


def test_manifest_read_is_bounded_and_repository_anchored(tmp_path: Path) -> None:
    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b"{" + b" " * 1_048_576 + b"}")
    compiler = PromptModuleCompiler(tmp_path)

    with pytest.raises(PromptCompilationError) as oversized_error:
        compiler.load_manifest(oversized)
    assert oversized_error.value.reason_code == "PROMPT_MANIFEST_BUDGET_EXCEEDED"

    outside = tmp_path.parent / f"{tmp_path.name}-outside-manifest.json"
    outside.write_text("{}", encoding="utf-8")
    try:
        with pytest.raises(PromptCompilationError) as outside_error:
            compiler.load_manifest(outside)
        assert outside_error.value.reason_code == "PROMPT_MANIFEST_PATH_UNSAFE"
    finally:
        outside.unlink()


def test_missing_source_is_reported_as_unavailable(tmp_path: Path) -> None:
    manifest = _manifest([_module("missing", "missing.md")], entries=["missing"])

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_SOURCE_UNAVAILABLE"
    )


@pytest.mark.parametrize("coerced_field", ("required", "max_module_bytes"))
def test_manifest_scalar_coercion_fails_closed(
    tmp_path: Path,
    coerced_field: str,
) -> None:
    _write(tmp_path, "source.md", "{{ value }}")
    manifest = _manifest(
        [_module("source", "source.md", required_variables=["value"])],
        entries=["source"],
        variables={
            "value": PromptVariableDefinition(
                type=PromptVariableType.string,
                required=False,
            )
        },
    )
    payload = manifest.model_dump(mode="json", by_alias=True)
    if coerced_field == "required":
        payload["variables"]["value"]["required"] = "false"
    else:
        payload["max_module_bytes"] = "262144"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PromptCompilationError) as raised:
        PromptModuleCompiler(tmp_path).load_manifest(path)

    assert raised.value.reason_code == "PROMPT_MANIFEST_INVALID"


def test_source_path_substitution_during_read_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.md"
    source.write_text("original", encoding="utf-8")
    manifest = _manifest([_module("source", "source.md")], entries=["source"])
    original_read = compiler_module.os.read
    replaced = False

    def replacing_read(descriptor: int, byte_count: int) -> bytes:
        nonlocal replaced
        chunk = original_read(descriptor, byte_count)
        if chunk and not replaced:
            source.replace(tmp_path / "original.md")
            source.write_text("replaced", encoding="utf-8")
            replaced = True
        return chunk

    monkeypatch.setattr(compiler_module.os, "read", replacing_read)

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_SOURCE_UNAVAILABLE"
    )


def test_source_parent_substitution_during_read_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "nested"
    parent.mkdir()
    source = parent / "source.md"
    source.write_text("original", encoding="utf-8")
    manifest = _manifest(
        [_module("source", "nested/source.md")],
        entries=["source"],
    )
    original_read = compiler_module.os.read
    replaced = False

    def replacing_read(descriptor: int, byte_count: int) -> bytes:
        nonlocal replaced
        chunk = original_read(descriptor, byte_count)
        if chunk and not replaced:
            parent.replace(tmp_path / "original-parent")
            parent.mkdir()
            (parent / "source.md").write_text("replaced", encoding="utf-8")
            replaced = True
        return chunk

    monkeypatch.setattr(compiler_module.os, "read", replacing_read)

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_SOURCE_UNAVAILABLE"
    )


def test_source_in_place_edit_with_restored_mtime_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.md"
    source.write_text("original", encoding="utf-8")
    original_stat = source.stat()
    manifest = _manifest([_module("source", "source.md")], entries=["source"])
    original_read = compiler_module.os.read
    changed = False

    def changing_read(descriptor: int, byte_count: int) -> bytes:
        nonlocal changed
        chunk = original_read(descriptor, byte_count)
        if chunk and not changed:
            source.write_text("changed!", encoding="utf-8")
            compiler_module.os.utime(
                source,
                ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
            )
            changed = True
        return chunk

    monkeypatch.setattr(compiler_module.os, "read", changing_read)

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_SOURCE_UNAVAILABLE"
    )


def test_nul_content_cannot_enter_shell_safe_compilation(tmp_path: Path) -> None:
    _write(tmp_path, "source.md", "unsafe\x00content")
    manifest = _manifest([_module("source", "source.md")], entries=["source"])

    assert (
        _error_code(PromptModuleCompiler(tmp_path), manifest)
        == "PROMPT_MODULE_CONTENT_INVALID"
    )


def test_prompt_artifact_repr_redacts_content_and_contracts_are_frozen(
    tmp_path: Path,
) -> None:
    secret = "raw-prompt-must-not-appear-in-repr"
    _write(tmp_path, "source.md", secret)
    manifest = _manifest([_module("source", "source.md")], entries=["source"])

    artifact = PromptModuleCompiler(tmp_path).compile(manifest)

    assert secret not in repr(artifact)
    with pytest.raises(ValidationError, match="frozen"):
        artifact.receipt.runtime_model_calls = True  # type: ignore[misc]
    for field_name in (
        "entry_module_ids",
        "ordered_module_ids",
        "source_receipts",
        "supplied_variable_names",
    ):
        collection = getattr(artifact.receipt, field_name)
        assert isinstance(collection, tuple)
        with pytest.raises(AttributeError):
            collection.append("tampered")


def test_schema_accepts_dogfooded_foundation_manifest() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    manifest = json.loads(FOUNDATION_MANIFEST.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(manifest)


@pytest.mark.parametrize(
    ("variable_type", "default", "allowed_values"),
    [
        ("string", 1, ["valid"]),
        ("integer", "invalid", [1]),
        ("boolean", 1, [True]),
        ("string", "valid", [1]),
        ("integer", 1, ["invalid"]),
        ("boolean", True, ["invalid"]),
    ],
)
def test_schema_rejects_variable_type_contract_mismatches(
    variable_type: str,
    default: str | int | bool,
    allowed_values: list[str | int | bool],
) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    manifest = json.loads(FOUNDATION_MANIFEST.read_text(encoding="utf-8"))
    manifest["variables"] = {
        "value": {
            "type": variable_type,
            "default": default,
            "allowed_values": allowed_values,
        }
    }

    assert list(Draft202012Validator(schema).iter_errors(manifest))


@pytest.mark.parametrize(
    "source_ref",
    ("safe/../outside.md", "safe/../../outside.md"),
)
def test_schema_rejects_traversing_source_refs(source_ref: str) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    manifest = json.loads(FOUNDATION_MANIFEST.read_text(encoding="utf-8"))
    manifest["modules"][0]["source_ref"] = source_ref

    assert list(Draft202012Validator(schema).iter_errors(manifest))


def test_schema_contract_rejects_duplicate_allowed_values() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    manifest = json.loads(FOUNDATION_MANIFEST.read_text(encoding="utf-8"))
    manifest["variables"] = {
        "value": {
            "type": "string",
            "allowed_values": ["duplicate", "duplicate"],
        }
    }

    assert prompt_module_manifest_schema_errors(schema, manifest)


def test_schema_contract_rejects_duplicate_module_ids() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    manifest = json.loads(FOUNDATION_MANIFEST.read_text(encoding="utf-8"))
    duplicate = dict(manifest["modules"][0])
    duplicate["source_ref"] = manifest["modules"][1]["source_ref"]
    manifest["modules"].append(duplicate)

    assert prompt_module_manifest_schema_errors(schema, manifest)


def test_cli_compiles_checks_golden_and_never_prints_prompt_text(
    tmp_path: Path,
) -> None:
    output = tmp_path / "compiled.md"
    receipt = tmp_path / "receipt.json"
    prompt_fragment = "W19 extension/plugin callable graduation"

    first = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "compile",
            "--manifest",
            str(FOUNDATION_MANIFEST),
            "--output",
            str(output),
            "--receipt",
            str(receipt),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    checked = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "compile",
            "--manifest",
            str(FOUNDATION_MANIFEST),
            "--check-receipt",
            str(receipt),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert prompt_fragment in output.read_text(encoding="utf-8")
    assert prompt_fragment not in first.stdout
    assert prompt_fragment not in checked.stdout
    assert json.loads(checked.stdout)["golden_receipt_verified"] is True
